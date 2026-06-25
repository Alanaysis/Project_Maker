#!/usr/bin/env python3
"""
Remote access VPN example.

This demonstrates a typical remote access VPN setup:
- Company network: 10.0.0.0/24
- VPN server at the company gateway
- Remote workers connect to access internal resources

Setup steps:
1. Generate CA and server/client certificates
2. Add user credentials
3. Start the server
4. Connect from remote machines
"""

import asyncio
import logging
import signal
import sys

from vpn.config import VPNConfig
from vpn.tunnel import VpnTunnel
from vpn.auth import PasswordAuthenticator


def setup_server_with_password_auth():
    """Set up a server with password authentication."""
    config = VPNConfig()
    config.server.listen_address = "0.0.0.0"
    config.server.port = 51820
    config.server.transport = "udp"
    config.server.max_clients = 50
    config.tun.name = "tun0"
    config.tun.address = "10.0.0.1"
    config.security.encryption = "aes-256-gcm"
    config.security.auth_method = "password"
    config.security.users_file = "users.json"
    return config


def setup_server_with_cert_auth():
    """Set up a server with certificate authentication."""
    config = VPNConfig()
    config.server.listen_address = "0.0.0.0"
    config.server.port = 51820
    config.tun.name = "tun0"
    config.tun.address = "10.0.0.1"
    config.security.encryption = "aes-256-gcm"
    config.security.auth_method = "certificate"
    config.security.ca_cert = "ca/ca.crt"
    config.security.ca_key = "ca/ca.key"
    return config


def setup_client_config(server_ip: str) -> VPNConfig:
    """Set up a client configuration."""
    config = VPNConfig()
    config.client.server_address = server_ip
    config.client.server_port = 51820
    config.client.transport = "udp"
    config.tun.name = "tun0"
    config.tun.address = "10.0.0.10"  # Client gets a different IP
    config.security.encryption = "aes-256-gcm"
    return config


async def run_server():
    """Run the VPN server."""
    config = setup_server_with_password_auth()
    tunnel = VpnTunnel(config, mode="server")

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(tunnel.stop()))

    print("=" * 60)
    print("  Remote Access VPN Server")
    print("=" * 60)
    print(f"  Listening: {config.server.listen_address}:{config.server.port}")
    print(f"  Network:   {config.tun.address}/24")
    print(f"  Auth:      {config.security.auth_method}")
    print("=" * 60)
    print("Press Ctrl+C to stop\n")

    await tunnel.start()

    while tunnel.is_running:
        await asyncio.sleep(5)
        stats = tunnel.get_stats()
        if stats["peer_count"] > 0:
            print(f"[Status] Connected clients: {stats['peer_count']}")


async def run_client(server_ip: str):
    """Run the VPN client."""
    config = setup_client_config(server_ip)
    tunnel = VpnTunnel(config, mode="client")

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(tunnel.stop()))

    print(f"Connecting to VPN server at {server_ip}...")
    await tunnel.start()

    while tunnel.is_running:
        await asyncio.sleep(1)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if len(sys.argv) < 2:
        print("Remote Access VPN")
        print()
        print("Usage:")
        print("  sudo python3 remote_access.py server")
        print("  sudo python3 remote_access.py client <server_ip>")
        print()
        print("First-time setup:")
        print("  1. Add users:    vpn adduser --username alice")
        print("  2. Start server: sudo python3 remote_access.py server")
        print("  3. Connect:      sudo python3 remote_access.py client 203.0.113.1")
        return

    mode = sys.argv[1]

    if mode == "server":
        await run_server()
    elif mode == "client":
        if len(sys.argv) < 3:
            print("Error: server IP required for client mode")
            return
        await run_client(sys.argv[2])


if __name__ == "__main__":
    asyncio.run(main())
