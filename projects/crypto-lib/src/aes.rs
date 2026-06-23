//! AES (Advanced Encryption Standard) implementation
//!
//! Supports AES-128, AES-192, and AES-256 with CBC mode of operation.
//!
//! # AES Algorithm Overview
//!
//! AES is a symmetric block cipher that encrypts data in 128-bit blocks.
//! The key size determines the number of rounds:
//! - AES-128: 10 rounds
//! - AES-192: 12 rounds
//! - AES-256: 14 rounds
//!
//! Each round consists of four transformations:
//! 1. SubBytes - Non-linear substitution using S-box
//! 2. ShiftRows - Cyclic shift of rows
//! 3. MixColumns - Mixing columns using polynomial multiplication
//! 4. AddRoundKey - XOR with round key

use crate::{CryptoError, CryptoResult};
use rand::Rng;

/// AES S-box for SubBytes transformation
const S_BOX: [[u8; 16]; 16] = [
    [0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76],
    [0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0],
    [0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15],
    [0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75],
    [0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84],
    [0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF],
    [0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8],
    [0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2],
    [0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73],
    [0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB],
    [0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79],
    [0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08],
    [0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A],
    [0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E],
    [0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF],
    [0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16],
];

/// Inverse S-box for InvSubBytes transformation
const INV_S_BOX: [[u8; 16]; 16] = [
    [0x52, 0x09, 0x6A, 0xD5, 0x30, 0x36, 0xA5, 0x38, 0xBF, 0x40, 0xA3, 0x9E, 0x81, 0xF3, 0xD7, 0xFB],
    [0x7C, 0xE3, 0x39, 0x82, 0x9B, 0x2F, 0xFF, 0x87, 0x34, 0x8E, 0x43, 0x44, 0xC4, 0xDE, 0xE9, 0xCB],
    [0x54, 0x7B, 0x94, 0x32, 0xA6, 0xC2, 0x23, 0x3D, 0xEE, 0x4C, 0x95, 0x0B, 0x42, 0xFA, 0xC3, 0x4E],
    [0x08, 0x2E, 0xA1, 0x66, 0x28, 0xD9, 0x24, 0xB2, 0x76, 0x5B, 0xA2, 0x49, 0x6D, 0x8B, 0xD1, 0x25],
    [0x72, 0xF8, 0xF6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xD4, 0xA4, 0x5C, 0xCC, 0x5D, 0x65, 0xB6, 0x92],
    [0x6C, 0x70, 0x48, 0x50, 0xFD, 0xED, 0xB9, 0xDA, 0x5E, 0x15, 0x46, 0x57, 0xA7, 0x8D, 0x9D, 0x84],
    [0x90, 0xD8, 0xAB, 0x00, 0x8C, 0xBC, 0xD3, 0x0A, 0xF7, 0xE4, 0x58, 0x05, 0xB8, 0xB3, 0x45, 0x06],
    [0xD0, 0x2C, 0x1E, 0x8F, 0xCA, 0x3F, 0x0F, 0x02, 0xC1, 0xAF, 0xBD, 0x03, 0x01, 0x13, 0x8A, 0x6B],
    [0x3A, 0x91, 0x11, 0x41, 0x4F, 0x67, 0xDC, 0xEA, 0x97, 0xF2, 0xCF, 0xCE, 0xF0, 0xB4, 0xE6, 0x73],
    [0x96, 0xAC, 0x74, 0x22, 0xE7, 0xAD, 0x35, 0x85, 0xE2, 0xF9, 0x37, 0xE8, 0x1C, 0x75, 0xDF, 0x6E],
    [0x47, 0xF1, 0x1A, 0x71, 0x1D, 0x29, 0xC5, 0x89, 0x6F, 0xB7, 0x62, 0x0E, 0xAA, 0x18, 0xBE, 0x1B],
    [0xFC, 0x56, 0x3E, 0x4B, 0xC6, 0xD2, 0x79, 0x20, 0x9A, 0xDB, 0xC0, 0xFE, 0x78, 0xCD, 0x5A, 0xF4],
    [0x1F, 0xDD, 0xA8, 0x33, 0x88, 0x07, 0xC7, 0x31, 0xB1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xEC, 0x5F],
    [0x60, 0x51, 0x7F, 0xA9, 0x19, 0xB5, 0x4A, 0x0D, 0x2D, 0xE5, 0x7A, 0x9F, 0x93, 0xC9, 0x9C, 0xEF],
    [0xA0, 0xE0, 0x3B, 0x4D, 0xAE, 0x2A, 0xF5, 0xB0, 0xC8, 0xEB, 0xBB, 0x3C, 0x83, 0x53, 0x99, 0x61],
    [0x17, 0x2B, 0x04, 0x7E, 0xBA, 0x77, 0xD6, 0x26, 0xE1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0C, 0x7D],
];

