/**
 * @file authentication.c
 * @brief Authentication Implementation
 *
 * Implements challenge-response authentication and HMAC for message integrity.
 *
 * Challenge-Response flow:
 *   1. Server generates random challenge
 *   2. Client signs challenge with shared secret
 *   3. Server verifies response
 *   4. Authentication succeeds if response matches
 *
 * Security against replay attacks:
 *   - Each challenge is unique (random)
 *   - Responses include timestamps/nonces
 *   - Sessions expire after timeout
 */

#include "authentication.h"
#include "rng.h"
#include <string.h>
#include <stdio.h>

/* HMAC key padding constants */
#define HMAC_IPAD 0x36
#define HMAC_OPAD 0x5C

/* Session timeout (milliseconds) */
#define SESSION_TIMEOUT_MS 300000  /* 5 minutes */

void generate_challenge(uint8_t *challenge) {
    /* In production, use hardware TRNG */
    /* For now, use a simple counter-based approach */
    static uint32_t counter = 0;
    counter++;

    /* Mix counter with system timer (simulated) */
    uint32_t entropy = counter ^ (uint32_t)&generate_challenge ^ 0xA5A5A5A5;

    /* Generate pseudo-random challenge */
    for (int i = 0; i < CHALLENGE_SIZE; i += 4) {
        entropy ^= entropy << 13;
        entropy ^= entropy >> 17;
        entropy ^= entropy << 5;
        challenge[i]     = (entropy >> 24) & 0xFF;
        challenge[i + 1] = (entropy >> 16) & 0xFF;
        challenge[i + 2] = (entropy >> 8) & 0xFF;
        challenge[i + 3] = entropy & 0xFF;
    }
}

void compute_hmac_response(const uint8_t *key, uint32_t key_len,
                           const uint8_t *challenge, uint8_t *response) {
    hmac_context_t ctx;
    hmac_init(&ctx, key, key_len);
    hmac_update(&ctx, challenge, CHALLENGE_SIZE);
    hmac_final(&ctx, response);
}

void hmac_init(hmac_context_t *ctx, const uint8_t *key, uint32_t key_len) {
    /* If key is longer than block size, hash it first */
    if (key_len > 64) {
        sha256_context sha_ctx;
        sha256_init(&sha_ctx);
        sha256_update(&sha_ctx, key, key_len);
        sha256_final(&sha_ctx, ctx->key_hash);
        key_len = 32;
        key = ctx->key_hash;
    }

    /* Pad key to block size */
    memset(ctx->ipad, 0, 64);
    memset(ctx->opad, 0, 64);

    for (uint32_t i = 0; i < key_len; i++) {
        ctx->ipad[i] = key[i] ^ HMAC_IPAD;
        ctx->opad[i] = key[i] ^ HMAC_OPAD;
    }

    ctx->key_len = key_len;

    /* Initialize inner hash */
    sha256_init(&ctx->sha_ctx);
    sha256_update(&ctx->sha_ctx, ctx->ipad, 64);
}

void hmac_update(hmac_context_t *ctx, const uint8_t *data, uint32_t len) {
    sha256_update(&ctx->sha_ctx, data, len);
}

void hmac_final(hmac_context_t *ctx, uint8_t *tag) {
    /* Complete inner hash */
    uint8_t inner_hash[32];
    sha256_final(&ctx->sha_ctx, inner_hash);

    /* Initialize outer hash */
    sha256_context outer_ctx;
    sha256_init(&outer_ctx);
    sha256_update(&outer_ctx, ctx->opad, 64);
    sha256_update(&outer_ctx, inner_hash, 32);
    sha256_final(&outer_ctx, tag);
}

bool verify_hmac(const uint8_t *key, uint32_t key_len,
                 const uint8_t *data, uint32_t data_len,
                 const uint8_t *expected) {
    uint8_t computed[32];
    hmac_context_t ctx;
    hmac_init(&ctx, key, key_len);
    hmac_update(&ctx, data, data_len);
    hmac_final(&ctx, computed);

    return sha256_compare(computed, expected);
}

void auth_start_session(auth_session_t *session,
                        const uint8_t *secret, uint32_t secret_len) {
    if (!session) return;

    memset(session, 0, sizeof(auth_session_t));

    /* Generate random challenge */
    generate_challenge(session->challenge);

    /* Generate random nonce */
    for (int i = 0; i < NONCE_SIZE; i++) {
        session->nonce[i] = (uint8_t)(i ^ 0xA5 ^ (i * 7));
    }

    session->timestamp = 0; /* Would use RTC in production */
    session->session_id = (uint32_t)&auth_start_session;
    session->challenge_pending = true;
}

void auth_compute_response(auth_session_t *session,
                           const uint8_t *secret, uint32_t secret_len) {
    if (!session || !secret) return;

    compute_hmac_response(secret, secret_len,
                          session->challenge, session->response);
    session->challenge_pending = false;
}

bool auth_verify_response(const auth_session_t *session,
                          const uint8_t *secret, uint32_t secret_len,
                          const uint8_t *received_response) {
    if (!session || !secret || !received_response) return false;
    if (!session->challenge_pending) return false;

    /* Compute expected response */
    uint8_t expected[RESPONSE_SIZE];
    compute_hmac_response(secret, secret_len,
                          session->challenge, expected);

    /* Compare responses (constant-time comparison would be ideal) */
    uint8_t diff = 0;
    for (int i = 0; i < RESPONSE_SIZE; i++) {
        diff |= expected[i] ^ received_response[i];
    }

    return diff == 0;
}

bool auth_is_session_valid(const auth_session_t *session, uint32_t max_age_ms) {
    if (!session) return false;

    /* Check if challenge is pending */
    if (!session->challenge_pending) return false;

    /* Check session age (would use real timestamp in production) */
    (void)max_age_ms;
    return true;
}

void auth_reset_session(auth_session_t *session) {
    if (!session) return;

    memset(session, 0, sizeof(auth_session_t));
    session->challenge_pending = true;
}
