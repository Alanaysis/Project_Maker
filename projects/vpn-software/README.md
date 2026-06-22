# VPN Software

A VPN software implementation with tunnel encryption and traffic forwarding, built from scratch using Rust.

## Project Overview

This project implements a VPN (Virtual Private Network) software that supports:
- Tunnel establishment and management
- Encryption using modern cryptographic algorithms
- Traffic forwarding through TUN devices
- WireGuard-inspired protocol design

### Learning Objectives

- Understand VPN protocols (OpenVPN, WireGuard)
- Master tunnel technology and encryption
- Learn network address translation (NAT)
- Implement secure key exchange
- Handle network packet processing

### Core Loop

```
Data Packet Capture → Encryption → Tunnel Encapsulation →
Transport → Decapsulation → Decryption → Forwarding
```

## Tech Stack

- **Language**: Rust
- **Encryption**: ChaCha20-Poly1305, X25519, BLAKE2s
- **Networking**: TUN/TAP devices, UDP sockets
- **Async Runtime**: Tokio
- **Dependencies**: ring, x25519-dalek, chacha20poly1305

## Project Structure

```
vpn-software/
├── src/
│   ├── lib.rs          # Library root
│   ├── main.rs         # CLI entry point
│   ├── cli.rs          # Command line interface
│   ├── config.rs       # Configuration management
│   ├── crypto.rs       # Cryptographic operations
│   ├── error.rs        # Error types
│   ├── packet.rs       # Packet parsing
│   ├── peer.rs         # Peer management
│   ├── protocol.rs     # VPN protocol implementation
│   ├── tunnel.rs       # VPN tunnel implementation
│   └── tun_device.rs   # TUN device management
├── tests/
│   └── integration_test.rs
├── examples/
│   ├── simple_vpn.rs   # Simple VPN demo
│   └── tun_demo.rs     # TUN device demo
├── docs/
│   ├── 01-RESEARCH.md  # Market research
│   ├── 02-REQUIREMENTS.md
│   ├── 03-DESIGN.md    # Technical design
│   ├── 04-PRODUCT.md   # Product thinking
│   └── 05-DEVELOPMENT.md
└── Cargo.toml
```

## Core Modules

### 1. Crypto Module (`src/crypto.rs`)

Implements cryptographic operations:
- Key exchange using X25519 (Curve25519 Diffie-Hellman)
- Symmetric encryption using ChaCha20-Poly1305
- Key derivation using HKDF-SHA256
- Nonce management for replay protection

### 2. Packet Module (`src/packet.rs`)

Handles packet parsing and construction:
- IPv4 header parsing
- VPN packet types (Handshake, Data, Cookie)
- Packet serialization/deserialization

### 3. Protocol Module (`src/protocol.rs`)

Implements WireGuard-inspired protocol:
- Handshake initiation and response
- Transport data messages
- Cookie-based DoS protection
- Message type handling

### 4. Tunnel Module (`src/tunnel.rs`)

Manages VPN tunnel lifecycle:
- Handshake initiation and processing
- Data encryption and decryption
- Packet routing between TUN and UDP
- Connection state management

### 5. TUN Device Module (`src/tun_device.rs`)

Handles TUN virtual network interfaces:
- Device creation and configuration
- Packet reading and writing
- Route management

### 6. Peer Module (`src/peer.rs`)

Manages VPN peer connections:
- Peer state tracking
- Allowed IP management
- Statistics collection

## Getting Started

### Prerequisites

- Rust 1.70+ (with cargo)
- Root privileges (for TUN device creation)
- Linux/macOS (TUN support required)

### Building

```bash
# Clone the repository
cd projects/vpn-software

# Build the project
cargo build

# Run tests
cargo test

# Run examples
cargo run --example simple_vpn
sudo cargo run --example tun_demo
```

### Usage

#### Generate Keys

```bash
cargo run -- generate-keys
```

#### Run as Server

```bash
sudo cargo run -- server --port 51820 --tun-name tun0 --tun-addr 10.0.0.1
```

#### Run as Client

```bash
sudo cargo run -- client --server 192.168.1.100 --port 51820 --tun-name tun0 --tun-addr 10.0.0.2
```

## Configuration

Create a `config.toml` file:

```toml
[server]
port = 51820
max_clients = 100
keepalive_interval = 25

[client]
server = "192.168.1.100"
port = 51820
connection_timeout = 30

[tun]
name = "tun0"
address = "10.0.0.1"
netmask = "255.255.255.0"
mtu = 1500

[security]
encryption = "chacha20poly1305"
key_exchange = "x25519"
handshake_timeout = 10

[logging]
level = "info"
```

## Key Concepts

### 1. Key Exchange (X25519)

X25519 is an elliptic curve Diffie-Hellman key exchange using Curve25519. It provides:
- 128-bit security level
- Fast computation
- Resistance to timing attacks

### 2. Encryption (ChaCha20-Poly1305)

ChaCha20-Poly1305 is an authenticated encryption algorithm:
- ChaCha20 stream cipher for encryption
- Poly1305 MAC for authentication
- 256-bit key, 96-bit nonce
- AEAD (Authenticated Encryption with Associated Data)

### 3. TUN Devices

TUN (network TUNnel) devices are virtual network interfaces:
- Operate at Layer 3 (IP packets)
- Used for routing traffic through VPN
- Created via `/dev/net/tun` on Linux

### 4. WireGuard Protocol

WireGuard protocol features:
- Noise Protocol Framework for key exchange
- Cryptokey routing (public key → allowed IPs)
- Silent peer handling (NAT traversal)
- Roaming support (endpoint changes)

## Architecture Decisions

### Why Rust?

1. **Memory Safety**: No buffer overflows, no data races
2. **Performance**: Zero-cost abstractions, minimal overhead
3. **Concurrency**: Built-in async/await support
4. **Ecosystem**: Excellent crypto libraries (ring, dalek)

### Why ChaCha20-Poly1305?

1. **Performance**: Fast on CPUs without AES-NI
2. **Security**: Resistant to timing attacks
3. **Simplicity**: Easy to implement correctly
4. **Standard**: Used by WireGuard, TLS 1.3

### Why X25519?

1. **Security**: 128-bit security level
2. **Speed**: Fast key exchange
3. **Simplicity**: Easy to implement
4. **Standard**: Used by Signal, WireGuard

## Testing

### Unit Tests

```bash
cargo test
```

### Integration Tests

```bash
cargo test --test integration_test
```

### Benchmarks

```bash
cargo bench
```

## Performance Considerations

1. **Zero-copy**: Minimize packet copying
2. **Async I/O**: Use Tokio for non-blocking operations
3. **Batch processing**: Process multiple packets together
4. **Memory pooling**: Reuse buffers for packets

## Security Considerations

1. **Key Management**: Secure key storage and rotation
2. **Replay Protection**: Nonce-based anti-replay
3. **DoS Protection**: Cookie-based handshake protection
4. **Forward Secrecy**: Ephemeral keys for each session

## Future Improvements

1. **Full WireGuard Protocol**: Complete Noise Protocol implementation
2. **NAT Traversal**: STUN/TURN support
3. **Multi-peer**: Support multiple simultaneous peers
4. **IPv6 Support**: Handle IPv6 packets
5. **Performance Optimization**: SIMD, kernel bypass

## References

- [WireGuard Protocol](https://www.wireguard.com/protocol/)
- [Noise Protocol Framework](https://noiseprotocol.org/)
- [ChaCha20-Poly1305](https://datatracker.ietf.org/doc/html/rfc7539)
- [X25519](https://datatracker.ietf.org/doc/html/rfc7748)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please read the contributing guidelines first.
