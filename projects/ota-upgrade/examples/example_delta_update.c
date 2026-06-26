/**
 * example_delta_update.c - Delta Update Demo
 *
 * This example demonstrates binary delta update:
 *   1. Create old firmware (version 1.0)
 *   2. Create new firmware (version 2.0, mostly same as old)
 *   3. Generate delta patch
 *   4. Apply patch to old firmware
 *   5. Verify result matches new firmware
 *
 * Learning objectives:
 *   - Understand why delta updates save bandwidth
 *   - See how patch is much smaller than full firmware
 *   - Verify patched firmware integrity
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ota_firmware.h"

/* (private key not needed for delta demo) */

int main(void) {
    printf("============================================================\n");
    printf("  Delta Update Demo\n");
    printf("============================================================\n\n");

    /* Create old firmware (version 1.0) - 1 KB of data */
    printf("[Step 1] Creating old firmware (v1.0)...\n");
    uint8_t old_fw[1024];
    for (int i = 0; i < 1024; i++) old_fw[i] = (uint8_t)(i * 7 + 10);

    uint32_t old_crc_ctx_data[64];
    (void)old_crc_ctx_data;
    OTA_CRC32Context crc_ctx;
    ota_crc32_init(&crc_ctx);
    uint32_t old_crc = ota_crc32_calculate(&crc_ctx, old_fw, 1024);
    printf("  Old firmware: 1024 bytes\n");
    printf("  Old CRC32: 0x%08X\n", old_crc);

    /* Create new firmware (version 2.0) - mostly same, a few bytes changed */
    printf("\n[Step 2] Creating new firmware (v2.0)...\n");
    uint8_t new_fw[1024];
    memcpy(new_fw, old_fw, 1024);

    /* Make small changes (simulating a real firmware update) */
    new_fw[50] = 0xFF;   /* Change byte at offset 50 */
    new_fw[51] = 0xEE;   /* Change byte at offset 51 */
    new_fw[200] = 0xDD;  /* Change byte at offset 200 */
    new_fw[201] = 0xCC;  /* Change byte at offset 201 */
    new_fw[1020] = 0x11; /* Change byte near end */

    uint32_t new_crc = ota_crc32_calculate(&crc_ctx, new_fw, 1024);
    printf("  New firmware: 1024 bytes\n");
    printf("  New CRC32: 0x%08X\n", new_crc);
    printf("  Changes: 5 bytes modified out of 1024\n");

    /* Generate delta patch */
    printf("\n[Step 3] Generating delta patch...\n");
    uint8_t patch[2048];
    size_t patch_size = 0;
    int ret = ota_delta_create(old_fw, 1024, new_fw, 1024, patch, &patch_size);
    if (ret != OTA_STATUS_OK) {
        printf("  ERROR: Failed to create patch: %d\n", ret);
        return 1;
    }

    OTA_DeltaHeader *delta = (OTA_DeltaHeader *)patch;
    printf("  Patch size: %zu bytes\n", patch_size);
    printf("  Full firmware size: 1024 bytes\n");
    printf("  Compression ratio: %.1f%%\n",
           (float)patch_size / 1024.0f * 100.0f);
    printf("  Space saved: %zu bytes (%.1f%%)\n",
           1024 - patch_size,
           (1.0f - (float)patch_size / 1024.0f) * 100.0f);
    printf("  Source version: %u\n", delta->source_version);
    printf("  Target version: %u\n", delta->target_version);

    /* Apply patch */
    printf("\n[Step 4] Applying patch to old firmware...\n");
    uint8_t patched_fw[1024];
    size_t patched_size = 0;
    ret = ota_delta_apply(old_fw, 1024, patch, patch_size,
                          patched_fw, &patched_size);
    if (ret != OTA_STATUS_OK) {
        printf("  ERROR: Failed to apply patch: %d\n", ret);
        return 1;
    }
    printf("  Patched firmware size: %zu bytes\n", patched_size);

    /* Verify patched firmware matches new firmware */
    printf("\n[Step 5] Verifying patched firmware...\n");
    int match = (memcmp(patched_fw, new_fw, 1024) == 0);
    printf("  Patched == New: %s\n", match ? "MATCH!" : "MISMATCH!");

    /* Compare CRC32 */
    uint32_t patched_crc = ota_crc32_calculate(&crc_ctx,
                                                 patched_fw, patched_size);
    printf("  Patched CRC32:  0x%08X\n", patched_crc);
    printf("  New CRC32:      0x%08X\n", new_crc);
    printf("  CRC32 match: %s\n",
           patched_crc == new_crc ? "YES" : "NO");

    /* Show what changed */
    printf("\n[Step 6] Changes between old and new firmware:\n");
    int change_count = 0;
    for (int i = 0; i < 1024; i++) {
        if (old_fw[i] != new_fw[i]) {
            printf("  Offset %4d: 0x%02X -> 0x%02X\n",
                   i, old_fw[i], new_fw[i]);
            change_count++;
        }
    }
    printf("  Total changed bytes: %d\n", change_count);

    printf("\n============================================================\n");
    printf("  Delta Update Summary\n");
    printf("============================================================\n");
    printf("  Full firmware download: 1024 bytes\n");
    printf("  Delta patch download:   %zu bytes\n", patch_size);
    printf("  Bandwidth saved:        %zu bytes (%.1f%%)\n",
           1024 - patch_size,
           (1.0f - (float)patch_size / 1024.0f) * 100.0f);
    printf("\n  For large firmware (1 MB) with 100 bytes changed:\n");
    printf("  Full download: 1,048,576 bytes\n");
    printf("  Delta patch:   ~128 bytes (header + small patch)\n");
    printf("  Savings:       ~99.99%%!\n");
    printf("============================================================\n");

    return 0;
}
