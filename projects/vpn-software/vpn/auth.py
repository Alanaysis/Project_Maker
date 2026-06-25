"""
Authentication module for VPN.

Supports two authentication methods:
1. Username/Password - using PBKDF2 for password hashing
2. Certificate - using X.509 certificates signed by a CA
"""

import os
import json
import hmac
from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, List

from vpn.crypto import (
    hash_password,
    verify_password,
    generate_ca,
    generate_certificate,
    verify_certificate,
    KeyPair,
)
from vpn.error import AuthError

from cryptography.hazmat.primitives import serialization
from cryptography import x509


@dataclass
class UserRecord:
    """A stored user record for password authentication."""
    username: str
    password_hash: bytes
    salt: bytes
    allowed_ips: List[str] = field(default_factory=list)
    enabled: bool = True


class PasswordAuthenticator:
    """
    Username/password authenticator.

    Stores user credentials with PBKDF2-hashed passwords.
    """

    def __init__(self) -> None:
        self._users: Dict[str, UserRecord] = {}

    def add_user(
        self,
        username: str,
        password: str,
        allowed_ips: Optional[List[str]] = None,
    ) -> None:
        """Add a user with a password."""
        password_hash, salt = hash_password(password)
        self._users[username] = UserRecord(
            username=username,
            password_hash=password_hash,
            salt=salt,
            allowed_ips=allowed_ips or ["0.0.0.0/0"],
        )

    def remove_user(self, username: str) -> bool:
        """Remove a user."""
        return self._users.pop(username, None) is not None

    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[List[str]]]:
        """
        Authenticate a user with username and password.

        Returns (success, allowed_ips) tuple.
        """
        record = self._users.get(username)
        if record is None or not record.enabled:
            return False, None

        if verify_password(password, record.password_hash, record.salt):
            return True, record.allowed_ips

        return False, None

    def authenticate_hash(self, username: str, password_hash: bytes) -> Tuple[bool, Optional[List[str]]]:
        """
        Authenticate using a pre-hashed password.

        The client sends PBKDF2(password, client_salt) and the server
        compares against the stored hash.
        """
        record = self._users.get(username)
        if record is None or not record.enabled:
            return False, None

        if hmac.compare_digest(password_hash, record.password_hash):
            return True, record.allowed_ips

        return False, None

    def save_to_file(self, path: str) -> None:
        """Save user database to a JSON file."""
        data = {}
        for username, record in self._users.items():
            data[username] = {
                "password_hash": record.password_hash.hex(),
                "salt": record.salt.hex(),
                "allowed_ips": record.allowed_ips,
                "enabled": record.enabled,
            }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, path: str) -> None:
        """Load user database from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        for username, info in data.items():
            self._users[username] = UserRecord(
                username=username,
                password_hash=bytes.fromhex(info["password_hash"]),
                salt=bytes.fromhex(info["salt"]),
                allowed_ips=info.get("allowed_ips", ["0.0.0.0/0"]),
                enabled=info.get("enabled", True),
            )


class CertificateAuthenticator:
    """
    Certificate-based authenticator.

    Uses a CA certificate to verify client certificates.
    """

    def __init__(self) -> None:
        self._ca_cert_pem: Optional[bytes] = None
        self._ca_key_pem: Optional[bytes] = None
        self._ca_password: Optional[bytes] = None
        # CN -> allowed_ips
        self._authorized_clients: Dict[str, List[str]] = {}

    def load_ca(
        self,
        ca_cert_path: str,
        ca_key_path: Optional[str] = None,
        ca_password: Optional[bytes] = None,
    ) -> None:
        """Load CA certificate and optionally its private key."""
        with open(ca_cert_path, "rb") as f:
            self._ca_cert_pem = f.read()
        if ca_key_path:
            with open(ca_key_path, "rb") as f:
                self._ca_key_pem = f.read()
            self._ca_password = ca_password

    def setup_ca(
        self,
        common_name: str = "VPN CA",
        valid_days: int = 3650,
        output_dir: str = ".",
    ) -> None:
        """Generate and save a new CA."""
        ca_key, ca_cert = generate_ca(common_name, valid_days)

        ca_key_pem = ca_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        ca_cert_pem = ca_cert.public_bytes(serialization.Encoding.PEM)

        os.makedirs(output_dir, exist_ok=True)

        key_path = os.path.join(output_dir, "ca.key")
        cert_path = os.path.join(output_dir, "ca.crt")

        with open(key_path, "wb") as f:
            f.write(ca_key_pem)
        with open(cert_path, "wb") as f:
            f.write(ca_cert_pem)

        # Set restrictive permissions on CA key
        os.chmod(key_path, 0o600)

        self._ca_key_pem = ca_key_pem
        self._ca_cert_pem = ca_cert_pem

    def issue_certificate(
        self,
        common_name: str,
        valid_days: int = 365,
        output_dir: str = ".",
    ) -> Tuple[str, str]:
        """
        Issue a new certificate signed by the CA.

        Returns (key_path, cert_path).
        """
        if self._ca_key_pem is None or self._ca_cert_pem is None:
            raise AuthError("CA not loaded. Call load_ca() or setup_ca() first.")

        ca_key = serialization.load_pem_private_key(self._ca_key_pem, self._ca_password)
        ca_cert = x509.load_pem_x509_certificate(self._ca_cert_pem)

        cert_key, cert = generate_certificate(ca_key, ca_cert, common_name, valid_days)

        key_pem = cert_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)

        os.makedirs(output_dir, exist_ok=True)

        key_path = os.path.join(output_dir, f"{common_name}.key")
        cert_path = os.path.join(output_dir, f"{common_name}.crt")

        with open(key_path, "wb") as f:
            f.write(key_pem)
        with open(cert_path, "wb") as f:
            f.write(cert_pem)

        os.chmod(key_path, 0o600)

        return key_path, cert_path

    def authorize_client(self, common_name: str, allowed_ips: Optional[List[str]] = None) -> None:
        """Authorize a client CN with specific allowed IPs."""
        self._authorized_clients[common_name] = allowed_ips or ["0.0.0.0/0"]

    def authenticate(self, cert_pem: bytes) -> Tuple[bool, Optional[List[str]]]:
        """
        Authenticate a client certificate.

        Returns (success, allowed_ips) tuple.
        """
        if self._ca_cert_pem is None:
            raise AuthError("CA certificate not loaded")

        # Verify certificate chain
        if not verify_certificate(cert_pem, self._ca_cert_pem):
            return False, None

        # Extract CN
        cert = x509.load_pem_x509_certificate(cert_pem)
        cn_attrs = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        if not cn_attrs:
            return False, None

        cn = cn_attrs[0].value

        # Check if CN is authorized
        if cn not in self._authorized_clients:
            return False, None

        return True, self._authorized_clients[cn]

    def save_authorizations(self, path: str) -> None:
        """Save authorized clients to file."""
        with open(path, "w") as f:
            json.dump(self._authorized_clients, f, indent=2)

    def load_authorizations(self, path: str) -> None:
        """Load authorized clients from file."""
        with open(path, "r") as f:
            self._authorized_clients = json.load(f)


# Need to import NameOID at module level for authenticate
from cryptography.x509.oid import NameOID  # noqa: E402
