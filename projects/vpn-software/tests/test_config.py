"""Tests for the configuration module."""

import pytest
from vpn.config import VPNConfig, ServerConfig, ClientConfig, TunConfig, SecurityConfig


class TestVPNConfig:
    def test_default_config(self):
        config = VPNConfig()
        assert config.server.port == 51820
        assert config.tun.name == "tun0"
        assert config.tun.address == "10.0.0.1"
        assert config.security.encryption == "aes-256-gcm"

    def test_from_dict(self):
        data = {
            "server": {"port": 8080, "transport": "tcp"},
            "tun": {"name": "tun1", "address": "10.0.1.1"},
            "security": {"auth_method": "certificate"},
        }
        config = VPNConfig.from_dict(data)
        assert config.server.port == 8080
        assert config.server.transport == "tcp"
        assert config.tun.name == "tun1"
        assert config.tun.address == "10.0.1.1"
        assert config.security.auth_method == "certificate"

    def test_save_load(self, tmp_path):
        path = str(tmp_path / "config.yaml")

        config = VPNConfig()
        config.server.port = 9999
        config.tun.address = "10.0.9.1"
        config.save_to_file(path)

        loaded = VPNConfig.load_from_file(path)
        assert loaded.server.port == 9999
        assert loaded.tun.address == "10.0.9.1"

    def test_load_missing_file(self):
        with pytest.raises(Exception):
            VPNConfig.load_from_file("/nonexistent/config.yaml")
