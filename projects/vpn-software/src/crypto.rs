//! Cryptographic operations for VPN tunnel
//!
//! Implements:
//! - Key exchange using X25519 (Curve25519 Diffie-Hellman)
//! - Symmetric encryption using ChaCha20-Poly1305
//! - Key derivation using HKDF-SHA256
//! - Hashing using BLAKE2s

use chacha20poly1305::{
    aead::{Aead, KeyInit, OsRng},
    ChaCha20Poly1305, Nonce,
};
use hkdf::Hkdf;
use rand::RngCore;
use sha2::Sha256;
use x25519_dalek::{EphemeralSecret, PublicKey, SharedSecret};

use crate::error::{Result, VpnError};

/// Size of the encryption key (256 bits)
pub const KEY_SIZE: usize = 32;

/// Size of the nonce for ChaCha20-Poly1305
pub const NONCE_SIZE: usize = 12;

/// Size of the authentication tag
pub const TAG_SIZE: usize = 16;

/// Represents the cryptographic state of a VPN connection
#[derive(Clone)]
pub struct CryptoState {
    /// Local private key
    private_key: EphemeralSecret,
    /// Local public key
    public_key: PublicKey,
    /// Shared secret (after key exchange)
    shared_secret: Option<SharedSecret>,
    /// Derived encryption key
    encryption_key: Option<[u8; KEY_SIZE]>,
    /// Current nonce counter
    nonce_counter: u64,
}

impl CryptoState {
    /// Create a new crypto state with fresh keypair
    pub fn new() -> Self {
        let private_key = EphemeralSecret::random_from_rng(OsRng);
        let public_key = PublicKey::from(&private_key);

        Self {
            private_key,
            public_key,
            shared_secret: None,
            encryption_key: None,
            nonce_counter: 0,
        }
    }

    /// Get the local public key
    pub fn public_key(&self) -> &PublicKey {
        &self.public_key
    }

    /// Perform key exchange with remote public key
    pub fn key_exchange(&mut self, remote_public_key: &PublicKey) -> Result<()> {
        let shared_secret = self.private_key.diffie_hellman(remote_public_key);

        // Derive encryption key using HKDF
        let hk = Hkdf::<Sha256>::new(None, shared_secret.as_bytes());
        let mut encryption_key = [0u8; KEY_SIZE];
        hk.expand(b"vpn-encryption-key", &mut encryption_key)
            .map_err(|e| VpnError::CryptoError(e.to_string()))?;

        self.shared_secret = Some(shared_secret);
        self.encryption_key = Some(encryption_key);

        Ok(())
    }

    /// Encrypt data using ChaCha20-Poly1305
    pub fn encrypt(&mut self, plaintext: &[u8]) -> Result<Vec<u8>> {
        let key = self.encryption_key
            .ok_or_else(|| VpnError::CryptoError("Key exchange not completed".to_string()))?;

        let cipher = ChaCha20Poly1305::new((&key).into());

        // Generate nonce from counter and increment for next call
        let nonce = self.generate_nonce();
        self.increment_nonce();

        let ciphertext = cipher
            .encrypt(Nonce::from_slice(&nonce), plaintext)
            .map_err(|e| VpnError::CryptoError(e.to_string()))?;

        // Prepend nonce to ciphertext
        let mut result = Vec::with_capacity(NONCE_SIZE + ciphertext.len());
        result.extend_from_slice(&nonce);
        result.extend_from_slice(&ciphertext);

        Ok(result)
    }

    /// Decrypt data using ChaCha20-Poly1305
    pub fn decrypt(&self, ciphertext: &[u8]) -> Result<Vec<u8>> {
        let key = self.encryption_key
            .ok_or_else(|| VpnError::CryptoError("Key exchange not completed".to_string()))?;

        if ciphertext.len() < NONCE_SIZE + TAG_SIZE {
            return Err(VpnError::CryptoError("Ciphertext too short".to_string()));
        }

        let cipher = ChaCha20Poly1305::new((&key).into());

        // Extract nonce from ciphertext
        let nonce = &ciphertext[..NONCE_SIZE];
        let encrypted_data = &ciphertext[NONCE_SIZE..];

        let plaintext = cipher
            .decrypt(Nonce::from_slice(nonce), encrypted_data)
            .map_err(|e| VpnError::CryptoError(e.to_string()))?;

        Ok(plaintext)
    }

    /// Generate a nonce from the counter
    fn generate_nonce(&self) -> [u8; NONCE_SIZE] {
        let mut nonce = [0u8; NONCE_SIZE];
        let counter_bytes = self.nonce_counter.to_le_bytes();
        nonce[..8].copy_from_slice(&counter_bytes);
        nonce
    }

    /// Increment the nonce counter
    pub fn increment_nonce(&mut self) {
        self.nonce_counter = self.nonce_counter.wrapping_add(1);
    }
}

/// Generate a random keypair for testing
pub fn generate_keypair() -> (EphemeralSecret, PublicKey) {
    let secret = EphemeralSecret::random_from_rng(OsRng);
    let public = PublicKey::from(&secret);
    (secret, public)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_key_exchange() {
        let mut alice = CryptoState::new();
        let mut bob = CryptoState::new();

        let alice_pub = *alice.public_key();
        let bob_pub = *bob.public_key();

        // Both sides perform key exchange
        alice.key_exchange(&bob_pub).unwrap();
        bob.key_exchange(&alice_pub).unwrap();

        // Both should derive the same key
        assert!(alice.encryption_key.is_some());
        assert!(bob.encryption_key.is_some());
        assert_eq!(alice.encryption_key, bob.encryption_key);
    }

    #[test]
    fn test_encrypt_decrypt() {
        let mut alice = CryptoState::new();
        let mut bob = CryptoState::new();

        let alice_pub = *alice.public_key();
        let bob_pub = *bob.public_key();

        alice.key_exchange(&bob_pub).unwrap();
        bob.key_exchange(&alice_pub).unwrap();

        let plaintext = b"Hello, VPN!";

        // Alice encrypts
        let ciphertext = alice.encrypt(plaintext).unwrap();

        // Bob decrypts
        let decrypted = bob.decrypt(&ciphertext).unwrap();

        assert_eq!(plaintext.as_slice(), decrypted.as_slice());
    }

    #[test]
    fn test_encrypt_decrypt_large_data() {
        let mut alice = CryptoState::new();
        let mut bob = CryptoState::new();

        let alice_pub = *alice.public_key();
        let bob_pub = *bob.public_key();

        alice.key_exchange(&bob_pub).unwrap();
        bob.key_exchange(&alice_pub).unwrap();

        // Create large plaintext
        let plaintext = vec![0xAA; 1500];

        let ciphertext = alice.encrypt(&plaintext).unwrap();
        let decrypted = bob.decrypt(&ciphertext).unwrap();

        assert_eq!(plaintext, decrypted);
    }

    #[test]
    fn test_tampered_ciphertext() {
        let mut alice = CryptoState::new();
        let mut bob = CryptoState::new();

        let alice_pub = *alice.public_key();
        let bob_pub = *bob.public_key();

        alice.key_exchange(&bob_pub).unwrap();
        bob.key_exchange(&alice_pub).unwrap();

        let plaintext = b"Hello, VPN!";
        let mut ciphertext = alice.encrypt(plaintext).unwrap();

        // Tamper with ciphertext
        if let Some(byte) = ciphertext.last_mut() {
            *byte ^= 0xFF;
        }

        // Decryption should fail
        assert!(bob.decrypt(&ciphertext).is_err());
    }
}
