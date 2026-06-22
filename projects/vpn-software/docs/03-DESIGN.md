# Technical Design: VPN Software

## Overview

This document describes the technical design of the VPN software, including architecture, data structures, interfaces, and implementation details.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    CLI / Config                          ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                      VPN Tunnel Manager                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Tunnel Manager  │  Peer Manager  │  Route Manager      ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                    Encryption Layer                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Key Exchange (X25519)  │  Symmetric Encryption         ││
│  │                         │  (ChaCha20-Poly1305)          ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                    Protocol Layer                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Handshake  │  Transport  │  Cookie  │  Message Parser  ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                    Transport Layer                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    UDP Socket                            ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                    Device Layer                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    TUN Device                            ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                      Operating System                        │
└─────────────────────────────────────────────────────────────┘
```

### Module Dependencies

```
┌──────────────┐
│    main      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    cli       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   tunnel     │
└──────┬───────┘
       │
       ├──►┌──────────────┐
       │   │    peer      │
       │   └──────────────┘
       │
       ├──►┌──────────────┐
       │   │   crypto     │
       │   └──────────────┘
       │
       ├──►┌──────────────┐
       │   │   protocol   │
       │   └──────────────┘
       │
       ├──►┌──────────────┐
       │   │   packet     │
       │   └──────────────┘
       │
       └──►┌──────────────┐
           │ tun_device   │
           └──────────────┘
```

---

## Data Structures

### 1. CryptoState

Represents the cryptographic state of a VPN connection.

```rust
pub struct CryptoState {
    /// Local private key
    private_key: EphemeralSecret,
    /// Local public key
    public_key: PublicKey,
    /// Shared secret (after key exchange)
    shared_secret: Option<SharedSecret>,
    /// Derived encryption key
    encryption_key: Option<[u8; 32]>,
    /// Current nonce counter
    nonce_counter: u64,
}
```

**Key Operations**:
- `new()`: Generate fresh keypair
- `key_exchange(remote_pub)`: Perform Diffie-Hellman
- `encrypt(plaintext) -> ciphertext`: Encrypt data
- `decrypt(ciphertext) -> plaintext`: Decrypt data

---

### 2. Peer

Represents a VPN peer connection.

```rust
pub struct Peer {
    /// Peer's public key
    public_key: [u8; 32],
    /// Peer's endpoint address
    endpoint: Option<SocketAddr>,
    /// Allowed IP addresses
    allowed_ips: Vec<Ipv4Addr>,
    /// Current state
    state: PeerState,
    /// Cryptographic state
    crypto: CryptoState,
    /// Last activity timestamp
    last_activity: Instant,
    /// Statistics
    rx_bytes: u64,
    tx_bytes: u64,
}
```

**Peer States**:
```
Disconnected ──► Handshaking ──► Connected ──► TimingOut ──► Disconnected
```

---

### 3. VpnTunnel

Main VPN tunnel manager.

```rust
pub struct VpnTunnel {
    /// Tunnel configuration
    config: TunnelConfig,
    /// UDP socket
    socket: Arc<UdpSocket>,
    /// TUN device
    tun: Arc<Mutex<TunDevice>>,
    /// Local crypto state
    crypto: CryptoState,
    /// Peer manager
    peers: Arc<Mutex<PeerManager>>,
    /// Running state
    running: Arc<Mutex<bool>>,
}
```

---

### 4. Protocol Messages

#### Handshake Initiation
```rust
pub struct HandshakeInitiation {
    message_type: u8,           // 1
    reserved: [u8; 3],
    sender_index: u32,
    encrypted_ephemeral: [u8; 32],
    encrypted_static: [u8; 48],
    encrypted_timestamp: [u8; 28],
    mac1: [u8; 16],
    mac2: [u8; 16],
}
// Total: 148 bytes
```

#### Handshake Response
```rust
pub struct HandshakeResponse {
    message_type: u8,           // 2
    reserved: [u8; 3],
    sender_index: u32,
    receiver_index: u32,
    encrypted_ephemeral: [u8; 32],
    encrypted_nothing: [u8; 16],
    mac1: [u8; 16],
    mac2: [u8; 16],
}
// Total: 92 bytes
```

#### Transport Data
```rust
pub struct TransportData {
    message_type: u8,           // 4
    reserved: [u8; 3],
    receiver_index: u32,
    counter: u64,
    encrypted_payload: Vec<u8>,
}
// Header: 16 bytes + payload
```

#### Cookie Reply
```rust
pub struct CookieReply {
    message_type: u8,           // 3
    reserved: [u8; 3],
    receiver_index: u32,
    encrypted_cookie: [u8; 48],
}
// Total: 64 bytes
```

---

### 5. IPv4 Header

```rust
pub struct Ipv4Header {
    version: u8,        // 4 bits
    ihl: u8,            // 4 bits
    dscp: u8,           // 6 bits
    ecn: u8,            // 2 bits
    total_length: u16,
    identification: u16,
    flags: u8,          // 3 bits
    fragment_offset: u16, // 13 bits
    ttl: u8,
    protocol: IpProtocol,
    checksum: u16,
    source: Ipv4Addr,
    destination: Ipv4Addr,
}
// Total: 20 bytes (minimum)
```

---

## Interfaces

### 1. CryptoState Interface

```rust
impl CryptoState {
    /// Create new crypto state with fresh keypair
    pub fn new() -> Self;

