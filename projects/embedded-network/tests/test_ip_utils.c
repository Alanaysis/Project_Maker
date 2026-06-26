/*
 * test_ip_utils.c - Unit tests for IP utility functions
 *
 * Tests IP address conversion, byte order functions, and MAC address
 * utilities used throughout the network stack.
 */

#include "embedded_net.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

/* Test result tracking */
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  TEST: %s ... ", name); tests_run++;
#define PASS()     printf("PASS\n"); tests_passed++
#define FAIL(msg)  printf("FAIL: %s\n", msg); tests_failed++

/* ============================================================================
 * Test: IP to string conversion
 * ============================================================================ */

static void test_ip_to_string(void) {
    TEST("ip_to_string");

    uint32_t ip = string_to_ip("192.168.1.100");
    const char *str = ip_to_string(ip);

    if (strcmp(str, "192.168.1.100") == 0) {
        PASS();
    } else {
        FAIL("IP string mismatch");
    }
}

/* ============================================================================
 * Test: String to IP conversion
 * ============================================================================ */

static void test_string_to_ip(void) {
    TEST("string_to_ip");

    uint32_t ip = string_to_ip("10.0.0.1");

    /* Check each byte */
    uint8_t *bytes = (uint8_t *)&ip;
    if (bytes[0] == 10 && bytes[1] == 0 && bytes[2] == 0 && bytes[3] == 1) {
        PASS();
    } else {
        FAIL("string to IP conversion failed");
    }
}

/* ============================================================================
 * Test: String to IP edge cases
 * ============================================================================ */

static void test_string_to_ip_edge_cases(void) {
    TEST("string_to_ip_edge_cases");

    /* Test various IP addresses */
    uint32_t ip1 = string_to_ip("0.0.0.0");
    uint32_t ip2 = string_to_ip("255.255.255.255");
    uint32_t ip3 = string_to_ip("127.0.0.1");

    int pass = 1;

    /* 0.0.0.0 */
    uint8_t *b1 = (uint8_t *)&ip1;
    if (b1[0] != 0 || b1[1] != 0 || b1[2] != 0 || b1[3] != 0) {
        pass = 0;
    }

    /* 255.255.255.255 */
    uint8_t *b2 = (uint8_t *)&ip2;
    if (b2[0] != 255 || b2[1] != 255 || b2[2] != 255 || b2[3] != 255) {
        pass = 0;
    }

    /* 127.0.0.1 */
    uint8_t *b3 = (uint8_t *)&ip3;
    if (b3[0] != 127 || b3[1] != 0 || b3[2] != 0 || b3[3] != 1) {
        pass = 0;
    }

    if (pass) {
        PASS();
    } else {
        FAIL("edge case conversion failed");
    }
}

/* ============================================================================
 * Test: Round-trip IP conversion
 * ============================================================================ */

static void test_ip_roundtrip(void) {
    TEST("ip_roundtrip");

    const char *test_ips[] = {
        "192.168.1.1",
        "10.0.0.1",
        "172.16.0.1",
        "8.8.8.8",
        "127.0.0.1",
        NULL
    };

    int pass = 1;
    for (int i = 0; test_ips[i] != NULL; i++) {
        uint32_t original = string_to_ip(test_ips[i]);
        const char *result = ip_to_string(original);
        uint32_t restored = string_to_ip(result);

        if (original != restored) {
            pass = 0;
            break;
        }
    }

    if (pass) {
        PASS();
    } else {
        FAIL("round-trip conversion failed");
    }
}

/* ============================================================================
 * Test: Byte order conversion (htons/htonl)
 * ============================================================================ */

static void test_byte_order(void) {
    TEST("byte_order");

    /* Test htons */
    uint16_t port = 0x0102;  /* Host order */
    uint16_t net = htons(port);

    /* Network byte order is big-endian: 0x0102 */
    uint8_t *b = (uint8_t *)&net;
    if (b[0] == 0x01 && b[1] == 0x02) {
        PASS();
    } else {
        FAIL("htons conversion failed");
    }
}

/* ============================================================================
 * Test: Byte order round-trip
 * ============================================================================ */

static void test_byte_order_roundtrip(void) {
    TEST("byte_order_roundtrip");

    uint16_t original = 0x1234;
    uint16_t converted = htons(original);
    uint16_t restored = ntohs(converted);

    if (original == restored) {
        PASS();
    } else {
        FAIL("byte order round-trip failed");
    }
}

/* ============================================================================
 * Test: 32-bit byte order
 * ============================================================================ */

static void test_long_byte_order(void) {
    TEST("long_byte_order");

    /* Use a raw value, not string_to_ip which already stores bytes directly */
    uint32_t val = 0xC0A80101;  /* 192.168.1.1 as raw uint32 */
    uint32_t net = htonl(val);

    /* Check network byte order (big-endian) */
    uint8_t *b = (uint8_t *)&net;
    if (b[0] == 192 && b[1] == 168 && b[2] == 1 && b[3] == 1) {
        PASS();
    } else {
        FAIL("htonl conversion failed");
    }
}

/* ============================================================================
 * Test: 32-bit byte order round-trip
 * ============================================================================ */

static void test_long_byte_order_roundtrip(void) {
    TEST("long_byte_order_roundtrip");

    uint32_t original = string_to_ip("10.20.30.40");
    uint32_t converted = htonl(original);
    uint32_t restored = ntohl(converted);

    if (original == restored) {
        PASS();
    } else {
        FAIL("long byte order round-trip failed");
    }
}

/* ============================================================================
 * Main test runner
 * ============================================================================ */

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    printf("========================================\n");
    printf("  IP Utility Unit Tests\n");
    printf("========================================\n\n");

    test_ip_to_string();
    test_string_to_ip();
    test_string_to_ip_edge_cases();
    test_ip_roundtrip();
    test_byte_order();
    test_byte_order_roundtrip();
    test_long_byte_order();
    test_long_byte_order_roundtrip();

    printf("\n========================================\n");
    printf("  Results: %d/%d passed", tests_passed, tests_run);
    if (tests_failed > 0) {
        printf(" (%d failed)", tests_failed);
    }
    printf("\n");
    printf("========================================\n");

    return tests_failed > 0 ? 1 : 0;
}
