/**
 * @file rng.c
 * @brief Random Number Generation Implementation
 *
 * Provides a CSPRNG (Cryptographically Secure Pseudo-Random Number Generator)
 * for embedded systems. In production, combine with hardware TRNG sources:
 *   - ADC noise sampling
 *   - Interrupt timing jitter
 *   - Cache timing variance
 *   - Hardware RNG peripheral
 *
 * This implementation uses a counter-based CSPRNG pattern:
 *   state = SHA-256(state || counter || entropy)
 *   output = SHA-256(state || counter || entropy + 1)
 */

#include "rng.h"
#include "sha256.h"
#include <string.h>

bool rng_init(rng_context *ctx, const uint8_t *seed, uint32_t seed_len) {
    if (!ctx || !seed) return false;
    if (seed_len < 16) return false;

    memset(ctx, 0, sizeof(rng_context));

    /* Initialize state with seed */
    memcpy(ctx->state, seed, seed_len < RNG_STATE_SIZE ? seed_len : RNG_STATE_SIZE);

    /* Initialize entropy pool */
    memcpy(ctx->entropy_pool, seed, seed_len < ENTROPY_POOL_SIZE ? seed_len : ENTROPY_POOL_SIZE);
    ctx->entropy_count = seed_len < ENTROPY_POOL_SIZE ? seed_len : ENTROPY_POOL_SIZE;

    ctx->counter = 0;
    ctx->initialized = true;

    return true;
}

void rng_add_entropy(rng_context *ctx, const uint8_t *entropy, uint32_t len) {
    if (!ctx || !entropy) return;

    /* Mix entropy into pool */
    for (uint32_t i = 0; i < len && ctx->entropy_count < ENTROPY_POOL_SIZE; i++) {
        ctx->entropy_pool[ctx->entropy_count] = entropy[i];
        ctx->entropy_count++;
    }

    /* Re-seed state with entropy pool */
    if (ctx->entropy_count >= RNG_STATE_SIZE) {
        uint8_t new_state[RNG_STATE_SIZE];
        sha256_hash(ctx->entropy_pool, ctx->entropy_count, new_state);
        memcpy(ctx->state, new_state, RNG_STATE_SIZE);
        ctx->entropy_count = 0;
    }
}

bool rng_generate(rng_context *ctx, uint8_t *output, uint32_t len) {
    if (!ctx || !output || !ctx->initialized) return false;

    uint32_t offset = 0;

    while (offset < len) {
        /* Mix counter and state */
        uint8_t input[64];
        uint32_t input_len = 0;

        /* Add counter */
        input[input_len++] = (ctx->counter >> 24) & 0xFF;
        input[input_len++] = (ctx->counter >> 16) & 0xFF;
        input[input_len++] = (ctx->counter >> 8) & 0xFF;
        input[input_len++] = ctx->counter & 0xFF;
        ctx->counter++;

        /* Add state */
        uint32_t state_copy = (RNG_STATE_SIZE < 28) ? RNG_STATE_SIZE : 28;
        if (input_len + state_copy > 64) state_copy = 64 - input_len;
        memcpy(input + input_len, ctx->state, state_copy);
        input_len += state_copy;

        /* Add entropy pool */
        uint32_t entropy_copy = ctx->entropy_count;
        if (input_len + entropy_copy > 64) entropy_copy = 64 - input_len;
        if (entropy_copy > 0) {
            memcpy(input + input_len, ctx->entropy_pool, entropy_copy);
            input_len += entropy_copy;
        }

        /* Hash to get random output */
        uint8_t hash[32];
        sha256_hash(input, input_len, hash);

        /* Copy to output */
        uint32_t copy_len = (len - offset) > 32 ? 32 : (len - offset);
        memcpy(output + offset, hash, copy_len);
        offset += copy_len;

        /* Update state with hash (for next iteration) */
        memcpy(ctx->state, hash, 32);
    }

    return true;
}

bool rng_generate_u32(rng_context *ctx, uint32_t *output) {
    uint8_t buf[4];
    if (!rng_generate(ctx, buf, 4)) return false;

    *output = ((uint32_t)buf[0] << 24) |
              ((uint32_t)buf[1] << 16) |
              ((uint32_t)buf[2] << 8) |
              ((uint32_t)buf[3]);
    return true;
}

bool rng_generate_range(rng_context *ctx, uint32_t max, uint32_t *output) {
    if (max == 0) return false;

    uint32_t val;
    if (!rng_generate_u32(ctx, &val)) return false;

    *output = val % max;
    return true;
}

bool rng_generate_nonce(rng_context *ctx, uint8_t *nonce, uint32_t nonce_len) {
    return rng_generate(ctx, nonce, nonce_len);
}

bool rng_reseed(rng_context *ctx, const uint8_t *entropy, uint32_t len) {
    if (!ctx || !entropy) return false;

    /* Mix new entropy */
    rng_add_entropy(ctx, entropy, len);

    /* Force re-seed */
    sha256_hash(ctx->entropy_pool, ctx->entropy_count, ctx->state);
    ctx->counter = 0;

    return true;
}

bool rng_is_initialized(const rng_context *ctx) {
    return ctx && ctx->initialized;
}