/// Round constants for key expansion
const RCON: [u8; 11] = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36];

/// AES key sizes
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum AesKeySize {
    Aes128,
    Aes192,
    Aes256,
}

impl AesKeySize {
    /// Returns the key size in bytes
    pub fn key_bytes(&self) -> usize {
        match self {
            AesKeySize::Aes128 => 16,
            AesKeySize::Aes192 => 24,
            AesKeySize::Aes256 => 32,
        }
    }

    /// Returns the number of rounds for this key size
    pub fn rounds(&self) -> usize {
        match self {
            AesKeySize::Aes128 => 10,
            AesKeySize::Aes192 => 12,
            AesKeySize::Aes256 => 14,
        }
    }
}

/// AES key for encryption/decryption
#[derive(Debug, Clone)]
pub struct AesKey {
    pub key: Vec<u8>,
    pub size: AesKeySize,
}

impl AesKey {
    /// Create a new AES key from bytes
    pub fn new(key: &[u8]) -> CryptoResult<Self> {
        let size = match key.len() {
            16 => AesKeySize::Aes128,
            24 => AesKeySize::Aes192,
            32 => AesKeySize::Aes256,
            _ => return Err(CryptoError::InvalidKeySize),
        };

        Ok(AesKey {
            key: key.to_vec(),
            size,
        })
    }

    /// Generate a random AES key
    pub fn generate(bit_size: u32) -> Self {
        let size = match bit_size {
            128 => AesKeySize::Aes128,
            192 => AesKeySize::Aes192,
            256 => AesKeySize::Aes256,
            _ => panic!("Invalid AES key size. Use 128, 192, or 256"),
        };

        let mut rng = rand::thread_rng();
        let key: Vec<u8> = (0..size.key_bytes()).map(|_| rng.gen()).collect();

        AesKey { key, size }
    }
}

/// AES cipher for encryption and decryption
pub struct AesCipher {
    key: AesKey,
    round_keys: Vec<[u8; 4]>,
}

impl AesCipher {
    /// Create a new AES cipher with the given key
    pub fn new(key: AesKey) -> Self {
        let round_keys = Self::key_expansion(&key);
        AesCipher { key, round_keys }
    }

    /// Encrypt plaintext using AES-CBC mode
    pub fn encrypt(&self, plaintext: &[u8]) -> Vec<u8> {
        let mut rng = rand::thread_rng();
        let iv: [u8; 16] = rng.gen();

        let padded = self.pkcs7_pad(plaintext);
        let mut ciphertext = iv.to_vec();

        let mut prev_block = iv;
        for chunk in padded.chunks(16) {
            let mut block = [0u8; 16];
            for i in 0..16 {
                block[i] = chunk[i] ^ prev_block[i];
            }

            let encrypted = self.encrypt_block(&block);
            ciphertext.extend_from_slice(&encrypted);
            prev_block = encrypted;
        }

        ciphertext
    }

    /// Decrypt ciphertext using AES-CBC mode
    pub fn decrypt(&self, ciphertext: &[u8]) -> Vec<u8> {
        if ciphertext.len() < 32 || ciphertext.len() % 16 != 0 {
            return Vec::new();
        }

        let iv: [u8; 16] = ciphertext[..16].try_into().unwrap();
        let mut plaintext = Vec::new();
        let mut prev_block = iv;

        for chunk in ciphertext[16..].chunks(16) {
            let decrypted = self.decrypt_block(chunk.try_into().unwrap());
            let mut block = [0u8; 16];
            for i in 0..16 {
                block[i] = decrypted[i] ^ prev_block[i];
            }
            plaintext.extend_from_slice(&block);
            prev_block = chunk.try_into().unwrap();
        }

        self.pkcs7_unpad(&plaintext)
    }

    /// Encrypt a single 128-bit block
    fn encrypt_block(&self, block: &[u8; 16]) -> [u8; 16] {
        let mut state = *block;
        let nr = self.key.size.rounds();

        // Initial round key addition
        self.add_round_key(&mut state, 0);

        // Main rounds
        for round in 1..nr {
            self.sub_bytes(&mut state);
            self.shift_rows(&mut state);
            self.mix_columns(&mut state);
            self.add_round_key(&mut state, round);
        }

        // Final round (no MixColumns)
        self.sub_bytes(&mut state);
        self.shift_rows(&mut state);
        self.add_round_key(&mut state, nr);

        state
    }

