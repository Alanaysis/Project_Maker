"""Tests for the protocol module."""

import pytest
from vpn.protocol import Session, SessionConfig, SessionState
from vpn.crypto import KeyPair


class TestSession:
    def test_creation(self):
        kp = KeyPair.generate()
        session = Session(session_id=1, local_keypair=kp)
        assert session.session_id == 1
        assert session.state == SessionState.INIT
        assert not session.is_established

    def test_handshake_init(self):
        kp = KeyPair.generate()
        session = Session(session_id=1, local_keypair=kp)

        init = session.initiate_handshake()
        assert session.state == SessionState.HANDSHAKE_SENT
        assert init.sender_index == 1
        assert len(init.public_key) == 33  # Compressed point
        assert len(init.ephemeral_key) == 33

    def test_handshake_roundtrip(self):
        # Server side
        server_kp = KeyPair.generate()
        server_session = Session(session_id=1, local_keypair=server_kp)

        # Client side
        client_kp = KeyPair.generate()
        client_session = Session(session_id=2, local_keypair=client_kp)

        # Client initiates
        init = client_session.initiate_handshake()

        # Server processes and responds
        response = server_session.process_handshake_init(init)
        assert server_session.state == SessionState.HANDSHAKE_COMPLETE

        # Client processes response
        client_session.process_handshake_response(response)
        assert client_session.state == SessionState.HANDSHAKE_COMPLETE

        # Both should have encryption keys
        assert client_session.crypto.has_key
        assert server_session.crypto.has_key

    def test_encrypt_decrypt(self):
        server_kp = KeyPair.generate()
        server_session = Session(session_id=1, local_keypair=server_kp)

        client_kp = KeyPair.generate()
        client_session = Session(session_id=2, local_keypair=client_kp)

        # Complete handshake
        init = client_session.initiate_handshake()
        response = server_session.process_handshake_init(init)
        client_session.process_handshake_response(response)

        # Mark as established
        client_session.mark_established()
        server_session.mark_established()

        # Client encrypts
        plaintext = b"Hello, VPN!"
        transport_packet = client_session.encrypt_packet(plaintext)

        # Server decrypts
        decrypted = server_session.decrypt_packet(transport_packet)
        assert decrypted == plaintext

    def test_keepalive(self):
        kp = KeyPair.generate()
        session = Session(session_id=1, local_keypair=kp)
        session.mark_established()

        # Initially should send keepalive (enough time has passed)
        session._last_keepalive_sent = 0  # Force
        assert session.should_send_keepalive()

        keepalive = session.create_keepalive()
        assert keepalive.session_id == 1

        # After sending, should not need another immediately
        assert not session.should_send_keepalive()

    def test_close(self):
        kp = KeyPair.generate()
        session = Session(session_id=1, local_keypair=kp)
        session.close()
        assert session.state == SessionState.CLOSED
