/**
 * example_basic_ota.c - Basic OTA Update Flow Demo
 *
 * This example demonstrates the complete OTA update lifecycle:
 *   1. Create firmware image (simulate firmware with version)
 *   2. Dual-bank initialization
 *   3. Download firmware in chunks
 *   4. Verify firmware (CRC32 + SHA256 + signature)
 *   5. Flash to pending bank
 *   6. Activate and reboot
 *
 * This is the core OTA update loop that every embedded OTA system implements.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ota_firmware.h"

/* Simulated firmware payload - in real systems this would be compiled code */
static uint8_t firmware_payload[1024];

/* Simulated private key for signing */
static const uint8_t private_key[32] = {
    0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE,
    0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,
    0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
    0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00
};

/* Simulated public key for verification */
static uint8_t public_key[256];

/* Print a progress bar for download simulation */
static void print_progress(float progress, const char *label) {
    int bar_width = 40;
    int fill = (int)(bar_width * progress);
    printf("\r  %s [", label);
    for (int i = 0; i < bar_width; i++) {
        if (i < fill) printf("#");
        else printf("-");
    }
    printf("] %.1f%%", progress * 100.0f);
    if (progress >= 1.0f) printf("\n");
}

int main(void) {
    printf("============================================================\n");
    printf("  OTA Firmware Upgrade System - Basic Update Flow Demo\n");
    printf("============================================================\n\n");

    /* Step 1: Generate simulated firmware payload */
    printf("[Step 1] Generating simulated firmware payload...\n");
    for (size_t i = 0; i < sizeof(firmware_payload); i++) {
        firmware_payload[i] = (uint8_t)(i * 7 + 42);
    }

    /* Generate public key from private key (simplified) */
    for (int i = 0; i < 256; i++) {
        public_key[i] = (uint8_t)(private_key[i % 32] * 37 + i * 23 + 1);
    }

    printf("  Firmware size: %zu bytes\n", sizeof(firmware_payload));
    printf("  Firmware version: 1.0.0\n\n");

    /* Step 2: Create firmware image with signature */
    printf("[Step 2] Creating firmware image...\n");
    OTA_FirmwareImage image;
    int ret = ota_image_create(&image, 0x010000,
                                firmware_payload, sizeof(firmware_payload),
                                private_key);
    if (ret != OTA_STATUS_OK) {
        printf("  ERROR: Failed to create firmware image: %d\n", ret);
        return 1;
    }

    printf("  Magic: 0x%08X\n", image.header.magic);
    printf("  Version: %d.%d.%d\n",
           (image.header.version >> 16) & 0xFF,
           (image.header.version >> 8) & 0xFF,
            image.header.version & 0xFF);
    printf("  CRC32: 0x%08X\n", image.header.checksum);
    printf("  SHA256: ");
    for (int i = 0; i < 8; i++) {
        printf("%02X", image.header.sha256_hash[i]);
    }
    printf("...\n");
    printf("  Size: %u bytes\n\n", image.header.size);

    /* Step 3: Initialize dual-bank A/B system */
    printf("[Step 3] Initializing dual-bank A/B system...\n");
    OTA_DualBank dualbank;
    ret = ota_dualbank_init(&dualbank, 4096, 4096);
    if (ret != OTA_STATUS_OK) {
        printf("  ERROR: Failed to initialize dual-bank: %d\n", ret);
        return 1;
    }
    printf("  Bank A size: 4096 bytes\n");
    printf("  Bank B size: 4096 bytes\n");
    printf("  Active bank: Bank %c\n\n", 'A' + ota_dualbank_get_active(&dualbank));

    /* Step 4: Simulate chunked download */
    printf("[Step 4] Simulating chunked download...\n");
    OTA_DownloadState download_state;
    ota_download_init(&download_state, image.header.size);

    /* Create a buffer for chunk data (copy from image) */
    uint8_t *chunk_buffer = (uint8_t *)malloc(image.header.size);
    ota_image_serialize(&image, chunk_buffer, image.header.size + 1024);

    size_t offset = 0;
    while (offset < image.header.size) {
        size_t chunk_len = (offset + OTA_CHUNK_SIZE <= image.header.size)
                           ? OTA_CHUNK_SIZE
                           : image.header.size - offset;
        ret = ota_download_chunk(&download_state,
                                  chunk_buffer + offset, chunk_len);
        if (ret != OTA_STATUS_OK) {
            printf("  ERROR: Download failed at offset %zu: %d\n", offset, ret);
            free(chunk_buffer);
            return 1;
        }
        offset += chunk_len;
        print_progress(ota_download_progress(&download_state), "Downloading");
    }
    free(chunk_buffer);
    printf("  Download complete!\n\n");

    /* Step 5: Verify firmware */
    printf("[Step 5] Verifying firmware...\n");
    OTA_SignatureVerifier verifier;
    ota_sig_init(&verifier, public_key, 256);

    /* Verify CRC32 */
    OTA_CRC32Context crc_ctx;
    ota_crc32_init(&crc_ctx);
    uint32_t computed_crc = ota_crc32_calculate(&crc_ctx,
                                                 image.payload,
                                                 image.payload_size);
    printf("  CRC32 check: %s\n",
           computed_crc == image.header.checksum ? "PASS" : "FAIL");

    /* Verify SHA256 */
    OTA_SHA256Context sha_ctx;
    ota_sha256_init(&sha_ctx);
    ota_sha256_update(&sha_ctx, image.payload, image.payload_size);
    uint8_t computed_hash[OTA_SHA256_SIZE];
    ota_sha256_final(&sha_ctx, computed_hash);
    int sha_match = (memcmp(computed_hash, image.header.sha256_hash,
                            OTA_SHA256_SIZE) == 0);
    printf("  SHA256 check: %s\n", sha_match ? "PASS" : "FAIL");

    /* Verify signature */
    bool sig_valid = ota_sig_verify(&verifier, image.payload,
                                     image.payload_size, image.signature);
    printf("  Signature check: %s\n", sig_valid ? "PASS" : "FAIL");

    if (!sha_match || !sig_valid) {
        printf("\n  VERIFICATION FAILED - aborting update!\n");
        ota_image_destroy(&image);
        return 1;
    }
    printf("\n  All verifications PASSED!\n\n");

    /* Step 6: Flash to pending bank */
    printf("[Step 6] Flashing firmware to pending bank...\n");
    ret = ota_dualbank_write(&dualbank, &image);
    if (ret != OTA_STATUS_OK) {
        printf("  ERROR: Flash failed: %d\n", ret);
        ota_image_destroy(&image);
        return 1;
    }
    printf("  Firmware written to Bank %c\n\n", 'A' + dualbank.pending_bank);

    /* Step 7: Activate and reboot */
    printf("[Step 7] Activating new firmware and simulating reboot...\n");
    uint32_t previous_bank = ota_dualbank_activate(&dualbank);
    printf("  Previous active: Bank %c\n", 'A' + previous_bank);
    printf("  New active: Bank %c\n", 'A' + ota_dualbank_get_active(&dualbank));

    /* Simulate bootloader booting from new bank */
    OTA_Bootloader bootloader;
    ota_bootloader_init(&bootloader);
    bool boot_ok = ota_bootloader_boot(&bootloader, &dualbank);
    printf("  Boot verification: %s\n", boot_ok ? "SUCCESS" : "FAILED");

    printf("\n============================================================\n");
    printf("  OTA Update Complete!\n");
    printf("============================================================\n");

    ota_image_destroy(&image);
    return 0;
}
