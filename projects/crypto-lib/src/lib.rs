//! # Crypto Library
//!
//! A cryptography library implementing AES symmetric encryption,
//! RSA asymmetric encryption, and Elliptic Curve Cryptography (ECC).
//!
//! ## Features
//!
//! - **AES**: AES-128/192/256 encryption and decryption with CBC mode
//! - **RSA**: RSA key generation, encryption, and decryption
//! - **ECC**: Elliptic Curve Diffie-Hellman key exchange
//!
//! ## Example
//!
//! ```rust
//! use crypto_lib::aes::{AesKey, AesCipher};
//!
//! let key = AesKey::generate(128);
//! let cipher = AesCipher::new(key);
//! let plaintext = b"Hello, World!";
//! let ciphertext = cipher.encrypt(plaintext);
//! let decrypted = cipher.decrypt(&ciphertext);
//! assert_eq!(decrypted, plaintext);
//! ```

pub mod aes;
pub mod rsa;
pub mod ecc;

/// Common error types for the crypto library
#[derive(Debug, Clone, PartialEq)]
pub enum CryptoError {
    InvalidKeySize,
    InvalidBlockSize,
    DecryptionFailed,
    InvalidInput,
    KeyGenerationFailed,
}

impl std::fmt::Display for CryptoError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CryptoError::InvalidKeySize => write!(f, "Invalid key size"),
            CryptoError::InvalidBlockSize => write!(f, "Invalid block size"),
            CryptoError::DecryptionFailed => write!(f, "Decryption failed"),
            CryptoError::InvalidInput => write!(f, "Invalid input"),
            CryptoError::KeyGenerationFailed => write!(f, "Key generation failed"),
        }
    }
}

impl std::error::Error for CryptoError {}

/// Result type for crypto operations
pub type CryptoResult<T> = Result<T, CryptoError>;
