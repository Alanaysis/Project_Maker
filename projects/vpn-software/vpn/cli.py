"""
Command-line interface for VPN software.

Usage:
    vpn server [--config config.yaml]
    vpn client --server <address> [--config config.yaml]
    vpn genkeys [--output-dir <dir>]
    vpn genca [--output-dir <dir>]
    vpn gencert --cn <common_name> [--ca-dir <dir>] [--output-dir <dir>]
    vpn adduser --username <name> [--users-file <path>]
"""

import os
import sys
import asyncio
import logging
import signal

import click

from vpn.config import VPNConfig
from vpn.tunnel import VpnTunnel
from vpn.crypto import KeyPair, generate_ca, generate_certificate
from vpn.auth import PasswordAuthenticator, CertificateAuthenticator


def setup_logging(level: str, log_file: str = None) -> None:
    """Configure logging."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


@click.group()
@click.option("--config", "-c", "config_file", default="config.yaml", help="Configuration file path")
@click.pass_context
def cli(ctx, config_file):
    """VPN Software - Secure tunnel implementation."""
    ctx.ensure_object(dict)
    ctx.obj["config_file"] = config_file


@cli.command()
@click.option("--port", "-p", default=None, type=int, help="Listening port")
@click.option("--tun-name", "-n", default=None, help="TUN device name")
@click.option("--tun-addr", "-a", default=None, help="TUN device address")
@click.option("--transport", "-t", default=None, type=click.Choice(["udp", "tcp"]), help="Transport protocol")
@click.pass_context
def server(ctx, port, tun_name, tun_addr, transport):
    """Run as VPN server."""
    config_file = ctx.obj["config_file"]

    if os.path.exists(config_file):
        config = VPNConfig.load_from_file(config_file)
    else:
        config = VPNConfig()

    # Override with CLI arguments
    if port is not None:
        config.server.port = port
    if tun_name:
        config.tun.name = tun_name
    if tun_addr:
        config.tun.address = tun_addr
    if transport:
        config.server.transport = transport

    setup_logging(config.logging.level, config.logging.file)

    logger = logging.getLogger("vpn")
    logger.info("Starting VPN server...")
    logger.info(f"  Port: {config.server.port}")
    logger.info(f"  Transport: {config.server.transport}")
    logger.info(f"  TUN: {config.tun.name} ({config.tun.address})")
    logger.info(f"  Auth: {config.security.auth_method}")

    tunnel = VpnTunnel(config, mode="server")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Handle shutdown signals
    def signal_handler():
        logger.info("Shutting down...")
        asyncio.ensure_future(tunnel.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        loop.run_until_complete(tunnel.start())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(tunnel.stop())
        loop.close()


@cli.command()
@click.option("--server", "-s", required=True, help="Server address")
@click.option("--port", "-p", default=None, type=int, help="Server port")
@click.option("--tun-name", "-n", default=None, help="TUN device name")
@click.option("--tun-addr", "-a", default=None, help="TUN device address")
@click.option("--transport", "-t", default=None, type=click.Choice(["udp", "tcp"]), help="Transport protocol")
@click.option("--username", "-u", default=None, help="Username for authentication")
@click.option("--password", "-P", default=None, help="Password for authentication")
@click.pass_context
def client(ctx, server, port, tun_name, tun_addr, transport, username, password):
    """Run as VPN client."""
    config_file = ctx.obj["config_file"]

    if os.path.exists(config_file):
        config = VPNConfig.load_from_file(config_file)
    else:
        config = VPNConfig()

    # Override with CLI arguments
    config.client.server_address = server
    if port is not None:
        config.client.server_port = port
    if tun_name:
        config.tun.name = tun_name
    if tun_addr:
        config.tun.address = tun_addr
    if transport:
        config.client.transport = transport

    setup_logging(config.logging.level, config.logging.file)

    logger = logging.getLogger("vpn")
    logger.info(f"Connecting to VPN server at {server}:{config.client.server_port}")
    logger.info(f"  Transport: {config.client.transport}")
    logger.info(f"  TUN: {config.tun.name} ({config.tun.address})")

    tunnel = VpnTunnel(config, mode="client")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def signal_handler():
        logger.info("Disconnecting...")
        asyncio.ensure_future(tunnel.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        loop.run_until_complete(tunnel.start())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(tunnel.stop())
        loop.close()


@cli.command()
@click.option("--output-dir", "-o", default=".", help="Output directory for keys")
def genkeys(output_dir):
    """Generate a new ECDH key pair."""
    kp = KeyPair.generate()
    os.makedirs(output_dir, exist_ok=True)

    key_path = os.path.join(output_dir, "vpn_private.pem")
    pub_path = os.path.join(output_dir, "vpn_public.pem")

    with open(key_path, "wb") as f:
        f.write(kp.private_pem())
    os.chmod(key_path, 0o600)

    with open(pub_path, "wb") as f:
        f.write(kp.public_pem())

    click.echo(f"Private key saved to: {key_path}")
    click.echo(f"Public key saved to: {pub_path}")
    click.echo("Keep your private key secure!")


@cli.command()
@click.option("--cn", default="VPN CA", help="CA common name")
@click.option("--days", default=3650, type=int, help="Validity period in days")
@click.option("--output-dir", "-o", default="ca", help="Output directory")
def genca(cn, days, output_dir):
    """Generate a CA certificate and key."""
    os.makedirs(output_dir, exist_ok=True)

    ca_key, ca_cert = generate_ca(cn, days)

    from cryptography.hazmat.primitives import serialization

    key_path = os.path.join(output_dir, "ca.key")
    cert_path = os.path.join(output_dir, "ca.crt")

    with open(key_path, "wb") as f:
        f.write(
            ca_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
    os.chmod(key_path, 0o600)

    with open(cert_path, "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

    click.echo(f"CA key saved to: {key_path}")
    click.echo(f"CA certificate saved to: {cert_path}")


@cli.command()
@click.option("--cn", required=True, help="Certificate common name")
@click.option("--days", default=365, type=int, help="Validity period in days")
@click.option("--ca-dir", default="ca", help="CA directory")
@click.option("--output-dir", "-o", default="certs", help="Output directory")
def gencert(cn, days, ca_dir, output_dir):
    """Generate a certificate signed by the CA."""
    from cryptography.hazmat.primitives import serialization
    from cryptography import x509

    ca_key_path = os.path.join(ca_dir, "ca.key")
    ca_cert_path = os.path.join(ca_dir, "ca.crt")

    if not os.path.exists(ca_key_path) or not os.path.exists(ca_cert_path):
        click.echo("Error: CA files not found. Run 'genca' first.")
        return

    with open(ca_key_path, "rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)
    with open(ca_cert_path, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())

    os.makedirs(output_dir, exist_ok=True)

    cert_key, cert = generate_certificate(ca_key, ca_cert, cn, days)

    key_path = os.path.join(output_dir, f"{cn}.key")
    cert_path = os.path.join(output_dir, f"{cn}.crt")

    with open(key_path, "wb") as f:
        f.write(
            cert_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
    os.chmod(key_path, 0o600)

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    click.echo(f"Key saved to: {key_path}")
    click.echo(f"Certificate saved to: {cert_path}")


@cli.command()
@click.option("--username", "-u", required=True, help="Username")
@click.option("--password", "-P", prompt=True, hide_input=True, confirmation_prompt=True, help="Password")
@click.option("--users-file", default="users.json", help="Users database file")
@click.option("--allowed-ips", default="0.0.0.0/0", help="Comma-separated allowed IPs")
def adduser(username, password, users_file, allowed_ips):
    """Add a user for password authentication."""
    auth = PasswordAuthenticator()
    if os.path.exists(users_file):
        auth.load_from_file(users_file)

    ips = [ip.strip() for ip in allowed_ips.split(",")]
    auth.add_user(username, password, ips)
    auth.save_to_file(users_file)

    click.echo(f"User '{username}' added to {users_file}")


@cli.command()
@click.pass_context
def showconfig(ctx):
    """Show current configuration."""
    config_file = ctx.obj["config_file"]

    if os.path.exists(config_file):
        config = VPNConfig.load_from_file(config_file)
    else:
        config = VPNConfig()

    config_dict = {
        "server": {
            "listen_address": config.server.listen_address,
            "port": config.server.port,
            "transport": config.server.transport,
            "max_clients": config.server.max_clients,
        },
        "tun": {
            "name": config.tun.name,
            "address": config.tun.address,
            "netmask": config.tun.netmask,
            "mtu": config.tun.mtu,
        },
        "security": {
            "encryption": config.security.encryption,
            "key_exchange": config.security.key_exchange,
            "auth_method": config.security.auth_method,
        },
    }

    import yaml
    click.echo(yaml.dump(config_dict, default_flow_style=False))


def main():
    """Entry point for the VPN CLI."""
    cli(obj={})
