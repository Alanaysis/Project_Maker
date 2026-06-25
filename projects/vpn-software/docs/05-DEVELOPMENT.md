# Development: VPN Software

## 1. Development Environment

### Prerequisites
```bash
# Python 3.10+
python3 --version

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e ".[dev]"
```

### System Requirements
- Linux (TUN device support)
- Root privileges (for TUN device creation)
- Python 3.10+

## 2. Project Structure

```
vpn-software/
├── vpn/                        # Main package
│   ├── __init__.py            # Package init, public API
│   ├── error.py               # Error types
│   ├── crypto.py              # Cryptographic operations
│   ├── packet.py              # Packet parsing/construction
│   ├── tun_device.py          # TUN device management
│   ├── peer.py                # Peer management
│   ├── auth.py                # Authentication
│   ├── protocol.py            # Session/protocol management
│   ├── config.py              # Configuration
│   ├── tunnel.py              # Tunnel manager (main)
│   └── cli.py                 # CLI entry point
├── tests/                     # Test suite
│   ├── test_crypto.py
│   ├── test_packet.py
│   ├── test_peer.py
│   ├── test_protocol.py
│   ├── test_auth.py
│   └── test_config.py
├── examples/                  # Example applications
│   ├── simple_server.py
│   ├── simple_client.py
│   ├── site_to_site.py
│   └── remote_access.py
├── docs/                      # Documentation
│   ├── 01-RESEARCH.md
│   ├── 02-REQUIREMENTS.md
│   ├── 03-DESIGN.md
│   ├── 04-PRODUCT.md
│   └── 05-DEVELOPMENT.md
├── pyproject.toml             # Build configuration
├── requirements.txt           # Dependencies
├── README.md                  # Project overview
└── LEARNING_NOTES.md          # Developer notes
```

## 3. Module Development Order

### Phase 1: Foundation (Core Crypto + Packets)
1. `vpn/error.py` - Error types
2. `vpn/crypto.py` - Key exchange, encryption
3. `vpn/packet.py` - Packet format

### Phase 2: Infrastructure
4. `vpn/tun_device.py` - TUN device
5. `vpn/peer.py` - Peer tracking
6. `vpn/config.py` - Configuration

### Phase 3: Protocol
7. `vpn/protocol.py` - Session management
8. `vpn/auth.py` - Authentication

### Phase 4: Integration
9. `vpn/tunnel.py` - Main tunnel manager
10. `vpn/cli.py` - CLI interface

### Phase 5: Testing + Documentation
11. Tests for all modules
12. Examples
13. Documentation

## 4. Running

### Start Server
```bash
# With password auth (default)
sudo python3 -m vpn.cli server --port 51820

# With certificate auth
sudo python3 -m vpn.cli server --config server_config.yaml
```

### Start Client
```bash
# Connect with password
sudo python3 -m vpn.cli client --server 192.168.1.100 --username alice

# Connect with certificate
sudo python3 -m vpn.cli client --server 192.168.1.100 --config client_config.yaml
```

### Generate Keys/Certificates
```bash
# Generate ECDH keypair
python3 -m vpn.cli genkeys --output-dir keys

# Generate CA
python3 -m vpn.cli genca --output-dir ca

# Issue certificate
python3 -m vpn.cli gencert --cn client1 --ca-dir ca --output-dir certs

# Add user for password auth
python3 -m vpn.cli adduser --username alice
```

## 5. Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Module
```bash
pytest tests/test_crypto.py -v
```

### Run with Coverage
```bash
pip install pytest-cov
pytest tests/ --cov=vpn --cov-report=html
```

### Test Categories

**Unit Tests** (no root required):
- `test_crypto.py` - Key exchange, encrypt/decrypt, password hashing, certificates
- `test_packet.py` - Packet serialization/parsing
- `test_peer.py` - Peer state management
- `test_protocol.py` - Session handshake, keepalive
- `test_auth.py` - Password and certificate authentication
- `test_config.py` - Configuration loading/saving

**Integration Tests** (require root):
- TUN device creation
- Full tunnel establishment
- End-to-end data transfer

## 6. Configuration Reference

### config.yaml
```yaml
server:
  listen_address: "0.0.0.0"    # Listen address
  port: 51820                   # Listen port
  transport: "udp"              # "udp" or "tcp"
  max_clients: 100              # Max concurrent clients
  keepalive_interval: 25.0      # Seconds between keepalives

client:
  server_address: "0.0.0.0"    # Server address
  server_port: 51820            # Server port
  transport: "udp"              # "udp" or "tcp"
  connection_timeout: 30.0      # Connection timeout
  auto_reconnect: true          # Reconnect on disconnect

tun:
  name: "tun0"                  # TUN device name
  address: "10.0.0.1"           # Local VPN address
  netmask: "255.255.255.0"      # Network mask
  mtu: 1500                     # Maximum transmission unit

security:
  encryption: "aes-256-gcm"     # Encryption algorithm
  key_exchange: "ecdh-p256"     # Key exchange algorithm
  auth_method: "password"       # "password" or "certificate"
  handshake_timeout: 10.0       # Handshake timeout
  rekey_interval: 3600.0        # Seconds between rekeying
  # Certificate auth paths:
  ca_cert: "ca/ca.crt"
  ca_key: "ca/ca.key"
  cert_file: "certs/client.crt"
  key_file: "certs/client.key"
  # Password auth:
  users_file: "users.json"

logging:
  level: "info"                 # debug, info, warning, error
  file: null                    # Log file path
```

## 7. Network Topology Examples

### Remote Access (Client-Server)
```
[Remote Client]  <--UDP:51820-->  [VPN Server]  <--->  [Internal Network]
   10.0.0.10          encrypted        10.0.0.1           192.168.1.0/24
```

### Site-to-Site
```
[Site A Network]  <--VPN Tunnel-->  [Site B Network]
 192.168.1.0/24    10.0.0.1-2        192.168.2.0/24
     |                                   |
  VPN Server                          VPN Client
  (10.0.0.1)                          (10.0.0.2)
```

## 8. Debugging

### Enable Debug Logging
```bash
sudo python3 -m vpn.cli -v server --port 51820
# Or set in config:
# logging:
#   level: "debug"
```

### Common Issues

**TUN permission denied**:
```
Error: Permission denied. TUN device requires root privileges.
Fix: Run with sudo
```

**TUN module not loaded**:
```
Error: /dev/net/tun not found.
Fix: sudo modprobe tun
```

**Connection refused**:
```
Check: Is server running? Is port open in firewall?
Fix: sudo ufw allow 51820/udp
```

## 9. Performance Considerations

- Python is not ideal for high-throughput packet processing
- For learning/development: perfectly adequate
- For production: consider C extensions for hot path
- asyncio provides non-blocking I/O for concurrent connections
- TUN read/write can be moved to separate threads if needed

## 10. Security Checklist

- [ ] Private keys stored with 0600 permissions
- [ ] Passwords hashed with PBKDF2 (600K+ iterations)
- [ ] AES-256-GCM used for all encryption
- [ ] Nonces are unique per encryption operation
- [ ] Certificates verified against CA
- [ ] No sensitive data in logs
- [ ] Clean shutdown closes all connections
