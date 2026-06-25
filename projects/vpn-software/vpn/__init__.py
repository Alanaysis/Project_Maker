"""
VPN Software - A secure VPN implementation in Python.

Architecture:
    +------------------------------------------------------+
    |                  Application Layer                    |
    +------------------------------------------------------+
    |               VPN Tunnel Manager                     |
    +------------------------------------------------------+
    |  Encryption Layer (AES-256-GCM) | Key Exchange (ECDH)|
    +------------------------------------------------------+
    |           UDP / TCP Transport Layer                   |
    +------------------------------------------------------+
    |              TUN Device Interface                     |
    +------------------------------------------------------+
    |                 Operating System                      |
    +------------------------------------------------------+

Core Loop:
    Data Packet -> Encryption -> Tunnel Encapsulation ->
    Transport -> Decapsulation -> Decryption -> Forwarding
"""

__version__ = "1.0.0"

from vpn.error import VpnError
from vpn.crypto import CryptoEngine
from vpn.tunnel import VpnTunnel
from vpn.peer import Peer, PeerManager
from vpn.tun_device import TunDevice

__all__ = [
    "VpnError",
    "CryptoEngine",
    "VpnTunnel",
    "Peer",
    "PeerManager",
    "TunDevice",
]
