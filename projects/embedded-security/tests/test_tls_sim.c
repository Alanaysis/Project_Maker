/**
 * @file test_tls_sim.c
 * @brief Unit tests for TLS simulation module
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "tls_sim.h"
#include "aes.h"

static int tests_run = 0;
static int tests_passed = 0;

#define TEST(name) do { printf("  TEST: %s... ", #name); tests_run++; } while(0)
#define PASS() do { printf("[PASS]\n"); tests_passed++; } while(0)
#define FAIL(msg) do { printf("[FAIL]: %s\n", msg); } while(0)
#define ASSERT(cond, msg) do { if (!(cond)) { FAIL(msg); return; } } while(0)

void test_client_hello_generation(void) {
    TEST(client_hello_generation);
    tls_context_t ctx;
    memset(&ctx, 0, sizeof(ctx));

    uint16_t ciphers[] = {
        TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
        TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA
    };

    tls_generate_client_hello(&ctx, ciphers, 2);

    ASSERT(ctx.client_hello.num_ciphers > 0,
           "Client hello should have cipher suites");
    PASS();
}

void test_server_hello_processing(void) {
    TEST(server_hello_processing);
    tls_context_t ctx;
    memset(&ctx, 0, sizeof(ctx));

    uint16_t ciphers[] = {TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256};
    tls_generate_client_hello(&ctx, ciphers, 1);

    ASSERT(tls_process_client_hello(&ctx),
           "Server hello processing should succeed");

    ASSERT(ctx.state == TLS_STATE_SERVER_HELLO_RECEIVED,
           "State should be SERVER_HELLO_RECEIVED");

    ASSERT(ctx.server_hello.cipher_suite > 0,
           "Selected cipher suite should be non-zero");
    PASS();
}

void test_handshake_completion(void) {
    TEST(handshake_completion);
    tls_context_t ctx;
    memset(&ctx, 0, sizeof(ctx));

    uint16_t ciphers[] = {TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256};
    tls_generate_client_hello(&ctx, ciphers, 1);
    tls_process_client_hello(&ctx);
    tls_process_server_hello(&ctx);

    ASSERT(tls_handshake_complete(&ctx),
           "Handshake should complete");

    ASSERT(ctx.state == TLS_STATE_ESTABLISHED,
           "State should be ESTABLISHED after handshake");

    /* Verify keys are derived */
    ASSERT(ctx.keys.master_secret[0] != 0 || ctx.keys.master_secret[1] != 0,
           "Master secret should be derived");
    PASS();
}

void test_encryption_decryption(void) {
    TEST(encryption_decryption);
    tls_context_t ctx;
    memset(&ctx, 0, sizeof(ctx));

    uint16_t ciphers[] = {TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256};
    tls_generate_client_hello(&ctx, ciphers, 1);
    tls_process_client_hello(&ctx);
    tls_process_server_hello(&ctx);
    tls_handshake_complete(&ctx);

    /* Encrypt */
    const char *plaintext = "TLS encrypted message";
    uint8_t ciphertext[128];
    tls_encrypt(&ctx, (const uint8_t *)plaintext, ciphertext, strlen(plaintext));

    /* Decrypt */
    uint8_t decrypted[128];
    tls_decrypt(&ctx, ciphertext, decrypted, strlen(plaintext));
    decrypted[strlen(plaintext)] = '\0';

    ASSERT(strcmp((char *)decrypted, plaintext) == 0,
           "Decrypted message should match original");
    PASS();
}

void test_prf_deterministic(void) {
    TEST(prf_deterministic);
    uint8_t secret[64] = {0x01};
    uint8_t seed[64] = {0x02};
    uint8_t result1[48], result2[48];

    tls_prf(secret, 64, "test_label", 10, seed, 64, result1, 48);
    tls_prf(secret, 64, "test_label", 10, seed, 64, result2, 48);

    ASSERT(memcmp(result1, result2, 48) == 0,
           "PRF should be deterministic");
    PASS();
}

void test_prf_different_labels(void) {
    TEST(prf_different_labels);
    uint8_t secret[64] = {0x03};
    uint8_t seed[64] = {0x04};
    uint8_t result1[48], result2[48];

    tls_prf(secret, 64, "label_a", 7, seed, 64, result1, 48);
    tls_prf(secret, 64, "label_b", 7, seed, 64, result2, 48);

    ASSERT(memcmp(result1, result2, 48) != 0,
           "Different labels should produce different PRF output");
    PASS();
}

void test_cipher_suite_strings(void) {
    TEST(cipher_suite_strings);
    const char *s1 = tls_cipher_suite_str(TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256);
    const char *s2 = tls_cipher_suite_str(TLS_RSA_WITH_AES_128_CBC_SHA);
    const char *s3 = tls_cipher_suite_str(0xFFFF);

    ASSERT(s1 != NULL, "Cipher suite string should not be NULL");
    ASSERT(s2 != NULL, "Cipher suite string should not be NULL");
    ASSERT(s3 != NULL, "Unknown cipher suite string should not be NULL");
    PASS();
}

int main(void) {
    printf("=== TLS Simulation Unit Tests ===\n\n");

    test_client_hello_generation();
    test_server_hello_processing();
    test_handshake_completion();
    test_encryption_decryption();
    test_prf_deterministic();
    test_prf_different_labels();
    test_cipher_suite_strings();

    printf("\n--- Results ---\n");
    printf("  Passed: %d / %d\n", tests_passed, tests_run);

    if (tests_passed == tests_run) {
        printf("  [ALL TESTS PASSED]\n");
        return 0;
    } else {
        printf("  [SOME TESTS FAILED]\n");
        return 1;
    }
}