    /// Decrypt a single 128-bit block
    fn decrypt_block(&self, block: &[u8; 16]) -> [u8; 16] {
        let mut state = *block;
        let nr = self.key.size.rounds();

        // Initial round key addition
        self.add_round_key(&mut state, nr);

        // Main rounds (in reverse)
        for round in (1..nr).rev() {
            self.inv_shift_rows(&mut state);
            self.inv_sub_bytes(&mut state);
            self.add_round_key(&mut state, round);
            self.inv_mix_columns(&mut state);
        }

        // Final round
        self.inv_shift_rows(&mut state);
        self.inv_sub_bytes(&mut state);
        self.add_round_key(&mut state, 0);

        state
    }

    /// SubBytes transformation
    fn sub_bytes(&self, state: &mut [u8; 16]) {
        for byte in state.iter_mut() {
            let row = (*byte >> 4) as usize;
            let col = (*byte & 0x0F) as usize;
            *byte = S_BOX[row][col];
        }
    }

    /// Inverse SubBytes transformation
    fn inv_sub_bytes(&self, state: &mut [u8; 16]) {
        for byte in state.iter_mut() {
            let row = (*byte >> 4) as usize;
            let col = (*byte & 0x0F) as usize;
            *byte = INV_S_BOX[row][col];
        }
    }

    /// ShiftRows transformation
    fn shift_rows(&self, state: &mut [u8; 16]) {
        // Row 0: no shift
        // Row 1: shift left by 1
        let temp = state[1];
        state[1] = state[5];
        state[5] = state[9];
        state[9] = state[13];
        state[13] = temp;

        // Row 2: shift left by 2
        let temp = state[2];
        state[2] = state[10];
        state[10] = temp;
        let temp = state[6];
        state[6] = state[14];
        state[14] = temp;

        // Row 3: shift left by 3 (or right by 1)
        let temp = state[15];
        state[15] = state[11];
        state[11] = state[7];
        state[7] = state[3];
        state[3] = temp;
    }

    /// Inverse ShiftRows transformation
    fn inv_shift_rows(&self, state: &mut [u8; 16]) {
        // Row 0: no shift
        // Row 1: shift right by 1
        let temp = state[13];
        state[13] = state[9];
        state[9] = state[5];
        state[5] = state[1];
        state[1] = temp;

        // Row 2: shift right by 2
        let temp = state[2];
        state[2] = state[10];
        state[10] = temp;
        let temp = state[6];
        state[6] = state[14];
        state[14] = temp;

        // Row 3: shift right by 3 (or left by 1)
        let temp = state[3];
        state[3] = state[7];
        state[7] = state[11];
        state[11] = state[15];
        state[15] = temp;
    }

    /// MixColumns transformation
    fn mix_columns(&self, state: &mut [u8; 16]) {
        for col in 0..4 {
            let c0 = state[col * 4];
            let c1 = state[col * 4 + 1];
            let c2 = state[col * 4 + 2];
            let c3 = state[col * 4 + 3];

            state[col * 4] = gmul(c0, 2) ^ gmul(c1, 3) ^ c2 ^ c3;
            state[col * 4 + 1] = c0 ^ gmul(c1, 2) ^ gmul(c2, 3) ^ c3;
            state[col * 4 + 2] = c0 ^ c1 ^ gmul(c2, 2) ^ gmul(c3, 3);
            state[col * 4 + 3] = gmul(c0, 3) ^ c1 ^ c2 ^ gmul(c3, 2);
        }
    }

    /// Inverse MixColumns transformation
    fn inv_mix_columns(&self, state: &mut [u8; 16]) {
        for col in 0..4 {
            let c0 = state[col * 4];
            let c1 = state[col * 4 + 1];
            let c2 = state[col * 4 + 2];
            let c3 = state[col * 4 + 3];

            state[col * 4] = gmul(c0, 0x0E) ^ gmul(c1, 0x0B) ^ gmul(c2, 0x0D) ^ gmul(c3, 0x09);
            state[col * 4 + 1] = gmul(c0, 0x09) ^ gmul(c1, 0x0E) ^ gmul(c2, 0x0B) ^ gmul(c3, 0x0D);
            state[col * 4 + 2] = gmul(c0, 0x0D) ^ gmul(c1, 0x09) ^ gmul(c2, 0x0E) ^ gmul(c3, 0x0B);
            state[col * 4 + 3] = gmul(c0, 0x0B) ^ gmul(c1, 0x0D) ^ gmul(c2, 0x09) ^ gmul(c3, 0x0E);
        }
    }

    /// AddRoundKey transformation
    fn add_round_key(&self, state: &mut [u8; 16], round: usize) {
        for col in 0..4 {
            let key_word = self.round_keys[round * 4 + col];
            state[col * 4] ^= key_word[0];
            state[col * 4 + 1] ^= key_word[1];
            state[col * 4 + 2] ^= key_word[2];
            state[col * 4 + 3] ^= key_word[3];
        }
    }

