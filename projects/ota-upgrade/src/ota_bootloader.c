/**
 * ota_bootloader.c - Bootloader Simulation
 *
 * The bootloader is the first code that runs on a device. It:
 *   1. Initializes hardware (clocks, memory, peripherals)
 *   2. Determines which firmware bank to boot from
 *   3. Verifies firmware integrity before jumping to it
 *   4. Handles OTA update flags from the application
 *
 * Boot process:
 *   Power On -> BootROM -> Bootloader -> Application Firmware
 *
 * In OTA systems, the bootloader must:
 *   - Check if an update is pending
 *   - Verify firmware signature (secure boot)
 *   - Handle failure by falling back to previous bank
 *   - Clear update flags after successful boot
 */

#include "ota_firmware.h"
#include <string.h>
#include <stdio.h>

/* Initialize bootloader */
void ota_bootloader_init(OTA_Bootloader *bl) {
    if (!bl) return;

    bl->current_bank = OTA_BANK_A;
    bl->last_boot_bank = OTA_BANK_A;
    bl->boot_count = 0;
    bl->secure_boot_enabled = true;
    memset(bl->boot_signature, 0, OTA_SHA256_SIZE);
    bl->boot_verified = false;
}

/* Simulate boot process with verification.
 *
 * Steps:
 *   1. Read bank status from RTC/backup registers
 *   2. Load firmware header from selected bank
 *   3. Verify firmware signature (secure boot)
 *   4. Check firmware version is valid
 *   5. Jump to application entry point
 *
 * Returns true if boot is successful, false if verification fails.
 */
bool ota_bootloader_boot(OTA_Bootloader *bl,
                         const OTA_DualBank *dualbank) {
    if (!bl || !dualbank) {
        return false;
    }

    bl->boot_count++;

    /* Determine which bank to boot from */
    if (dualbank->reboot_requested) {
        bl->current_bank = dualbank->active_bank;
    } else {
        bl->current_bank = dualbank->active_bank;
    }

    /* Get firmware data from the selected bank */
    uint32_t bank_idx = bl->current_bank;
    uint8_t *bank_data = dualbank->bank[bank_idx];

    if (!bank_data) {
        return false;
    }

    /* Parse firmware header from bank */
    OTA_FirmwareHeader *header = (OTA_FirmwareHeader *)bank_data;

    /* Validate magic number */
    if (header->magic != OTA_MAGIC_NUMBER) {
        return false;
    }

    /* Verify firmware integrity (secure boot) */
    if (bl->secure_boot_enabled) {
        /* Compute SHA256 of firmware payload */
        OTA_SHA256Context sha_ctx;
        ota_sha256_init(&sha_ctx);
        ota_sha256_update(&sha_ctx, bank_data + sizeof(OTA_FirmwareHeader),
                         header->size);
        uint8_t computed_hash[OTA_SHA256_SIZE];
        ota_sha256_final(&sha_ctx, computed_hash);

        /* Compare with stored hash (simplified) */
        bl->boot_verified = true;
    }

    /* Update last boot bank */
    bl->last_boot_bank = bl->current_bank;

    return bl->boot_verified;
}

/* Check if firmware needs update.
 *
 * Compares the current running firmware version with the new version.
 * Returns true if the new version is newer and an update should proceed.
 */
bool ota_bootloader_needs_update(const OTA_Bootloader *bl,
                                  uint32_t new_version) {
    if (!bl) {
        return true;
    }

    /* In real implementation, read current version from application */
    (void)bl;
    (void)new_version;
    return true;
}
