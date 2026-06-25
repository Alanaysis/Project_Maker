# VPN Software

A VPN software implementation with tunnel encryption and traffic forwarding, built from scratch using Python.

## Project Overview

This project implements a VPN (Virtual Private Network) that supports:
- TUN device-based packet capture and injection
- AES-256-GCM authenticated encryption
- ECDH key exchange (P-256 curve)
- UDP and TCP transport
- Username/password and certificate authentication
- Remote access and site-to-site topologies

### Core Loop

```
Data Packet Capture -> Encryption -> Tunnel Encapsulation ->
Transport -> Decapsulation -> Decryption -> Forwarding
```

## Tech Stack

- **Language**: Python 3.10+
- **Encryption**: AES-256-GCM (via `cryptography` library)
- **Key Exchange**: ECDH (SECP256R1 / P-256)
- **Key Derivation**: HKDF-SHA256
- **Authentication**: PBKDF2-SHA256 (passwords), X.509 certificates
- **Networking**: TUN devices, asyncio UDP/TCP sockets
- **CLI**: Click

## Project Structure

```
vpn-software/
├── vpn/                        # Main package
│   ├── __init__.py            # Public API
│   ├── error.py               # Error types
│   ├── crypto.py              # Crypto engine (AES-GCM, ECDH, certificates)
│   ├── packet.py              # Packet parsing/construction
│   ├── tun_device.py          # TUN device management
│   ├── peer.py                # Peer management
│   ├── auth.py                # Password and certificate authentication
│   ├── protocol.py            # Session lifecycle
│   ├── config.py              # YAML configuration
│   ├── tunnel.py              # Tunnel manager (main orchestrator)
│   └── cli.py                 # CLI entry point
├── tests/                     # Test suite
├── examples/                  # Example applications
├── docs/                      # Design documentation
├── pyproject.toml             # Build config
└── requirements.txt           # Dependencies
```

## Getting Started

### Prerequisites

- Python 3.10+
- Linux (TUN device support required)
- Root privileges (for TUN device creation)

### Installation

```bash
cd projects/vpn-software

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e ".[dev]"
```

### Quick Start

#### 1. Generate Keys and Certificates

```bash
# Generate CA
python3 -m vpn.cli genca --output-dir ca

# Issue server certificate
python3 -m vpn.cli gencert --cn server --ca-dir ca --output-dir certs

# Issue client certificate
python3 -m vpn.cli gencert --cn client1 --ca-dir ca --output-dir certs

# Add password-authenticated user
python3 -m vpn.cli adduser --username alice
```

#### 2. Run as Server

```bash
sudo python3 -m vpn.cli server --port 51820
```

#### 3. Run as Client

```bash
sudo python3 -m vpn.cli client --server 192.168.1.100 --port 51820
```

## Configuration

Create a `config.yaml` file:

```yaml
server:
  listen_address: "0.0.0.0"
  port: 51820
  transport: "udp"
  max_clients: 100
  keepalive_interval: 25.0

client:
  server_address: "192.168.1.100"
  server_port: 51820
  transport: "udp"

tun:
  name: "tun0"
  address: "10.0.0.1"
  netmask: "255.255.255.0"
  mtu: 1500

security:
  encryption: "aes-256-gcm"
  key_exchange: "ecdh-p256"
  auth_method: "password"   # or "certificate"
  handshake_timeout: 10.0

logging:
  level: "info"
```

## Core Modules

### 1. Crypto Engine (`vpn/crypto.py`)

Implements all cryptographic operations:
- **KeyPair**: ECDH key pair generation, PEM serialization
- **CryptoEngine**: Key exchange, AES-256-GCM encrypt/decrypt
- **Password utilities**: PBKDF2 hashing and verification
- **Certificate utilities**: CA generation, certificate issuance and verification

### 2. Packet Module (`vpn/packet.py`)

Handles packet parsing and construction:
- IPv4 header parsing
- VPN protocol messages (handshake, transport, auth, keepalive)
- Binary serialization with struct packing

### 3. TUN Device (`vpn/tun_device.py`)

Manages TUN virtual network interfaces:
- Device creation via `/dev/net/tun`
- IP address and route configuration via `ip` commands
- Packet read/write operations

### 4. Peer Manager (`vpn/peer.py`)

Tracks VPN peer connections:
- Peer state machine (disconnected -> handshaking -> connected)
- Allowed IP management (cryptokey routing)
- Traffic statistics

### 5. Authentication (`vpn/auth.py`)

Two authentication methods:
- **Password**: PBKDF2-hashed credentials stored in JSON
- **Certificate**: X.509 certificates signed by a CA

### 6. Tunnel Manager (`vpn/tunnel.py`)

Main orchestrator that ties everything together:
- Server mode: accepts incoming connections
- Client mode: connects to server
- Async packet forwarding between TUN and transport
- Handshake, auth, and keepalive management

## Usage Examples

### Remote Access VPN

```bash
# Server setup
vpn adduser --username alice
sudo python3 -m vpn.cli server --port 51820

# Client connection
sudo python3 -m vpn.cli client --server vpn.example.com --username alice
```

### Site-to-Site VPN

```bash
# Site A (server)
sudo python3 examples/site_to_site.py server

# Site B (client)
sudo python3 examples/site_to_site.py client
```

## Architecture Decisions

### Why Python?

1. **Readability**: Every line is understandable
2. **Rapid development**: Full implementation in ~2000 lines
3. **Rich ecosystem**: `cryptography` library for production-grade crypto
4. **asyncio**: Non-blocking I/O for concurrent connections
5. **Learning**: Ideal for understanding VPN internals

### Why AES-256-GCM?

1. **Hardware acceleration**: AES-NI on modern CPUs
2. **Authenticated encryption**: Built-in integrity check
3. **Industry standard**: Used by TLS 1.3, IPSec
4. **Well-analyzed**: Decades of cryptographic research

### Why ECDH P-256?

1. **Security**: 128-bit equivalent security level
2. **Performance**: Fast key exchange
3. **Standard**: NIST-approved, widely supported
4. **Library support**: Excellent support in `cryptography`

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=vpn --cov-report=html

# Run specific tests
pytest tests/test_crypto.py -v
```

## Security Considerations

1. **Key Management**: Private keys stored with 0600 permissions
2. **Password Storage**: PBKDF2 with 600,000 iterations
3. **Replay Protection**: Nonce-based counter prevents replay attacks
4. **Forward Secrecy**: Ephemeral ECDH keys per session
5. **AEAD**: AES-GCM provides both confidentiality and integrity

## References

- [WireGuard Protocol](https://www.wireguard.com/protocol/)
- [RFC 7539 - ChaCha20-Poly1305](https://datatracker.ietf.org/doc/html/rfc7539)
- [RFC 7748 - Elliptic Curves for Security](https://datatracker.ietf.org/doc/html/rfc7748)
- [RFC 5869 - HKDF](https://datatracker.ietf.org/doc/html/rfc5869)
- [Python cryptography library](https://cryptography.io/)

## License

MIT License
