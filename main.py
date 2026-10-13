"""
Here is how code works

First we generate a private key (unique for every user) and a public  key both can be done with the cryptography librabry
Second we create 4 functions ( jab private key bytes m ho unko str me krne ke liye and vice versa) same public key ke liye bytes -> str, str -> bytes
we need a address of every user a address is simply a hash of public key

this is a main step
Jab bhi koi transaction hoti h toh sender lets say alice will sign its transaction using private key mtlb.. jab koi sender
kisko ko money bhejega toh hum ek sign create krege using sender ka private key, sender ki public key, receiver ka address, amount
kitni baar etc; kyu? jab ek transaction dusre node me jayega toh we can check it signautre match krta h ya nhi  amount se, address se, public
key etc by chance agar kisne kuch beech m body me kuch ulta sidha kiya toh signauture simply match hi nhi krega, failling transaction
"""

import hashlib
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


# ---------------------------------------------------------------------------
# 1. KEYS
# ---------------------------------------------------------------------------
def generate_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    # simply generating private and public key using Library and returning both
    private_key = Ed25519PrivateKey.generate()   # private
    public_key = private_key.public_key()       # public
    return private_key, public_key


def public_key_to_hex(public_key:Ed25519PublicKey) -> str:
    # public key (bytes) to str
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return raw.hex()


def public_key_from_hex(hex_string: str) -> Ed25519PublicKey:
    # public key (str) to bytes
    return Ed25519PublicKey.from_public_bytes(bytes.fromhex(hex_string))


def private_key_to_hex(private_key) -> str:
    # private key (bytes) to str
    raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return raw.hex()


def private_key_from_hex(hex_string: str) -> Ed25519PrivateKey:
    # private key (str) to bytes
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(hex_string))


# Simply calculating a address first 20 bytes
def address_from_public_key_hex(public_key_hex: str) -> str:
    digest = hashlib.sha256(bytes.fromhex(public_key_hex)).hexdigest()
    return digest[:40]


#Sign
def serialize(data: dict) -> bytes:
    """
    Turn a dict into exact bytes. Sorting keys and removing spaces means
    every node produces the SAME bytes for the same transaction. If the
    bytes differed even slightly, the signature check would fail.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


#creating a signature
def sign(private_key, data: dict) -> str:
    signature = private_key.sign(serialize(data))
    return signature.hex()

# verifying if signature matches the body
def verify(public_key_hex: str, data: dict, signature_hex: str) -> bool:
    try:
        public_key = public_key_from_hex(public_key_hex)
        public_key.verify(bytes.fromhex(signature_hex), serialize(data))
        return True
    except (InvalidSignature, ValueError):
        return False


def create_signed_transaction(private_key:Ed25519PrivateKey, public_key:Ed25519PublicKey, to_address, amount:int, nonce:int) -> dict:
    # this is simply compiling all the data into a dict which will be send to another nodes;
    public_key_hex = public_key_to_hex(public_key)
    body = {
        "from": address_from_public_key_hex(public_key_hex),
        "to": to_address,
        "amount": amount,
        "nonce": nonce,
    }
    return {
        "body": body,
        "public_key": public_key_hex,
        "signature": sign(private_key, body),
    }


def verify_transaction(tx: dict) -> bool:
    """What every node does when a transaction arrives (signature part)."""
    # Check A: the public key must really belong to the "from" address.
    if address_from_public_key_hex(tx["public_key"]) != tx["body"]["from"]:
        return False
    # Check B: the signature must match the body and that public key.
    return verify(tx["public_key"], tx["body"], tx["signature"])


# ---------------------------------------------------------------------------
# DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Two wallets
    alice_priv, alice_pub = generate_keypair()
    bob_priv, bob_pub = generate_keypair()

    alice_addr = address_from_public_key_hex(public_key_to_hex(alice_pub))
    bob_addr = address_from_public_key_hex(public_key_to_hex(bob_pub))

    print("Alice private key (secret!):", private_key_to_hex(alice_priv))
    print("Alice public key:           ", public_key_to_hex(alice_pub))
    print("Alice address:              ", alice_addr)
    print("Bob address:                ", bob_addr)
    print()

    # Alice signs a transaction: send 5 coins to Bob
    tx = create_signed_transaction(alice_priv, alice_pub, bob_addr, amount=5, nonce=0)
    print("Transaction:", json.dumps(tx, indent=2))
    print()

    # Test 1: honest transaction
    print("1) Honest transaction valid?        ", verify_transaction(tx))

    # Test 2: someone changes the amount after signing
    tampered = json.loads(json.dumps(tx))
    tampered["body"]["amount"] = 500
    print("2) Amount changed to 500, valid?    ", verify_transaction(tampered))

    # Test 3: Bob signs a transaction pretending to be Alice
    fake_body = {"from": alice_addr, "to": bob_addr, "amount": 5, "nonce": 1}
    forged = {
        "body": fake_body,
        "public_key": public_key_to_hex(bob_pub),
        "signature": sign(bob_priv, fake_body),
    }
    print("3) Bob pretends to be Alice, valid? ", verify_transaction(forged))

    # Test 4: wallet saved and reloaded from hex still works
    reloaded = private_key_from_hex(private_key_to_hex(alice_priv))
    tx2 = create_signed_transaction(reloaded, reloaded.public_key(), bob_addr, 1, 1)
    print("4) Reloaded wallet signs, valid?    ", verify_transaction(tx2))