"""
Cryptographic engine for VPN tunnel.

Implements:
- AES-256-GCM authenticated encryption
- ECDH key exchange (SECP256R1 / P-256)
- HKDF key derivation
- Certificate-based authentication
- Password-based authentication (PBKDF2)
"""

import os
import struct
import hashlib
import hmac
import datetime
from dataclasses import dataclass, field
from typing import Optional, Tuple

from cryptography.hazmat.primitives.asymmetric import ec, padding as asym_padding, utils
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDH,
    SECP256R1,
    ECDSA,
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
    generate_private_key,
)
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography import x509
from cryptography.x509.oid import NameOID

from vpn.error import CryptoError, AuthError

# Constants
KEY_SIZE = 32  # 256 bits for AES-256
NONCE_SIZE = 12  # 96 bits for AES-GCM
TAG_SIZE = 16  # 128 bits authentication tag
SALT_SIZE = 16
PBKDF2_ITERATIONS = 600_000


@dataclass
class KeyPair:
    """An ECDH key pair."""

    private_key: EllipticCurvePrivateKey
    public_key: EllipticCurvePublicKey

    def public_bytes(self) -> bytes:
        """Serialize the public key to bytes."""
        return self.private_key.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.CompressedPoint,
        )

    @staticmethod
    def from_private_key(private_key: EllipticCurvePrivateKey) -> "KeyPair":
        return KeyPair(private_key=private_key, public_key=private_key.public_key())

    @staticmethod
    def generate() -> "KeyPair":
        """Generate a new ECDH key pair."""
        private_key = generate_private_key(SECP256R1())
        return KeyPair(
            private_key=private_key, public_key=private_key.public_key()
        )

    @staticmethod
    def from_pem(private_pem: bytes, password: Optional[bytes] = None) -> "KeyPair":
        """Load a key pair from PEM-encoded private key."""
        private_key = serialization.load_pem_private_key(private_pem, password=password)
        if not isinstance(private_key, EllipticCurvePrivateKey):
            raise CryptoError("Loaded key is not an EC key")
        return KeyPair.from_private_key(private_key)

    def private_pem(self, password: Optional[bytes] = None) -> bytes:
        """Export private key as PEM."""
        encryption = (
            serialization.BestAvailableEncryption(password)
            if password
            else serialization.NoEncryption()
        )
        return self.private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            encryption,
        )

    def public_pem(self) -> bytes:
        """Export public key as PEM."""
        return self.public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )


class CryptoEngine:
    """
    Core cryptographic engine for the VPN.

    Handles key exchange, encryption, and decryption using
    ECDH + AES-256-GCM with HKDF key derivation.
    """

    def __init__(self, keypair: Optional[KeyPair] = None) -> None:
        self._keypair: KeyPair = keypair or KeyPair.generate()
        self._shared_secret: Optional[bytes] = None
        self._encryption_key: Optional[bytes] = None
        self._nonce_counter: int = 0

    @property
    def public_key(self) -> bytes:
        """Get the local public key as compressed point bytes."""
        return self._keypair.public_bytes()

    @property
    def public_key_pem(self) -> bytes:
        """Get the local public key as PEM."""
        return self._keypair.public_pem()

    def get_keypair(self) -> KeyPair:
        """Get the internal key pair."""
        return self._keypair

    # ---- Key Exchange ----

    def key_exchange(self, remote_public_key_bytes: bytes) -> None:
        """
        Perform ECDH key exchange with a remote peer.

        Derives a shared AES-256 key using HKDF-SHA256.
        """
        try:
            remote_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
                SECP256R1(), remote_public_key_bytes
            )
        except Exception as e:
            raise CryptoError(f"Invalid remote public key: {e}")

        try:
            shared_key = self._keypair.private_key.exchange(ECDH(), remote_public_key)
        except Exception as e:
            raise CryptoError(f"ECDH exchange failed: {e}")

        # Derive encryption key using HKDF
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=None,
            info=b"vpn-aes-256-gcm-key",
        )
        self._encryption_key = hkdf.derive(shared_key)
        self._shared_secret = shared_key

    @property
    def has_key(self) -> bool:
        """Check if encryption key has been derived."""
        return self._encryption_key is not None

    # ---- Encryption / Decryption ----

    def _generate_nonce(self) -> bytes:
        """Generate a nonce from the counter (counter || zero-padding)."""
        nonce = bytearray(NONCE_SIZE)
        struct.pack_into("<Q", nonce, 0, self._nonce_counter)
        return bytes(nonce)

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypt data using AES-256-GCM.

        Returns: nonce (12 bytes) || ciphertext || tag (16 bytes)
        """
        if self._encryption_key is None:
            raise CryptoError("Key exchange not completed")

        nonce = self._generate_nonce()
        self._nonce_counter = (self._nonce_counter + 1) & 0xFFFFFFFFFFFFFFFF

        aesgcm = AESGCM(self._encryption_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # Prepend nonce to ciphertext
        return nonce + ciphertext

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM.

        Expects: nonce (12 bytes) || ciphertext || tag (16 bytes)
        """
        if self._encryption_key is None:
            raise CryptoError("Key exchange not completed")

        if len(data) < NONCE_SIZE + TAG_SIZE:
            raise CryptoError("Ciphertext too short")

        nonce = data[:NONCE_SIZE]
        ciphertext = data[NONCE_SIZE:]

        aesgcm = AESGCM(self._encryption_key)
        try:
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise CryptoError(f"Decryption failed: {e}")


# ---- Password Authentication ----


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Hash a password using PBKDF2-SHA256.

    Returns (hash, salt).
    """
    if salt is None:
        salt = os.urandom(SALT_SIZE)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    password_hash = kdf.derive(password.encode("utf-8"))
    return password_hash, salt


def verify_password(password: str, password_hash: bytes, salt: bytes) -> bool:
    """Verify a password against its hash."""
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, password_hash)


# ---- Certificate Utilities ----


def generate_ca(
    common_name: str = "VPN CA",
    valid_days: int = 3650,
) -> Tuple[EllipticCurvePrivateKey, x509.Certificate]:
    """
    Generate a self-signed CA certificate.

    Returns (private_key, certificate).
    """
    ca_key = generate_private_key(SECP256R1())
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
    )
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=valid_days))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )
    return ca_key, cert


def generate_certificate(
    ca_key: EllipticCurvePrivateKey,
    ca_cert: x509.Certificate,
    common_name: str,
    valid_days: int = 365,
) -> Tuple[EllipticCurvePrivateKey, x509.Certificate]:
    """
    Generate a client/server certificate signed by a CA.

    Returns (private_key, certificate).
    """
    cert_key = generate_private_key(SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(cert_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=valid_days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )
    return cert_key, cert


def verify_certificate(
    cert_pem: bytes,
    ca_cert_pem: bytes,
) -> bool:
    """
    Verify a certificate against a CA certificate.

    Returns True if valid, False otherwise.
    """
    try:
        cert = x509.load_pem_x509_certificate(cert_pem)
        ca_cert = x509.load_pem_x509_certificate(ca_cert_pem)
        # Verify the signature using ECDSA
        ca_public_key = ca_cert.public_key()
        ca_public_key.verify(
            cert.signature,
            cert.tbs_certificate_bytes,
            ECDSA(cert.signature_hash_algorithm),
        )
        return True
    except Exception:
        return False
