/**
 * @file tls_sim.c
 * @brief TLS/DTLS Handshake Simulation
 *
 * Simulates the TLS 1.2 handshake protocol for educational purposes.
 * Demonstrates key exchange, cipher negotiation, and key derivation.
 *
 * TLS 1.2 Handshake flow:
 *   ClientHello -> ServerHello -> Certificate -> ServerKeyExchange
 *   -> ClientKeyExchange -> ChangeCipherSpec -> Finished
 *   <- ChangeCipherSpec <- Finished
 *
 * Key derivation (simplified):
 *   master_secret = PRF(pre_master_secret, "master secret", client_hello.random + server_hello.random)
 *   key_block = PRF(master_secret, "key expansion", server_hello.random + client_hello.random)
 *   client_write_key = key_block[0..15]
 *   server_write_key = key_block[16..31]
 */

#include "tls_sim.h"
#include "rng.h"
#include <string.h>
#include <stdio.h>

/* PRF label constants */
#define LABEL_MASTER_SECRET "master secret"
#define LABEL_KEY_EXPANSION "key expansion"

/* PRF expansion function (simplified TLS PRF) */
void tls_prf(const uint8_t *secret, uint32_t secret_len,
             const char *label, uint32_t label_len,
             const uint8_t *seed, uint32_t seed_len,
             uint8_t *result, uint32_t result_len) {
    /* Simplified TLS PRF using SHA-256
     * Real TLS PRF uses both SHA-256 and MD5 for compatibility */

    /* Step 1: Compute A(1) = HMAC(secret, label + seed) */
    uint32_t half_secret = (secret_len + 1) / 2;
    uint32_t a_len = label_len + seed_len;
    uint8_t *a = malloc(a_len + 1);
    uint8_t *a_prev = malloc(a_len + 16);
    uint8_t *a_half = malloc(a_len + 16);

    memcpy(a, label, label_len);
    memcpy(a + label_len, seed, seed_len);

    /* A(1) = HMAC(secret, label || seed) - simplified as SHA-256(secret || label || seed) */
    uint8_t *combined = malloc(secret_len + a_len);
    memcpy(combined, secret, secret_len);
    memcpy(combined + secret_len, a, a_len);

    sha256_hash(combined, secret_len + a_len, a_prev);
    memcpy(a_half, a_prev, a_len > 32 ? 32 : a_len);

    /* Expand: S(i) = HMAC(secret, A(i-1)) XOR HMAC(secret, A(i)) */
    uint32_t offset = 0;
    while (offset < result_len) {
        /* Compute HMAC-like operation */
        uint8_t hmac_input[128];
        uint32_t hmac_len = half_secret + 32 + label_len + seed_len;

        memset(hmac_input, 0, sizeof(hmac_input));
        memcpy(hmac_input, secret + (secret_len - half_secret), half_secret);
        memcpy(hmac_input + half_secret, a_prev, 32);
        memcpy(hmac_input + half_secret + 32, label, label_len);
        memcpy(hmac_input + half_secret + 32 + label_len, seed, seed_len);

        uint8_t hmac_result[32];
        sha256_hash(hmac_input, hmac_len, hmac_result);

        /* Combine with previous iteration */
        uint32_t copy_len = (result_len - offset) > 32 ? 32 : (result_len - offset);
        for (uint32_t j = 0; j < copy_len; j++) {
            result[offset + j] ^= hmac_result[j];
        }

        /* Update A for next iteration */
        memcpy(a_prev, a_half, 32);
        memcpy(a_half, hmac_result, 32);

        offset += 32;
    }

    free(a);
    free(a_prev);
    free(a_half);
    free(combined);
}

