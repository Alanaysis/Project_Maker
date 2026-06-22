# Development Manual: VPN Software

## Overview

This document provides development guidelines, environment setup instructions, and core module explanations for the VPN software project.

## Development Environment Setup

### Prerequisites

1. **Rust Toolchain**
   ```bash
   # Install Rust
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # Verify installation
   rustc --version
   cargo --version
   ```

2. **System Dependencies**
   
   **Linux (Ubuntu/Debian)**:
   ```bash
   sudo apt update
   sudo apt install -y build-essential libssl-dev pkg-config
   ```
   
   **macOS**:
   ```bash
   brew install openssl pkg-config
   ```

3. **TUN Device Support**
   
   **Linux**:
   ```bash
   # Check if TUN module is loaded
   lsmod | grep tun
   
   # Load if needed
   sudo modprobe tun
   
   # Ensure /dev/net/tun exists
   ls -la /dev/net/tun
   ```

4. **Development Tools**
   ```bash
   # Install useful tools
   cargo install cargo-watch
   cargo install cargo-edit
   cargo install cargo-audit
   ```

---

### Project Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd vpn-software
   ```

2. **Build Project**
   ```bash
   # Debug build
   cargo build
   
   # Release build
   cargo build --release
   ```

3. **Run Tests**
   ```bash
   # All tests
   cargo test
   
   # Specific test
   cargo test test_name
   
   # With output
   cargo test -- --nocapture
   ```

4. **Run Examples**
   ```bash
   # Simple VPN demo
   cargo run --example simple_vpn
   
   # TUN device demo (requires root)
   sudo cargo run --example tun_demo
   ```

---

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make Changes**
   ```bash
   # Edit code
   vim src/module.rs
   
   # Run tests frequently
   cargo test
   ```

3. **Run Linter**
   ```bash
   cargo clippy
   ```

4. **Format Code**
   ```bash
   cargo fmt
   ```

5. **Check for Vulnerabilities**
   ```bash
   cargo audit
   ```

6. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add my feature"
   ```

7. **Push and Create PR**
   ```bash
   git push origin feature/my-feature
   ```

---

## Core Module Explanations

### 1. Crypto Module (`src/crypto.rs`)

**Purpose**: Handles all cryptographic operations.

**Key Concepts**:

1. **X25519 Key Exchange**
   - Elliptic curve Diffie-Hellman
   - 128-bit security level
   - Fast and secure

2. **ChaCha20-Poly1305 Encryption**
   - AEAD (Authenticated Encryption with Associated Data)
   - 256-bit key, 96-bit nonce
   - Resistant to timing attacks

3. **HKDF Key Derivation**
   - Extract-and-expand paradigm
   - Derives multiple keys from shared secret
   - Standardized in RFC 5869

**Implementation Details**:

```rust
// Key exchange
pub fn key_exchange(&mut self, remote_pub: &PublicKey) -> Result<()> {
    let shared_secret = self.private_key.diffie_hellman(remote_pub);
    
    // Derive encryption key using HKDF
    let hk = Hkdf::<Sha256>::new(None, shared_secret.as_bytes());
    let mut encryption_key = [0u8; 32];
    hk.expand(b"vpn-encryption-key", &mut encryption_key)?;
    
    self.encryption_key = Some(encryption_key);
    Ok(())
}
```

**Learning Points**:
- How Diffie-Hellman works
- Why we need key derivation
- How AEAD encryption works
- Nonce management for replay protection

---

### 2. Packet Module (`src/packet.rs`)

**Purpose**: Parse and construct network packets.

**Key Concepts**:

1. **IPv4 Header Structure**
   - Version, IHL, DSCP, ECN
   - Total length, identification
   - Flags, fragment offset
   - TTL, protocol, checksum
   - Source and destination IP

2. **Packet Parsing**
   - Read bytes in order
   - Convert from network byte order (big-endian)
   - Validate fields

3. **Packet Construction**
   - Build header fields
   - Calculate checksum
   - Serialize to bytes

**Implementation Details**:

```rust
pub fn parse(data: &[u8]) -> Result<Self> {
    let version = (data[0] >> 4) & 0x0F;
    if version != 4 {
        return Err(VpnError::InvalidPacket("Not IPv4".to_string()));
    }
    
    let total_length = u16::from_be_bytes([data[2], data[3]]);
    // ... parse other fields
}
```

**Learning Points**:
- Network byte order (big-endian)
- Bit manipulation for flags
- Checksum calculation
- Packet validation

---

### 3. Protocol Module (`src/protocol.rs`)

