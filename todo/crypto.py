import os
from dataclasses import dataclass
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

# Note: cryptography doesn't expose Argon2 KDF in stable API; we use Scrypt with strong params.
# For portability, we default to Scrypt here. Parameters chosen for interactive logins.

SCRYPT_N = 2 ** 15  # CPU/memory cost
SCRYPT_R = 8
SCRYPT_P = 1
KEY_LEN = 32
SALT_LEN = 16
NONCE_LEN = 12


@dataclass
class KdfParams:
    name: str
    n: int
    r: int
    p: int
    salt: bytes

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "n": self.n,
            "r": self.r,
            "p": self.p,
            "salt": self.salt.hex(),
        }

    @staticmethod
    def from_dict(data: dict) -> "KdfParams":
        return KdfParams(
            name=data["name"],
            n=int(data["n"]),
            r=int(data["r"]),
            p=int(data["p"]),
            salt=bytes.fromhex(data["salt"]),
        )


def derive_key(password: str, params: KdfParams) -> bytes:
    kdf = Scrypt(salt=params.salt, length=KEY_LEN, n=params.n, r=params.r, p=params.p)
    return kdf.derive(password.encode("utf-8"))


def default_kdf_params() -> KdfParams:
    return KdfParams(name="scrypt", n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, salt=os.urandom(SALT_LEN))


def encrypt_json(password: str, plaintext_json_bytes: bytes) -> Tuple[dict, bytes, bytes]:
    params = default_kdf_params()
    key = derive_key(password, params)
    aes = AESGCM(key)
    nonce = os.urandom(NONCE_LEN)
    ciphertext = aes.encrypt(nonce, plaintext_json_bytes, None)
    return params.to_dict(), nonce, ciphertext


def decrypt_json(password: str, kdf_params_dict: dict, nonce: bytes, ciphertext: bytes) -> bytes:
    params = KdfParams.from_dict(kdf_params_dict)
    key = derive_key(password, params)
    aes = AESGCM(key)
    return aes.decrypt(nonce, ciphertext, None)
