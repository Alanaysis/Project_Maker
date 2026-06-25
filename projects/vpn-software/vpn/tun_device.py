"""
TUN device management for VPN tunnel.

Handles creation and management of TUN virtual network interfaces
on Linux. TUN devices operate at Layer 3 (IP packets).
"""

import os
import fcntl
import struct
import subprocess
import socket
from dataclasses import dataclass
from typing import Optional

from vpn.error import TunDeviceError

# Linux TUN constants
TUNSETIFF = 0x400454CA
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000
IFF_TAP = 0x0002


@dataclass
class TunConfig:
    """TUN device configuration."""
    name: str = "tun0"
    address: str = "10.0.0.1"
    netmask: str = "255.255.255.0"
    mtu: int = 1500
    # Optional: peer address for point-to-point mode
    peer_address: Optional[str] = None


class TunDevice:
    """
    TUN virtual network interface.

    Creates and manages a TUN device for capturing/reading IP packets.
    Requires root privileges on Linux.
    """

    def __init__(self, config: TunConfig) -> None:
        self._config = config
        self._fd: Optional[int] = None
        self._name: Optional[str] = None
        self._opened = False

    @property
    def config(self) -> TunConfig:
        return self._config

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def is_open(self) -> bool:
        return self._opened

    def open(self) -> None:
        """Open and configure the TUN device."""
        try:
            # Open TUN clone device
            self._fd = os.open("/dev/net/tun", os.O_RDWR)

            # Prepare the ifreq struct
            # struct ifreq { char ifr_name[16]; unsigned short ifr_flags; ... }
            ifr_flags = IFF_TUN | IFF_NO_PI
            ifr = struct.pack("16sH", self._config.name.encode("utf-8"), ifr_flags)
            result = fcntl.ioctl(self._fd, TUNSETIFF, ifr)

            # Extract actual device name
            self._name = result[:16].rstrip(b"\x00").decode("utf-8")
            self._opened = True

            # Configure the interface
            self._configure_interface()

        except PermissionError:
            raise TunDeviceError(
                "Permission denied. TUN device requires root privileges."
            )
        except FileNotFoundError:
            raise TunDeviceError(
                "/dev/net/tun not found. Ensure TUN module is loaded."
            )
        except OSError as e:
            raise TunDeviceError(f"Failed to open TUN device: {e}")

    def _configure_interface(self) -> None:
        """Configure IP address, netmask, and MTU on the TUN device."""
        try:
            # Set IP address
            subprocess.run(
                ["ip", "addr", "add", f"{self._config.address}/{self._calc_prefix()}",
                 "dev", self._name],
                check=True,
                capture_output=True,
            )

            # Set MTU
            subprocess.run(
                ["ip", "link", "set", "dev", self._name, "mtu", str(self._config.mtu)],
                check=True,
                capture_output=True,
            )

            # Bring interface up
            subprocess.run(
                ["ip", "link", "set", "dev", self._name, "up"],
                check=True,
                capture_output=True,
            )

        except subprocess.CalledProcessError as e:
            raise TunDeviceError(f"Failed to configure TUN interface: {e.stderr.decode()}")

    def _calc_prefix(self) -> int:
        """Calculate CIDR prefix length from netmask."""
        mask_int = struct.unpack("!I", socket.inet_aton(self._config.netmask))[0]
        return bin(mask_int).count("1")

    def read_packet(self) -> bytes:
        """Read an IP packet from the TUN device."""
        if not self._opened or self._fd is None:
            raise TunDeviceError("TUN device not open")

        try:
            buf = os.read(self._fd, self._config.mtu + 64)
            return buf
        except OSError as e:
            raise TunDeviceError(f"Failed to read from TUN: {e}")

    def write_packet(self, packet: bytes) -> None:
        """Write an IP packet to the TUN device."""
        if not self._opened or self._fd is None:
            raise TunDeviceError("TUN device not open")

        try:
            os.write(self._fd, packet)
        except OSError as e:
            raise TunDeviceError(f"Failed to write to TUN: {e}")

    def close(self) -> None:
        """Close the TUN device."""
        if self._fd is not None:
            try:
                # Remove IP address
                subprocess.run(
                    ["ip", "addr", "del", f"{self._config.address}/{self._calc_prefix()}",
                     "dev", self._name],
                    capture_output=True,
                )
                # Bring interface down
                subprocess.run(
                    ["ip", "link", "set", "dev", self._name, "down"],
                    capture_output=True,
                )
            except Exception:
                pass
            os.close(self._fd)
            self._fd = None
            self._opened = False

    def __enter__(self) -> "TunDevice":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class RouteManager:
    """Manages system routing table for VPN traffic."""

    @staticmethod
    def add_route(destination: str, gateway: str, dev: Optional[str] = None) -> None:
        """Add a route to the system routing table."""
        cmd = ["ip", "route", "add", destination, "via", gateway]
        if dev:
            cmd.extend(["dev", dev])
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise TunDeviceError(f"Failed to add route: {e.stderr.decode()}")

    @staticmethod
    def delete_route(destination: str) -> None:
        """Delete a route from the system routing table."""
        try:
            subprocess.run(
                ["ip", "route", "del", destination],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            pass  # Route may not exist

    @staticmethod
    def add_default_route(gateway: str, dev: str) -> None:
        """Add a default route through the VPN."""
        # Save the original default route
        try:
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True, text=True,
            )
            original_default = result.stdout.strip()

            # Add specific route to VPN server through original gateway
            if original_default:
                subprocess.run(
                    ["ip", "route", "add"] + original_default.split(),
                    capture_output=True,
                )
        except Exception:
            pass

        # Add new default route through VPN
        subprocess.run(
            ["ip", "route", "add", "default", "via", gateway, "dev", dev],
            check=True, capture_output=True,
        )

    @staticmethod
    def restore_default_route() -> None:
        """Restore the original default route."""
        try:
            subprocess.run(
                ["ip", "route", "del", "default"],
                capture_output=True,
            )
        except Exception:
            pass
