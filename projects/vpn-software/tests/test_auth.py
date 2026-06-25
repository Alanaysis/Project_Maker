"""Tests for the authentication module."""

import os
import pytest
from vpn.auth import PasswordAuthenticator, CertificateAuthenticator


class TestPasswordAuthenticator:
    def test_add_and_authenticate(self):
        auth = PasswordAuthenticator()
        auth.add_user("alice", "password123", ["10.0.0.2/32"])

        success, ips = auth.authenticate("alice", "password123")
        assert success
        assert ips == ["10.0.0.2/32"]

    def test_wrong_password(self):
        auth = PasswordAuthenticator()
        auth.add_user("alice", "password123")

        success, ips = auth.authenticate("alice", "wrongpassword")
        assert not success

    def test_unknown_user(self):
        auth = PasswordAuthenticator()

        success, ips = auth.authenticate("unknown", "password")
        assert not success

    def test_remove_user(self):
        auth = PasswordAuthenticator()
        auth.add_user("alice", "password123")

        assert auth.remove_user("alice")
        success, _ = auth.authenticate("alice", "password123")
        assert not success

    def test_save_load(self, tmp_path):
        path = str(tmp_path / "users.json")

        auth = PasswordAuthenticator()
        auth.add_user("alice", "password123", ["10.0.0.2/32"])
        auth.add_user("bob", "secret456", ["10.0.0.3/32"])
        auth.save_to_file(path)

        auth2 = PasswordAuthenticator()
        auth2.load_from_file(path)

        success, ips = auth2.authenticate("alice", "password123")
        assert success
        assert ips == ["10.0.0.2/32"]

        success, ips = auth2.authenticate("bob", "secret456")
        assert success

    def test_default_allowed_ips(self):
        auth = PasswordAuthenticator()
        auth.add_user("alice", "password123")

        success, ips = auth.authenticate("alice", "password123")
        assert success
        assert "0.0.0.0/0" in ips


class TestCertificateAuthenticator:
    def test_setup_and_issue(self, tmp_path):
        auth = CertificateAuthenticator()
        ca_dir = str(tmp_path / "ca")
        cert_dir = str(tmp_path / "certs")

        # Setup CA
        auth.setup_ca("Test CA", output_dir=ca_dir)
        assert os.path.exists(os.path.join(ca_dir, "ca.key"))
        assert os.path.exists(os.path.join(ca_dir, "ca.crt"))

        # Issue certificate
        key_path, cert_path = auth.issue_certificate("client1", output_dir=cert_dir)
        assert os.path.exists(key_path)
        assert os.path.exists(cert_path)

    def test_authenticate_certificate(self, tmp_path):
        auth = CertificateAuthenticator()
        ca_dir = str(tmp_path / "ca")
        cert_dir = str(tmp_path / "certs")

        auth.setup_ca("Test CA", output_dir=ca_dir)
        auth.load_ca(
            os.path.join(ca_dir, "ca.crt"),
            os.path.join(ca_dir, "ca.key"),
        )

        # Issue and authorize a client
        key_path, cert_path = auth.issue_certificate("client1", output_dir=cert_dir)
        auth.authorize_client("client1", ["10.0.0.2/32"])

        # Authenticate
        with open(cert_path, "rb") as f:
            cert_pem = f.read()

        success, ips = auth.authenticate(cert_pem)
        assert success
        assert ips == ["10.0.0.2/32"]

    def test_unauthorized_client(self, tmp_path):
        auth = CertificateAuthenticator()
        ca_dir = str(tmp_path / "ca")
        cert_dir = str(tmp_path / "certs")

        auth.setup_ca("Test CA", output_dir=ca_dir)
        auth.load_ca(
            os.path.join(ca_dir, "ca.crt"),
            os.path.join(ca_dir, "ca.key"),
        )

        # Issue certificate but do not authorize
        key_path, cert_path = auth.issue_certificate("unknown_client", output_dir=cert_dir)

        with open(cert_path, "rb") as f:
            cert_pem = f.read()

        success, ips = auth.authenticate(cert_pem)
        assert not success
