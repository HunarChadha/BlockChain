from nacl import bindings as b
import os
import hashlib

def Add(A:bytes, B:bytes) -> bytes:
    return b.crypto_core_ed25519_add(A, B)

def ScalarMultiply(A:bytes, B:bytes)-> bytes:
    return b.crypto_scalarmult_ed25519_noclamp(A, B)

def GMultiply(A:bytes) -> bytes:
    return b.crypto_scalarmult_ed25519_base_noclamp(A)

def Hash(A:bytes) -> bytes:
    return hashlib.sha256(A).digest()

def Secret()-> bytes:
    return b.crypto_core_ed25519_scalar_reduce(os.urandom(64))





