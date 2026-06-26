/**
 * test_dualbank.c - Dual-bank A/B Update Unit Tests
 *
 * Tests for the dual-bank update mechanism:
 *   - Bank initialization
 *   - Write and verify
 *   - Activation and rollback
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

/* Test dual-bank initialization */
static int test_dualbank_init(void) {
    OTA_DualBank bank;
    int ret = ota_dualbank_init(&bank, 4096, 4096);
    return ret == OTA_STATUS_OK && bank.active_bank == OTA_BANK_A;
}

/* Test dual-bank bank selection */
static int test_dualbank_banks(void) {
    OTA_DualBank bank;
    ota_dualbank_init(&bank, 4096, 4096);
    return bank.bank[OTA_BANK_A] != NULL && bank.bank[OTA_BANK_B] != NULL;
}

/* Test write to pending bank */
static int test_dualbank_write(void) {
    OTA_DualBank bank;
    ota_dualbank_init(&bank, 4096, 4096);

    uint8_t payload[] = "Write test data for dual-bank";
    OTA_FirmwareImage image;
    ota_image_create(&image, 0x010000, payload, sizeof(payload) - 1, private_key);

    int ret = ota_dualbank_write(&bank, &image);
    int ok = (ret == OTA_STATUS_OK && bank.update_in_progress == false);
    ota_image_destroy(&image);
    return ok;
}

/* Test verify valid firmware */
static int test_dualbank_verify_valid(void) {
    OTA_DualBank bank;
    ota_dualbank_init(&bank, 4096, 4096);

    uint8_t payload[] = "Verify valid test";
    OTA_FirmwareImage image;
    ota_image_create(&image, 0x010000, payload, sizeof(payload) - 1, private_key);

    bool ok = ota_dualbank_verify(&bank, &image);
    ota_image_destroy(&image);
    return ok;
}

/* Test activate bank switch */
static int test_dualbank_activate(void) {
    OTA_DualBank bank;
    ota_dualbank_init(&bank, 4096, 4096);
    uint32_t old_active = bank.active_bank;

    ota_dualbank_activate(&bank);
    return bank.active_bank != old_active && bank.reboot_requested == true;
}

/* Test rollback */
static int test_dualbank_rollback(void) {
    OTA_DualBank bank;
    ota_dualbank_init(&bank, 4096, 4096);

    /* Simulate having switched to Bank B */
    bank.active_bank = OTA_BANK_B;
    int ret = ota_dualbank_rollback(&bank);
    return ret == OTA_STATUS_OK && bank.active_bank == OTA_BANK_A;
}

/* Test get active bank */
static int test_dualbank_get_active(void) {
    OTA_DualBank bank;
    ota_dualbank_init(&bank, 4096, 4096);
    return ota_dualbank_get_active(&bank) == OTA_BANK_A;
}

/* Test write too large firmware */
static int test_dualbank_too_large(void) {
    OTA_DualBank bank;
    ota_dualbank_init(&bank, 128, 128);

    uint8_t payload[256];
    memset(payload, 0xAA, 256);
    OTA_FirmwareImage image;
    ota_image_create(&image, 0x010000, payload, 256, private_key);

    int ret = ota_dualbank_write(&bank, &image);
    ota_image_destroy(&image);
    return ret == OTA_STATUS_ERR_SIZE;
}

/* Test null handling */
static int test_dualbank_null(void) {
    int ret = ota_dualbank_init(NULL, 4096, 4096);
    return ret != OTA_STATUS_OK;
}

int main(void) {
    printf("============================================================\n");
    printf("  Dual-bank A/B Update Unit Tests\n");
    printf("============================================================\n\n");

    TEST(dualbank_init);
    TEST(dualbank_banks);
    TEST(dualbank_write);
    TEST(dualbank_verify_valid);
    TEST(dualbank_activate);
    TEST(dualbank_rollback);
    TEST(dualbank_get_active);
    TEST(dualbank_too_large);
    TEST(dualbank_null);

    printf("\n============================================================\n");
    printf("  Results: %d/%d tests passed\n", tests_passed, tests_run);
    printf("============================================================\n");

    return (tests_passed == tests_run) ? 0 : 1;
}
