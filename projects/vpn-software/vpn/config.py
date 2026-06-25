"""
Configuration management for VPN software.

Supports YAML configuration files with sensible defaults.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, List

from vpn.error import ConfigError


@dataclass
class ServerConfig:
    """Server-specific configuration."""
    listen_address: str = "0.0.0.0"
    port: int = 51820
    transport: str = "udp"  # "udp" or "tcp"
    max_clients: int = 100
    keepalive_interval: float = 25.0


@dataclass
class ClientConfig:
    """Client-specific configuration."""
    server_address: str = "0.0.0.0"
    server_port: int = 51820
    transport: str = "udp"
    connection_timeout: float = 30.0
    auto_reconnect: bool = True


@dataclass
class TunConfig:
    """TUN device configuration."""
    name: str = "tun0"
    address: str = "10.0.0.1"
    netmask: str = "255.255.255.0"
    mtu: int = 1500


@dataclass
class SecurityConfig:
    """Security configuration."""
    encryption: str = "aes-256-gcm"
    key_exchange: str = "ecdh-p256"
    auth_method: str = "password"  # "password" or "certificate"
    handshake_timeout: float = 10.0
    rekey_interval: float = 3600.0
    # Certificate paths (if auth_method == "certificate")
    ca_cert: Optional[str] = None
    ca_key: Optional[str] = None
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    # Password auth database
    users_file: Optional[str] = None


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "info"
    file: Optional[str] = None
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


@dataclass
class VPNConfig:
    """Main VPN configuration."""
    server: ServerConfig = field(default_factory=ServerConfig)
    client: ClientConfig = field(default_factory=ClientConfig)
    tun: TunConfig = field(default_factory=TunConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @staticmethod
    def from_dict(data: dict) -> "VPNConfig":
        """Create config from a dictionary."""
        config = VPNConfig()

        if "server" in data:
            s = data["server"]
            config.server = ServerConfig(
                listen_address=s.get("listen_address", "0.0.0.0"),
                port=s.get("port", 51820),
                transport=s.get("transport", "udp"),
                max_clients=s.get("max_clients", 100),
                keepalive_interval=s.get("keepalive_interval", 25.0),
            )

        if "client" in data:
            c = data["client"]
            config.client = ClientConfig(
                server_address=c.get("server_address", "0.0.0.0"),
                server_port=c.get("server_port", 51820),
                transport=c.get("transport", "udp"),
                connection_timeout=c.get("connection_timeout", 30.0),
                auto_reconnect=c.get("auto_reconnect", True),
            )

        if "tun" in data:
            t = data["tun"]
            config.tun = TunConfig(
                name=t.get("name", "tun0"),
                address=t.get("address", "10.0.0.1"),
                netmask=t.get("netmask", "255.255.255.0"),
                mtu=t.get("mtu", 1500),
            )

        if "security" in data:
            sec = data["security"]
            config.security = SecurityConfig(
                encryption=sec.get("encryption", "aes-256-gcm"),
                key_exchange=sec.get("key_exchange", "ecdh-p256"),
                auth_method=sec.get("auth_method", "password"),
                handshake_timeout=sec.get("handshake_timeout", 10.0),
                rekey_interval=sec.get("rekey_interval", 3600.0),
                ca_cert=sec.get("ca_cert"),
                ca_key=sec.get("ca_key"),
                cert_file=sec.get("cert_file"),
                key_file=sec.get("key_file"),
                users_file=sec.get("users_file"),
            )

        if "logging" in data:
            lg = data["logging"]
            config.logging = LoggingConfig(
                level=lg.get("level", "info"),
                file=lg.get("file"),
                format=lg.get("format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s"),
            )

        return config

    @staticmethod
    def load_from_file(path: str) -> "VPNConfig":
        """Load configuration from a YAML file."""
        if not os.path.exists(path):
            raise ConfigError(f"Config file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

        return VPNConfig.from_dict(data)

    def save_to_file(self, path: str) -> None:
        """Save configuration to a YAML file."""
        data = {
            "server": {
                "listen_address": self.server.listen_address,
                "port": self.server.port,
                "transport": self.server.transport,
                "max_clients": self.server.max_clients,
                "keepalive_interval": self.server.keepalive_interval,
            },
            "client": {
                "server_address": self.client.server_address,
                "server_port": self.client.server_port,
                "transport": self.client.transport,
                "connection_timeout": self.client.connection_timeout,
                "auto_reconnect": self.client.auto_reconnect,
            },
            "tun": {
                "name": self.tun.name,
                "address": self.tun.address,
                "netmask": self.tun.netmask,
                "mtu": self.tun.mtu,
            },
            "security": {
                "encryption": self.security.encryption,
                "key_exchange": self.security.key_exchange,
                "auth_method": self.security.auth_method,
                "handshake_timeout": self.security.handshake_timeout,
                "rekey_interval": self.security.rekey_interval,
            },
            "logging": {
                "level": self.logging.level,
            },
        }

        # Include optional fields
        if self.security.ca_cert:
            data["security"]["ca_cert"] = self.security.ca_cert
        if self.security.cert_file:
            data["security"]["cert_file"] = self.security.cert_file
        if self.security.key_file:
            data["security"]["key_file"] = self.security.key_file
        if self.security.users_file:
            data["security"]["users_file"] = self.security.users_file
        if self.logging.file:
            data["logging"]["file"] = self.logging.file

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
