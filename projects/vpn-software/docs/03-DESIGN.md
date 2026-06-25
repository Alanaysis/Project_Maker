# Design: VPN Software

## 1. Architecture Overview

### Layered Architecture

```
+------------------------------------------------------+
|                  Application Layer                    |
|  (CLI, Configuration, Authentication)                |
+------------------------------------------------------+
|               VPN Tunnel Manager                     |
|  (Session lifecycle, Packet routing, Peer management)|
+------------------------------------------------------+
|  Encryption Layer (AES-256-GCM) | Key Exchange (ECDH)|
|  (CryptoEngine, KeyPair)                             |
+------------------------------------------------------+
|           UDP / TCP Transport Layer                   |
|  (socket, asyncio streams)                           |
+------------------------------------------------------+
|              TUN Device Interface                     |
|  (TunDevice, RouteManager)                           |
+------------------------------------------------------+
|                 Operating System                      |
+------------------------------------------------------+
```

### Component Interaction

```
CLI --> VpnTunnel --> TunDevice (read/write packets)
                |-> Transport (UDP/TCP send/recv)
                |-> Session (encrypt/decrypt)
                |-> PeerManager (track connections)
                |-> Auth (verify credentials)
```

## 2. Module Design

### 2.1 CryptoEngine (`vpn/crypto.py`)

**Responsibility**: All cryptographic operations.

```
CryptoEngine
  +-- KeyPair
  |     +-- generate() -> KeyPair
  |     +-- from_pem(bytes) -> KeyPair
  |     +-- public_bytes() -> bytes (33-byte compressed point)
  |     +-- private_pem() -> bytes
  |
  +-- key_exchange(remote_public_key: bytes)
  +-- encrypt(plaintext: bytes) -> bytes  [nonce || ciphertext || tag]
  +-- decrypt(data: bytes) -> bytes
```

**Key derivation flow**:
```
ECDH(local_private, remote_public) -> shared_secret
HKDF(shared_secret, info="vpn-aes-256-gcm-key") -> encryption_key
```

**Encryption format**:
```
[12-byte nonce] [N-byte ciphertext] [16-byte GCM tag]
```

### 2.2 Packet Module (`vpn/packet.py`)

**Responsibility**: Packet parsing and construction.

```
Packet Types:
  - HandshakeInitPacket: [magic(4)][ver(1)][type(1)][idx(2)][pubkey(32)][ephemeral(32)][mac(16)]
  - HandshakeResponsePacket: [magic(4)][ver(1)][type(1)][sender_idx(2)][recv_idx(2)][pubkey(32)][ephemeral(32)][mac(16)]
  - TransportDataPacket: [magic(4)][ver(1)][type(1)][session_id(4)][counter(8)][encrypted_payload(N)]
  - AuthRequestPacket: [magic(4)][ver(1)][type(1)][session_id(4)][auth_type(1)][username_len(2)][username(N)][credential(N)]
  - AuthResponsePacket: [magic(4)][ver(1)][type(1)][session_id(4)][success(1)][msg_len(2)][message(N)]
  - KeepalivePacket: [magic(4)][ver(1)][type(1)][session_id(4)]
```

**Magic number**: `0x56504E01` ("VPN\x01")

### 2.3 TUN Device (`vpn/tun_device.py`)

**Responsibility**: Virtual network interface management.

```
TunDevice
  +-- open() -> None          # Create and configure TUN
  +-- close() -> None         # Destroy TUN
  +-- read_packet() -> bytes  # Read IP packet from TUN
  +-- write_packet(bytes)     # Write IP packet to TUN

RouteManager (static)
  +-- add_route(dest, gw, dev)
  +-- delete_route(dest)
  +-- add_default_route(gw, dev)
```

**Linux TUN creation**:
```python
fd = os.open("/dev/net/tun", os.O_RDWR)
ifr = struct.pack("16sH", b"tun0", IFF_TUN | IFF_NO_PI)
fcntl.ioctl(fd, TUNSETIFF, ifr)
```

### 2.4 Peer Manager (`vpn/peer.py`)

**Responsibility**: Track and manage VPN peer connections.

