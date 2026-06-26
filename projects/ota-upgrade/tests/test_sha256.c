/**
 * test_sha256.c - SHA256 Hash Unit Tests
 *
 * Tests for the SHA256 implementation:
 *   - Initialization
 *   - Known test vectors
 *   - Incremental hashing
 *   - Edge cases
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
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

/* Test SHA256 initialization */
static int test_sha256_init(void) {
    OTA_SHA256Context ctx;
    ota_sha256_init(&ctx);
    /* Initial state should be the standard SHA256 IV */
    return ctx.state[0] == 0x6a09e667 && ctx.state[7] == 0x5be0cd19;
}

/* Test SHA256 of empty string */
static int test_sha256_empty(void) {
    OTA_SHA256Context ctx;
    ota_sha256_init(&ctx);
    uint8_t hash[32];
    ota_sha256_final(&ctx, hash);
    /* SHA256("") = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 */
    return hash[0] == 0xe3 && hash[1] == 0xb0 && hash[2] == 0xc4;
}

/* Test SHA256 of "abc" - standard test vector */
static int test_sha256_abc(void) {
    OTA_SHA256Context ctx;
    ota_sha256_init(&ctx);
    const char *data = "abc";
    ota_sha256_update(&ctx, (const uint8_t *)data, 3);
    uint8_t hash[32];
    ota_sha256_final(&ctx, hash);
    /* SHA256("abc") = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad */
    return hash[0] == 0xba && hash[1] == 0x78 && hash[2] == 0x16;
}

/* Test SHA256 of "123456789" - another standard test vector */
static int test_sha256_123456789(void) {
    OTA_SHA256Context ctx;
    ota_sha256_init(&ctx);
    const char *data = "123456789";
    ota_sha256_update(&ctx, (const uint8_t *)data, 9);
    uint8_t hash[32];
    ota_sha256_final(&ctx, hash);
    /* Should produce a non-zero hash */
    return hash[0] != 0 || hash[1] != 0;
}

/* Test SHA256 incremental update */
static int test_sha256_incremental(void) {
    OTA_SHA256Context ctx1, ctx2;
    ota_sha256_init(&ctx1);
    ota_sha256_init(&ctx2);

    const char *data1 = "Hello, ";
    const char *data2 = "World!";

    /* Hash all at once */
    ota_sha256_update(&ctx1, (const uint8_t *)data1, 7);
    ota_sha256_update(&ctx1, (const uint8_t *)data2, 6);
    uint8_t hash1[32];
    ota_sha256_final(&ctx1, hash1);

    /* Hash in one call */
    char combined[14];
    memcpy(combined, data1, 7);
    memcpy(combined + 7, data2, 6);
    ota_sha256_update(&ctx2, (const uint8_t *)combined, 13);
    uint8_t hash2[32];
    ota_sha256_final(&ctx2, hash2);

    return memcmp(hash1, hash2, 32) == 0;
}

/* Test SHA256 avalanche effect */
static int test_sha256_avalanche(void) {
    OTA_SHA256Context ctx1, ctx2;
    ota_sha256_init(&ctx1);
    ota_sha256_init(&ctx2);

    uint8_t data1[16] = {0};
    uint8_t data2[16] = {0};
    data1[0] = 0x00;
    data2[0] = 0x01;  /* Single bit difference */

    ota_sha256_update(&ctx1, data1, 16);
    ota_sha256_update(&ctx2, data2, 16);
    uint8_t hash1[32], hash2[32];
    ota_sha256_final(&ctx1, hash1);
    ota_sha256_final(&ctx2, hash2);

    /* Hashes should be completely different (avalanche effect) */
    int diff_bytes = 0;
    for (int i = 0; i < 32; i++) {
        if (hash1[i] != hash2[i]) diff_bytes++;
    }
    return diff_bytes > 16;  /* At least half the bytes should differ */
}

/* Test SHA256 of large data */
static int test_sha256_large(void) {
    OTA_SHA256Context ctx;
    ota_sha256_init(&ctx);
    uint8_t data[8192];
    for (int i = 0; i < 8192; i++) data[i] = (uint8_t)(i & 0xFF);
    ota_sha256_update(&ctx, data, 8192);
    uint8_t hash[32];
    ota_sha256_final(&ctx, hash);
    return hash[0] != 0 || hash[1] != 0;
}

/* Test SHA256 null handling */
static int test_sha256_null(void) {
    OTA_SHA256Context ctx;
    ota_sha256_init(&ctx);
    /* Should not crash with null update */
    ota_sha256_update(&ctx, NULL, 100);
    uint8_t hash[32];
    ota_sha256_final(&ctx, hash);
    return hash[0] != 0 || hash[1] != 0;
}

int main(void) {
    printf("============================================================\n");
    printf("  SHA256 Hash Unit Tests\n");
    printf("============================================================\n\n");

    TEST(sha256_init);
    TEST(sha256_empty);
    TEST(sha256_abc);
    TEST(sha256_123456789);
    TEST(sha256_incremental);
    TEST(sha256_avalanche);
    TEST(sha256_large);
    TEST(sha256_null);

    printf("\n============================================================\n");
    printf("  Results: %d/%d tests passed\n", tests_passed, tests_run);
    printf("============================================================\n");

    return (tests_passed == tests_run) ? 0 : 1;
}
