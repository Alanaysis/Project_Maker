"""Tests for the packet module."""

import struct
import pytest
from vpn.packet import (
    IPv4Header,
    IPv4Packet,
    HandshakeInitPacket,
    HandshakeResponsePacket,
    TransportDataPacket,
    AuthRequestPacket,
    AuthResponsePacket,
    KeepalivePacket,
    MessageType,
    parse_message_type,
    HEADER_MAGIC,
)


class TestIPv4Header:
    def test_parse_minimal(self):
        data = bytearray(20)
        data[0] = 0x45  # version=4, ihl=5
        data[1] = 0x00
        data[2:4] = struct.pack("!H", 20)  # total length
        data[8] = 64  # TTL
        data[9] = 17  # UDP
        data[12:16] = bytes([10, 0, 0, 1])  # source
        data[16:20] = bytes([10, 0, 0, 2])  # destination

        header = IPv4Header.parse(bytes(data))
        assert header.version == 4
        assert header.ihl == 5
        assert header.total_length == 20
        assert header.ttl == 64
        assert header.protocol == 17
        assert header.source == "10.0.0.1"
        assert header.destination == "10.0.0.2"

    def test_serialize_roundtrip(self):
        header = IPv4Header(
            total_length=40,
            protocol=6,
            source="192.168.1.1",
            destination="192.168.1.2",
        )
        data = header.to_bytes()
        parsed = IPv4Header.parse(data)

        assert parsed.source == "192.168.1.1"
        assert parsed.destination == "192.168.1.2"
        assert parsed.protocol == 6

    def test_short_header_raises(self):
        with pytest.raises(Exception):
            IPv4Header.parse(b"\x45" * 10)

    def test_wrong_version_raises(self):
        data = bytearray(20)
        data[0] = 0x65  # version=6
        with pytest.raises(Exception):
            IPv4Header.parse(bytes(data))


class TestIPv4Packet:
    def test_parse_and_serialize(self):
        header = IPv4Header(
            total_length=28,
            source="10.0.0.1",
            destination="10.0.0.2",
        )
        payload = b"\x00" * 8
        packet_bytes = header.to_bytes() + payload

        packet = IPv4Packet.parse(packet_bytes)
        assert packet.source == "10.0.0.1"
        assert packet.destination == "10.0.0.2"
        assert packet.payload == payload


class TestHandshakeInitPacket:
    def test_serialize_parse(self):
        packet = HandshakeInitPacket(
            sender_index=1,
            public_key=b"\xAA" * 32,
            ephemeral_key=b"\xBB" * 32,
            mac=b"\xCC" * 16,
        )

        data = packet.to_bytes()
        parsed = HandshakeInitPacket.parse(data)

        assert parsed.sender_index == 1
        assert parsed.public_key == b"\xAA" * 32
        assert parsed.ephemeral_key == b"\xBB" * 32
        assert parsed.mac == b"\xCC" * 16

    def test_short_packet_raises(self):
        with pytest.raises(Exception):
            HandshakeInitPacket.parse(b"\x00" * 10)


class TestHandshakeResponsePacket:
    def test_serialize_parse(self):
        packet = HandshakeResponsePacket(
            sender_index=2,
            receiver_index=1,
            public_key=b"\xAA" * 32,
            ephemeral_key=b"\xBB" * 32,
        )

        data = packet.to_bytes()
        parsed = HandshakeResponsePacket.parse(data)

        assert parsed.sender_index == 2
        assert parsed.receiver_index == 1


class TestTransportDataPacket:
    def test_serialize_parse(self):
        packet = TransportDataPacket(
            session_id=42,
            counter=100,
            encrypted_payload=b"\xDD" * 100,
        )

        data = packet.to_bytes()
        parsed = TransportDataPacket.parse(data)

        assert parsed.session_id == 42
        assert parsed.counter == 100
        assert parsed.encrypted_payload == b"\xDD" * 100

    def test_header_size(self):
        packet = TransportDataPacket(session_id=1, counter=0)
        assert len(packet.to_bytes()) == TransportDataPacket.HEADER_SIZE


class TestAuthPackets:
    def test_auth_request_password(self):
        packet = AuthRequestPacket(
            session_id=1,
            auth_type=1,
            username="testuser",
            password_hash=b"\xAA" * 32,
        )
        data = packet.to_bytes()
        parsed = AuthRequestPacket.parse(data)

        assert parsed.session_id == 1
        assert parsed.auth_type == 1
        assert parsed.username == "testuser"
        assert parsed.password_hash == b"\xAA" * 32

    def test_auth_request_certificate(self):
        cert = b"-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
        packet = AuthRequestPacket(
            session_id=1,
            auth_type=2,
            username="",
            certificate=cert,
        )
        data = packet.to_bytes()
        parsed = AuthRequestPacket.parse(data)

        assert parsed.auth_type == 2
        assert parsed.certificate == cert

    def test_auth_response(self):
        packet = AuthResponsePacket(
            session_id=1,
            success=True,
            message="OK",
        )
        data = packet.to_bytes()
        parsed = AuthResponsePacket.parse(data)

        assert parsed.session_id == 1
        assert parsed.success is True
        assert parsed.message == "OK"


class TestKeepalivePacket:
    def test_serialize_parse(self):
        packet = KeepalivePacket(session_id=42)
        data = packet.to_bytes()
        parsed = KeepalivePacket.parse(data)
        assert parsed.session_id == 42


class TestParseMessageType:
    def test_handshake_init(self):
        packet = HandshakeInitPacket(
            sender_index=1,
            public_key=b"\x00" * 32,
            ephemeral_key=b"\x00" * 32,
        )
        assert parse_message_type(packet.to_bytes()) == MessageType.HANDSHAKE_INIT

    def test_transport_data(self):
        packet = TransportDataPacket(session_id=1, counter=0)
        assert parse_message_type(packet.to_bytes()) == MessageType.TRANSPORT_DATA

    def test_keepalive(self):
        packet = KeepalivePacket(session_id=1)
        assert parse_message_type(packet.to_bytes()) == MessageType.KEEPALIVE

    def test_short_data_raises(self):
        with pytest.raises(Exception):
            parse_message_type(b"\x00" * 3)