void tls_generate_client_hello(tls_context_t *ctx,
                                const uint16_t *supported_ciphers,
                                uint8_t num_ciphers) {
    if (!ctx || !supported_ciphers) return;

    memset(&ctx->client_hello, 0, sizeof(tls_client_hello_t));

    /* Generate random client hello random (48 bytes in real TLS, 32 here) */
    rng_context rng;
    uint8_t seed[32];
    for (int i = 0; i < 32; i++) seed[i] = (uint8_t)(i ^ 0xA5);
    rng_init(&rng, seed, 32);
    rng_generate(&rng, ctx->client_hello.random, 32);

    /* Session ID (empty for new session) */
    ctx->client_hello.session_id_len = 0;

    /* Supported cipher suites */
    ctx->client_hello.num_ciphers = num_ciphers > 8 ? 8 : num_ciphers;
    for (uint8_t i = 0; i < num_ciphers; i++) {
        ctx->client_hello.cipher_suites[i] = supported_ciphers[i];
    }
}

bool tls_process_client_hello(tls_context_t *ctx) {
    if (!ctx) return false;

    /* Select best cipher suite (first one in client's list for simplicity) */
    if (ctx->client_hello.num_ciphers > 0) {
        ctx->cipher_suite = (tls_cipher_suite_t)ctx->client_hello.cipher_suites[0];
    } else {
        ctx->cipher_suite = TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256;
    }

    /* Generate server random */
    rng_context rng;
    uint8_t seed[32];
    for (int i = 0; i < 32; i++) seed[i] = (uint8_t)(i ^ 0x5A);
    rng_init(&rng, seed, 32);
    rng_generate(&rng, ctx->server_hello.random, 32);

    /* Copy session ID */
    ctx->server_hello.session_id_len = ctx->client_hello.session_id_len;
    memcpy(ctx->server_hello.session_id, ctx->client_hello.session_id,
           ctx->server_hello.session_id_len);

    ctx->server_hello.cipher_suite = ctx->cipher_suite;
    ctx->server_hello.compression_method = 0; /* No compression */

    ctx->state = TLS_STATE_SERVER_HELLO_RECEIVED;
    return true;
}

bool tls_process_server_hello(tls_context_t *ctx) {
    if (!ctx) return false;

    /* Cipher suite is already selected in process_client_hello */
    ctx->state = TLS_STATE_CERTIFICATE_RECEIVED;
    return true;
}

void tls_compute_pre_master_secret(tls_context_t *ctx) {
    if (!ctx) return;

    /* Simulated Diffie-Hellman key exchange
     * In real TLS:
     *   - Server generates DH key pair
     *   - Client generates DH key pair
     *   - Both compute shared secret: g^(ab) mod p
     * Here we simulate with a random pre-master secret */

    rng_context rng;
    uint8_t seed[32];
    for (int i = 0; i < 32; i++) seed[i] = (uint8_t)(i ^ 0x2A);
    rng_init(&rng, seed, 32);
    rng_generate(&rng, ctx->keys.pre_master_secret, 48);

    /* Simulate public key exchange */
    for (int i = 0; i < 64; i++) {
        ctx->server_pub_key[i] = (uint8_t)(i * 7 + 0xB3);
        ctx->client_pub_key[i] = (uint8_t)(i * 13 + 0x7B);
    }
}

void tls_derive_master_secret(tls_context_t *ctx) {
    if (!ctx) return;

    /* master_secret = PRF(pre_master_secret, "master secret", random) */
    uint8_t random[64];
    memcpy(random, ctx->client_hello.random, 32);
    memcpy(random + 32, ctx->server_hello.random, 32);

    tls_prf(ctx->keys.pre_master_secret, 48,
            LABEL_MASTER_SECRET, 13,
            random, 64,
            ctx->keys.master_secret, PRF_RESULT_SIZE);
}

