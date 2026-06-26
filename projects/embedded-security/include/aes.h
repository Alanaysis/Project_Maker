/**
 * @file aes.h
 * @brief AES-128 Encryption Module (Educational Implementation)
 *
 * Implements AES-128 block cipher from scratch for educational purposes.
 * Based on NIST FIPS 197 specification.
 *
 * Security concepts:
 * - Block cipher: Fixed-size block encryption (128 bits)
 * - Substitution-permutation network (SPN)
 * - Key expansion: Deriving round keys from master key
 * - Confusion and diffusion: Shannon's principles
 */

#ifndef EMBEDDED_SECURITY_AES_H
#define EMBEDDED_SECURITY_AES_H

#include <stdint.h>
#include <stdbool.h>

#define AES_BLOCK_SIZE   16   /* 128 bits */
#define AES_KEY_SIZE_128 16   /* 128 bits */
#define AES_KEY_SIZE_192 24   /* 192 bits */
#define AES_KEY_SIZE_256 32   /* 256 bits */
#define AES_MAX_ROUNDS   14   /* For AES-256 */
#define AES_MAX_KEY_WORDS 16  /* 256-bit key / 32 bits */

/* AES context structure */
typedef struct {
    uint32_t expanded_key[4 * (AES_MAX_ROUNDS + 1)];
    int      rounds;
} aes_context_t;

/* State matrix (4x4 bytes, column-major) */
typedef struct {
    uint8_t bytes[16];
} aes_state_t;

/* S-box for substitution step (256 entries) */
extern const uint8_t aes_sbox[256];

/* Inverse S-box for decryption */
extern const uint8_t aes_inv_sbox[256];

/* Rcon (round constants) for key expansion */
extern const uint8_t aes_rcon[11];

/**
 * Initialize AES context for encryption
 * @param ctx AES context
 * @param key Encryption key (16/24/32 bytes)
 * @param key_len Key length in bytes
 * @return true on success
 */
bool aes_encrypt_init(aes_context_t *ctx, const uint8_t *key, int key_len);

/**
 * Initialize AES context for decryption
 * @param ctx AES context
 * @param key Decryption key (must match encryption key)
 * @param key_len Key length in bytes
 * @return true on success
 */
bool aes_decrypt_init(aes_context_t *ctx, const uint8_t *key, int key_len);

/**
 * Encrypt a single 128-bit block
 * @param ctx AES context
 * @param plaintext Input plaintext block (16 bytes)
 * @param ciphertext Output ciphertext block (16 bytes)
 */
void aes_encrypt_block(const aes_context_t *ctx,
                       const uint8_t *plaintext,
                       uint8_t *ciphertext);

/**
 * Decrypt a single 128-bit block
 * @param ctx AES context
 * @param ciphertext Input ciphertext block (16 bytes)
 * @param plaintext Output plaintext block (16 bytes)
 */
void aes_decrypt_block(const aes_context_t *ctx,
                       const uint8_t *ciphertext,
                       uint8_t *plaintext);

/**
 * Encrypt data in ECB mode (educational only - not for production)
 * In production, use CBC, CTR, or GCM mode
 * @param ctx AES context
 * @param input Input data (multiple of 16 bytes)
 * @param output Output buffer (same length as input)
 * @param length Data length in bytes
 */
void aes_encrypt_ecb(const aes_context_t *ctx,
                     const uint8_t *input,
                     uint8_t *output,
                     uint32_t length);

/**
 * Decrypt data in ECB mode (educational only)
 * @param ctx AES context
 * @param input Input data (multiple of 16 bytes)
 * @param output Output buffer (same length as input)
 * @param length Data length in bytes
 */
void aes_decrypt_ecb(const aes_context_t *ctx,
                     const uint8_t *input,
                     uint8_t *output,
                     uint32_t length);

/**
 * XOR two 128-bit blocks
 * @param a First block
 * @param b Second block
 * @param result Output a XOR b
 */
void aes_xor_block(const uint8_t *a, const uint8_t *b, uint8_t *result);

/**
 * Convert between byte array and state matrix
 */
void aes_bytes_to_state(const uint8_t *bytes, aes_state_t *state);
void aes_state_to_bytes(const aes_state_t *state, uint8_t *bytes);

/**
 * Get human-readable string for AES mode
 */
const char *aes_mode_str(int mode);

#endif /* EMBEDDED_SECURITY_AES_H */
