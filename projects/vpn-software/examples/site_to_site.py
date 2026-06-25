#!/usr/bin/env python3
"""
Site-to-site VPN example.

This demonstrates connecting two networks through a VPN tunnel:
- Site A: 192.168.1.0/24 (server at 192.168.1.1)
- Site B: 192.168.2.0/24 (client connecting to server)
- VPN subnet: 10.0.0.0/24

Network layout:
    [Site A: 192.168.1.0/24] <-- VPN Tunnel --> [Site B: 192.168.2.0/24]
         10.0.0.1                                     10.0.0.2
"""

import asyncio
import logging
import signal
import sys

from vpn.config import VPNConfig
from vpn.tunnel import VpnTunnel


def create_server_config() -> VPNConfig:
    """Create configuration for Site A (server)."""
    config = VPNConfig()
    config.server.listen_address = "0.0.0.0"
    config.server.port = 51820
    config.server.transport = "udp"
    config.tun.name = "tun0"
    config.tun.address = "10.0.0.1"
    config.tun.netmask = "255.255.255.0"
    config.security.encryption = "aes-256-gcm"
    config.security.auth_method = "certificate"
    config.security.ca_cert = "ca/ca.crt"
    config.security.ca_key = "ca/ca.key"
    return config


def create_client_config() -> VPNConfig:
    """Create configuration for Site B (client)."""
    config = VPNConfig()
    config.client.server_address = "203.0.113.1"  # Public IP of Site A
    config.client.server_port = 51820
    config.client.transport = "udp"
    config.tun.name = "tun0"
    config.tun.address = "10.0.0.2"
    config.tun.netmask = "255.255.255.0"
    config.security.encryption = "aes-256-gcm"
    config.security.auth_method = "certificate"
    config.security.cert_file = "certs/site-b.crt"
    config.security.key_file = "certs/site-b.key"
    return config


async def run_site(config: VPNConfig, mode: str):
    """Run a site-to-site VPN endpoint."""
    tunnel = VpnTunnel(config, mode=mode)

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(tunnel.stop()))

    await tunnel.start()

    site_name = "Site A (Server)" if mode == "server" else "Site B (Client)"
    print(f"{site_name} VPN running")
    print(f"  TUN: {config.tun.name} ({config.tun.address})")

    while tunnel.is_running:
        await asyncio.sleep(5)
        stats = tunnel.get_stats()
        print(f"  [{site_name}] RX: {stats['total_rx_bytes']}, TX: {stats['total_tx_bytes']}")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 site_to_site.py server  # Run Site A")
        print("  python3 site_to_site.py client  # Run Site B")
        print()
        print("Setup:")
        print("  1. Generate CA:     vpn genca --output-dir ca")
        print("  2. Issue certs:     vpn gencert --cn site-a --ca-dir ca --output-dir certs")
        print("  3.                 vpn gencert --cn site-b --ca-dir ca --output-dir certs")
        print("  4. Run server:      sudo python3 site_to_site.py server")
        print("  5. Run client:      sudo python3 site_to_site.py client")
        return

    mode = sys.argv[1]

    if mode == "server":
        config = create_server_config()
        await run_site(config, "server")
    elif mode == "client":
        config = create_client_config()
        await run_site(config, "client")
    else:
        print(f"Unknown mode: {mode}")


if __name__ == "__main__":
    asyncio.run(main())
