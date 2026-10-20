import argparse #Lets user pass arguments from the terminal
import secrets #Generates random values suitable for security-related purposes, such as cryptographic keys.
import trio
from multiaddr import Multiaddr
import json

from main import verify_transaction

from libp2p import new_host #A host is the networking component representing your local peer
from libp2p.crypto.secp256k1 import create_new_key_pair #cryptographic key pair using the secp256k1 elliptic curve, a key pair contains: private and public key
from libp2p.peer.peerinfo import info_from_p2p_addr #takes a multiaddress that includes a peer ID and converts it into a PeerInfo object (object that contains the information libp2p needs to identify and and contact destination peer)
from libp2p.utils.address_validation import (
    get_available_interfaces, #prepares listening addresses for the host.
    get_optimal_binding_address, #provides a suitable address to advertise to another node.
)
from libp2p.custom_types import TProtocol #TProtocol represents a protocol identifier in the form expected by libp2p. We're using it to identify our protocol.
from libp2p.network.stream.exceptions import StreamEOF #An exception associated with reaching the end of a stream. We import it so we can handle that situation separately from other errors.
from libp2p.network.stream.net_stream import INetStream #INetStream is a type describing the stream interface our handler works with.

TX_PROTOCOL_ID = TProtocol("/blockchain/tx/1.0.0") 
MAX_READ_LEN = 1024 #We're using this as the maximum number of bytes requested in a single read. 
SEEN_TRANSACTIONS = set() #This set will remember which transactions we've already processed, so relayed transactions don't circulate forever.


async def broadcast_tx(host, transaction, exclude_peer=None):
    message = {
        "type": "transaction",
        "transaction": transaction,
    }

    payload = json.dumps(message).encode("utf-8") + b"\n"

    peers = host.get_connected_peers()
    print("Connected peers:", peers)

    for peer_id in peers:
        if peer_id == exclude_peer:
            continue

        try:
            print(f"Attempting broadcast to: {peer_id}")
            stream = await host.new_stream(
                peer_id,
                [TX_PROTOCOL_ID],
            )

            try:
                await stream.write(payload)
                print(f"Broadcast transaction to peer: {peer_id}")
            finally:
                await stream.close()

        except Exception as error:
            print(f"Could not broadcast to {peer_id}: {error}")


def make_transaction_stream_handler(host): #made it a factory function so it can access the current node's host.
    
    #Runs on the receiving side. It waits for incoming messages and sends them back.
    async def transaction_stream_handler(stream: INetStream) -> None: #stream is the channel used to exchange a particular kind of data during the connection between our nodes." -> None" means the function isn't intended to return a value to its caller.
        print("🚨 TRANSACTION HANDLER INVOKED 🚨")
        buffer = b"" #buffer stores the bytes we've received so far, but doesn't yet form a complete message.

        try:
            peer_id = stream.muxed_conn.peer_id #stream.muxed_conn provides access to the underlying multiplexed connection (see docs). Its peer_id identifies the remote peer associated with that connection. 
            print(f"Received stream from peer: {peer_id}")

            while True:
                chunk = await stream.read(MAX_READ_LEN) #chunk is the next piece of data received from the network.

                if not chunk:
                    break

                buffer += chunk #adds the new bytes to anything already waiting.

                while b"\n" in buffer: #lets the handler process multiple complete messages, even if they arrive together, separated by delimiter "\n"
                    message, buffer = buffer.split(b"\n", 1) #separates the first complete message from the remaining bytes.

                    text = message.decode("utf-8")
                    
                    try:
                        data = json.loads(text)
                        if not isinstance(data, dict):
                            print("Rejected: message must be a JSON object.")
                            continue
                        
                        if data.get("type") != "transaction":
                            print("Rejected: unexpected message type.")
                            continue
                            
                        transaction = data.get("transaction")
                        
                        if not isinstance(transaction, dict):
                            print("Rejected: transaction must be a JSON object.")
                            continue

                        if not all (
                            key in transaction
                            for key in ("body", "public_key", "signature")
                        ):
                            print("Rejected: signed transaction is missing fields.")
                            continue
                        
                        if not isinstance(transaction["body"], dict):
                            print("Rejected: transaction body must be an object.")
                            continue
                        
                        if not all(
                            key in transaction["body"]
                            for key in ("from", "to", "amount", "nonce")
                        ):
                            print("Rejected: transaction body is missing fields.")
                            continue

                        try:
                            is_valid = verify_transaction(transaction)
                        except (KeyError, TypeError, ValueError):
                            is_valid = False

                        if not is_valid:
                            print("Rejected: transaction signature is invalid.")
                            continue

                        fingerprint = json.dumps(
                            transaction,
                            sort_keys=True,
                            separators=(",", ":")
                        )

                        if fingerprint in SEEN_TRANSACTIONS:
                            print("Duplicate transaction ignored.")
                            continue

                        SEEN_TRANSACTIONS.add(fingerprint)

                        print(f"Valid signed transaction received: {transaction}")

                        await broadcast_tx(
                            host,
                            transaction,
                            exclude_peer=peer_id
                        )

                    
                    except json.JSONDecodeError:
                        print(f"Received text: {text}")
                        #now it can distinguish a transaction message from other json messages.

            
        except StreamEOF: #An EOF-related condition indicates that the stream has reached its end. The exact behavior depends on how the other side closes or finishes the stream.
            print("The other peer closed the stream.")

        except Exception as error:
            print(f"Error handling message: {error}")

        finally:
            await stream.close()

    return transaction_stream_handler



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
        


