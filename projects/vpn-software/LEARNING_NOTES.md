# Learning Notes: VPN Software

## Key Concepts Learned

### 1. TUN/TAP Devices

TUN (network TUNnel) devices are virtual network interfaces that operate at Layer 3 (IP packets). They are the foundation of most VPN implementations.

**How it works**:
- The OS creates a virtual network interface (`tun0`)
- Applications see it as a real network interface
- When the OS sends a packet to `tun0`, it appears in the TUN file descriptor
- When we write a packet to the TUN file descriptor, the OS receives it as if it came from the network

**Linux implementation**:
```python
fd = os.open("/dev/net/tun", os.O_RDWR)
ifr = struct.pack("16sH", b"tun0", IFF_TUN | IFF_NO_PI)
fcntl.ioctl(fd, TUNSETIFF, ifr)
# Now fd reads/writes IP packets
```

### 2. ECDH Key Exchange

Elliptic Curve Diffie-Hellman allows two parties to establish a shared secret over an insecure channel.

**The math**:
- Alice has private key `a`, public key `A = a*G`
- Bob has private key `b`, public key `B = b*G`
- Shared secret: `S = a*B = b*A = a*b*G`

**Why P-256?**
- 128-bit security level
- Fast computation
- Widely supported and standardized

### 3. AES-256-GCM

AES-GCM (Galois/Counter Mode) is an Authenticated Encryption with Associated Data (AEAD) cipher.

**Properties**:
- **Confidentiality**: AES-CTR encrypts the plaintext
- **Integrity**: GHASH provides authentication tag
- **AEAD**: Can authenticate additional data without encrypting it

**Encryption format**:
```
[12-byte nonce] [ciphertext] [16-byte authentication tag]
```

**Key insight**: The authentication tag means we can detect any tampering with the ciphertext.

### 4. HKDF Key Derivation

HKDF (HMAC-based Key Derivation Function) derives one or more cryptographic keys from a shared secret.

**Two-step process**:
1. **Extract**: `PRK = HMAC-Hash(salt, input_key_material)`
2. **Expand**: `OKM = HMAC-Hash(PRK, info || counter)`

**Why not use the shared secret directly?**
- The raw ECDH output may not be uniformly random
- HKDF produces keys of the desired length
- Different `info` strings produce different keys from the same secret

### 5. PBKDF2 Password Hashing

PBKDF2 (Password-Based Key Derivation Function 2) turns a password into a cryptographic key.

**Why not SHA-256(password)?**
- SHA-256 is fast -> attackers can try billions of passwords per second
- PBKDF2 uses many iterations (600,000) to slow down brute-force attacks
- Random salt prevents rainbow table attacks

### 6. VPN Protocol Design

**Handshake flow**:
```
Client -> Server: HandshakeInit (public key, ephemeral key)
Server -> Client: HandshakeResponse (public key, ephemeral key)
Both sides: Derive shared secret via ECDH
Both sides: Derive encryption key via HKDF
Client -> Server: AuthRequest (credentials)
Server -> Client: AuthResponse (success/failure)
Both sides: Encrypted transport begins
```

**Key design decisions**:
- Include ephemeral keys for forward secrecy
- Authentication after key exchange (credentials are encrypted)
- Keepalive packets to detect dead peers
- Nonce counter to prevent replay attacks

### 7. asyncio for Network I/O

Python's asyncio provides non-blocking I/O, essential for a VPN that must simultaneously:
- Read packets from the TUN device
- Receive packets from the network
- Send keepalives
- Check for timeouts

**Pattern**:
```python
async def main():
    asyncio.create_task(tun_read_loop())
    asyncio.create_task(network_read_loop())
    asyncio.create_task(maintenance_loop())
    await run_forever()
```

### 8. X.509 Certificates

Certificates bind a public key to an identity (Common Name).

**Chain of trust**:
```
CA Certificate (self-signed)
    |
    +-- Server Certificate (signed by CA)
    +-- Client Certificate (signed by CA)
```

**Verification**: Check that the certificate's signature was made by the CA's private key.

## Architecture Lessons

### Separation of Concerns
Each module has a single responsibility:
- `crypto.py` knows nothing about networks
- `tun_device.py` knows nothing about encryption
- `tunnel.py` orchestrates everything

### Error Handling
Custom exception hierarchy makes errors clear:
```python
VpnError (base)
  +-- CryptoError
  +-- NetworkError
  +-- ProtocolError
  +-- TunDeviceError
  +-- AuthError
```

### Configuration
YAML with sensible defaults means the simplest case requires zero configuration:
```python
config = VPNConfig()  # Works with defaults
config.server.port = 8080  # Override specific values
```

## Security Lessons

1. **Never roll your own crypto**: Use well-tested libraries
2. **Always authenticate encryption**: Use AEAD modes (GCM, Poly1305)
3. **Use unique nonces**: Counter-based nonces are simple and safe
4. **Hash passwords slowly**: PBKDF2/bcrypt/scrypt, never raw SHA-256
5. **Protect private keys**: Restrictive file permissions (0600)
6. **Forward secrecy**: Use ephemeral keys so past sessions can't be decrypted