    /// Get local public key
    pub fn public_key(&self) -> &PublicKey;

    /// Perform key exchange with remote public key
    pub fn key_exchange(&mut self, remote_pub: &PublicKey) -> Result<()>;

    /// Encrypt data
    pub fn encrypt(&self, plaintext: &[u8]) -> Result<Vec<u8>>;

    /// Decrypt data
    pub fn decrypt(&self, ciphertext: &[u8]) -> Result<Vec<u8>>;
}
```

---

### 2. TunDevice Interface

```rust
impl TunDevice {
    /// Create new TUN device
    pub fn new(config: TunConfig) -> Result<Self>;

    /// Get device name
    pub fn name(&self) -> &str;

    /// Read packet from device
    pub fn read_packet(&mut self) -> Result<Vec<u8>>;

    /// Write packet to device
    pub fn write_packet(&mut self, packet: &[u8]) -> Result<()>;

    /// Set IP address
    pub fn set_address(&mut self, addr: Ipv4Addr) -> Result<()>;

    /// Set MTU
    pub fn set_mtu(&mut self, mtu: u32) -> Result<()>;
}
```

---

### 3. VpnTunnel Interface

```rust
impl VpnTunnel {
    /// Create new VPN tunnel
    pub async fn new(config: TunnelConfig) -> Result<Self>;

    /// Start the tunnel
    pub async fn start(&self) -> Result<()>;

    /// Stop the tunnel
    pub async fn stop(&self) -> Result<()>;

    /// Add a peer
    pub async fn add_peer(&self, pub_key: [u8; 32], endpoint: Option<SocketAddr>) -> Result<()>;

    /// Get tunnel statistics
    pub async fn stats(&self) -> TunnelStats;
}
```

---

### 4. PeerManager Interface

```rust
impl PeerManager {
    /// Create new peer manager
    pub fn new() -> Self;

    /// Add a peer
    pub fn add_peer(&mut self, peer: Peer);

    /// Remove a peer
    pub fn remove_peer(&mut self, pub_key: &[u8; 32]) -> Option<Peer>;

    /// Get peer by public key
    pub fn get_peer(&self, pub_key: &[u8; 32]) -> Option<&Peer>;

    /// Find peer by IP address
    pub fn find_peer_by_ip(&self, ip: &Ipv4Addr) -> Option<&Peer>;

    /// Get peer count
    pub fn peer_count(&self) -> usize;

    /// Update all peers (check timeouts)
    pub fn update(&mut self);
}
```

---

## Packet Flow

### Outgoing Packet Flow

```
Application sends data
        │
        ▼
OS routes packet to TUN device
        │
        ▼
VPN reads packet from TUN
        │
        ▼
Parse IPv4 header
        │
        ▼
Find destination peer
        │
        ▼
Encrypt packet with peer's key
        │
        ▼
Create TransportData message
        │
        ▼
Send via UDP socket
```

### Incoming Packet Flow

```
Receive packet via UDP socket
        │
        ▼
Parse message type
        │
        ├──► HandshakeInitiation
        │         │
        │         ▼
        │    Process handshake
        │
        ├──► HandshakeResponse
        │         │
        │         ▼
        │    Complete handshake
        │
        ├──► TransportData
        │         │
        │         ▼
        │    Decrypt payload
        │         │
        │         ▼
        │    Write to TUN device
        │
        └──► CookieReply
                  │
                  ▼
             Handle DoS protection
```

---

## Key Exchange Protocol

### Noise IK Handshake

```
Initiator                           Responder
    │                                   │
    │  HandshakeInitiation              │
    │  ─────────────────────────────►   │
    │  - sender_index                   │
    │  - encrypted_ephemeral            │
    │  - encrypted_static               │
    │  - encrypted_timestamp            │
    │  - mac1, mac2                     │
    │                                   │
    │                                   │
    │  HandshakeResponse                │
    │  ◄─────────────────────────────   │
    │  - sender_index                   │
    │  - receiver_index                 │
    │  - encrypted_ephemeral            │
    │  - encrypted_nothing              │
    │  - mac1, mac2                     │
    │                                   │
    │  TransportData                    │
    │  ◄───────────────────────────►    │
    │  - receiver_index                 │
    │  - counter                        │
    │  - encrypted_payload              │
    └───────────────────────────────────┘