**Purpose**: Implement VPN protocol messages.

**Key Concepts**:

1. **Message Types**
   - HandshakeInitiation (type 1)
   - HandshakeResponse (type 2)
   - CookieReply (type 3)
   - TransportData (type 4)

2. **Handshake Protocol**
   - Noise IK pattern
   - 1-RTT handshake
   - Ephemeral key exchange

3. **Transport Protocol**
   - Encrypted data packets
   - Counter-based nonces
   - Replay protection

**Implementation Details**:

```rust
pub struct HandshakeInitiation {
    pub message_type: u8,
    pub reserved: [u8; 3],
    pub sender_index: u32,
    pub encrypted_ephemeral: [u8; 32],
    pub encrypted_static: [u8; 48],
    pub encrypted_timestamp: [u8; 28],
    pub mac1: [u8; 16],
    pub mac2: [u8; 16],
}
```

**Learning Points**:
- Protocol design principles
- Message framing
- Handshake state machine
- DoS protection mechanisms

---

### 4. Tunnel Module (`src/tunnel.rs`)

**Purpose**: Manage VPN tunnel lifecycle.

**Key Concepts**:

1. **Async I/O**
   - Tokio runtime
   - Non-blocking operations
   - Concurrent task execution

2. **Packet Flow**
   - TUN → Encrypt → UDP
   - UDP → Decrypt → TUN
   - Bidirectional forwarding

3. **Peer Management**
   - Connection state tracking
   - Handshake initiation
   - Timeout handling

**Implementation Details**:

```rust
pub async fn start(&self) -> Result<()> {
    // Start TUN reader task
    self.start_tun_reader().await;
    
    // Start socket reader task
    self.start_socket_reader().await;
    
    // Initiate handshake if needed
    if let Some(peer_endpoint) = &self.config.peer_endpoint {
        self.initiate_handshake(peer_endpoint).await?;
    }
    
    Ok(())
}
```

**Learning Points**:
- Async/await in Rust
- Task spawning and management
- Shared state with Arc<Mutex<>>
- Error handling in async context

---

### 5. TUN Device Module (`src/tun_device.rs`)

**Purpose**: Manage TUN virtual network interfaces.

**Key Concepts**:

1. **TUN Device Creation**
   - Open /dev/net/tun
   - Set interface flags
   - Configure IP address

2. **Packet I/O**
   - Read raw IP packets
   - Write raw IP packets
   - Handle MTU

3. **Route Management**
   - Add/remove routes
   - Gateway configuration
   - Subnet routing

**Implementation Details**:

```rust
pub fn new(config: TunConfig) -> Result<Self> {
    let mut tun_config = tun::Configuration::default();
    tun_config
        .address(config.address)
        .netmask(config.netmask)
        .mtu(config.mtu as i32)
        .up();
    
    let device = tun::create(&tun_config)?;
    Ok(Self { device, config })
}
```

**Learning Points**:
- Linux TUN/TAP subsystem
- Network interface configuration
- Route management
- File descriptor I/O

---

### 6. Peer Module (`src/peer.rs`)

**Purpose**: Manage VPN peer connections.

**Key Concepts**:

1. **Peer State Machine**
   - Disconnected → Handshaking → Connected → TimingOut
   - State transitions
   - Timeout handling

2. **Allowed IPs**
   - IP-to-peer mapping
   - Routing decisions
   - Access control

3. **Statistics**
   - Bytes sent/received
   - Connection duration
   - Error counts

**Implementation Details**:

```rust
pub enum PeerState {
    Disconnected,
    Handshaking,
    Connected,
    TimingOut,
}

pub struct Peer {
    public_key: [u8; 32],
    endpoint: Option<SocketAddr>,
    allowed_ips: Vec<Ipv4Addr>,
    state: PeerState,
    crypto: CryptoState,
    // ... statistics
}
```

**Learning Points**:
- State machine design
- Peer management patterns
- Statistics collection
- Resource cleanup

---

## Testing Strategy

### Unit Tests

**Location**: `#[cfg(test)]` modules in each source file

**Purpose**: Test individual functions and methods

**Example**:
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_key_exchange() {
        let mut alice = CryptoState::new();
        let mut bob = CryptoState::new();

        let alice_pub = *alice.public_key();
        let bob_pub = *bob.public_key();

        alice.key_exchange(&bob_pub).unwrap();
        bob.key_exchange(&alice_pub).unwrap();

        assert_eq!(alice.encryption_key, bob.encryption_key);
    }
}
```

**Running**:
```bash
# All unit tests
cargo test

# Specific module
cargo test crypto::

