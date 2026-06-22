//! VPN tunnel implementation
//!
//! Manages the VPN tunnel lifecycle including:
//! - Handshake initiation and processing
//! - Data encryption and decryption
//! - Packet routing
//! - Connection state management

use std::net::SocketAddr;
use std::sync::Arc;

use tokio::net::UdpSocket;
use tokio::sync::Mutex;

use crate::crypto::CryptoState;
use crate::error::{Result, VpnError};
use crate::packet::{DataPacket, HandshakePacket, Ipv4Packet};
use crate::peer::{Peer, PeerManager, PeerState};
use crate::protocol::{HandshakeInitiation, HandshakeResponse, MessageType, TransportData};
use crate::tun_device::{TunConfig, TunDevice};

/// VPN tunnel configuration
#[derive(Debug, Clone)]
pub struct TunnelConfig {
    /// Local listening port
    pub listen_port: u16,
    /// TUN device configuration
    pub tun_config: TunConfig,
    /// Peer public key (for simple mode)
    pub peer_public_key: Option<[u8; 32]>,
    /// Peer endpoint (for simple mode)
    pub peer_endpoint: Option<SocketAddr>,
}

impl Default for TunnelConfig {
    fn default() -> Self {
        Self {
            listen_port: 51820,
            tun_config: TunConfig::default(),
            peer_public_key: None,
            peer_endpoint: None,
        }
    }
}

/// VPN tunnel state
pub struct VpnTunnel {
    /// Tunnel configuration
    config: TunnelConfig,
    /// UDP socket for tunnel traffic
    socket: Arc<UdpSocket>,
    /// TUN device
    tun: Arc<Mutex<TunDevice>>,
    /// Local crypto state
    crypto: Arc<Mutex<CryptoState>>,
    /// Peer manager
    peers: Arc<Mutex<PeerManager>>,
    /// Running state
    running: Arc<Mutex<bool>>,
}

impl VpnTunnel {
    /// Create a new VPN tunnel
    pub async fn new(config: TunnelConfig) -> Result<Self> {
        // Create UDP socket
        let socket = UdpSocket::bind(format!("0.0.0.0:{}", config.listen_port))
            .await
            .map_err(|e| VpnError::NetworkError(format!("Failed to bind UDP socket: {}", e)))?;

        // Create TUN device
        let tun = TunDevice::new(config.tun_config.clone())?;

        // Create crypto state
        let crypto = CryptoState::new();

        // Create peer manager
        let peers = PeerManager::new();

        Ok(Self {
            config,
            socket: Arc::new(socket),
            tun: Arc::new(Mutex::new(tun)),
            crypto: Arc::new(Mutex::new(crypto)),
            peers: Arc::new(Mutex::new(peers)),
            running: Arc::new(Mutex::new(false)),
        })
    }

    /// Start the VPN tunnel
    pub async fn start(&self) -> Result<()> {
        let mut running = self.running.lock().await;
        if *running {
            return Err(VpnError::NetworkError("Tunnel already running".to_string()));
        }
        *running = true;
        drop(running);

        tracing::info!("Starting VPN tunnel on port {}", self.config.listen_port);

        // Start packet forwarding tasks
        self.start_tun_reader().await;
        self.start_socket_reader().await;

        // Initiate handshake with peer if configured
        if let (Some(peer_key), Some(peer_endpoint)) = (
            &self.config.peer_public_key,
            &self.config.peer_endpoint,
        ) {
            self.initiate_handshake(peer_key, peer_endpoint).await?;
        }

        Ok(())
    }

    /// Stop the VPN tunnel
    pub async fn stop(&self) -> Result<()> {
        let mut running = self.running.lock().await;
        *running = false;
        tracing::info!("Stopping VPN tunnel");
        Ok(())
    }

    /// Add a peer to the tunnel
    pub async fn add_peer(&self, public_key: [u8; 32], endpoint: Option<SocketAddr>) -> Result<()> {
        let mut peers = self.peers.lock().await;
        let peer = Peer::new(public_key, endpoint);
        peers.add_peer(peer);
        tracing::info!("Added peer: {:?}", public_key);
        Ok(())
    }

    /// Initiate handshake with a peer
    async fn initiate_handshake(&self, peer_key: &[u8; 32], peer_endpoint: &SocketAddr) -> Result<()> {
        let mut peers = self.peers.lock().await;

        if let Some(peer) = peers.get_peer_mut(peer_key) {
            peer.set_state(PeerState::Handshaking);
            peer.set_endpoint(*peer_endpoint);
            peer.increment_handshake_attempts();

            // Create handshake initiation message
            let initiation = HandshakeInitiation {
                message_type: MessageType::HandshakeInitiation as u8,
                reserved: [0; 3],
                sender_index: 1, // Simplified
                encrypted_ephemeral: [0; 32],
                encrypted_static: [0; 48],
                encrypted_timestamp: [0; 28],
                mac1: [0; 16],
                mac2: [0; 16],
            };

            let bytes = initiation.to_bytes();
            self.socket.send_to(&bytes, peer_endpoint).await
                .map_err(|e| VpnError::NetworkError(format!("Failed to send handshake: {}", e)))?;

            tracing::info!("Initiated handshake with peer at {}", peer_endpoint);
        }

        Ok(())
    }

