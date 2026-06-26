/**
 * @file rng.h
 * @brief Random Number Generation Module
 *
 * Provides random number generation for cryptographic operations.
 * In production embedded systems, use hardware TRNG (True Random Number Generator).
 * This implementation uses a CSPRNG (Cryptographically Secure PRNG) approach.
 *
 * Security concepts:
 * - TRNG vs PRNG: True randomness vs pseudo-randomness
 * - Entropy collection: Gathering unpredictable inputs
 * - CSPRNG: Cryptographically secure PRNG
 * - Nonce generation: Unique random values for each operation
 */

#ifndef EMBEDDED_SECURITY_RNG_H
#define EMBEDDED_SECURITY_RNG_H

#include <stdint.h>
#include <stdbool.h>

#define RNG_STATE_SIZE  32
#define RNG_OUTPUT_SIZE 32
#define ENTROPY_POOL_SIZE 64

/* CSPRNG context */
typedef struct {
    uint8_t  state[RNG_STATE_SIZE];
    uint8_t  entropy_pool[ENTROPY_POOL_SIZE];
    uint32_t entropy_count;
    uint32_t counter;
    bool     initialized;
} rng_context;

/**
 * Initialize RNG context
 * @param ctx RNG context
 * @param seed Initial seed (at least 32 bytes of entropy)
 * @param seed_len Seed length
 * @return true on success
 */
bool rng_init(rng_context *ctx, const uint8_t *seed, uint32_t seed_len);

/**
 * Add entropy to the RNG pool
 * In embedded systems, this could come from:
 * - Timer jitter
 * - ADC noise
 * - Interrupt timing variance
 * @param ctx RNG context
 * @param entropy Entropy data
 * @param len Entropy length
 */
void rng_add_entropy(rng_context *ctx, const uint8_t *entropy, uint32_t len);

/**
 * Generate cryptographically secure random bytes
 * @param ctx RNG context
 * @param output Output buffer (at least 'len' bytes)
 * @param len Number of bytes to generate
 * @return true on success
 */
bool rng_generate(rng_context *ctx, uint8_t *output, uint32_t len);

/**
 * Generate a random 32-bit number
 * @param ctx RNG context
 * @param output Output 32-bit value
 * @return true on success
 */
bool rng_generate_u32(rng_context *ctx, uint32_t *output);

/**
 * Generate a random number in range [0, max)
 * @param ctx RNG context
 * @param max Upper bound (exclusive)
 * @param output Output value
 * @return true on success
 */
bool rng_generate_range(rng_context *ctx, uint32_t max, uint32_t *output);

/**
 * Generate a nonce (number used once)
 * Nonces must be unique for each cryptographic operation
 * @param ctx RNG context
 * @param nonce Output nonce (at least 16 bytes)
 * @param nonce_len Nonce length
 * @return true on success
 */
bool rng_generate_nonce(rng_context *ctx, uint8_t *nonce, uint32_t nonce_len);

/**
 * Re-seed the RNG with fresh entropy
 * Should be called periodically in long-running systems
 * @param ctx RNG context
 * @param entropy Fresh entropy data
 * @param len Entropy length
 * @return true on success
 */
bool rng_reseed(rng_context *ctx, const uint8_t *entropy, uint32_t len);

/**
 * Check if RNG is properly initialized
 * @param ctx RNG context
 * @return true if initialized
 */
bool rng_is_initialized(const rng_context *ctx);

#endif /* EMBEDDED_SECURITY_RNG_H */