# With output
cargo test -- --nocapture
```

---

### Integration Tests

**Location**: `tests/` directory

**Purpose**: Test module interactions

**Example**:
```rust
#[test]
fn test_full_packet_flow() {
    // Create crypto states
    let mut sender = CryptoState::new();
    let mut receiver = CryptoState::new();
    
    // Key exchange
    sender.key_exchange(receiver.public_key()).unwrap();
    receiver.key_exchange(sender.public_key()).unwrap();
    
    // Encrypt and decrypt
    let plaintext = b"Hello, VPN!";
    let ciphertext = sender.encrypt(plaintext).unwrap();
    let decrypted = receiver.decrypt(&ciphertext).unwrap();
    
    assert_eq!(plaintext.as_slice(), decrypted.as_slice());
}
```

**Running**:
```bash
# All integration tests
cargo test --test integration_test

# Specific test
cargo test --test integration_test test_name
```

---

### Benchmarks

**Location**: `benches/` directory

**Purpose**: Measure performance

**Example**:
```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn bench_encrypt(c: &mut Criterion) {
    let mut crypto = CryptoState::new();
    // ... setup
    
    c.bench_function("encrypt 1500 bytes", |b| {
        b.iter(|| {
            crypto.encrypt(black_box(&plaintext)).unwrap()
        })
    });
}

criterion_group!(benches, bench_encrypt);
criterion_main!(benches);
```

**Running**:
```bash
cargo bench
```

---

## Code Quality

### Linting

```bash
# Run Clippy
cargo clippy

# With all warnings
cargo clippy -- -W clippy::all
```

### Formatting

```bash
# Format code
cargo fmt

# Check formatting
cargo fmt -- --check
```

### Security Audit

```bash
# Check for vulnerabilities
cargo audit
```

---

## Debugging

### Logging

```rust
use tracing::{info, warn, error, debug};

// Set log level via environment variable
// RUST_LOG=debug cargo run

info!("Tunnel started");
warn!("Peer timeout");
error!("Failed to read packet: {}", e);
debug!("Packet: {:?}", packet);
```

### GDB Debugging

```bash
# Build with debug symbols
cargo build

# Run with GDB
gdb target/debug/vpn-software
```

### Performance Profiling

```bash
# Build with profiling
cargo build --release

# Run with perf
perf record target/release/vpn-software
perf report
```

---

## Common Tasks

### Adding a New Module

1. Create `src/new_module.rs`
2. Add `pub mod new_module;` to `src/lib.rs`
3. Implement module functionality
4. Add tests
5. Update documentation

### Adding a New Protocol Message

1. Add message struct to `src/protocol.rs`
2. Implement parse/to_bytes methods
3. Add tests
4. Update message handling in `src/tunnel.rs`

### Adding a New Configuration Option

1. Add field to config struct in `src/config.rs`
2. Add default value
3. Update TOML example in documentation
4. Add validation if needed

---

## Troubleshooting

### TUN Device Permission Error

**Error**: `Failed to create TUN device: Permission denied`

**Solution**:
```bash
sudo cargo run -- <command>
```

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port
lsof -i :51820

# Kill process
kill -9 <PID>
```

### Build Errors

**Error**: `failed to run custom build command for openssl-sys`

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install libssl-dev pkg-config

# macOS
brew install openssl
export OPENSSL_DIR=$(brew --prefix openssl)
```

---

## Contributing

### Code Style

- Follow Rust conventions
- Use meaningful variable names
- Add comments for complex logic
- Keep functions small and focused

### Commit Messages

Format: `type(scope): description`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(crypto): add key rotation support
fix(tunnel): handle peer disconnection
docs(readme): update installation instructions
```

### Pull Request Process

1. Create feature branch
2. Make changes
3. Run tests
4. Update documentation
5. Create PR
6. Address review comments
7. Merge

---

## Resources

### Rust

- [The Rust Book](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
- [Tokio Documentation](https://tokio.rs/)

### Networking

- [Beej's Guide to Network Programming](https://beej.us/guide/bgnet/)
- [TCP/IP Illustrated](https://www.amazon.com/TCP-Illustrated-Vol-Addison-Wesley/dp/0201633469)

### Cryptography

- [Cryptography Engineering](https://www.amazon.com/Cryptography-Engineering-Principles-Practical-Applications/dp/0470474246)
- [Noise Protocol Framework](https://noiseprotocol.org/)

### VPN

- [WireGuard Protocol](https://www.wireguard.com/protocol/)
- [OpenVPN Documentation](https://openvpn.net/community-resources/)
