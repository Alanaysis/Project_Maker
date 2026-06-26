/**
 * @file test_sha256.c
 * @brief Unit tests for SHA-256 implementation
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "sha256.h"

static int tests_run = 0;
static int tests_passed = 0;

#define TEST(name) do { printf("  TEST: %s... ", #name); tests_run++; } while(0)
#define PASS() do { printf("[PASS]\n"); tests_passed++; } while(0)
#define FAIL(msg) do { printf("[FAIL]: %s\n", msg); } while(0)
#define ASSERT(cond, msg) do { if (!(cond)) { FAIL(msg); return; } } while(0)

void test_empty_message(void) {
    TEST(empty_message);
    uint8_t digest[32];
    sha256_hash((const uint8_t *)"", 0, digest);

    /* SHA-256 of empty string is known */
    uint8_t expected[] = {
        0xe3, 0xb0, 0xc4, 0x42, 0x98, 0xfc, 0x1c, 0x14,
        0x9a, 0xfb, 0xf4, 0xc8, 0x99, 0x6f, 0xb9, 0x24,
        0x27, 0xae, 0x41, 0xe4, 0x64, 0x9b, 0x93, 0x4c,
        0xa4, 0x95, 0x99, 0x1b, 0x78, 0x52, 0xb8, 0x55
    };
    ASSERT(sha256_compare(digest, expected), "Empty message hash mismatch");
    PASS();
}

void test_single_byte(void) {
    TEST(single_byte);
    uint8_t digest[32];
    sha256_hash((const uint8_t *)"a", 1, digest);

    uint8_t expected[] = {
        0xca, 0x97, 0x81, 0x12, 0xc1, 0xff, 0x38, 0x9e,
        0x1b, 0x40, 0x21, 0x98, 0x74, 0xad, 0xdc, 0x16,
        0xe8, 0x52, 0x9c, 0xb4, 0x18, 0x0b, 0xdd, 0xa4,
        0x42, 0xd5, 0x3d, 0x1f, 0x0d, 0x4d, 0x02, 0x09
    };
    ASSERT(sha256_compare(digest, expected), "Single byte hash mismatch");
    PASS();
}

void test_hello_world(void) {
    TEST(hello_world);
    uint8_t digest[32];
    sha256_hash((const uint8_t *)"Hello, World!", 13, digest);

    uint8_t expected[] = {
        0x65, 0xda, 0xe8, 0xc1, 0x32, 0x2f, 0x8b, 0x16,
        0x21, 0x25, 0x46, 0x54, 0x38, 0x12, 0x47, 0x26,
        0x4a, 0x67, 0x77, 0x5a, 0x04, 0x0d, 0x78, 0x57,
        0x18, 0x1a, 0x97, 0x2a, 0x29, 0x08, 0x4c, 0x6a
    };
    ASSERT(sha256_compare(digest, expected), "Hello World hash mismatch");
    PASS();
}

void test_incremental_hash(void) {
    TEST(incremental_hash);
    sha256_context ctx;
    sha256_init(&ctx);

    sha256_update(&ctx, (const uint8_t *)"Hello", 5);
    sha256_update(&ctx, (const uint8_t *)", World!", 8);

    uint8_t digest[32];
    sha256_final(&ctx, digest);

    uint8_t expected[] = {
        0x65, 0xda, 0xe8, 0xc1, 0x32, 0x2f, 0x8b, 0x16,
        0x21, 0x25, 0x46, 0x54, 0x38, 0x12, 0x47, 0x26,
        0x4a, 0x67, 0x77, 0x5a, 0x04, 0x0d, 0x78, 0x57,
        0x18, 0x1a, 0x97, 0x2a, 0x29, 0x08, 0x4c, 0x6a
    };
    ASSERT(sha256_compare(digest, expected), "Incremental hash mismatch");
    PASS();
}

void test_avalanche_effect(void) {
    TEST(avalanche_effect);
    uint8_t data1[] = "Test message A";
    uint8_t data2[] = "Test message B";  /* Only last byte differs */

    uint8_t digest1[32], digest2[32];
    sha256_hash(data1, sizeof(data1) - 1, digest1);
    sha256_hash(data2, sizeof(data2) - 1, digest2);

    int diff_bits = 0;
    for (int i = 0; i < 32; i++) {
        uint8_t xor_val = digest1[i] ^ digest2[i];
        while (xor_val) {
            diff_bits += xor_val & 1;
            xor_val >>= 1;
        }
    }

    /* Avalanche effect: ~50% of bits should change (128 bits out of 256) */
    ASSERT(diff_bits > 100 && diff_bits < 150,
           "Avalanche effect insufficient (got "
           "100-150 bit changes, expected ~128)");
    PASS();
}

void test_compare_function(void) {
    TEST(compare_function);
    uint8_t a[32], b[32], c[32];
    for (int i = 0; i < 32; i++) {
        a[i] = (uint8_t)i;
        b[i] = (uint8_t)i;
        c[i] = (uint8_t)(i ^ 0xFF);
    }

    ASSERT(sha256_compare(a, b), "Equal digests should compare equal");
    ASSERT(!sha256_compare(a, c), "Different digests should not compare equal");
    PASS();
}

int main(void) {
    printf("=== SHA-256 Unit Tests ===\n\n");

    test_empty_message();
    test_single_byte();
    test_hello_world();
    test_incremental_hash();
    test_avalanche_effect();
    test_compare_function();

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
