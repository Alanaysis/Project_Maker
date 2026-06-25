"""Tests for the peer module."""

import time
import pytest
from vpn.peer import Peer, PeerManager, PeerState


class TestPeer:
    def test_creation(self):
        peer = Peer(
            public_key=b"\xAA" * 32,
            endpoint=("192.168.1.1", 51820),
            session_id=1,
        )
        assert peer.public_key == b"\xAA" * 32
        assert peer.endpoint == ("192.168.1.1", 51820)
        assert peer.state == PeerState.DISCONNECTED

    def test_allowed_ips(self):
        peer = Peer(public_key=b"\xAA" * 32)
        peer.add_allowed_ip("10.0.0.2")
        peer.add_allowed_ip("10.0.0.3")

        assert peer.is_ip_allowed("10.0.0.2")
        assert peer.is_ip_allowed("10.0.0.3")
        assert not peer.is_ip_allowed("10.0.0.4")

    def test_remove_allowed_ip(self):
        peer = Peer(public_key=b"\xAA" * 32)
        peer.add_allowed_ip("10.0.0.2")
        peer.remove_allowed_ip("10.0.0.2")
        assert not peer.is_ip_allowed("10.0.0.2")

    def test_state_transitions(self):
        peer = Peer(public_key=b"\xAA" * 32)
        assert peer.state == PeerState.DISCONNECTED

        peer.state = PeerState.HANDSHAKING
        assert peer.state == PeerState.HANDSHAKING

        peer.state = PeerState.CONNECTED
        assert peer.state == PeerState.CONNECTED

    def test_stats(self):
        peer = Peer(public_key=b"\xAA" * 32)
        peer.update_rx(100)
        peer.update_tx(200)

        assert peer.stats.rx_bytes == 100
        assert peer.stats.tx_bytes == 200
        assert peer.stats.rx_packets == 1
        assert peer.stats.tx_packets == 1

    def test_handshake_counter(self):
        peer = Peer(public_key=b"\xAA" * 32)
        assert peer.handshake_attempts == 0

        peer.increment_handshake()
        assert peer.handshake_attempts == 1

        peer.reset_handshake()
        assert peer.handshake_attempts == 0

    def test_activity_tracking(self):
        peer = Peer(public_key=b"\xAA" * 32)
        peer.update_activity()
        assert peer.time_since_activity < 1.0


class TestPeerManager:
    def test_add_remove(self):
        manager = PeerManager()
        peer = Peer(public_key=b"\xAA" * 32)

        manager.add_peer(peer)
        assert manager.peer_count == 1

        removed = manager.remove_peer(b"\xAA" * 32)
        assert removed is not None
        assert manager.peer_count == 0

    def test_lookup_by_key(self):
        manager = PeerManager()
        peer = Peer(public_key=b"\xAA" * 32)
        manager.add_peer(peer)

        found = manager.get_peer_by_key(b"\xAA" * 32)
        assert found is not None
        assert found.public_key == b"\xAA" * 32

        assert manager.get_peer_by_key(b"\xBB" * 32) is None

    def test_lookup_by_session(self):
        manager = PeerManager()
        peer = Peer(public_key=b"\xAA" * 32, session_id=42)
        manager.add_peer(peer)

        found = manager.get_peer_by_session(42)
        assert found is not None

        assert manager.get_peer_by_session(99) is None

    def test_lookup_by_ip(self):
        manager = PeerManager()
        peer = Peer(public_key=b"\xAA" * 32)
        peer.add_allowed_ip("10.0.0.2")
        manager.add_peer(peer)
        manager.register_ip("10.0.0.2", b"\xAA" * 32)

        found = manager.get_peer_by_ip("10.0.0.2")
        assert found is not None

        assert manager.get_peer_by_ip("10.0.0.3") is None

    def test_total_traffic(self):
        manager = PeerManager()

        peer1 = Peer(public_key=b"\xAA" * 32)
        peer1.update_rx(100)
        peer1.update_tx(200)
        manager.add_peer(peer1)

        peer2 = Peer(public_key=b"\xBB" * 32)
        peer2.update_rx(300)
        peer2.update_tx(400)
        manager.add_peer(peer2)

        total_rx, total_tx = manager.total_traffic()
        assert total_rx == 400
        assert total_tx == 600
