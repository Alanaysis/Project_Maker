"""
VPN Tunnel Manager.

The core component that ties together:
- TUN device for local packet capture
- UDP/TCP transport for remote communication
- Encryption for data confidentiality
- Peer management for connection tracking
- Protocol for session lifecycle
"""

import os
import socket
import struct
import asyncio
import logging
import time
from typing import Optional, Dict, Tuple

from vpn.config import VPNConfig
from vpn.crypto import CryptoEngine, KeyPair
from vpn.packet import (
    MessageType,
    HandshakeInitPacket,
    HandshakeResponsePacket,
    TransportDataPacket,
    AuthRequestPacket,
    AuthResponsePacket,
    KeepalivePacket,
    parse_message_type,
    IPv4Packet,
)
from vpn.peer import Peer, PeerManager, PeerState
from vpn.protocol import Session, SessionConfig, SessionState
from vpn.tun_device import TunDevice, TunConfig, RouteManager
from vpn.auth import PasswordAuthenticator, CertificateAuthenticator
from vpn.error import VpnError, NetworkError

logger = logging.getLogger(__name__)


class VpnTunnel:
    """
    Main VPN tunnel that manages the full VPN lifecycle.

    Operates in two modes:
    - Server: listens for incoming connections
    - Client: connects to a server
    """

    def __init__(self, config: VPNConfig, mode: str = "server") -> None:
        """
        Initialize the VPN tunnel.

        Args:
            config: VPN configuration
            mode: "server" or "client"
        """
        self._config = config
        self._mode = mode
        self._running = False

        # Core components
        self._local_keypair = KeyPair.generate()
        self._peer_manager = PeerManager(timeout=config.server.keepalive_interval * 3)
        self._session_counter = 0
        self._sessions: Dict[int, Session] = {}

        # TUN device
        tun_config = TunConfig(
            name=config.tun.name,
            address=config.tun.address,
            netmask=config.tun.netmask,
            mtu=config.tun.mtu,
        )
        self._tun = TunDevice(tun_config)

        # Transport
        self._transport_socket: Optional[socket.socket] = None
        self._tcp_server: Optional[asyncio.Server] = None

        # Authentication
        self._password_auth: Optional[PasswordAuthenticator] = None
        self._cert_auth: Optional[CertificateAuthenticator] = None
        self._setup_authentication()

        # Client mode state
        self._client_session: Optional[Session] = None
        self._client_peer: Optional[Peer] = None

        # Statistics
        self._start_time: float = 0

    def _setup_authentication(self) -> None:
        """Set up authentication based on config."""
        sec = self._config.security

        if sec.auth_method == "password":
            self._password_auth = PasswordAuthenticator()
            if sec.users_file and os.path.exists(sec.users_file):
                self._password_auth.load_from_file(sec.users_file)
        elif sec.auth_method == "certificate":
            self._cert_auth = CertificateAuthenticator()
            if sec.ca_cert:
                self._cert_auth.load_ca(
                    sec.ca_cert,
                    sec.ca_key,
                )

    def _next_session_id(self) -> int:
        self._session_counter += 1
        return self._session_counter

    # ---- Lifecycle ----

    async def start(self) -> None:
        """Start the VPN tunnel."""
        if self._running:
            return

        self._running = True
        self._start_time = time.time()

        # Open TUN device
        self._tun.open()
        logger.info(f"TUN device opened: {self._tun.name} ({self._config.tun.address})")

        if self._mode == "server":
            await self._start_server()
        else:
            await self._start_client()

    async def _start_server(self) -> None:
        """Start in server mode."""
        cfg = self._config.server

        if cfg.transport == "tcp":
            await self._start_tcp_server()
        else:
            await self._start_udp_server()

    async def _start_udp_server(self) -> None:
        """Start UDP server."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self._config.server.listen_address, self._config.server.port))
        sock.setblocking(False)

        self._transport_socket = sock
        logger.info(f"UDP server listening on {self._config.server.listen_address}:{self._config.server.port}")

        # Start reader tasks
        asyncio.create_task(self._udp_read_loop())
        asyncio.create_task(self._tun_read_loop())
        asyncio.create_task(self._maintenance_loop())

    async def _start_tcp_server(self) -> None:
        """Start TCP server."""
        async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            addr = writer.get_extra_info("peername")
            logger.info(f"TCP client connected: {addr}")
            try:
                await self._tcp_client_loop(reader, writer, addr)
            except Exception as e:
                logger.error(f"TCP client error: {e}")
            finally:
                writer.close()
                await writer.wait_closed()

        self._tcp_server = await asyncio.start_server(
            handle_client,
            self._config.server.listen_address,
            self._config.server.port,
        )
        logger.info(f"TCP server listening on {self._config.server.listen_address}:{self._config.server.port}")

        asyncio.create_task(self._tun_read_loop())
        asyncio.create_task(self._maintenance_loop())

    async def _start_client(self) -> None:
        """Start in client mode and connect to server."""
        cfg = self._config.client

        if cfg.transport == "tcp":
            await self._start_tcp_client()
        else:
            await self._start_udp_client()

    async def _start_udp_client(self) -> None:
        """Start UDP client."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)

        self._transport_socket = sock

        # Create client session
        session_id = self._next_session_id()
        self._client_session = Session(
            session_id=session_id,
            local_keypair=self._local_keypair,
            config=SessionConfig(
                keepalive_interval=self._config.server.keepalive_interval,
                handshake_timeout=self._config.security.handshake_timeout,
            ),
        )

        # Create client peer
        self._client_peer = Peer(
            public_key=b"",
            endpoint=(self._config.client.server_address, self._config.client.server_port),
            session_id=session_id,
        )
        self._peer_manager.add_peer(self._client_peer)

        # Initiate handshake
        init_packet = self._client_session.initiate_handshake()
        server_addr = (cfg.server_address, cfg.server_port)
        self._send_udp(init_packet.to_bytes(), server_addr)

        logger.info(f"Connecting to VPN server at {server_addr}")

        # Start reader tasks
        asyncio.create_task(self._udp_read_loop())
        asyncio.create_task(self._tun_read_loop())
        asyncio.create_task(self._maintenance_loop())

    async def _start_tcp_client(self) -> None:
        """Start TCP client."""
        cfg = self._config.client
        reader, writer = await asyncio.open_connection(cfg.server_address, cfg.server_port)

        session_id = self._next_session_id()
        self._client_session = Session(
            session_id=session_id,
            local_keypair=self._local_keypair,
        )

        # Initiate handshake
        init_packet = self._client_session.initiate_handshake()
        writer.write(init_packet.to_bytes())
        await writer.drain()

        asyncio.create_task(self._tcp_read_loop(reader))
        asyncio.create_task(self._tun_read_loop())
        asyncio.create_task(self._maintenance_loop())

    async def stop(self) -> None:
        """Stop the VPN tunnel."""
        if not self._running:
            return

        self._running = False

        # Close sessions
        for session in self._sessions.values():
            session.close()
        if self._client_session:
            self._client_session.close()

        # Close transport
        if self._transport_socket:
            self._transport_socket.close()
        if self._tcp_server:
            self._tcp_server.close()
            await self._tcp_server.wait_closed()

        # Close TUN
        self._tun.close()

        logger.info("VPN tunnel stopped")

    # ---- Packet I/O ----

    def _send_udp(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Send data via UDP."""
        if self._transport_socket:
            try:
                self._transport_socket.sendto(data, addr)
            except OSError as e:
                logger.error(f"UDP send error: {e}")

    async def _udp_read_loop(self) -> None:
        """Read packets from UDP socket."""
        loop = asyncio.get_event_loop()
        buf = bytearray(65535)

        while self._running:
            try:
                data, addr = await loop.sock_recvfrom(self._transport_socket, 65535)
                await self._process_incoming(data, addr)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._running:
                    logger.error(f"UDP read error: {e}")

    async def _tcp_read_loop(self, reader: asyncio.StreamReader) -> None:
        """Read packets from TCP stream."""
        while self._running:
            try:
                # Read length prefix (4 bytes)
                length_data = await reader.readexactly(4)
                length = struct.unpack("!I", length_data)[0]
                data = await reader.readexactly(length)
                addr = ("tcp", 0)
                await self._process_incoming(data, addr)
            except asyncio.IncompleteReadError:
                logger.info("TCP connection closed")
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._running:
                    logger.error(f"TCP read error: {e}")

    async def _tcp_client_loop(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        addr: Tuple[str, int],
    ) -> None:
        """Handle a TCP client connection."""
        while self._running:
            try:
                length_data = await reader.readexactly(4)
                length = struct.unpack("!I", length_data)[0]
                data = await reader.readexactly(length)
                await self._process_incoming(data, addr)
            except asyncio.IncompleteReadError:
                break
            except asyncio.CancelledError:
                break

    async def _tun_read_loop(self) -> None:
        """Read packets from TUN device and forward to peers."""
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                packet = await loop.run_in_executor(None, self._tun.read_packet)
                await self._process_outgoing(packet)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._running:
                    logger.error(f"TUN read error: {e}")

    # ---- Packet Processing ----

    async def _process_incoming(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Process an incoming packet from the transport."""
        try:
            msg_type = parse_message_type(data)
        except Exception:
            logger.warning(f"Received invalid packet from {addr}")
            return

        if msg_type == MessageType.HANDSHAKE_INIT:
            await self._handle_handshake_init(data, addr)
        elif msg_type == MessageType.HANDSHAKE_RESPONSE:
            await self._handle_handshake_response(data, addr)
        elif msg_type == MessageType.TRANSPORT_DATA:
            await self._handle_transport_data(data, addr)
        elif msg_type == MessageType.AUTH_REQUEST:
            await self._handle_auth_request(data, addr)
        elif msg_type == MessageType.AUTH_RESPONSE:
            await self._handle_auth_response(data, addr)
        elif msg_type == MessageType.KEEPALIVE:
            await self._handle_keepalive(data, addr)
        elif msg_type == MessageType.DISCONNECT:
            await self._handle_disconnect(data, addr)

    async def _handle_handshake_init(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle incoming handshake initiation (server side)."""
        packet = HandshakeInitPacket.parse(data)
        logger.info(f"Handshake initiation from {addr}, session {packet.sender_index}")

        # Create new session for this peer
        session_id = self._next_session_id()
        session = Session(
            session_id=session_id,
            local_keypair=self._local_keypair,
        )
        self._sessions[session_id] = session

        # Create peer
        peer = Peer(
            public_key=packet.public_key,
            endpoint=addr,
            session_id=session_id,
        )
        self._peer_manager.add_peer(peer)
        peer.state = PeerState.HANDSHAKING

        # Process handshake and send response
        response = session.process_handshake_init(packet)
        self._send_udp(response.to_bytes(), addr)

    async def _handle_handshake_response(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle handshake response (client side)."""
        packet = HandshakeResponsePacket.parse(data)
        logger.info(f"Handshake response from {addr}, session {packet.receiver_index}")

        session = self._client_session
        if session is None:
            logger.warning("Received handshake response but no client session")
            return

        session.process_handshake_response(packet)

        # Update peer with remote public key
        if self._client_peer:
            self._client_peer._public_key = packet.public_key
            self._client_peer.state = PeerState.AUTHENTICATING

        # Send authentication
        if self._config.security.auth_method == "password" and self._password_auth:
            # In client mode, the client should have credentials configured
            logger.info("Session ready for authentication")
            session.mark_established()
            if self._client_peer:
                self._client_peer.state = PeerState.CONNECTED
        elif self._config.security.auth_method == "certificate" and self._config.security.cert_file:
            with open(self._config.security.cert_file, "rb") as f:
                cert_pem = f.read()
            auth_req = session.create_cert_auth_request(cert_pem)
            self._send_udp(auth_req.to_bytes(), addr)
        else:
            # No auth configured, mark as established
            session.mark_established()
            if self._client_peer:
                self._client_peer.state = PeerState.CONNECTED

    async def _handle_transport_data(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle incoming encrypted transport data."""
        packet = TransportDataPacket.parse(data)

        # Find session
        session = self._sessions.get(packet.session_id)
        if session is None:
            session = self._client_session
        if session is None or not session.is_established:
            logger.warning(f"Received transport data for unknown session {packet.session_id}")
            return

        try:
            plaintext = session.decrypt_packet(packet)

            # Write to TUN device
            self._tun.write_packet(plaintext)

            # Update peer stats
            peer = self._peer_manager.get_peer_by_session(packet.session_id)
            if peer:
                peer.update_rx(len(data))

        except Exception as e:
            logger.error(f"Failed to process transport data: {e}")

    async def _handle_auth_request(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle authentication request (server side)."""
        packet = AuthRequestPacket.parse(data)

        session = self._sessions.get(packet.session_id)
        if session is None:
            return

        peer = self._peer_manager.get_peer_by_session(packet.session_id)
        if peer is None:
            return

        success = False
        allowed_ips = None

        if packet.auth_type == 1 and self._password_auth:
            # Password authentication
            if len(packet.password_hash) >= 32:
                password_hash = packet.password_hash[:32]
                success, allowed_ips = self._password_auth.authenticate_hash(
                    packet.username, password_hash
                )
                if success:
                    peer.username = packet.username
                    logger.info(f"User '{packet.username}' authenticated from {addr}")

        elif packet.auth_type == 2 and self._cert_auth:
            # Certificate authentication
            success, allowed_ips = self._cert_auth.authenticate(packet.certificate)
            if success:
                logger.info(f"Certificate authenticated from {addr}")

        # Send response
        response = AuthResponsePacket(
            session_id=packet.session_id,
            success=success,
            message="Authenticated" if success else "Authentication failed",
        )
        self._send_udp(response.to_bytes(), addr)

        if success:
            peer.authenticated = True
            peer.state = PeerState.CONNECTED
            session.mark_established()

            # Set allowed IPs
            if allowed_ips:
                for ip in allowed_ips:
                    peer.add_allowed_ip(ip)
                    self._peer_manager.register_ip(ip, peer.public_key)

            # Assign VPN IP to peer (simplified)
            # In a real implementation, this would use an IP pool
            logger.info(f"Peer authenticated and connected: {peer}")
        else:
            peer.state = PeerState.DISCONNECTED

    async def _handle_auth_response(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle authentication response (client side)."""
        packet = AuthResponsePacket.parse(data)

        if packet.success:
            logger.info("Authentication successful")
            if self._client_session:
                self._client_session.mark_established()
            if self._client_peer:
                self._client_peer.authenticated = True
                self._client_peer.state = PeerState.CONNECTED
        else:
            logger.error(f"Authentication failed: {packet.message}")

    async def _handle_keepalive(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle keepalive packet."""
        packet = KeepalivePacket.parse(data)
        session = self._sessions.get(packet.session_id) or self._client_session
        if session:
            session.process_keepalive()

    async def _handle_disconnect(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle disconnect packet."""
        logger.info(f"Peer at {addr} disconnected")
        # Find and remove the peer
        for peer in self._peer_manager.all_peers:
            if peer.endpoint == addr:
                peer.state = PeerState.DISCONNECTED
                break

    async def _process_outgoing(self, packet: bytes) -> None:
        """Process an outgoing packet from TUN."""
        try:
            ip_packet = IPv4Packet.parse(packet)
        except Exception:
            return

        dest_ip = ip_packet.destination

        # Find peer by destination IP
        peer = self._peer_manager.get_peer_by_ip(dest_ip)

        # In client mode, send everything to server
        if peer is None and self._mode == "client":
            peer = self._client_peer

        if peer is None:
            return

        session = self._sessions.get(peer.session_id) or self._client_session
        if session is None or not session.is_established:
            return

        try:
            transport_packet = session.encrypt_packet(packet)
            data = transport_packet.to_bytes()

            if peer.endpoint:
                if self._mode == "client":
                    # Client sends to server
                    self._send_udp(data, peer.endpoint)
                else:
                    self._send_udp(data, peer.endpoint)

                peer.update_tx(len(data))
        except Exception as e:
            logger.error(f"Failed to send packet: {e}")

    # ---- Maintenance ----

    async def _maintenance_loop(self) -> None:
        """Periodic maintenance tasks."""
        while self._running:
            try:
                await asyncio.sleep(1.0)

                # Check handshake timeouts (client mode)
                if self._client_session and self._client_session.state == SessionState.HANDSHAKE_SENT:
                    if self._client_session.check_handshake_timeout():
                        if self._client_session._handshake_attempts < 5:
                            init = self._client_session.initiate_handshake()
                            server_addr = (
                                self._config.client.server_address,
                                self._config.client.server_port,
                            )
                            self._send_udp(init.to_bytes(), server_addr)
                        else:
                            logger.error("Handshake failed after max attempts")
                            break

                # Send keepalives
                if self._client_session and self._client_session.should_send_keepalive():
                    keepalive = self._client_session.create_keepalive()
                    if self._client_peer and self._client_peer.endpoint:
                        self._send_udp(keepalive.to_bytes(), self._client_peer.endpoint)

                # Update peer manager (check timeouts)
                removed = self._peer_manager.update()
                for key in removed:
                    session = self._sessions.pop(key, None)
                    if session:
                        session.close()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Maintenance error: {e}")

    # ---- Public API ----

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def tun_name(self) -> Optional[str]:
        return self._tun.name

    @property
    def peer_count(self) -> int:
        return self._peer_manager.peer_count

    def get_stats(self) -> dict:
        """Get tunnel statistics."""
        total_rx, total_tx = self._peer_manager.total_traffic()
        return {
            "running": self._running,
            "mode": self._mode,
            "tun_device": self._tun.name,
            "tun_address": self._config.tun.address,
            "peer_count": self._peer_manager.peer_count,
            "total_rx_bytes": total_rx,
            "total_tx_bytes": total_tx,
            "uptime": time.time() - self._start_time if self._start_time else 0,
        }
