//! Error types for VPN software

use thiserror::Error;

/// Main error type for VPN operations
#[derive(Error, Debug)]
pub enum VpnError {
    #[error("TUN device error: {0}")]
    TunDeviceError(String),

    #[error("Crypto error: {0}")]
    CryptoError(String),

    #[error("Network error: {0}")]
    NetworkError(String),

    #[error("Protocol error: {0}")]
    ProtocolError(String),

    #[error("Peer error: {0}")]
    PeerError(String),

    #[error("Configuration error: {0}")]
    ConfigError(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Invalid packet: {0}")]
    InvalidPacket(String),

    #[error("Handshake failed: {0}")]
    HandshakeFailed(String),

    #[error("Connection timeout")]
    ConnectionTimeout,

    #[error("Peer not found: {0}")]
    PeerNotFound(String),

    #[error("Invalid key: {0}")]
    InvalidKey(String),
}

/// Result type alias for VPN operations
pub type Result<T> = std::result::Result<T, VpnError>;
