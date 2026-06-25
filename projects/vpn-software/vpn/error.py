"""Error types for VPN software."""


class VpnError(Exception):
    """Base exception for all VPN errors."""

    pass


class TunDeviceError(VpnError):
    """TUN/TAP device operation errors."""

    pass


class CryptoError(VpnError):
    """Cryptographic operation errors."""

    pass


class NetworkError(VpnError):
    """Network communication errors."""

    pass


class ProtocolError(VpnError):
    """VPN protocol errors."""

    pass


class PeerError(VpnError):
    """Peer management errors."""

    pass


class ConfigError(VpnError):
    """Configuration errors."""

    pass


class InvalidPacketError(VpnError):
    """Invalid packet format errors."""

    pass


class HandshakeError(VpnError):
    """Handshake process errors."""

    pass


class AuthError(VpnError):
    """Authentication errors."""

    pass
