/**
 * @file authentication.h
 * @brief Authentication Module - Challenge-Response and HMAC
 *
 * Implements device and message authentication mechanisms.
 *
 * Security concepts:
 * - Challenge-response: Prove identity without sharing secrets
 * - HMAC: Message authentication code for integrity and authenticity
 * - Nonce: Prevent replay attacks
 */

#ifndef EMBEDDED_SECURITY_AUTHENTICATION_H
#define EMBEDDED_SECURITY_AUTHENTICATION_H

#include <stdint.h>
#include <stdbool.h>
#include "sha256.h"

#define CHALLENGE_SIZE    32
#define RESPONSE_SIZE     32
#define HMAC_KEY_SIZE     32
#define HMAC_TAG_SIZE     32
#define NONCE_SIZE        16

/* Challenge-response authentication state */
typedef struct {
    uint8_t  challenge[CHALLENGE_SIZE];
    uint8_t  response[RESPONSE_SIZE];
    uint32_t timestamp;
    uint8_t  nonce[NONCE_SIZE];
    bool     challenge_pending;
    uint32_t session_id;
} auth_session_t;

/* HMAC context for incremental computation */
typedef struct {
    uint8_t  ipad[64];     /* Inner padding */
    uint8_t  opad[64];     /* Outer padding */
    uint8_t  key_hash[32]; /* Hashed key (if key > block size) */
    uint32_t key_len;
    sha256_context sha_ctx;
} hmac_context_t;

/**
 * Generate a random challenge for authentication
 * In production, use hardware RNG or TRNG
 * @param challenge Output challenge buffer (32 bytes)
 */
void generate_challenge(uint8_t *challenge);

/**
 * Compute HMAC-SHA256 response to challenge
 * Uses shared secret key to sign the challenge
 * @param key     Shared secret key
 * @param key_len Key length
 * @param challenge Input challenge
 * @param response Output HMAC response (32 bytes)
 */
void compute_hmac_response(const uint8_t *key, uint32_t key_len,
                           const uint8_t *challenge, uint8_t *response);

/**
 * Verify HMAC-SHA256 response
 * @param key     Shared secret key
 * @param key_len Key length
 * @param data    Data to verify
 * @param data_len Data length
 * @param expected Expected HMAC tag
 * @return true if HMAC is valid
 */
bool verify_hmac(const uint8_t *key, uint32_t key_len,
                 const uint8_t *data, uint32_t data_len,
                 const uint8_t *expected);

/**
 * Initialize HMAC context for incremental computation
 * @param ctx HMAC context
 * @param key HMAC key
 * @param key_len Key length
 */
void hmac_init(hmac_context_t *ctx, const uint8_t *key, uint32_t key_len);

/**
 * Update HMAC with data (can be called multiple times)
 * @param ctx HMAC context
 * @param data Data to include
 * @param len Data length
 */
void hmac_update(hmac_context_t *ctx, const uint8_t *data, uint32_t len);

/**
 * Finalize HMAC computation and get tag
 * @param ctx HMAC context
 * @param tag Output HMAC tag (32 bytes)
 */
void hmac_final(hmac_context_t *ctx, uint8_t *tag);

/**
 * Start authentication session with challenge
 * @param session Session context
 * @param secret Shared secret key
 * @param secret_len Secret length
 */
void auth_start_session(auth_session_t *session,
                        const uint8_t *secret, uint32_t secret_len);

/**
 * Compute response to current challenge
 * @param session Session context
 * @param secret Shared secret key
 * @param secret_len Secret length
 */
void auth_compute_response(auth_session_t *session,
                           const uint8_t *secret, uint32_t secret_len);

/**
 * Verify a received response
 * @param session Session context
 * @param secret Shared secret key
 * @param secret_len Secret length
 * @param received_response Response to verify
 * @return true if response matches
 */
bool auth_verify_response(const auth_session_t *session,
                          const uint8_t *secret, uint32_t secret_len,
                          const uint8_t *received_response);

/**
 * Check if session has expired (replay protection)
 * @param session Session context
 * @param max_age_ms Maximum session age in milliseconds
 * @return true if session is still valid
 */
bool auth_is_session_valid(const auth_session_t *session, uint32_t max_age_ms);

/**
 * Reset session (invalidate current challenge)
 * @param session Session context
 */
void auth_reset_session(auth_session_t *session);

#endif /* EMBEDDED_SECURITY_AUTHENTICATION_H */
