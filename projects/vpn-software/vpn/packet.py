"""
VPN packet parsing and construction.

Handles:
- IPv4/IPv6 packet parsing
- VPN protocol packets (handshake, data, keepalive)
- Packet serialization/deserialization
"""

import struct
import socket
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional, List

from vpn.error import InvalidPacketError, ProtocolError


# ---- Protocol Constants ----

class MessageType(IntEnum):
    """VPN protocol message types."""
    HANDSHAKE_INIT = 1
    HANDSHAKE_RESPONSE = 2
    TRANSPORT_DATA = 3
    KEEPALIVE = 4
    AUTH_REQUEST = 5
    AUTH_RESPONSE = 6
    DISCONNECT = 7


HEADER_MAGIC = 0x56504E01  # "VPN\x01"
PROTOCOL_VERSION = 1

# Packet sizes
HANDSHAKE_INIT_SIZE = 4 + 1 + 1 + 32 + 32 + 16  # magic + ver + type + pubkey + ephemeral + mac
HANDSHAME_RESPONSE_SIZE = 4 + 1 + 1 + 32 + 32 + 16
TRANSPORT_HEADER_SIZE = 4 + 1 + 1 + 4 + 8  # magic + ver + type + session_id + counter
AUTH_REQUEST_HEADER_SIZE = 4 + 1 + 1 + 4  # magic + ver + type + session_id


# ---- IPv4 Packet ----

@dataclass
class IPv4Header:
    """Parsed IPv4 header."""
    version: int = 4
    ihl: int = 5
    dscp: int = 0
    ecn: int = 0
    total_length: int = 0
    identification: int = 0
    flags: int = 0
    fragment_offset: int = 0
    ttl: int = 64
    protocol: int = 17  # UDP
    checksum: int = 0
    source: str = "0.0.0.0"
    destination: str = "0.0.0.0"

    MIN_SIZE = 20

    @staticmethod
    def parse(data: bytes) -> "IPv4Header":
        """Parse an IPv4 header from raw bytes."""
        if len(data) < IPv4Header.MIN_SIZE:
            raise InvalidPacketError("IPv4 header too short")

        version_ihl = data[0]
        version = (version_ihl >> 4) & 0x0F
        if version != 4:
            raise InvalidPacketError(f"Not IPv4: version={version}")

        ihl = version_ihl & 0x0F
        header_len = ihl * 4

        if len(data) < header_len:
            raise InvalidPacketError("IPv4 header length mismatch")

        dscp_ecn = data[1]
        total_length = struct.unpack("!H", data[2:4])[0]
        identification = struct.unpack("!H", data[4:6])[0]
        flags_frag = struct.unpack("!H", data[6:8])[0]
        flags = (flags_frag >> 13) & 0x07
        fragment_offset = flags_frag & 0x1FFF
        ttl = data[8]
        protocol = data[9]
        checksum = struct.unpack("!H", data[10:12])[0]
        source = socket.inet_ntoa(data[12:16])
        destination = socket.inet_ntoa(data[16:20])

        return IPv4Header(
            version=version,
            ihl=ihl,
            dscp=(dscp_ecn >> 2) & 0x3F,
            ecn=dscp_ecn & 0x03,
            total_length=total_length,
            identification=identification,
            flags=flags,
            fragment_offset=fragment_offset,
            ttl=ttl,
            protocol=protocol,
            checksum=checksum,
            source=source,
            destination=destination,
        )

    def to_bytes(self) -> bytes:
        """Serialize header to bytes."""
        dscp_ecn = ((self.dscp & 0x3F) << 2) | (self.ecn & 0x03)
        flags_frag = ((self.flags & 0x07) << 13) | (self.fragment_offset & 0x1FFF)
        src = socket.inet_aton(self.source)
        dst = socket.inet_aton(self.destination)

        header = struct.pack(
            "!BBHHHBBHII",
            (self.version << 4) | (self.ihl & 0x0F),
            dscp_ecn,
            self.total_length,
            self.identification,
            flags_frag,
            self.ttl,
            self.protocol,
            self.checksum,
            int.from_bytes(src, "big"),
            int.from_bytes(dst, "big"),
        )
        return header

    @property
    def header_length(self) -> int:
        return self.ihl * 4


@dataclass
class IPv4Packet:
    """A parsed IPv4 packet."""
    header: IPv4Header
    payload: bytes = b""

    @staticmethod
    def parse(data: bytes) -> "IPv4Packet":
        """Parse a complete IPv4 packet."""
        header = IPv4Header.parse(data)
        payload = data[header.header_length:header.total_length]
        return IPv4Packet(header=header, payload=payload)

    def to_bytes(self) -> bytes:
        """Serialize the packet."""
        return self.header.to_bytes() + self.payload

    @property
    def destination(self) -> str:
        return self.header.destination

    @property
    def source(self) -> str:
        return self.header.source


