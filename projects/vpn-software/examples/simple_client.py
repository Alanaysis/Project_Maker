#!/usr/bin/env python3
"""
Simple VPN client example.

This demonstrates how to connect to a VPN server using the library API.

Usage (requires root for TUN device):
    sudo python3 simple_client.py
"""

import asyncio
import logging
import signal

from vpn.config import VPNConfig
from vpn.tunnel import VpnTunnel


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Configure the VPN
    config = VPNConfig()
    config.client.server_address = "192.168.1.100"  # Change to your server IP
    config.client.server_port = 51820
    config.client.transport = "udp"
    config.tun.name = "tun0"
    config.tun.address = "10.0.0.2"
    config.security.encryption = "aes-256-gcm"

    # Create and start tunnel
    tunnel = VpnTunnel(config, mode="client")

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(tunnel.stop()))

    print(f"Connecting to VPN server at {config.client.server_address}:{config.client.server_port}")
    print(f"  TUN device: {config.tun.name} ({config.tun.address})")
    print("Press Ctrl+C to disconnect")

    await tunnel.start()

    # Keep running until stopped
    while tunnel.is_running:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
