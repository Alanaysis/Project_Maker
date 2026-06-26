/**
 * test_delta.c - Delta Update Unit Tests
 *
 * Tests for the delta (binary diff/patch) module.
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

/* Test delta patch creation */
static int test_delta_create(void) {
    uint8_t old_fw[256], new_fw[256];
    for (int i = 0; i < 256; i++) old_fw[i] = (uint8_t)i;
    memcpy(new_fw, old_fw, 256);
    new_fw[100] = 0xFF;  /* Change one byte */

    uint8_t patch[512];
    size_t patch_size = 0;
    int ret = ota_delta_create(old_fw, 256, new_fw, 256, patch, &patch_size);
    return ret == OTA_STATUS_OK && patch_size > 0 && patch_size < 256;
}

/* Test delta patch application */
static int test_delta_apply(void) {
    uint8_t old_fw[256], new_fw[256];
    for (int i = 0; i < 256; i++) old_fw[i] = (uint8_t)i;
    memcpy(new_fw, old_fw, 256);
    new_fw[100] = 0xFF;

    uint8_t patch[512];
    size_t patch_size = 0;
    ota_delta_create(old_fw, 256, new_fw, 256, patch, &patch_size);

    uint8_t result[256];
    size_t result_size = 0;
    int ret = ota_delta_apply(old_fw, 256, patch, patch_size, result, &result_size);
    return ret == OTA_STATUS_OK && result_size == 256;
}

/* Test delta roundtrip */
static int test_delta_roundtrip(void) {
    uint8_t old_fw[256], new_fw[256];
    for (int i = 0; i < 256; i++) old_fw[i] = (uint8_t)(i * 3 + 7);
    memcpy(new_fw, old_fw, 256);
    new_fw[50] = 0x11;
    new_fw[100] = 0x22;
    new_fw[150] = 0x33;

    uint8_t patch[512];
    size_t patch_size = 0;
    ota_delta_create(old_fw, 256, new_fw, 256, patch, &patch_size);

    uint8_t result[256];
    size_t result_size = 0;
    ota_delta_apply(old_fw, 256, patch, patch_size, result, &result_size);

    return memcmp(result, new_fw, 256) == 0;
}

/* Test delta with identical data */
static int test_delta_identical(void) {
    uint8_t data[256];
    for (int i = 0; i < 256; i++) data[i] = (uint8_t)i;

    uint8_t patch[512];
    size_t patch_size = 0;
    int ret = ota_delta_create(data, 256, data, 256, patch, &patch_size);
    return ret == OTA_STATUS_OK && patch_size > 0;
}

/* Test delta with completely different data */
static int test_delta_different(void) {
    uint8_t data1[256], data2[256];
    for (int i = 0; i < 256; i++) {
        data1[i] = (uint8_t)i;
        data2[i] = (uint8_t)(i ^ 0xFF);
    }

    uint8_t patch[512];
    size_t patch_size = 0;
    int ret = ota_delta_create(data1, 256, data2, 256, patch, &patch_size);
    return ret == OTA_STATUS_OK;
}

/* Test delta null handling */
static int test_delta_null(void) {
    uint8_t patch[512];
    size_t patch_size = 0;
    int ret = ota_delta_create(NULL, 256, (uint8_t *)"test", 4, patch, &patch_size);
    return ret != OTA_STATUS_OK;
}

/* Test delta header checksums */
static int test_delta_header(void) {
    uint8_t old_fw[256], new_fw[256];
    for (int i = 0; i < 256; i++) old_fw[i] = (uint8_t)i;
    memcpy(new_fw, old_fw, 256);
    new_fw[0] ^= 0xFF;

    uint8_t patch[512];
    size_t patch_size = 0;
    ota_delta_create(old_fw, 256, new_fw, 256, patch, &patch_size);

    OTA_DeltaHeader *delta = (OTA_DeltaHeader *)patch;
    /* Checksums should be different */
    return delta->original_checksum != delta->target_checksum;
}

int main(void) {
    printf("============================================================\n");
    printf("  Delta Update Unit Tests\n");
    printf("============================================================\n\n");

    TEST(delta_create);
    TEST(delta_apply);
    TEST(delta_roundtrip);
    TEST(delta_identical);
    TEST(delta_different);
    TEST(delta_null);
    TEST(delta_header);

    printf("\n============================================================\n");
    printf("  Results: %d/%d tests passed\n", tests_passed, tests_run);
    printf("============================================================\n");

    return (tests_passed == tests_run) ? 0 : 1;
}
