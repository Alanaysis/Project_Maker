/*
 * test_checksum.c - Unit tests for checksum functions
 *
 * Tests the Internet Checksum implementation used by IP, ICMP, TCP, and UDP.
 */

#include "embedded_net.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  TEST: %s ... ", name); tests_run++;
#define PASS()     printf("PASS\n"); tests_passed++
#define FAIL(msg) do { printf("FAIL: " msg "\n"); tests_failed++; } while(0)

/* ============================================================================
 * Test: Basic checksum produces non-zero for non-zero data
 * ============================================================================ */

static void test_basic_checksum(void) {
    TEST("basic_checksum");

    uint8_t data[] = {0x12, 0x34, 0x56, 0x78};
    uint16_t result = checksum(data, 4);

    /* Checksum of non-zero data should not be 0x0000 */
    if (result != 0x0000) {
        PASS();
    } else {
        FAIL("checksum is zero for non-zero data");
    }
}

/* ============================================================================
 * Test: Checksum with odd number of bytes
 * ============================================================================ */

static void test_odd_length_checksum(void) {
    TEST("odd_length_checksum");

    uint8_t data[] = {0x12, 0x34, 0x56};
    uint16_t result = checksum(data, 3);

    if (result != 0x0000) {
        PASS();
    } else {
        FAIL("odd length checksum failed");
    }
}

/* ============================================================================
 * Test: Zero-length checksum
 * ============================================================================ */

static void test_zero_length_checksum(void) {
    TEST("zero_length_checksum");

    uint8_t data[] = {0x00};
    uint16_t result = checksum(data, 0);

    /* Checksum of empty data should be 0xFFFF (ones' complement of 0) */
    if (result == 0xFFFF) {
        PASS();
    } else {
        FAIL("expected 0xFFFF for empty data");
    }
}

/* ============================================================================
 * Test: All zeros checksum
 * ============================================================================ */

static void test_all_zeros_checksum(void) {
    TEST("all_zeros_checksum");

    uint8_t data[] = {0x00, 0x00, 0x00, 0x00};
    uint16_t result = checksum(data, 4);

    /* Checksum of all zeros should be 0xFFFF */
    if (result == 0xFFFF) {
        PASS();
    } else {
        FAIL("expected 0xFFFF for all zeros");
    }
}

/* ============================================================================
 * Test: All ones data
 * ============================================================================ */

static void test_all_ones_checksum(void) {
    TEST("all_ones_checksum");

    uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF};
    uint16_t result = checksum(data, 4);

    /* Verify: insert checksum and check sum = 0x0000 */
    uint8_t verify_data[4];
    verify_data[0] = data[0];
    verify_data[1] = data[1];
    verify_data[2] = (uint8_t)(result >> 8);
    verify_data[3] = (uint8_t)(result & 0xFF);
    uint16_t sum = checksum(verify_data, 4);

    if (sum == 0x0000) {
        PASS();
    } else {
        FAIL("all-ones verification failed");
    }
}

/* ============================================================================
 * Test: Pseudo-header checksum
 * ============================================================================ */

static void test_pseudo_checksum(void) {
    TEST("pseudo_checksum");

    uint32_t src = string_to_ip("192.168.1.100");
    uint32_t dst = string_to_ip("192.168.1.1");

    uint16_t cksum = pseudo_checksum(src, dst, IP_PROTO_TCP, 100);

    if (cksum != 0) {
        PASS();
    } else {
        FAIL("pseudo checksum is zero");
    }
}

/* ============================================================================
 * Test: Large data checksum
 * ============================================================================ */

static void test_large_data_checksum(void) {
    TEST("large_data_checksum");

    uint8_t data[1024];
    for (int i = 0; i < 1024; i++) {
        data[i] = (uint8_t)(i & 0xFF);
    }

    uint16_t result = checksum(data, 1024);

    if (result != 0x0000) {
        PASS();
    } else {
        FAIL("large data checksum is zero");
    }
}

/* ============================================================================
 * Test: Checksum is deterministic
 * ============================================================================ */

static void test_checksum_deterministic(void) {
    TEST("checksum_deterministic");

    uint8_t data[] = {0xAB, 0xCD, 0xEF, 0x01};
    uint16_t result1 = checksum(data, 4);
    uint16_t result2 = checksum(data, 4);

    if (result1 == result2) {
        PASS();
    } else {
        FAIL("checksum not deterministic");
    }
}

/* ============================================================================
 * Test: Single byte checksum
 * ============================================================================ */

static void test_single_byte_checksum(void) {
    TEST("single_byte_checksum");

    uint8_t data[] = {0x42};
    uint16_t result = checksum(data, 1);

    /* Should produce a valid checksum value */
    if (result != 0xFFFF) {  /* 0x0042 complemented */
        PASS();
    } else {
        FAIL("single byte checksum unexpected");
    }
}

/* ============================================================================
 * Main test runner
 * ============================================================================ */

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    printf("========================================\n");
    printf("  Checksum Unit Tests\n");
    printf("========================================\n\n");

    test_basic_checksum();
    test_odd_length_checksum();
    test_zero_length_checksum();
    test_all_zeros_checksum();
    test_all_ones_checksum();
    test_pseudo_checksum();
    test_large_data_checksum();
    test_checksum_deterministic();
    test_single_byte_checksum();

    printf("\n========================================\n");
    printf("  Results: %d/%d passed", tests_passed, tests_run);
    if (tests_failed > 0) {
        printf(" (%d failed)", tests_failed);
    }
    printf("\n");
    printf("========================================\n");

    return tests_failed > 0 ? 1 : 0;
}
