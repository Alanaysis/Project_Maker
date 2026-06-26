/**
 * test_signature.c - Signature Verification Unit Tests
 *
 * Tests for the simulated RSA/ECDSA signature module.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ota_firmware.h"

static int tests_run = 0;
static int tests_passed = 0;

#define TEST(name) do { \
    printf("  TEST: %s ... ", #name); \
    tests_run++; \
    if (test_##name()) { \
        tests_passed++; \
        printf("PASS\n"); \
    } else { \
        printf("FAIL\n"); \
    } \
} while(0)

static const uint8_t private_key[32] = {
    0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE,
    0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,
    0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
    0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00
};

/* Generate public key from private key */
static void gen_public_key(uint8_t *pub, const uint8_t *priv) {
    for (int i = 0; i < 256; i++) {
        pub[i] = (uint8_t)(priv[i % 32] * 37 + i * 23 + 1);
    }
}

/* Test signature creation */
static int test_sig_sign(void) {
    uint8_t data[] = "sign me";
    uint8_t sig[OTA_SIGNATURE_SIZE];
    return ota_sig_sign(data, 7, private_key, sig);
}

/* Test signature verification with correct key */
static int test_sig_verify_valid(void) {
    uint8_t data[] = "verify me";
    uint8_t sig[OTA_SIGNATURE_SIZE];
    ota_sig_sign(data, 9, private_key, sig);

    uint8_t pub_key[256];
    gen_public_key(pub_key, private_key);

    OTA_SignatureVerifier verifier;
    ota_sig_init(&verifier, pub_key, 256);
    return ota_sig_verify(&verifier, data, 9, sig);
}

/* Test signature verification with wrong key */
static int test_sig_verify_invalid(void) {
    uint8_t data[] = "verify me";
    uint8_t sig[OTA_SIGNATURE_SIZE];
    ota_sig_sign(data, 9, private_key, sig);

    /* Use different "public" key */
    uint8_t wrong_pub[256];
    for (int i = 0; i < 256; i++) wrong_pub[i] = (uint8_t)(i + 50);

    OTA_SignatureVerifier verifier;
    ota_sig_init(&verifier, wrong_pub, 256);
    /* Should fail with wrong key */
    return !ota_sig_verify(&verifier, data, 9, sig);
}

/* Test signature tampering detection */
static int test_sig_tamper(void) {
    uint8_t data[] = "tamper test";
    uint8_t sig[OTA_SIGNATURE_SIZE];
    ota_sig_sign(data, 11, private_key, sig);

    /* Tamper with signature */
    sig[0] ^= 0xFF;

    uint8_t pub_key[256];
    gen_public_key(pub_key, private_key);

    OTA_SignatureVerifier verifier;
    ota_sig_init(&verifier, pub_key, 256);
    return !ota_sig_verify(&verifier, data, 11, sig);
}

/* Test signature of different data */
static int test_sig_different_data(void) {
    uint8_t data1[] = "hello";
    uint8_t data2[] = "world";
    uint8_t sig1[OTA_SIGNATURE_SIZE], sig2[OTA_SIGNATURE_SIZE];

    ota_sig_sign(data1, 5, private_key, sig1);
    ota_sig_sign(data2, 5, private_key, sig2);

    /* Signatures should be different */
    return memcmp(sig1, sig2, OTA_SIGNATURE_SIZE) != 0;
}

/* Test same data produces same signature */
static int test_sig_deterministic(void) {
    uint8_t data[] = "deterministic";
    uint8_t sig1[OTA_SIGNATURE_SIZE], sig2[OTA_SIGNATURE_SIZE];

    ota_sig_sign(data, 13, private_key, sig1);
    ota_sig_sign(data, 13, private_key, sig2);

    return memcmp(sig1, sig2, OTA_SIGNATURE_SIZE) == 0;
}

/* Test null handling */
static int test_sig_null(void) {
    uint8_t sig[OTA_SIGNATURE_SIZE];
    return !ota_sig_sign(NULL, 10, private_key, sig);
}

int main(void) {
    printf("============================================================\n");
    printf("  Signature Verification Unit Tests\n");
    printf("============================================================\n\n");

    TEST(sig_sign);
    TEST(sig_verify_valid);
    TEST(sig_verify_invalid);
    TEST(sig_tamper);
    TEST(sig_different_data);
    TEST(sig_deterministic);
    TEST(sig_null);

    printf("\n============================================================\n");
    printf("  Results: %d/%d tests passed\n", tests_passed, tests_run);
    printf("============================================================\n");

    return (tests_passed == tests_run) ? 0 : 1;
}
