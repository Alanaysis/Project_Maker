"""Tests for the crypto module."""

import pytest
from vpn.crypto import (
    CryptoEngine,
    KeyPair,
    hash_password,
    verify_password,
    generate_ca,
    generate_certificate,
    verify_certificate,
    CryptoError,
)


class TestKeyPair:
    def test_generate(self):
        kp = KeyPair.generate()
        assert kp.private_key is not None
        assert kp.public_key is not None

    def test_public_bytes(self):
        kp = KeyPair.generate()
        pub_bytes = kp.public_bytes()
        assert isinstance(pub_bytes, bytes)
        assert len(pub_bytes) == 33  # Compressed point on P-256

    def test_pem_round_trip(self):
        kp = KeyPair.generate()
        pem = kp.private_pem()
        assert b"PRIVATE KEY" in pem

        kp2 = KeyPair.from_pem(pem)
        assert kp2.public_bytes() == kp.public_bytes()

    def test_public_pem(self):
        kp = KeyPair.generate()
        pem = kp.public_pem()
        assert b"PUBLIC KEY" in pem


class TestCryptoEngine:
    def test_key_exchange(self):
        alice = CryptoEngine()
        bob = CryptoEngine()

        alice.key_exchange(bob.public_key)
        bob.key_exchange(alice.public_key)

        assert alice.has_key
        assert bob.has_key

    def test_shared_key_agreement(self):
        alice = CryptoEngine()
        bob = CryptoEngine()

        alice.key_exchange(bob.public_key)
        bob.key_exchange(alice.public_key)

        # Both should derive the same key (encrypt/decrypt round trip)
        plaintext = b"Hello, VPN!"
        ciphertext = alice.encrypt(plaintext)
        decrypted = bob.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_encrypt_decrypt(self):
        alice = CryptoEngine()
        bob = CryptoEngine()

        alice.key_exchange(bob.public_key)
        bob.key_exchange(alice.public_key)

        plaintext = b"Hello, VPN!"
        ciphertext = alice.encrypt(plaintext)

        # Ciphertext should be different from plaintext
        assert ciphertext != plaintext

        # Bob can decrypt
        decrypted = bob.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_encrypt_large_data(self):
        alice = CryptoEngine()
        bob = CryptoEngine()

        alice.key_exchange(bob.public_key)
        bob.key_exchange(alice.public_key)

        plaintext = b"\xAA" * 1500  # MTU-sized packet
        ciphertext = alice.encrypt(plaintext)
        decrypted = bob.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_tampered_ciphertext(self):
        alice = CryptoEngine()
        bob = CryptoEngine()

        alice.key_exchange(bob.public_key)
        bob.key_exchange(alice.public_key)

        ciphertext = alice.encrypt(b"Hello")
        tampered = bytearray(ciphertext)
        tampered[-1] ^= 0xFF

        with pytest.raises(CryptoError):
            bob.decrypt(bytes(tampered))

    def test_encrypt_without_key(self):
        engine = CryptoEngine()
        with pytest.raises(CryptoError):
            engine.encrypt(b"test")

    def test_decrypt_without_key(self):
        engine = CryptoEngine()
        with pytest.raises(CryptoError):
            engine.decrypt(b"test" * 10)

    def test_decrypt_short_ciphertext(self):
        engine = CryptoEngine()
        engine._encryption_key = b"\x00" * 32
        with pytest.raises(CryptoError):
            engine.decrypt(b"short")

    def test_unique_nonces(self):
        alice = CryptoEngine()
        bob = CryptoEngine()
        alice.key_exchange(bob.public_key)
        bob.key_exchange(alice.public_key)

        # Encrypt multiple messages
        ct1 = alice.encrypt(b"msg1")
        ct2 = alice.encrypt(b"msg2")

        # Nonces should be different (first 12 bytes)
        assert ct1[:12] != ct2[:12]


class TestPasswordAuth:
    def test_hash_password(self):
        password_hash, salt = hash_password("testpassword")
        assert len(password_hash) == 32
        assert len(salt) == 16

    def test_verify_password(self):
        password = "secure_password_123"
        password_hash, salt = hash_password(password)
        assert verify_password(password, password_hash, salt)

    def test_wrong_password(self):
        password_hash, salt = hash_password("correct_password")
        assert not verify_password("wrong_password", password_hash, salt)

    def test_different_salts(self):
        h1, s1 = hash_password("password")
        h2, s2 = hash_password("password")
        # Different salts should produce different hashes
        assert s1 != s2
        assert h1 != h2


class TestCertificates:
    def test_generate_ca(self):
        ca_key, ca_cert = generate_ca("Test CA", 365)
        assert ca_cert.issuer == ca_cert.subject  # Self-signed
        cn = ca_cert.subject.get_attributes_for_oid(
            __import__("cryptography", fromlist=["x509"]).x509.oid.NameOID.COMMON_NAME
        )[0].value
        assert cn == "Test CA"

    def test_generate_and_verify_certificate(self):
        ca_key, ca_cert = generate_ca("Test CA")
        cert_key, cert = generate_certificate(ca_key, ca_cert, "client1")

        # Serialize and verify
        from cryptography.hazmat.primitives import serialization
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        ca_pem = ca_cert.public_bytes(serialization.Encoding.PEM)

        assert verify_certificate(cert_pem, ca_pem)

    def test_invalid_certificate(self):
        ca_key, ca_cert = generate_ca("Test CA")
        # A random certificate should not verify
        _, other_cert = generate_certificate(ca_key, ca_cert, "other")

        from cryptography.hazmat.primitives import serialization
        # Generate a different CA
        other_ca_key, other_ca_cert = generate_ca("Other CA")
        cert_pem = other_cert.public_bytes(serialization.Encoding.PEM)
        wrong_ca_pem = other_ca_cert.public_bytes(serialization.Encoding.PEM)

        assert not verify_certificate(cert_pem, wrong_ca_pem)
