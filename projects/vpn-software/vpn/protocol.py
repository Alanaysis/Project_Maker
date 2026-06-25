"""
VPN protocol implementation.

Handles the VPN handshake, session management, and data transfer protocol.
Supports both UDP and TCP transports.
"""

import os
import struct
import time
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from vpn.crypto import CryptoEngine, KeyPair
from vpn.packet import (
    MessageType,
    HandshakeInitPacket,
    HandshakeResponsePacket,
    TransportDataPacket,
    AuthRequestPacket,
    AuthResponsePacket,
    KeepalivePacket,
)
from vpn.error import ProtocolError, HandshakeError

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """VPN session state."""
    INIT = "init"
    HANDSHAKE_SENT = "handshake_sent"
    HANDSHAKE_COMPLETE = "handshake_complete"
    AUTHENTICATING = "authenticating"
    ESTABLISHED = "established"
    REKEYING = "rekeying"
    CLOSED = "closed"


@dataclass
class SessionConfig:
    """Session configuration."""
    keepalive_interval: float = 25.0
    rekey_interval: float = 3600.0  # 1 hour
    handshake_timeout: float = 10.0
    max_handshake_attempts: int = 5
    mtu: int = 1500


class Session:
    """
    VPN session managing the lifecycle of a single connection.

    Handles:
    - Handshake initiation/response
    - Key derivation
    - Authentication exchange
    - Data encryption/decryption
    - Keepalive
    - Rekeying
    """

    def __init__(
        self,
        session_id: int,
        local_keypair: KeyPair,
        config: Optional[SessionConfig] = None,
    ) -> None:
        self._session_id = session_id
        self._state = SessionState.INIT
        self._config = config or SessionConfig()

        # Cryptography
        self._local_keypair = local_keypair
        self._crypto = CryptoEngine(keypair=local_keypair)

        # Handshake state
        self._remote_public_key: Optional[bytes] = None
        self._remote_ephemeral: Optional[bytes] = None
        self._handshake_start: float = 0
        self._handshake_attempts: int = 0

        # Session timing
        self._established_at: float = 0
        self._last_keepalive_sent: float = 0
        self._last_keepalive_received: float = 0
        self._last_rekey: float = 0

    @property
    def session_id(self) -> int:
        return self._session_id

    @property
    def state(self) -> SessionState:
        return self._state

    @property
    def is_established(self) -> bool:
        return self._state == SessionState.ESTABLISHED

    @property
    def crypto(self) -> CryptoEngine:
        return self._crypto

    # ---- Handshake ----

    def initiate_handshake(self) -> HandshakeInitPacket:
        """
        Create a handshake initiation packet.

        Starts the key exchange process.
        """
        self._state = SessionState.HANDSHAKE_SENT
        self._handshake_start = time.time()
        self._handshake_attempts += 1

        # Generate ephemeral key pair for this handshake
        ephemeral_kp = KeyPair.generate()

        packet = HandshakeInitPacket(
            sender_index=self._session_id,
            public_key=self._local_keypair.public_bytes(),
            ephemeral_key=ephemeral_kp.public_bytes(),
        )

        logger.info(f"Session {self._session_id}: Handshake initiation sent (attempt {self._handshake_attempts})")
        return packet

    def process_handshake_init(
        self, packet: HandshakeInitPacket
    ) -> HandshakeResponsePacket:
        """
        Process an incoming handshake initiation.

        Returns a handshake response.
        """
        self._remote_public_key = packet.public_key
        self._remote_ephemeral = packet.ephemeral_key

        # Perform key exchange with remote public key
        self._crypto.key_exchange(packet.public_key)

        # Generate our ephemeral key
        ephemeral_kp = KeyPair.generate()

        response = HandshakeResponsePacket(
            sender_index=self._session_id,
            receiver_index=packet.sender_index,
            public_key=self._local_keypair.public_bytes(),
            ephemeral_key=ephemeral_kp.public_bytes(),
        )

        self._state = SessionState.HANDSHAKE_COMPLETE
        logger.info(f"Session {self._session_id}: Handshake response sent")
        return response

    def process_handshake_response(self, packet: HandshakeResponsePacket) -> None:
        """Process an incoming handshake response."""
        self._remote_public_key = packet.public_key
        self._remote_ephemeral = packet.ephemeral_key

        # Perform key exchange
        self._crypto.key_exchange(packet.public_key)

        self._state = SessionState.HANDSHAKE_COMPLETE
        logger.info(f"Session {self._session_id}: Handshake complete")

    def check_handshake_timeout(self) -> bool:
        """Check if the handshake has timed out."""
        if self._state != SessionState.HANDSHAKE_SENT:
            return False
        return (time.time() - self._handshake_start) > self._config.handshake_timeout

    # ---- Authentication ----

    def create_auth_request(
        self, username: str, password: str
    ) -> AuthRequestPacket:
        """Create a password authentication request."""
        from vpn.crypto import hash_password
        password_hash, salt = hash_password(password)
        # Send hash + salt for server-side verification
        return AuthRequestPacket(
            session_id=self._session_id,
            auth_type=1,
            username=username,
            password_hash=password_hash + salt,
        )

    def create_cert_auth_request(
        self, cert_pem: bytes
    ) -> AuthRequestPacket:
        """Create a certificate authentication request."""
        return AuthRequestPacket(
            session_id=self._session_id,
            auth_type=2,
            username="",
            certificate=cert_pem,
        )

    def mark_established(self) -> None:
        """Mark the session as fully established."""
        self._state = SessionState.ESTABLISHED
        self._established_at = time.time()
        self._last_rekey = time.time()
        logger.info(f"Session {self._session_id}: Established")

    # ---- Data Transfer ----

    def encrypt_packet(self, plaintext: bytes) -> TransportDataPacket:
        """Encrypt data into a transport packet."""
        if not self.is_established:
            raise ProtocolError("Session not established")

        encrypted = self._crypto.encrypt(plaintext)
        return TransportDataPacket(
            session_id=self._session_id,
            counter=self._crypto._nonce_counter - 1,
            encrypted_payload=encrypted,
        )

    def decrypt_packet(self, packet: TransportDataPacket) -> bytes:
        """Decrypt a transport data packet."""
        if not self.is_established:
            raise ProtocolError("Session not established")

        return self._crypto.decrypt(packet.encrypted_payload)

    # ---- Keepalive ----

    def should_send_keepalive(self) -> bool:
        """Check if we should send a keepalive."""
        if not self.is_established:
            return False
        return (time.time() - self._last_keepalive_sent) >= self._config.keepalive_interval

    def create_keepalive(self) -> KeepalivePacket:
        """Create a keepalive packet."""
        self._last_keepalive_sent = time.time()
        return KeepalivePacket(session_id=self._session_id)

    def process_keepalive(self) -> None:
        """Process a received keepalive."""
        self._last_keepalive_received = time.time()

    def check_keepalive_timeout(self) -> bool:
        """Check if keepalive has timed out (peer may be dead)."""
        if not self.is_established:
            return False
        timeout = self._config.keepalive_interval * 3
        return (time.time() - self._last_keepalive_received) > timeout

    # ---- Rekeying ----

    def should_rekey(self) -> bool:
        """Check if we should initiate rekeying."""
        if not self.is_established:
            return False
        return (time.time() - self._last_rekey) >= self._config.rekey_interval

    def close(self) -> None:
        """Close the session."""
        self._state = SessionState.CLOSED
        logger.info(f"Session {self._session_id}: Closed")
