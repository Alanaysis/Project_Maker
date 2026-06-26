/**
 * @file test_authentication.c
 * @brief Unit tests for authentication module
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "authentication.h"
#include "sha256.h"

static int tests_run = 0;
static int tests_passed = 0;

#define TEST(name) do { printf("  TEST: %s... ", #name); tests_run++; } while(0)
#define PASS() do { printf("[PASS]\n"); tests_passed++; } while(0)
#define FAIL(msg) do { printf("[FAIL]: %s\n", msg); } while(0)
#define ASSERT(cond, msg) do { if (!(cond)) { FAIL(msg); return; } } while(0)

void test_hmac_computation(void) {
    TEST(hmac_computation);
    uint8_t key[32] = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                        0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10,
                        0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
                        0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20};
    uint8_t data[] = "test message for HMAC";
    uint8_t tag[32];

    hmac_context ctx;
    hmac_init(&ctx, key, 32);
    hmac_update(&ctx, data, sizeof(data) - 1);
    hmac_final(&ctx, tag);

    /* Verify tag is deterministic */
    hmac_context ctx2;
    hmac_init(&ctx2, key, 32);
    hmac_update(&ctx2, data, sizeof(data) - 1);
    uint8_t tag2[32];
    hmac_final(&ctx2, tag2);

    ASSERT(sha256_compare(tag, tag2), "HMAC should be deterministic");
    PASS();
}

void test_hmac_verification(void) {
    TEST(hmac_verification);
    uint8_t key[32] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00, 0x11,
                        0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99,
                        0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
                        0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00};
    uint8_t data[] = "authenticated message";

    /* Compute valid HMAC */
    uint8_t valid_tag[32];
    hmac_context ctx;
    hmac_init(&ctx, key, 32);
    hmac_update(&ctx, data, sizeof(data) - 1);
    hmac_final(&ctx, valid_tag);

    /* Verify valid HMAC passes */
    ASSERT(verify_hmac(key, 32, data, sizeof(data) - 1, valid_tag),
           "Valid HMAC should verify");

    /* Tampered data should fail */
    uint8_t tampered_data[] = "authenticated messagX";
    ASSERT(!verify_hmac(key, 32, tampered_data, sizeof(tampered_data) - 1, valid_tag),
           "Tampered data HMAC should fail");
    PASS();
}

void test_challenge_response(void) {
    TEST(challenge_response);
    uint8_t secret[32] = {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,
                           0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
                           0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00,
                           0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF};

    auth_session_t session;
    auth_start_session(&session, secret, 32);
    auth_compute_response(&session, secret, 32);

    /* Response should be generated */
    ASSERT(!session.challenge_pending, "Response should be computed");

    /* Verify response matches */
    ASSERT(auth_verify_response(&session, secret, 32, session.response),
           "Correct response should verify");

    /* Wrong key should fail */
    uint8_t wrong_secret[32];
    for (int i = 0; i < 32; i++) {
        wrong_secret[i] = (uint8_t)(secret[i] ^ 0xFF);
    }
    ASSERT(!auth_verify_response(&session, wrong_secret, 32, session.response),
           "Wrong key response should not verify");
    PASS();
}

void test_challenge_uniqueness(void) {
    TEST(challenge_uniqueness);
    uint8_t secret[32] = {0xAB};
    auth_session_t s1, s2;

    auth_start_session(&s1, secret, 32);
    auth_start_session(&s2, secret, 32);

    /* Challenges should be different */
    ASSERT(memcmp(s1.challenge, s2.challenge, 32) != 0,
           "Different challenges should be generated");
    PASS();
}

void test_session_reset(void) {
    TEST(session_reset);
    uint8_t secret[32] = {0xCD};
    auth_session_t session;

    auth_start_session(&session, secret, 32);
    auth_compute_response(&session, secret, 32);

    /* Reset and verify pending */
    auth_reset_session(&session);
    ASSERT(session.challenge_pending, "Session should be pending after reset");
    PASS();
}

int main(void) {
    printf("=== Authentication Unit Tests ===\n\n");

    test_hmac_computation();
    test_hmac_verification();
    test_challenge_response();
    test_challenge_uniqueness();
    test_session_reset();

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