    /// Start reading from TUN device
    async fn start_tun_reader(&self) {
        let tun = self.tun.clone();
        let socket = self.socket.clone();
        let peers = self.peers.clone();
        let crypto = self.crypto.clone();
        let running = self.running.clone();

        tokio::spawn(async move {
            loop {
                {
                    let running = running.lock().await;
                    if !running {
                        break;
                    }
                }

                let packet = {
                    let mut tun = tun.lock().await;
                    match tun.read_packet() {
                        Ok(packet) => packet,
                        Err(e) => {
                            tracing::error!("Failed to read from TUN: {}", e);
                            continue;
                        }
                    }
                };

                // Process outgoing packet
                if let Err(e) = Self::process_outgoing_packet(&socket, &peers, &crypto, &packet).await {
                    tracing::error!("Failed to process outgoing packet: {}", e);
                }
            }
        });
    }

    /// Start reading from UDP socket
    async fn start_socket_reader(&self) {
        let tun = self.tun.clone();
        let socket = self.socket.clone();
        let peers = self.peers.clone();
        let crypto = self.crypto.clone();
        let running = self.running.clone();

        tokio::spawn(async move {
            let mut buf = vec![0u8; 65535];

            loop {
                {
                    let running = running.lock().await;
                    if !running {
                        break;
                    }
                }

                let (len, addr) = match socket.recv_from(&mut buf).await {
                    Ok(result) => result,
                    Err(e) => {
                        tracing::error!("Failed to receive from socket: {}", e);
                        continue;
                    }
                };

                let data = &buf[..len];

                // Process incoming packet
                if let Err(e) = Self::process_incoming_packet(&tun, &peers, &crypto, data, addr).await {
                    tracing::error!("Failed to process incoming packet: {}", e);
                }
            }
        });
    }

    /// Process an outgoing packet from TUN
    async fn process_outgoing_packet(
        socket: &UdpSocket,
        peers: &Arc<Mutex<PeerManager>>,
        crypto: &Arc<Mutex<CryptoState>>,
        packet: &[u8],
    ) -> Result<()> {
        // Parse the IP packet
        let ip_packet = Ipv4Packet::parse(packet)?;

        // Find the peer for this destination
        let peers = peers.lock().await;
        let peer = peers.find_peer_by_ip(&ip_packet.header.destination)
            .ok_or_else(|| VpnError::PeerNotFound(format!(
                "No peer found for destination: {}",
                ip_packet.header.destination
            )))?;

        if let Some(endpoint) = peer.endpoint() {
            // Encrypt the packet payload
            let encrypted_payload = {
                let mut crypto = crypto.lock().await;
                crypto.encrypt(packet)?
            };

            // Create data packet
            let data_packet = DataPacket {
                receiver_index: 0, // Would be set from peer state
                counter: 0,        // Would be from crypto state
                encrypted_payload,
            };

            let bytes = data_packet.to_bytes();
            socket.send_to(&bytes, endpoint).await
                .map_err(|e| VpnError::NetworkError(format!("Failed to send packet: {}", e)))?;

            tracing::debug!("Sent {} bytes to {}", bytes.len(), endpoint);
        }

        Ok(())
    }

    /// Process an incoming packet from UDP socket
    async fn process_incoming_packet(
        tun: &Arc<Mutex<TunDevice>>,
        peers: &Arc<Mutex<PeerManager>>,
        crypto: &Arc<Mutex<CryptoState>>,
        data: &[u8],
        addr: SocketAddr,
    ) -> Result<()> {
        // Parse message type
        if data.is_empty() {
            return Err(VpnError::ProtocolError("Empty packet".to_string()));
        }

        let message_type = MessageType::try_from(data[0])?;

        match message_type {
            MessageType::HandshakeInitiation => {
                tracing::info!("Received handshake initiation from {}", addr);
                // Would process handshake here
            }
            MessageType::HandshakeResponse => {
                tracing::info!("Received handshake response from {}", addr);
                // Would complete handshake here
            }
            MessageType::TransportData => {
                // Parse transport data
                let transport = TransportData::parse(data)?;

                // Decrypt payload
                let plaintext = {
                    let crypto = crypto.lock().await;
                    crypto.decrypt(&transport.encrypted_payload)?
                };

                // Write to TUN device
                let mut tun = tun.lock().await;
                tun.write_packet(&plaintext)?;

                tracing::debug!("Received {} bytes from {}", plaintext.len(), addr);
            }
            MessageType::CookieReply => {
                tracing::info!("Received cookie reply from {}", addr);
                // Would handle DoS protection here
            }
        }

        Ok(())
    }

    /// Get tunnel statistics
    pub async fn stats(&self) -> TunnelStats {
        let peers = self.peers.lock().await;
        let mut total_rx = 0;
        let mut total_tx = 0;

        for peer in peers.peers().values() {
            total_rx += peer.rx_bytes();
            total_tx += peer.tx_bytes();
        }

        TunnelStats {
            peer_count: peers.peer_count(),
            total_rx_bytes: total_rx,
            total_tx_bytes: total_tx,
        }
    }
}

/// Tunnel statistics
#[derive(Debug, Clone)]
pub struct TunnelStats {
    /// Number of connected peers
    pub peer_count: usize,
    /// Total received bytes
    pub total_rx_bytes: u64,
    /// Total transmitted bytes
    pub total_tx_bytes: u64,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::Ipv4Addr;

    #[test]
    fn test_tunnel_config_default() {
        let config = TunnelConfig::default();
        assert_eq!(config.listen_port, 51820);
        assert_eq!(config.tun_config.name, "tun0");
    }

    #[test]
    fn test_tunnel_stats() {
        let stats = TunnelStats {
            peer_count: 2,
            total_rx_bytes: 1024,
            total_tx_bytes: 2048,
        };

        assert_eq!(stats.peer_count, 2);
        assert_eq!(stats.total_rx_bytes, 1024);
        assert_eq!(stats.total_tx_bytes, 2048);
    }
}
