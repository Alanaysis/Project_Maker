"""
Peer management for VPN connections.

Tracks peer state, authentication, allowed IPs, and statistics.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List

from vpn.crypto import CryptoEngine
from vpn.error import PeerError


class PeerState(Enum):
    """Connection state of a VPN peer."""
    DISCONNECTED = "disconnected"
    HANDSHAKING = "handshaking"
    AUTHENTICATING = "authenticating"
    CONNECTED = "connected"
    TIMING_OUT = "timing_out"


@dataclass
class PeerStats:
    """Traffic statistics for a peer."""
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_packets: int = 0
    tx_packets: int = 0
    connected_since: float = 0.0
    last_activity: float = 0.0


class Peer:
    """
    Represents a VPN peer connection.

    Manages cryptographic state, authentication, allowed IPs,
    and traffic statistics for a single peer.
    """

    def __init__(
        self,
        public_key: bytes,
        endpoint: Optional[tuple] = None,
        session_id: int = 0,
    ) -> None:
        self._public_key = public_key
        self._endpoint = endpoint  # (host, port)
        self._session_id = session_id
        self._state = PeerState.DISCONNECTED
        self._crypto = CryptoEngine()
        self._allowed_ips: List[str] = []
        self._stats = PeerStats()
        self._handshake_attempts = 0
        self._last_activity = time.time()
        self._authenticated = False
        self._username: Optional[str] = None

    # ---- Properties ----

    @property
    def public_key(self) -> bytes:
        return self._public_key

    @property
    def endpoint(self) -> Optional[tuple]:
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value: Optional[tuple]) -> None:
        self._endpoint = value
        self._last_activity = time.time()

    @property
    def session_id(self) -> int:
        return self._session_id

    @session_id.setter
    def session_id(self, value: int) -> None:
        self._session_id = value

    @property
    def state(self) -> PeerState:
        return self._state

    @state.setter
    def state(self, value: PeerState) -> None:
        self._state = value
        self._last_activity = time.time()
        if value == PeerState.CONNECTED:
            self._stats.connected_since = time.time()

    @property
    def crypto(self) -> CryptoEngine:
        return self._crypto

    @property
    def authenticated(self) -> bool:
        return self._authenticated

    @authenticated.setter
    def authenticated(self, value: bool) -> None:
        self._authenticated = value

    @property
    def username(self) -> Optional[str]:
        return self._username

    @username.setter
    def username(self, value: Optional[str]) -> None:
        self._username = value

    @property
    def stats(self) -> PeerStats:
        return self._stats

    # ---- Allowed IPs ----

    def add_allowed_ip(self, ip: str) -> None:
        """Add an IP address that this peer is allowed to send to/receive from."""
        if ip not in self._allowed_ips:
            self._allowed_ips.append(ip)

    def remove_allowed_ip(self, ip: str) -> None:
        """Remove an allowed IP."""
        if ip in self._allowed_ips:
            self._allowed_ips.remove(ip)

    @property
    def allowed_ips(self) -> List[str]:
        return self._allowed_ips.copy()

    def is_ip_allowed(self, ip: str) -> bool:
        """Check if an IP is in the allowed list."""
        return ip in self._allowed_ips

    # ---- Handshake ----

    @property
    def handshake_attempts(self) -> int:
        return self._handshake_attempts

    def increment_handshake(self) -> None:
        self._handshake_attempts += 1
        self._last_activity = time.time()

    def reset_handshake(self) -> None:
        self._handshake_attempts = 0

    # ---- Activity / Stats ----

    def update_activity(self) -> None:
        self._last_activity = time.time()

    @property
    def time_since_activity(self) -> float:
        return time.time() - self._last_activity

    def update_rx(self, n_bytes: int) -> None:
        self._stats.rx_bytes += n_bytes
        self._stats.rx_packets += 1
        self._stats.last_activity = time.time()
        self._last_activity = time.time()

    def update_tx(self, n_bytes: int) -> None:
        self._stats.tx_bytes += n_bytes
        self._stats.tx_packets += 1
        self._stats.last_activity = time.time()
        self._last_activity = time.time()

    def __repr__(self) -> str:
        return (
            f"Peer(session={self._session_id}, state={self._state.value}, "
            f"endpoint={self._endpoint}, ips={self._allowed_ips})"
        )


class PeerManager:
    """
    Manages multiple VPN peers.

    Tracks all connected peers and provides lookup by
    public key, session ID, or IP address.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        self._peers: Dict[bytes, Peer] = {}  # public_key -> Peer
        self._session_map: Dict[int, bytes] = {}  # session_id -> public_key
        self._ip_map: Dict[str, bytes] = {}  # ip -> public_key
        self._timeout = timeout

    # ---- Peer Management ----

    def add_peer(self, peer: Peer) -> None:
        """Register a new peer."""
        self._peers[peer.public_key] = peer
        if peer.session_id:
            self._session_map[peer.session_id] = peer.public_key
        for ip in peer.allowed_ips:
            self._ip_map[ip] = peer.public_key

    def remove_peer(self, public_key: bytes) -> Optional[Peer]:
        """Remove a peer."""
        peer = self._peers.pop(public_key, None)
        if peer:
            if peer.session_id in self._session_map:
                del self._session_map[peer.session_id]
            for ip in peer.allowed_ips:
                self._ip_map.pop(ip, None)
        return peer

    def get_peer_by_key(self, public_key: bytes) -> Optional[Peer]:
        return self._peers.get(public_key)

    def get_peer_by_session(self, session_id: int) -> Optional[Peer]:
        key = self._session_map.get(session_id)
        if key:
            return self._peers.get(key)
        return None

    def get_peer_by_ip(self, ip: str) -> Optional[Peer]:
        key = self._ip_map.get(ip)
        if key:
            return self._peers.get(key)
        return None

    # ---- Iteration ----

    @property
    def peer_count(self) -> int:
        return len(self._peers)

    @property
    def all_peers(self) -> list:
        return list(self._peers.values())

    # ---- Maintenance ----

    def update(self) -> List[bytes]:
        """
        Update all peers: check for timeouts.

        Returns list of public keys for peers that were removed.
        """
        to_remove: List[bytes] = []

        for key, peer in self._peers.items():
            if peer.state == PeerState.CONNECTED:
                if peer.time_since_activity > self._timeout:
                    peer.state = PeerState.TIMING_OUT
            elif peer.state == PeerState.TIMING_OUT:
                if peer.time_since_activity > self._timeout * 2:
                    to_remove.append(key)

        for key in to_remove:
            self.remove_peer(key)

        return to_remove

    def register_ip(self, ip: str, public_key: bytes) -> None:
        """Register an IP address mapping for a peer."""
        self._ip_map[ip] = public_key

    def total_traffic(self) -> tuple:
        """Get total (rx_bytes, tx_bytes) across all peers."""
        total_rx = sum(p.stats.rx_bytes for p in self._peers.values())
        total_tx = sum(p.stats.tx_bytes for p in self._peers.values())
        return total_rx, total_tx
