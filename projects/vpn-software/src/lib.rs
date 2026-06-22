//! # VPN Software
//!
//! A VPN software implementation with tunnel encryption and traffic forwarding.
//!
//! ## Architecture
//!
//! The VPN follows a layered architecture:
//!
//! ```text
//! ┌─────────────────────────────────────────────────────────────┐
//! │                      Application Layer                       │
//! ├─────────────────────────────────────────────────────────────┤
//! │                    VPN Tunnel Manager                        │
//! ├─────────────────────────────────────────────────────────────┤
//! │  Encryption Layer (ChaCha20-Poly1305)  │  Key Exchange (X25519)  │
//! ├─────────────────────────────────────────────────────────────┤
//! │                    UDP Transport Layer                        │
//! ├─────────────────────────────────────────────────────────────┤
//! │                    TUN Device Interface                      │
//! ├─────────────────────────────────────────────────────────────┤
//! │                      Operating System                        │
//! └─────────────────────────────────────────────────────────────┘
//! ```
//!
//! ## Core Loop
//!
//! ```text
//! Data Packet Capture → Encryption → Tunnel Encapsulation →
//! Transport → Decapsulation → Decryption → Forwarding
//! ```

pub mod crypto;
pub mod error;
pub mod packet;
pub mod peer;
pub mod protocol;
pub mod tunnel;
pub mod tun_device;

// Re-export main types
pub use error::{VpnError, Result};
pub use tunnel::VpnTunnel;
pub use tun_device::TunDevice;
pub use peer::Peer;
pub use crypto::CryptoState;
