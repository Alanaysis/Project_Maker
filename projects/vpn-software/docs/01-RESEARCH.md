# Research: VPN Software

## 1. VPN Technology Overview

A Virtual Private Network (VPN) creates an encrypted connection over a public network, enabling secure communication between remote endpoints. VPNs are fundamental to modern network security.

### Core Concepts

- **Tunneling**: Encapsulating private network packets within public network protocols
- **Encryption**: Protecting data confidentiality during transit
- **Authentication**: Verifying the identity of connecting parties
- **Key Exchange**: Securely establishing shared encryption keys

## 2. VPN Protocol Analysis

### WireGuard
- Modern, lightweight VPN protocol
- Uses Noise Protocol Framework for key exchange
- ChaCha20-Poly1305 for encryption
- Curve25519 for key exchange
- Kernel-level implementation for performance
- Simple protocol design (1% the code of OpenVPN)

### OpenVPN
- Mature, widely deployed
- Uses TLS for key exchange
- Supports multiple encryption algorithms
- User-space implementation
- Highly configurable
- Supports both TCP and UDP transports

### IPSec/IKEv2
- Industry standard for site-to-site VPNs
- Complex protocol suite
- Strong security guarantees
- Native OS support on most platforms
- Good for mobile devices (MOBIKE)

### SSL/TLS VPN
- Uses standard TLS protocol
- Easy to deploy (uses port 443)
- Good firewall traversal
- Web-based and client-based modes

## 3. TUN/TAP Devices

### TUN (Layer 3)
- Operates at IP packet level
- Captures/routs IP packets
- Used for routing-based VPNs
- More efficient for IP-only traffic

### TAP (Layer 2)
- Operates at Ethernet frame level
- Captures all Ethernet traffic
- Required for bridged VPNs
- Supports non-IP protocols

### Linux Implementation
- Accessed via `/dev/net/tun`
- Created using `ioctl(TUNSETIFF)`
- Configured with `ip` commands
- Requires root privileges

## 4. Cryptographic Choices

### Encryption: AES-256-GCM
- **Why**: Hardware acceleration (AES-NI), widely vetted
- **Alternative**: ChaCha20-Poly1305 (better on non-x86)
- **Mode**: AEAD (Authenticated Encryption with Associated Data)
- **Key Size**: 256 bits

### Key Exchange: ECDH (P-256)
- **Why**: Strong security, good performance
- **Alternative**: X25519 (simpler, constant-time)
- **Security Level**: 128-bit equivalent

### Key Derivation: HKDF-SHA256
- **Why**: Standard (RFC 5869), well-analyzed
- **Purpose**: Derive encryption keys from shared secret

### Authentication
- **Password**: PBKDF2 with high iteration count
- **Certificate**: X.509 certificates signed by CA

## 5. Transport Layer

### UDP
- Lower latency (no handshake/acknowledgment overhead)
- Better for real-time traffic
- NAT traversal easier
- Packet loss not automatically recovered
- Used by WireGuard, most VPNs

### TCP
- Reliable delivery
- Good for restricted networks
- TCP-over-TCP problem (meltdown)
- Higher latency
- Used by OpenVPN, SSL VPNs

## 6. Architecture Patterns

### Peer-to-Peer
- Each node connects directly to others
- No central server
- Good for mesh networks
- Example: Tailscale, ZeroTier

### Client-Server
- Central server handles routing
- Clients connect to server
- Easier to manage
- Example: OpenVPN, WireGuard (hub-spoke)

### Hub-and-Spoke
- Central hub routes all traffic
- Spokes only connect to hub
- Simple routing
- Single point of failure

## 7. Implementation Language: Python

### Advantages
- Rapid development
- Rich cryptographic libraries (`cryptography`)
- asyncio for async I/O
- Good TUN/TAP support via `fcntl`
- Easy to understand and maintain

### Tradeoffs
- Slower than C/Rust for packet processing
- GIL limits true parallelism
- Not suitable for high-throughput production VPN
- Excellent for learning and prototyping

## 8. References

- [WireGuard Protocol](https://www.wireguard.com/protocol/)
- [Noise Protocol Framework](https://noiseprotocol.org/)
- [RFC 7539 - ChaCha20-Poly1305](https://datatracker.ietf.org/doc/html/rfc7539)
- [RFC 7748 - Elliptic Curves for Security](https://datatracker.ietf.org/doc/html/rfc7748)
- [RFC 5869 - HKDF](https://datatracker.ietf.org/doc/html/rfc5869)
- [Linux TUN/TAP Documentation](https://www.kernel.org/doc/Documentation/networking/tuntap.txt)
- [Python cryptography library](https://cryptography.io/)