    /// Key expansion algorithm
    fn key_expansion(key: &AesKey) -> Vec<[u8; 4]> {
        let nk = key.key.len() / 4;
        let nr = key.size.rounds();
        let total_words = 4 * (nr + 1);

        let mut w: Vec<[u8; 4]> = Vec::with_capacity(total_words);

        // Copy key to first nk words
        for i in 0..nk {
            let word = [
                key.key[i * 4],
                key.key[i * 4 + 1],
                key.key[i * 4 + 2],
                key.key[i * 4 + 3],
            ];
            w.push(word);
        }

        // Expand key
        for i in nk..total_words {
            let mut temp = w[i - 1];

            if i % nk == 0 {
                // RotWord
                temp = [temp[1], temp[2], temp[3], temp[0]];

                // SubWord
                for byte in temp.iter_mut() {
                    let row = (*byte >> 4) as usize;
                    let col = (*byte & 0x0F) as usize;
                    *byte = S_BOX[row][col];
                }

                // XOR with Rcon
                temp[0] ^= RCON[i / nk];
            } else if nk > 6 && i % nk == 4 {
                // SubWord for AES-256
                for byte in temp.iter_mut() {
                    let row = (*byte >> 4) as usize;
                    let col = (*byte & 0x0F) as usize;
                    *byte = S_BOX[row][col];
                }
            }

            let prev = w[i - nk];
            w.push([
                prev[0] ^ temp[0],
                prev[1] ^ temp[1],
                prev[2] ^ temp[2],
                prev[3] ^ temp[3],
            ]);
        }

        w
    }

    /// PKCS7 padding
    fn pkcs7_pad(&self, data: &[u8]) -> Vec<u8> {
        let block_size = 16;
        let padding_len = block_size - (data.len() % block_size);
        let mut padded = data.to_vec();
        padded.extend(vec![padding_len as u8; padding_len]);
        padded
    }

    /// PKCS7 unpadding
    fn pkcs7_unpad(&self, data: &[u8]) -> Vec<u8> {
        if data.is_empty() {
            return Vec::new();
        }

        let padding_len = *data.last().unwrap() as usize;
        if padding_len == 0 || padding_len > 16 || padding_len > data.len() {
            return data.to_vec();
        }

        // Verify padding
        for i in data.len() - padding_len..data.len() {
            if data[i] != padding_len as u8 {
                return data.to_vec();
            }
        }

        data[..data.len() - padding_len].to_vec()
    }
}

/// Galois Field multiplication (GF(2^8))
fn gmul(a: u8, b: u8) -> u8 {
    let mut p = 0u8;
    let mut a_val = a;
    let mut b_val = b;

    for _ in 0..8 {
        if b_val & 1 != 0 {
            p ^= a_val;
        }

        let hi_bit = a_val & 0x80;
        a_val <<= 1;
        if hi_bit != 0 {
            a_val ^= 0x1B; // AES irreducible polynomial
        }
        b_val >>= 1;
    }

    p
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_aes128_encrypt_decrypt() {
        let key = AesKey::generate(128);
        let cipher = AesCipher::new(key);

        let plaintext = b"Hello, World! This is a test message.";
        let ciphertext = cipher.encrypt(plaintext);
        let decrypted = cipher.decrypt(&ciphertext);

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_aes192_encrypt_decrypt() {
        let key = AesKey::generate(192);
        let cipher = AesCipher::new(key);

        let plaintext = b"AES-192 test with longer key size for more security.";
        let ciphertext = cipher.encrypt(plaintext);
        let decrypted = cipher.decrypt(&ciphertext);

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_aes256_encrypt_decrypt() {
        let key = AesKey::generate(256);
        let cipher = AesCipher::new(key);

        let plaintext = b"AES-256 provides the strongest encryption among AES variants.";
        let ciphertext = cipher.encrypt(plaintext);
        let decrypted = cipher.decrypt(&ciphertext);

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_aes_empty_input() {
        let key = AesKey::generate(128);
        let cipher = AesCipher::new(key);

        let plaintext = b"";
        let ciphertext = cipher.encrypt(plaintext);
        let decrypted = cipher.decrypt(&ciphertext);

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_aes_exact_block_size() {
        let key = AesKey::generate(128);
        let cipher = AesCipher::new(key);

        let plaintext = b"1234567890123456"; // Exactly 16 bytes
        let ciphertext = cipher.encrypt(plaintext);
        let decrypted = cipher.decrypt(&ciphertext);

        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_gmul() {
        assert_eq!(gmul(0x57, 0x83), 0xC1);
        assert_eq!(gmul(0x02, 0x01), 0x02);
        assert_eq!(gmul(0x03, 0x01), 0x03);
    }

    #[test]
    fn test_s_box() {
        assert_eq!(S_BOX[0][0], 0x63); // S(0x00) = 0x63
        assert_eq!(S_BOX[0][1], 0x7C); // S(0x01) = 0x7C
    }
}