```

---

## Encryption Design

### Key Derivation

```
Shared Secret (X25519)
        │
        ▼
HKDF-SHA256
        │
        ├──► Encryption Key (32 bytes)
        │
        └──► Authentication Key (32 bytes)
```

### Packet Encryption

```
Plaintext Packet
        │
        ▼
ChaCha20-Poly1305 Encryption
        │
        ├──► Nonce (12 bytes)
        │
        ├──► Ciphertext
        │
        └──► Authentication Tag (16 bytes)
```

### Nonce Generation

```
Counter (64-bit)
        │
        ▼
Convert to bytes (little-endian)
        │
        ▼
Pad to 12 bytes
        │
        ▼
Nonce (12 bytes)
```

---

## Error Handling

### Error Types

```rust
pub enum VpnError {
    TunDeviceError(String),
    CryptoError(String),
    NetworkError(String),
    ProtocolError(String),
    PeerError(String),
    ConfigError(String),
    IoError(io::Error),
    InvalidPacket(String),
    HandshakeFailed(String),
    ConnectionTimeout,
    PeerNotFound(String),
    InvalidKey(String),
}
```

### Error Propagation

```
Low-level error
        │
        ▼
Wrap in VpnError variant
        │
        ▼
Propagate with ?
        │
        ▼
Handle at appropriate level
```

---

## Concurrency Model

### Async Tasks

```
Main Task
    │
    ├──► TUN Reader Task
    │    - Reads packets from TUN
    │    - Sends to tunnel
    │
    ├──► Socket Reader Task
    │    - Receives packets from UDP
    │    - Processes and writes to TUN
    │
    └──► Peer Manager Task
         - Updates peer states
         - Handles timeouts
         - Initiates handshakes
```

### Shared State

```
Arc<Mutex<TunDevice>>
    │
    ├──► TUN Reader Task
    │
    └──► Socket Reader Task

Arc<Mutex<PeerManager>>
    │
    ├──► TUN Reader Task
    │
    ├──► Socket Reader Task
    │
    └──► Peer Manager Task
```

---

## Security Considerations

### 1. Key Management

- Ephemeral keys for each session
- No persistent key storage (by default)
- Key rotation on reconnection

### 2. Replay Protection

- 64-bit counter per peer
- Sliding window for out-of-order packets
- Reject duplicate counters

### 3. DoS Protection

- Cookie-based handshake protection
- Rate limiting on handshakes
- MAC verification before processing

### 4. Forward Secrecy

- Ephemeral Diffie-Hellman keys
- Session keys derived from ephemeral keys
- No long-term key compromise risk

---

## Performance Optimizations

### 1. Zero-Copy

- Minimize packet copying
- Use references where possible
- Batch processing for multiple packets

### 2. Async I/O

- Tokio for non-blocking operations
- Epoll/kqueue for event notification
- Minimal thread context switching

### 3. Memory Pooling

- Reuse packet buffers
- Pre-allocate common structures
- Avoid allocations in hot path

### 4. SIMD

- ChaCha20 SIMD optimizations
- Poly1305 SIMD optimizations
- Available in ring crate

---

## Testing Strategy

### Unit Tests

- Crypto operations
- Packet parsing
- Peer management
- Protocol messages

### Integration Tests

- End-to-end tunnel establishment
- Data transfer through tunnel
- Peer connection lifecycle
- Error handling

### Performance Tests

- Throughput measurement
- Latency measurement
- CPU/Memory usage
- Concurrent connections

### Security Tests

- Replay attack detection
- Tampered packet rejection
- Key exchange verification
- DoS protection

---

## Future Extensions

### 1. NAT Traversal

- STUN/TURN support
- UDP hole punching
- Relay servers

### 2. IPv6 Support

- IPv6 packet parsing
- Dual-stack support
- IPv6 routing

### 3. TCP Fallback

- TCP transport option
- Automatic fallback
- Connection multiplexing

### 4. Multi-Peer

- Mesh networking
- Automatic peer discovery
- Load balancing

---

## References

- [WireGuard Protocol](https://www.wireguard.com/protocol/)
- [Noise Protocol Framework](https://noiseprotocol.org/)
- [ChaCha20-Poly1305 RFC](https://datatracker.ietf.org/doc/html/rfc7539)
- [X25519 RFC](https://datatracker.ietf.org/doc/html/rfc7748)
