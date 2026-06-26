/**
 * @file sha256.h
 * @brief SHA-256 Hash Function Implementation
 *
 * Implements SHA-256 (Secure Hash Algorithm) per FIPS 180-4.
 * Produces a 256-bit (32-byte) hash digest.
 *
 * Security concepts:
 * - Hash function: Fixed-size output from arbitrary input
 * - Avalanche effect: Small input change causes large output change
 * - Pre-image resistance: Cannot reverse hash to find input
 */

#ifndef EMBEDDED_SECURITY_SHA256_H
#define EMBEDDED_SECURITY_SHA256_H

#include <stdint.h>
#include <stdbool.h>

#define SHA256_BLOCK_SIZE    64   /* 512 bits */
#define SHA256_DIGEST_SIZE   32   /* 256 bits */
#define SHA256_WORKING_WORDS 64

/* SHA-256 context for incremental hashing */
typedef struct {
    uint32_t state[8];       /* Current hash state (H0-H7) */
    uint8_t  buffer[64];     /* Input buffer */
    uint32_t total_len;      /* Total bytes hashed */
    bool     finalized;
} sha256_context;

/* SHA-256 constant K[0..63] - first 32 bits of fractional parts of cube roots */
extern const uint32_t sha256_k[64];

/**
 * Initialize SHA-256 context
 * @param ctx SHA-256 context
 */
void sha256_init(sha256_context *ctx);

/**
 * Update SHA-256 hash with data
 * Can be called multiple times for streaming data
 * @param ctx SHA-256 context
 * @param data Data to hash
 * @param len Data length in bytes
 */
void sha256_update(sha256_context *ctx, const uint8_t *data, uint32_t len);

/**
 * Finalize SHA-256 hash and get digest
 * @param ctx SHA-256 context
 * @param digest Output digest (32 bytes)
 * @return true on success
 */
bool sha256_final(sha256_context *ctx, uint8_t *digest);

/**
 * One-shot SHA-256 hash computation
 * @param data Input data
 * @param len Data length
 * @param digest Output digest (32 bytes)
 */
void sha256_hash(const uint8_t *data, uint32_t len, uint8_t *digest);

/**
 * Compare two SHA-256 digests
 * @param a First digest
 * @param b Second digest
 * @return true if digests are identical
 */
bool sha256_compare(const uint8_t *a, const uint8_t *b);

/**
 * Print SHA-256 digest in hex format
 * @param digest Digest to print
 */
void sha256_print(const uint8_t *digest);

#endif /* EMBEDDED_SECURITY_SHA256_H */
