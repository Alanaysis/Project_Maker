//! Peer management for VPN connections

use std::net::SocketAddr;
use std::time::Instant;

use crate::crypto::CryptoState;
use crate::error::{Result, VpnError};

/// Represents the state of a VPN peer
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PeerState {
    /// Peer is disconnected
    Disconnected,
    /// Handshake in progress
    Handshaking,
    /// Peer is connected and active
    Connected,
    /// Peer connection is timing out
    TimingOut,
}

/// Represents a VPN peer
pub struct Peer {
    /// Peer's public key
    public_key: [u8; 32],
    /// Peer's endpoint address
    endpoint: Option<SocketAddr>,
    /// Allowed IP addresses
    allowed_ips: Vec<std::net::Ipv4Addr>,
    /// Current state
    state: PeerState,
    /// Cryptographic state for this peer
    crypto: CryptoState,
    /// Last activity timestamp
    last_activity: Instant,
    /// Handshake attempts
    handshake_attempts: u32,
    /// RX bytes counter
    rx_bytes: u64,
    /// TX bytes counter
    tx_bytes: u64,
}

impl Peer {
    /// Create a new peer
    pub fn new(public_key: [u8; 32], endpoint: Option<SocketAddr>) -> Self {
        Self {
            public_key,
            endpoint,
            allowed_ips: Vec::new(),
            state: PeerState::Disconnected,
            crypto: CryptoState::new(),
            last_activity: Instant::now(),
            handshake_attempts: 0,
            rx_bytes: 0,
            tx_bytes: 0,
        }
    }

    /// Get the peer's public key
    pub fn public_key(&self) -> &[u8; 32] {
        &self.public_key
    }

    /// Get the peer's endpoint
    pub fn endpoint(&self) -> Option<&SocketAddr> {
        self.endpoint.as_ref()
    }

    /// Set the peer's endpoint
    pub fn set_endpoint(&mut self, endpoint: SocketAddr) {
        self.endpoint = Some(endpoint);
        self.last_activity = Instant::now();
    }

    /// Get the peer's state
    pub fn state(&self) -> &PeerState {
        &self.state
    }

    /// Set the peer's state
    pub fn set_state(&mut self, state: PeerState) {
        self.state = state;
        self.last_activity = Instant::now();
    }

    /// Add an allowed IP address
    pub fn add_allowed_ip(&mut self, ip: std::net::Ipv4Addr) {
        self.allowed_ips.push(ip);
    }

    /// Get allowed IP addresses
    pub fn allowed_ips(&self) -> &[std::net::Ipv4Addr] {
        &self.allowed_ips
    }

    /// Check if an IP is allowed for this peer
    pub fn is_ip_allowed(&self, ip: &std::net::Ipv4Addr) -> bool {
        self.allowed_ips.contains(ip)
    }

    /// Get the crypto state
    pub fn crypto(&self) -> &CryptoState {
        &self.crypto
    }

    /// Get a mutable reference to the crypto state
    pub fn crypto_mut(&mut self) -> &mut CryptoState {
        &mut self.crypto
    }

    /// Update last activity timestamp
    pub fn update_activity(&mut self) {
        self.last_activity = Instant::now();
    }

    /// Get time since last activity
    pub fn time_since_activity(&self) -> std::time::Duration {
        self.last_activity.elapsed()
    }

    /// Increment handshake attempts
    pub fn increment_handshake_attempts(&mut self) {
        self.handshake_attempts += 1;
    }

    /// Get handshake attempts count
    pub fn handshake_attempts(&self) -> u32 {
        self.handshake_attempts
    }

    /// Reset handshake attempts
    pub fn reset_handshake_attempts(&mut self) {
        self.handshake_attempts = 0;
    }

    /// Update RX bytes
    pub fn update_rx_bytes(&mut self, bytes: u64) {
        self.rx_bytes += bytes;
        self.update_activity();
    }

    /// Update TX bytes
    pub fn update_tx_bytes(&mut self, bytes: u64) {
        self.tx_bytes += bytes;
        self.update_activity();
    }

    /// Get RX bytes
    pub fn rx_bytes(&self) -> u64 {
        self.rx_bytes
    }

    /// Get TX bytes
    pub fn tx_bytes(&self) -> u64 {
        self.tx_bytes
    }
}

/// Peer manager for handling multiple peers
pub struct PeerManager {
    /// Map of public key to peer
    peers: std::collections::HashMap<[u8; 32], Peer>,
}