void tls_derive_keys(tls_context_t *ctx) {
    if (!ctx) return;

    /* key_block = PRF(master_secret, "key expansion", random) */
    uint8_t random[64];
    memcpy(random, ctx->client_hello.random, 32);
    memcpy(random + 32, ctx->server_hello.random, 32);

    uint8_t key_block[96];
    tls_prf(ctx->keys.master_secret, 48,
            LABEL_KEY_EXPANSION, 13,
            random, 64,
            key_block, 96);

    /* Extract keys */
    memcpy(ctx->keys.client_write_key, key_block, 16);
    memcpy(ctx->keys.server_write_key, key_block + 16, 16);
    memcpy(ctx->keys.client_write_iv, key_block + 32, 12);
    memcpy(ctx->keys.server_write_iv, key_block + 44, 12);
    memcpy(ctx->keys.client_mac_key, key_block + 56, 32);
    memcpy(ctx->keys.server_mac_key, key_block + 88, 32);
}

bool tls_handshake_complete(tls_context_t *ctx) {
    if (!ctx) return false;

    /* Step 1: Compute pre-master secret */
    tls_compute_pre_master_secret(ctx);

    /* Step 2: Derive master secret */
    tls_derive_master_secret(ctx);

    /* Step 3: Derive encryption keys */
    tls_derive_keys(ctx);

    /* Step 4: Initialize AES contexts with derived keys */
    aes_encrypt_init(&ctx->enc_ctx, ctx->keys.server_write_key, 16);
    aes_decrypt_init(&ctx->dec_ctx, ctx->keys.client_write_key, 16);

    ctx->state = TLS_STATE_ESTABLISHED;
    return true;
}

void tls_encrypt(tls_context_t *ctx, const uint8_t *plaintext,
                 uint8_t *ciphertext, uint32_t length) {
    if (!ctx || ctx->state != TLS_STATE_ESTABLISHED) return;

    /* Pad to block size */
    uint32_t padded_len = (length + 15) / 16 * 16;

    /* Add padding */
    for (uint32_t i = length; i < padded_len; i++) {
        ciphertext[i] = (uint8_t)(padded_len - length);
    }

    /* Encrypt with AES (ECB mode for simulation) */
    aes_encrypt_ecb(&ctx->enc_ctx, plaintext, ciphertext, padded_len);

    ctx->bytes_sent += length;
}

void tls_decrypt(tls_context_t *ctx, const uint8_t *ciphertext,
                 uint8_t *plaintext, uint32_t length) {
    if (!ctx || ctx->state != TLS_STATE_ESTABLISHED) return;

    /* Decrypt */
    aes_decrypt_ecb(&ctx->dec_ctx, ciphertext, plaintext, length);

    /* Remove padding */
    uint8_t pad_len = plaintext[length - 1];
    if (pad_len <= length) {
        for (uint32_t i = length - pad_len; i < length; i++) {
            plaintext[i] = 0;
        }
    }

    ctx->bytes_received += length;
}

const char *tls_state_str(tls_state_t state) {
    switch (state) {
        case TLS_STATE_IDLE:              return "Idle";
        case TLS_STATE_CLIENT_HELLO_SENT: return "ClientHello sent";
        case TLS_STATE_SERVER_HELLO_RECEIVED: return "ServerHello received";
        case TLS_STATE_CERTIFICATE_RECEIVED: return "Certificate received";
        case TLS_STATE_KEY_EXCH_COMPLETE: return "Key exchange complete";
        case TLS_STATE_FINISHED_SENT:     return "Finished sent";
        case TLS_STATE_ESTABLISHED:       return "Established";
        default:                          return "Unknown";
    }
}

const char *tls_cipher_suite_str(uint16_t suite) {
    switch (suite) {
        case TLS_NULL_WITH_NULL_NULL:
            return "NULL_WITH_NULL_NULL";
        case TLS_RSA_WITH_AES_128_CBC_SHA:
            return "RSA_WITH_AES_128_CBC_SHA";
        case TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA:
            return "ECDHE_RSA_WITH_AES_128_CBC_SHA";
        case TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256:
            return "ECDHE_RSA_WITH_AES_128_GCM_SHA256";
        default:
            return "Unknown";
    }
}