```
Peer
  +-- public_key: bytes
  +-- endpoint: (host, port)
  +-- session_id: int
  +-- state: PeerState (DISCONNECTED, HANDSHAKING, AUTHENTICATING, CONNECTED, TIMING_OUT)
  +-- crypto: CryptoEngine
  +-- allowed_ips: list[str]
  +-- stats: PeerStats (rx/tx bytes/packets)

PeerManager
  +-- add_peer(peer)
  +-- remove_peer(public_key)
  +-- get_peer_by_key/session/ip()
  +-- update() -> list[removed_keys]  # Check timeouts
```

### 2.5 Session (`vpn/protocol.py`)

**Responsibility**: Manage VPN session lifecycle.

```
Session State Machine:
  INIT -> HANDSHAKE_SENT -> HANDSHAKE_COMPLETE -> ESTABLISHED -> CLOSED

Session
  +-- initiate_handshake() -> HandshakeInitPacket
  +-- process_handshake_init(init) -> HandshakeResponsePacket
  +-- process_handshake_response(response)
  +-- encrypt_packet(plaintext) -> TransportDataPacket
  +-- decrypt_packet(transport_packet) -> bytes
  +-- create_keepalive() -> KeepalivePacket
  +-- should_rekey() -> bool
```

### 2.6 Authentication (`vpn/auth.py`)

**Responsibility**: Verify user credentials.

```
PasswordAuthenticator
  +-- add_user(username, password, allowed_ips)
  +-- authenticate(username, password) -> (bool, allowed_ips)
  +-- save_to_file(path) / load_from_file(path)

CertificateAuthenticator
  +-- setup_ca(cn, days, output_dir)
  +-- load_ca(cert_path, key_path)
  +-- issue_certificate(cn, days) -> (key_path, cert_path)
  +-- authorize_client(cn, allowed_ips)
  +-- authenticate(cert_pem) -> (bool, allowed_ips)
```

### 2.7 Tunnel Manager (`vpn/tunnel.py`)

**Responsibility**: Orchestrate all components.

```
VpnTunnel(config, mode)
  +-- start() / stop()
  +-- get_stats() -> dict

Internal:
  +-- _start_server() / _start_client()
  +-- _udp_read_loop() / _tcp_read_loop()
  +-- _tun_read_loop()
  +-- _maintenance_loop()
  +-- _process_incoming(data, addr)
  +-- _process_outgoing(packet)
```

## 3. Data Flow

### 3.1 Outgoing (Local -> Remote)

```
Application sends packet
    |
    v
OS routes to TUN device
    |
    v
TunDevice.read_packet() -> raw IP bytes
    |
    v
Parse IPv4 destination
    |
    v
PeerManager.get_peer_by_ip(dest) -> Peer
    |
    v
Session.encrypt_packet(plaintext) -> TransportDataPacket
    |
    v
Transport.sendto(data, peer.endpoint)
```

### 3.2 Incoming (Remote -> Local)

```
Transport.recvfrom(data, addr)
    |
    v
Parse message type
    |
    v
If HANDSHAKE_INIT:
    Session.process_handshake_init() -> response
    Transport.sendto(response, addr)

If TRANSPORT_DATA:
    Session.decrypt_packet(encrypted) -> plaintext
    TunDevice.write_packet(plaintext)

If KEEPALIVE:
    Session.process_keepalive()
```

## 4. Handshake Flow

```
Client                              Server
  |                                    |
  |--- HandshakeInit ----------------->|
  |    [sender_index, public_key,      |
  |     ephemeral_key]                 |
  |                                    |
  |<-- HandshakeResponse --------------|
  |    [sender_index, receiver_index,  |
  |     public_key, ephemeral_key]     |
  |                                    |
  |--- AuthRequest ------------------->|
  |    [username, password_hash]       |
  |                                    |
  |<-- AuthResponse -------------------|
  |    [success, message]              |
  |                                    |
  |<===== Encrypted Transport ========>|
```

## 5. Security Design

### Key Hierarchy
```
Master Secret = ECDH(local_priv, remote_pub)
    |
    v
Encryption Key = HKDF-SHA256(master, info="vpn-aes-256-gcm-key")
    |
    v
AES-256-GCM(key, nonce, plaintext) -> ciphertext || tag
```

### Nonce Management
- 12-byte nonce: 8-byte counter + 4 bytes zero
- Counter increments with each encryption
- Prevents replay attacks
- Counter wraps at 2^64

### Password Storage
- PBKDF2-HMAC-SHA256
- 600,000 iterations
- 16-byte random salt per user
- 32-byte derived key