impl PeerManager {
    /// Create a new peer manager
    pub fn new() -> Self {
        Self {
            peers: std::collections::HashMap::new(),
        }
    }

    /// Add a peer
    pub fn add_peer(&mut self, peer: Peer) {
        self.peers.insert(*peer.public_key(), peer);
    }

    /// Remove a peer
    pub fn remove_peer(&mut self, public_key: &[u8; 32]) -> Option<Peer> {
        self.peers.remove(public_key)
    }

    /// Get a peer by public key
    pub fn get_peer(&self, public_key: &[u8; 32]) -> Option<&Peer> {
        self.peers.get(public_key)
    }

    /// Get a mutable peer by public key
    pub fn get_peer_mut(&mut self, public_key: &[u8; 32]) -> Option<&mut Peer> {
        self.peers.get_mut(public_key)
    }

    /// Find peer by IP address
    pub fn find_peer_by_ip(&self, ip: &std::net::Ipv4Addr) -> Option<&Peer> {
        self.peers.values().find(|peer| peer.is_ip_allowed(ip))
    }

    /// Get all peers
    pub fn peers(&self) -> &std::collections::HashMap<[u8; 32], Peer> {
        &self.peers
    }

    /// Get peer count
    pub fn peer_count(&self) -> usize {
        self.peers.len()
    }

    /// Get peers that need handshake
    pub fn peers_needing_handshake(&self) -> Vec<&Peer> {
        self.peers
            .values()
            .filter(|p| *p.state() == PeerState::Disconnected || *p.state() == PeerState::TimingOut)
            .collect()
    }

    /// Update all peers (check timeouts, etc.)
    pub fn update(&mut self) {
        let timeout = std::time::Duration::from_secs(30);
        let mut to_remove = Vec::new();

        for (key, peer) in &mut self.peers {
            if peer.time_since_activity() > timeout && *peer.state() == PeerState::Connected {
                peer.set_state(PeerState::TimingOut);
            }

            if peer.time_since_activity() > timeout * 2 && *peer.state() == PeerState::TimingOut {
                to_remove.push(*key);
            }
        }

        for key in to_remove {
            self.peers.remove(&key);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::{Ipv4Addr, SocketAddrV4};

    #[test]
    fn test_peer_creation() {
        let public_key = [0xAA; 32];
        let endpoint = SocketAddr::V4(SocketAddrV4::new(Ipv4Addr::new(192, 168, 1, 1), 51820));

        let peer = Peer::new(public_key, Some(endpoint));

        assert_eq!(peer.public_key(), &[0xAA; 32]);
        assert_eq!(peer.endpoint().unwrap(), &endpoint);
        assert_eq!(*peer.state(), PeerState::Disconnected);
    }

    #[test]
    fn test_peer_allowed_ips() {
        let mut peer = Peer::new([0xAA; 32], None);

        peer.add_allowed_ip(Ipv4Addr::new(10, 0, 0, 2));
        peer.add_allowed_ip(Ipv4Addr::new(10, 0, 0, 3));

        assert!(peer.is_ip_allowed(&Ipv4Addr::new(10, 0, 0, 2)));
        assert!(peer.is_ip_allowed(&Ipv4Addr::new(10, 0, 0, 3)));
        assert!(!peer.is_ip_allowed(&Ipv4Addr::new(10, 0, 0, 4)));
    }

    #[test]
    fn test_peer_manager() {
        let mut manager = PeerManager::new();

        let peer1 = Peer::new([0xAA; 32], None);
        let peer2 = Peer::new([0xBB; 32], None);

        manager.add_peer(peer1);
        manager.add_peer(peer2);

        assert_eq!(manager.peer_count(), 2);
        assert!(manager.get_peer(&[0xAA; 32]).is_some());
        assert!(manager.get_peer(&[0xCC; 32]).is_none());
    }

    #[test]
    fn test_find_peer_by_ip() {
        let mut manager = PeerManager::new();

        let mut peer = Peer::new([0xAA; 32], None);
        peer.add_allowed_ip(Ipv4Addr::new(10, 0, 0, 2));

        manager.add_peer(peer);

        let found = manager.find_peer_by_ip(&Ipv4Addr::new(10, 0, 0, 2));
        assert!(found.is_some());
        assert_eq!(found.unwrap().public_key(), &[0xAA; 32]);

        let not_found = manager.find_peer_by_ip(&Ipv4Addr::new(10, 0, 0, 3));
        assert!(not_found.is_none());
    }
}
