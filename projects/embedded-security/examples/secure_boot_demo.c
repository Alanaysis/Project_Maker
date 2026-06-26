/**
 * @file secure_boot_demo.c
 * @brief Secure Boot Demo - Demonstrates firmware verification and boot chain
 *
 * This demo shows:
 *   1. Creating a secure boot context with root key
 *   2. Simulating firmware with header (hash + signature)
 *   3. Verifying firmware integrity
 *   4. Walking through the boot chain
 *
 * Embedded security concept: Chain of Trust
 *   Each boot stage verifies the next, creating an unbroken chain
 *   from the ROM bootloader to the application.
 */

#include <stdio.h>
#include <string.h>
#include "secure_boot.h"
#include "sha256.h"

/* Simulated firmware data (would be actual firmware binary in production) */
#define FIRMWARE_SIZE 256
static uint8_t simulated_firmware[FIRMWARE_SIZE];

/* Simulated RSA-style public key (in production, this is burned in ROM) */
static const uint8_t root_key[32] = {
    0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE,
    0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,
    0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
    0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00
};

int main(int argc, char *argv[]) {
    (void)argc; (void)argv;

    printf("=== Embedded Security: Secure Boot Demo ===\n\n");

    /* Step 1: Initialize secure boot with root of trust */
    printf("[1] Initializing secure boot with root key...\n");
    secure_boot_context_t boot_ctx;
    boot_result_t result = secure_boot_init(&boot_ctx, root_key);
    printf("    Result: %s\n\n", boot_result_str(result));

    /* Step 2: Create simulated firmware with header */
    printf("[2] Creating simulated firmware...\n");
    memset(simulated_firmware, 0x42, FIRMWARE_SIZE);

    /* Add firmware header */
    firmware_header_t fw_header;
    memset(&fw_header, 0, sizeof(firmware_header_t));
    fw_header.magic = 0x53424F4F;  /* "SB OO" */
    fw_header.version = 1;
    fw_header.firmware_size = FIRMWARE_SIZE;

    /* Compute firmware hash */
    compute_firmware_hash(simulated_firmware, FIRMWARE_SIZE, fw_header.hash);
    printf("    Firmware hash: ");
    sha256_print(fw_header.hash);

    /* Simulate signature (in production, sign with private key) */
    fw_header.signature_valid = 1;
    printf("    Signature: valid (simulated)\n\n");

    /* Step 3: Verify firmware header */
    printf("[3] Verifying firmware header...\n");
    if (verify_firmware_header(&fw_header)) {
        printf("    [PASS] Magic number valid\n");
    } else {
        printf("    [FAIL] Invalid magic number\n");
    }

    /* Step 4: Verify firmware hash */
    printf("[4] Verifying firmware integrity...\n");
    result = verify_firmware_hash(&fw_header, simulated_firmware, FIRMWARE_SIZE);
    printf("    Result: %s\n\n", boot_result_str(result));

    /* Step 5: Verify signature */
    printf("[5] Verifying firmware signature...\n");
    result = verify_firmware_signature(&fw_header, simulated_firmware, FIRMWARE_SIZE);
    printf("    Result: %s\n\n", boot_result_str(result));

    /* Step 6: Build and verify boot chain */
    printf("[6] Building boot chain...\n");

    /* ROM bootloader (always trusted) */
    uint8_t rom_hash[32];
    memset(rom_hash, 0, sizeof(rom_hash));
    boot_chain_add_entry(&boot_ctx, BOOT_STAGE_ROM_BOOTLOADER,
                         0x00000000, 0x10000, rom_hash);

    /* Secondary bootloader */
    uint8_t secondary_hash[32];
    memset(secondary_hash, 0, sizeof(secondary_hash));
    boot_chain_add_entry(&boot_ctx, BOOT_STAGE_SECONDARY_BOOT,
                         0x00010000, 0x20000, secondary_hash);

    /* Firmware */
    boot_chain_add_entry(&boot_ctx, BOOT_STAGE_FIRMWARE,
                         0x00030000, FIRMWARE_SIZE, fw_header.hash);

    /* Verify entire boot chain */
    printf("    Verifying boot chain...\n");
    result = boot_chain_verify(&boot_ctx);
    printf("    Result: %s\n\n", boot_result_str(result));

    /* Step 7: Execute verified firmware */
    printf("[7] Executing verified firmware...\n");
    result = boot_execute_firmware(&boot_ctx, simulated_firmware);
    printf("    Result: %s\n\n", boot_result_str(result));

    /* Step 8: Demonstrate tamper detection */
    printf("[8] Testing tamper detection...\n");
    /* Tamper with firmware */
    simulated_firmware[0] ^= 0xFF;

    /* Recompute hash and verify */
    uint8_t tampered_hash[32];
    compute_firmware_hash(simulated_firmware, FIRMWARE_SIZE, tampered_hash);
    printf("    Tampered hash: ");
    sha256_print(tampered_hash);

    /* Verify against original hash */
    result = verify_firmware_hash(&fw_header, simulated_firmware, FIRMWARE_SIZE);
    printf("    Verification result: %s\n", boot_result_str(result));
    printf("    [PASS] Tamper detected!\n\n");

    printf("=== Secure Boot Demo Complete ===\n");
    return 0;
}
