/**
 * @file tls_sim.h
 * @brief TLS/DTLS Handshake Simulation Module
 *
 * Simulates the TLS 1.2 handshake protocol for educational purposes.
 * Demonstrates the key exchange and cipher suite negotiation process.
 *
 * Security concepts:
 * - TLS handshake: Establishing secure communication channel
 * - Key exchange: Diffie-Hellman style key agreement
 * - Cipher suite negotiation: Agreeing on encryption algorithms
 * - Certificate verification: Identity authentication
 */

#ifndef EMBEDDED_SECURITY_TLS_SIM_H
#define EMBEDDED_SECURITY_TLS_SIM_H

#include <stdint.h>
#include <stdbool.h>
#include "aes.h"
#include "sha256.h"

/* TLS protocol version (simulated TLS 1.2) */
#define TLS_VERSION_MAJOR  3
#define TLS_VERSION_MINOR  3   /* TLS 1.2 */

/* TLS record types */
typedef enum {
    TLS_CHANGE_CIPHER_SPEC = 20,
    TLS_ALERT              = 21,
    TLS_HANDSHAKE          = 22,
    TLS_APPLICATION_DATA   = 23
} tls_record_type_t;

/* TLS handshake message types */
typedef enum {
    TLS_HELLO_REQUEST     = 0,
    TLS_CLIENT_HELLO      = 1,
    TLS_SERVER_HELLO      = 2,
    TLS_CERTIFICATE       = 11,
    TLS_SERVER_KEY_EXCH   = 12,
    TLS_CERT_REQ          = 13,
    TLS_SERVER_HELLO_DONE = 14,
    TLS_CLIENT_KEY_EXCH   = 16,
    TLS_CERT_VERIFY       = 15,
    TLS_FINISHED          = 20
} tls_handshake_type_t;

/* Cipher suites (simplified) */
typedef enum {
    TLS_NULL_WITH_NULL_NULL     = 0x00,
    TLS_RSA_WITH_AES_128_CBC_SHA = 0x2F,
    TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA = 0xC013,
    TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 = 0xC02F
} tls_cipher_suite_t;

/* TLS handshake state machine */
typedef enum {
    TLS_STATE_IDLE = 0,
    TLS_STATE_CLIENT_HELLO_SENT,
    TLS_STATE_SERVER_HELLO_RECEIVED,
    TLS_STATE_CERTIFICATE_RECEIVED,
    TLS_STATE_KEY_EXCH_COMPLETE,
    TLS_STATE_FINISHED_SENT,
    TLS_STATE_ESTABLISHED
} tls_state_t;

/* PRF (Pseudo-Random Function) for key derivation */
#define PRF_SECRET_SIZE  64
#define PRF_LABEL_SIZE   32
#define PRF_RESULT_SIZE  48   /* master secret is 48 bytes */

/* Master secret and keys */
typedef struct {
    uint8_t  pre_master_secret[48];
    uint8_t  master_secret[48];
    uint8_t  client_write_key[16];
    uint8_t  server_write_key[16];
    uint8_t  client_write_iv[12];
    uint8_t  server_write_iv[12];
    uint8_t  client_mac_key[32];
    uint8_t  server_mac_key[32];
} tls_keys_t;

/* Client hello message */
typedef struct {
    uint8_t  random[32];
    uint32_t session_id_len;
    uint8_t  session_id[32];
    uint16_t cipher_suites[8];
    uint8_t  num_ciphers;
} tls_client_hello_t;

/* Server hello message */
typedef struct {
    uint8_t  random[32];
    uint32_t session_id_len;
    uint8_t  session_id[32];
    uint16_t cipher_suite;
    uint8_t  compression_method;
} tls_server_hello_t;

/* TLS connection context */
typedef struct {
    tls_state_t state;
    tls_cipher_suite_t cipher_suite;
    tls_client_hello_t client_hello;
    tls_server_hello_t server_hello;
    tls_keys_t keys;
    aes_context_t enc_ctx;
    aes_context_t dec_ctx;
    uint8_t  server_pub_key[64];   /* Simulated public key */
    uint8_t  client_pub_key[64];   /* Simulated public key */
    uint32_t bytes_sent;
    uint32_t bytes_received;
} tls_context_t;

/**
 * Generate a client hello message
 * @param ctx TLS context
 * @param supported_ciphers Array of supported cipher suites
 * @param num_ciphers Number of cipher suites
 */
void tls_generate_client_hello(tls_context_t *ctx,
                                const uint16_t *supported_ciphers,
                                uint8_t num_ciphers);

/**
 * Process client hello and generate server hello
 * @param ctx TLS context
 * @return true if server hello generated successfully
 */
bool tls_process_client_hello(tls_context_t *ctx);

/**
 * Process server hello and extract cipher suite
 * @param ctx TLS context
 * @return true if cipher suite is acceptable
 */
bool tls_process_server_hello(tls_context_t *ctx);

/**
 * Compute TLS PRF (Pseudo-Random Function) for key derivation
 * Simplified version of TLS PRF using SHA-256
 * @param secret  Secret input
 * @param secret_len Secret length
 * @param label   Label (e.g., "master secret")
 * @param label_len Label length
 * @param seed    Seed for PRF
 * @param seed_len Seed length
 * @param result  Output PRF result
 * @param result_len Output length
 */
void tls_prf(const uint8_t *secret, uint32_t secret_len,
             const char *label, uint32_t label_len,
             const uint8_t *seed, uint32_t seed_len,
             uint8_t *result, uint32_t result_len);

/**
 * Compute pre-master secret (simulated DH key exchange)
 * @param ctx TLS context
 */
void tls_compute_pre_master_secret(tls_context_t *ctx);

/**
 * Derive master secret from pre-master secret
 * @param ctx TLS context
 */
void tls_derive_master_secret(tls_context_t *ctx);

/**
 * Derive encryption keys from master secret
 * @param ctx TLS context
 */
void tls_derive_keys(tls_context_t *ctx);

/**
 * Complete the handshake and establish connection
 * @param ctx TLS context
 * @return true if handshake completed successfully
 */
bool tls_handshake_complete(tls_context_t *ctx);

/**
 * Encrypt application data using derived keys
 * @param ctx TLS context
 * @param plaintext Input data
 * @param ciphertext Output encrypted data
 * @param length Data length
 */
void tls_encrypt(tls_context_t *ctx, const uint8_t *plaintext,
                 uint8_t *ciphertext, uint32_t length);

/**
 * Decrypt application data using derived keys
 * @param ctx TLS context
 * @param ciphertext Input encrypted data
 * @param plaintext Output decrypted data
 * @param length Data length
 */
void tls_decrypt(tls_context_t *ctx, const uint8_t *ciphertext,
                 uint8_t *plaintext, uint32_t length);

/**
 * Get current TLS state as string
 * @param state TLS state
 * @return String description
 */
const char *tls_state_str(tls_state_t state);

/**
 * Get cipher suite name as string
 * @param suite Cipher suite
 * @return String description
 */
const char *tls_cipher_suite_str(uint16_t suite);

#endif /* EMBEDDED_SECURITY_TLS_SIM_H */
