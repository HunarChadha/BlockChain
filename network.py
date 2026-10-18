import argparse #Lets user pass arguments from the terminal
import secrets #Generates random values suitable for security-related purposes, such as cryptographic keys.
import trio
from multiaddr import Multiaddr
import json

from libp2p import new_host #A host is the networking component representing your local peer
from libp2p.crypto.secp256k1 import create_new_key_pair #cryptographic key pair using the secp256k1 elliptic curve, a key pair contains: private and public key
from libp2p.peer.peerinfo import info_from_p2p_addr #takes a multiaddress that includes a peer ID and converts it into a PeerInfo object (object that contains the information libp2p needs to identify and and contact destination peer)
from libp2p.utils.address_validation import (
    get_available_interfaces, #prepares listening addresses for the host.
    get_optimal_binding_address, #provides a suitable address to advertise to another node.
)
from libp2p.custom_types import TProtocol #TProtocol represents a protocol identifier in the form expected by libp2p. We're using it to identify our echo protocol.
from libp2p.network.stream.exceptions import StreamEOF #An exception associated with reaching the end of a stream. We import it so we can handle that situation separately from other errors.
from libp2p.network.stream.net_stream import INetStream #INetStream is a type describing the stream interface our handler works with.

PROTOCOL_ID = TProtocol("/echo/1.0.0") #This is the name of our protocol, echo describes what it does: return received data and 1.0.0 is the version label.
MAX_READ_LEN = 1024 #We're using this as the maximum number of bytes requested in a single read. 

#Runs on the receiving side. It waits for incoming messages and sends them back.
async def echo_stream_handler(stream: INetStream) -> None: #stream is the channel used to exchange a particular kind of data during the connection between our nodes." -> None" means the function isn't intended to return a value to its caller.
    buffer = b"" #buffer stores the bytes we've received so far, but doesn't yet form a complete message.

    try:
        peer_id = stream.muxed_conn.peer_id #stream.muxed_conn provides access to the underlying multiplexed connection (see docs). Its peer_id identifies the remote peer associated with that connection. 
        print(f"Received stream from peer: {peer_id}")

        while True:
            chunk = await stream.read(1024) #chunk is the next piece of data received from the network.

            if not chunk:
                break

            buffer += chunk #adds the new bytes to anything already waiting.

            while b"\n" in buffer: #lets the handler process multiple complete messages, even if they arrive together, separated by delimiter "\n"
                message, buffer = buffer.split(b"\n", 1) #separates the first complete message from the remaining bytes.

                text = message.decode("utf-8")
                try:
                    data = json.loads(text)
                    if data.get("type") == "transaction":
                         transaction = data.get("transaction")
                         if not isinstance(transaction, dict):
                             print("Rejected: transaction must be a JSON object.")
                         elif not all(key in transaction for key in ("from", "to", "amount", "nonce")):
                             print("Rejected: transaction is missing required fields.")
                         else:
                             print(f"Received transaction: {transaction}")
                    else:
                        print(f"Received JSON: {data}")
                except json.JSONDecodeError:
                    print(f"Received text: {text}")
                    #now it can distinguish a transaction message from other json messages.

                await stream.write(message + b"\n") #sends the same bytes to the sender
                #This is called an echo handler because it repeats the received message to whoever sent it.
        
    except StreamEOF: #An EOF-related condition indicates that the stream has reached its end. The exact behavior depends on how the other side closes or finishes the stream.
        print("The other peer closed the stream.")

    except Exception as error:
        print(f"Error handling message: {error}")

    finally:
        await stream.close()



#runs on the sending side. It reads the reply and figures out when the complete message has arrived.
async def read_line(stream: INetStream, buffer: bytearray) -> bytes: #bytearray is a mutable collection of bytes, so we can add and remove data without creating a new buffer every time.
    while b"\n" not in buffer:
        chunk = await stream.read(1024) 

        if not chunk:
            break

        buffer.extend(chunk) #stores incoming data

    if b"\n" not in buffer:
        return b""

    newline_index = buffer.index(b"\n") #finds the position of first new line
    message = bytes(buffer[:newline_index]) #selects everything from the beginning of the buffer up to, but not including, the newline.
    del buffer[:newline_index + 1] #removes the message we just read, including its newline, while preserving any additional data already received.

    return message #gives the caller one complete message without its newline.
        


async def main(port: int, peer_address: str | None):
    # Create this node's identity
    key_pair = create_new_key_pair(secrets.token_bytes(32))
    host = new_host(key_pair=key_pair)

    # Prepare the listening addresses
    listen_addrs = get_available_interfaces(port)

    # Start the host
    async with host.run(listen_addrs=listen_addrs):
        peer_id = host.get_id().to_string()
        
        host.set_stream_handler(PROTOCOL_ID, echo_stream_handler) #Whenever a peer opens a stream using /echo/1.0.0, pass that stream to echo_stream_handler()

        print(f"Node started on port {port}")
        print(f"Peer ID: {peer_id}")

        if peer_address:
            # Connect to another peer
            address = Multiaddr(peer_address)
            peer_info = info_from_p2p_addr(address)

            await host.connect(peer_info) #establishes the peer connection;

            print(f"Connected to peer: {peer_info.peer_id}")

            #Open a stream using our echo protocol
            stream = await host.new_stream(peer_info.peer_id, [PROTOCOL_ID]) #opens a stream over which we can exchange application data.

            #Sends and receives messages
            buffer = bytearray()

            try:
                while True:
                    message_text = input("Enter your message (or 'quit' to exit): ")

                    if message_text.lower() == "quit":
                        break

                    message = message_text.encode("utf-8") + b"\n" #marks the end of the message.
                    await stream.write(message)
 
                    response = await read_line(stream, buffer) #Reads incoming bytes until it has one complete newline-terminated message, then stores that message in response.
                    if not response:
                        print("Other peer has closed the stream.")
                        break
                    
                    print(f"Received reply: {response.decode('utf-8')}")

            finally:
                await stream.close()

            print("Node is staying alive and listening...")
            await trio.sleep_forever()
        
        else:
            # Display the address another node can use
            address = get_optimal_binding_address(port)
            full_address = f"{address}/p2p/{peer_id}"

            print("Waiting for another node to connect.")
            print(f"Peer address: {full_address}")

        await trio.sleep_forever()

''' The above code establishes a connection between two nodes and carry out the excahnge of messages. To test it, in first terminal run this code:
    python network.py --port 8000 
    This will give you the Peer Address of Node A. 
    Now in the second terminal, activate .venv and run this code:
    python network.py --port 8001 --peer "<NODE A's PEER ID>" (for checking the connection only)
    python network.py --port 8001 --peer "<NODE A's address>" (for checking the exchange of message, can sun this only for obth the things though)
    This confirms Node B has established a libp2p connection to Node A. Both nodes should remain running. '''
 


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--peer", type=str, default=None)
    args = parser.parse_args()

    trio.run(main, args.port, args.peer)