# ---- VPN Protocol Packets ----

@dataclass
class HandshakeInitPacket:
    """Handshake initiation packet."""
    sender_index: int = 0
    public_key: bytes = b""
    ephemeral_key: bytes = b""
    mac: bytes = b""

    def to_bytes(self) -> bytes:
        """Serialize the handshake initiation."""
        header = struct.pack(
            "!IBBH",
            HEADER_MAGIC,
            PROTOCOL_VERSION,
            MessageType.HANDSHAKE_INIT,
            self.sender_index,
        )
        return header + self.public_key + self.ephemeral_key + self.mac

    @staticmethod
    def parse(data: bytes) -> "HandshakeInitPacket":
        """Parse a handshake initiation packet."""
        if len(data) < 8 + 32 + 32:
            raise ProtocolError("Handshake init packet too short")

        magic = struct.unpack("!I", data[0:4])[0]
        if magic != HEADER_MAGIC:
            raise ProtocolError(f"Invalid magic: {magic:#x}")

        version = data[4]
        if version != PROTOCOL_VERSION:
            raise ProtocolError(f"Unsupported version: {version}")

        msg_type = data[5]
        if msg_type != MessageType.HANDSHAKE_INIT:
            raise ProtocolError(f"Expected handshake init, got {msg_type}")

        sender_index = struct.unpack("!H", data[6:8])[0]
        public_key = data[8:40]
        ephemeral_key = data[40:72]
        mac = data[72:88] if len(data) >= 88 else b""

        return HandshakeInitPacket(
            sender_index=sender_index,
            public_key=public_key,
            ephemeral_key=ephemeral_key,
            mac=mac,
        )


@dataclass
class HandshakeResponsePacket:
    """Handshake response packet."""
    sender_index: int = 0
    receiver_index: int = 0
    public_key: bytes = b""
    ephemeral_key: bytes = b""
    mac: bytes = b""

    def to_bytes(self) -> bytes:
        header = struct.pack(
            "!IBBHH",
            HEADER_MAGIC,
            PROTOCOL_VERSION,
            MessageType.HANDSHAKE_RESPONSE,
            self.sender_index,
            self.receiver_index,
        )
        return header + self.public_key + self.ephemeral_key + self.mac

    @staticmethod
    def parse(data: bytes) -> "HandshakeResponsePacket":
        if len(data) < 10 + 32 + 32:
            raise ProtocolError("Handshake response too short")

        magic = struct.unpack("!I", data[0:4])[0]
        if magic != HEADER_MAGIC:
            raise ProtocolError(f"Invalid magic: {magic:#x}")

        msg_type = data[5]
        if msg_type != MessageType.HANDSHAKE_RESPONSE:
            raise ProtocolError(f"Expected handshake response, got {msg_type}")

        sender_index = struct.unpack("!H", data[6:8])[0]
        receiver_index = struct.unpack("!H", data[8:10])[0]
        public_key = data[10:42]
        ephemeral_key = data[42:74]
        mac = data[74:90] if len(data) >= 90 else b""

        return HandshakeResponsePacket(
            sender_index=sender_index,
            receiver_index=receiver_index,
            public_key=public_key,
            ephemeral_key=ephemeral_key,
            mac=mac,
        )


@dataclass
class TransportDataPacket:
    """Encrypted transport data packet."""
    session_id: int = 0
    counter: int = 0
    encrypted_payload: bytes = b""

    HEADER_SIZE = TRANSPORT_HEADER_SIZE

    def to_bytes(self) -> bytes:
        header = struct.pack(
            "!IBBIQ",
            HEADER_MAGIC,
            PROTOCOL_VERSION,
            MessageType.TRANSPORT_DATA,
            self.session_id,
            self.counter,
        )
        return header + self.encrypted_payload

    @staticmethod
    def parse(data: bytes) -> "TransportDataPacket":
        if len(data) < TRANSPORT_HEADER_SIZE:
            raise ProtocolError("Transport data packet too short")

        magic = struct.unpack("!I", data[0:4])[0]
        if magic != HEADER_MAGIC:
            raise ProtocolError(f"Invalid magic: {magic:#x}")

        msg_type = data[5]
        if msg_type != MessageType.TRANSPORT_DATA:
            raise ProtocolError(f"Expected transport data, got {msg_type}")

        session_id = struct.unpack("!I", data[6:10])[0]
        counter = struct.unpack("!Q", data[10:18])[0]
        encrypted_payload = data[18:]

        return TransportDataPacket(
            session_id=session_id,
            counter=counter,
            encrypted_payload=encrypted_payload,
        )