async def print_network_status(host):
    print("\n" + "=" * 55)
    print("             NODE NETWORK STATUS")
    print("=" * 55)

    # This node's identity
    own_id = host.get_id().to_string()
    print(f"\nMy Peer ID: {own_id}")

    # This node's own addresses
    print("\nMy Addresses:")
    for address in host.get_addrs():
        print(f"  {address}")

    # Peers that are actually connected right now
    connected_peers = host.get_connected_peers()

    print(f"\nConnected Peers: {len(connected_peers)}")

    if not connected_peers:
        print("  No peers connected.")

    for peer_id in connected_peers:
        peer_id_str = peer_id.to_string()
        print(f"\n  Peer ID: {peer_id_str}")

        # Addresses known for this peer
        peer_addresses = host.get_peerstore().addrs(peer_id)

        if peer_addresses:
            for address in peer_addresses:
                address_str = str(address)

                # Add the peer ID if the address doesn't include it
                if not address_str.endswith(f"/p2p/{peer_id_str}"):
                    address_str += f"/p2p/{peer_id_str}"

                print(f"  Peer Address: {address_str}")
        else:
            print("  Peer address: Not available in peerstore.")

    print("\n" + "=" * 55)



async def main(port: int, peer_address: str | None):
    # Create this node's identity
    key_pair = create_new_key_pair(secrets.token_bytes(32))
    host = new_host(key_pair=key_pair)

    # Prepare the listening addresses
    listen_addrs = get_available_interfaces(port)

    # Start the host
    async with host.run(listen_addrs=listen_addrs):
        peer_id = host.get_id().to_string()
        
        host.set_stream_handler(TX_PROTOCOL_ID, make_transaction_stream_handler(host)) #Whenever a peer opens a stream , pass that stream to this function
        print("Registered transaction protocol:", TX_PROTOCOL_ID)
        print("Node ready to receive transactions.")    

        print(f"Node started on port {port}")

        if peer_address:
            # Connect to another peer
            address = Multiaddr(peer_address)
            peer_info = info_from_p2p_addr(address)

            await host.connect(peer_info)

            print(f"Connected to peer: {peer_info.peer_id}")
            print("Node is staying alive and listening...")

        else:

            print("Waiting for another node to connect.")

        while True:
            await print_network_status(host)
            await trio.sleep(30)


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
