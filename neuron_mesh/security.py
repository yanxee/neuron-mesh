from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def b64e(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def b64d(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


class NodeIdentity:
    def __init__(self, data_dir: Path) -> None:
        self.private_key_path = data_dir / "node_key.pem"
        self._private = self._load_or_create()
        public_raw = self._private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        self.public_key_b64 = b64e(public_raw)
        self.node_id = hashlib.sha256(public_raw).hexdigest()[:32]

    def _load_or_create(self) -> Ed25519PrivateKey:
        if self.private_key_path.exists():
            key = serialization.load_pem_private_key(
                self.private_key_path.read_bytes(), password=None
            )
            if not isinstance(key, Ed25519PrivateKey):
                raise TypeError("node_key.pem is not an Ed25519 private key")
            return key

        key = Ed25519PrivateKey.generate()
        pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        temp_path = self.private_key_path.with_suffix(".tmp")
        temp_path.write_bytes(pem)
        os.replace(temp_path, self.private_key_path)
        return key

    def sign(self, value: Any) -> str:
        return b64e(self._private.sign(canonical_json(value)))

    @staticmethod
    def verify(public_key_b64: str, value: Any, signature_b64: str) -> bool:
        try:
            public_key = Ed25519PublicKey.from_public_bytes(b64d(public_key_b64))
            public_key.verify(b64d(signature_b64), canonical_json(value))
            return True
        except Exception:
            return False


class MemoryCipher:
    def __init__(self, data_dir: Path) -> None:
        key_path = data_dir / "memory_master.key"
        if key_path.exists():
            master = key_path.read_bytes()
        else:
            master = secrets.token_bytes(32)
            key_path.write_bytes(master)
        self.key_id = hashlib.sha256(master).hexdigest()[:16]
        self._encryption_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"neuron-mesh-memory-v1",
            info=b"content-encryption",
        ).derive(master)
        self._index_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"neuron-mesh-memory-v1",
            info=b"blind-index",
        ).derive(master)
        self._aead = AESGCM(self._encryption_key)

    def seal(self, plaintext: bytes, memory_id: str) -> tuple[bytes, bytes]:
        nonce = secrets.token_bytes(12)
        cipher = self._aead.encrypt(nonce, plaintext, memory_id.encode("utf-8"))
        return cipher, nonce

    def open(self, cipher: bytes, nonce: bytes, memory_id: str) -> bytes:
        return self._aead.decrypt(nonce, cipher, memory_id.encode("utf-8"))

    def blind_token(self, token: str) -> str:
        return hmac.new(
            self._index_key, token.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def tokenize(self, text: str) -> set[str]:
        lowered = text.casefold()
        latin = re.findall(r"[a-z0-9_]{2,}", lowered)
        cjk_runs = re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]+", lowered)
        tokens = set(latin)
        for run in cjk_runs:
            if len(run) == 1:
                tokens.add(run)
            else:
                tokens.update(run[i : i + 2] for i in range(len(run) - 1))
        return {self.blind_token(token) for token in tokens}


def bearer_matches(expected: str, supplied: str | None) -> bool:
    if not supplied or not supplied.startswith("Bearer "):
        return False
    return hmac.compare_digest(expected, supplied.removeprefix("Bearer ").strip())