@dataclass
class AuthRequestPacket:
    """Authentication request packet (username/password or certificate)."""
    session_id: int = 0
    auth_type: int = 0  # 1=password, 2=certificate
    username: str = ""
    password_hash: bytes = b""
    certificate: bytes = b""

    def to_bytes(self) -> bytes:
        username_bytes = self.username.encode("utf-8")
        header = struct.pack(
            "!IBBIB",
            HEADER_MAGIC,
            PROTOCOL_VERSION,
            MessageType.AUTH_REQUEST,
            self.session_id,
            self.auth_type,
        )
        if self.auth_type == 1:
            # Password auth
            return (
                header
                + struct.pack("!H", len(username_bytes))
                + username_bytes
                + self.password_hash
            )
        else:
            # Certificate auth
            return (
                header
                + struct.pack("!H", len(username_bytes))
                + username_bytes
                + struct.pack("!I", len(self.certificate))
                + self.certificate
            )

    @staticmethod
    def parse(data: bytes) -> "AuthRequestPacket":
        if len(data) < 11:
            raise ProtocolError("Auth request too short")

        magic = struct.unpack("!I", data[0:4])[0]
        if magic != HEADER_MAGIC:
            raise ProtocolError(f"Invalid magic: {magic:#x}")

        msg_type = data[5]
        if msg_type != MessageType.AUTH_REQUEST:
            raise ProtocolError(f"Expected auth request, got {msg_type}")

        session_id = struct.unpack("!I", data[6:10])[0]
        auth_type = data[10]
        offset = 11

        username_len = struct.unpack("!H", data[offset:offset + 2])[0]
        offset += 2
        username = data[offset:offset + username_len].decode("utf-8")
        offset += username_len

        if auth_type == 1:
            password_hash = data[offset:offset + 32]
            return AuthRequestPacket(
                session_id=session_id,
                auth_type=auth_type,
                username=username,
                password_hash=password_hash,
            )
        else:
            cert_len = struct.unpack("!I", data[offset:offset + 4])[0]
            offset += 4
            certificate = data[offset:offset + cert_len]
            return AuthRequestPacket(
                session_id=session_id,
                auth_type=auth_type,
                username=username,
                certificate=certificate,
            )


@dataclass
class AuthResponsePacket:
    """Authentication response packet."""
    session_id: int = 0
    success: bool = False
    message: str = ""

    def to_bytes(self) -> bytes:
        msg_bytes = self.message.encode("utf-8")
        header = struct.pack(
            "!IBBIB",
            HEADER_MAGIC,
            PROTOCOL_VERSION,
            MessageType.AUTH_RESPONSE,
            self.session_id,
            1 if self.success else 0,
        )
        return header + struct.pack("!H", len(msg_bytes)) + msg_bytes

    @staticmethod
    def parse(data: bytes) -> "AuthResponsePacket":
        if len(data) < 11:
            raise ProtocolError("Auth response too short")

        magic = struct.unpack("!I", data[0:4])[0]
        if magic != HEADER_MAGIC:
            raise ProtocolError(f"Invalid magic: {magic:#x}")

        session_id = struct.unpack("!I", data[6:10])[0]
        success = data[10] == 1
        msg_len = struct.unpack("!H", data[11:13])[0]
        message = data[13:13 + msg_len].decode("utf-8")

        return AuthResponsePacket(
            session_id=session_id,
            success=success,
            message=message,
        )


@dataclass
class KeepalivePacket:
    """Keepalive packet."""
    session_id: int = 0

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!IBBI",
            HEADER_MAGIC,
            PROTOCOL_VERSION,
            MessageType.KEEPALIVE,
            self.session_id,
        )

    @staticmethod
    def parse(data: bytes) -> "KeepalivePacket":
        if len(data) < 10:
            raise ProtocolError("Keepalive packet too short")
        session_id = struct.unpack("!I", data[6:10])[0]
        return KeepalivePacket(session_id=session_id)


def parse_message_type(data: bytes) -> MessageType:
    """Parse just the message type from raw bytes."""
    if len(data) < 6:
        raise ProtocolError("Packet too short")
    magic = struct.unpack("!I", data[0:4])[0]
    if magic != HEADER_MAGIC:
        raise ProtocolError(f"Invalid magic: {magic:#x}")
    return MessageType(data[5])
