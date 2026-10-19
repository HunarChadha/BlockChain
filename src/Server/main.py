from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)
from Database import DataBase
def hex_to_bytes(hex_string) ->  bytes:
    return bytes.fromhex(hex_string)

def encode(details:dict) -> bytes:
    details = f'sign|{details["pub"]}|{details["address"]}|{details["amount"]}|{details["nonce"]}'.encode()
    return details

def verify(data:dict) -> bool:
    details = data['details']
    if details['nonce'] != DataBase.fetch_data(details['pub']):
        return False
    try:
        public_key = Ed25519PublicKey.from_public_bytes(hex_to_bytes(data["pub"]))
        public_key.verify(bytes.fromhex(data["sign"]), encode(data["details"]))
        return True
    except Exception as e:
        print(e)
        return False

