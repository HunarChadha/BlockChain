
import json
import trio

from multiaddr import Multiaddr
from libp2p import new_host
from libp2p.crypto.secp256k1 import create_new_key_pair
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.custom_types import TProtocol

from main import generate_keypair, create_signed_transaction

PROTOCOL_ID = TProtocol("/blockchain/tx/1.0.0")


async def main(peer_address):
    # Generate a genuine signed transaction.
    private_key, public_key = generate_keypair()

    tx = create_signed_transaction(
        private_key,
        public_key,
        "recipient_test_address",
        5,
        0,
    )

    message = {
        "type": "transaction",
        "transaction": tx,
    }

    # Connect to Node A.
    key_pair = create_new_key_pair()
    host = new_host(key_pair=key_pair)

    async with host.run(listen_addrs=[]):
        address = Multiaddr(peer_address)
        peer_info = info_from_p2p_addr(address)

        await host.connect(peer_info)

        stream = await host.new_stream(
            peer_info.peer_id,
            [PROTOCOL_ID],
        )

        try:
            payload = json.dumps(message).encode("utf-8") + b"\n"
            await stream.write(payload)

            print("Sent signed transaction:")
            print(json.dumps(message, indent=2))

        finally:
            await stream.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print('Usage: python send_transaction.py "<NODE_A_PEER_ADDRESS>"')
        raise SystemExit(1)

    trio.run(main, sys.argv[1])
