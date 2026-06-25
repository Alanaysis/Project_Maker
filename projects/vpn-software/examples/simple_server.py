#!/usr/bin/env python3
"""
Simple VPN server example.

This demonstrates how to start a basic VPN server using the library API.

Usage (requires root for TUN device):
    sudo python3 simple_server.py
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
    config.server.listen_address = "0.0.0.0"
    config.server.port = 51820
    config.server.transport = "udp"
    config.tun.name = "tun0"
    config.tun.address = "10.0.0.1"
    config.security.encryption = "aes-256-gcm"
    config.security.auth_method = "password"

    # Create and start tunnel
    tunnel = VpnTunnel(config, mode="server")

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(tunnel.stop()))

    print("Starting VPN server...")
    print(f"  Listening on {config.server.listen_address}:{config.server.port}")
    print(f"  TUN device: {config.tun.name} ({config.tun.address})")
    print("Press Ctrl+C to stop")

    await tunnel.start()

    # Keep running until stopped
    while tunnel.is_running:
        await asyncio.sleep(1)
        stats = tunnel.get_stats()
        if stats["peer_count"] > 0:
            print(f"  Peers: {stats['peer_count']}, "
                  f"RX: {stats['total_rx_bytes']}, TX: {stats['total_tx_bytes']}")


if __name__ == "__main__":
    asyncio.run(main())
