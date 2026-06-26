/**
 * ota_dualbank.c - Dual-bank A/B Update Mechanism
 *
 * Dual-bank A/B update is the industry standard for safe OTA firmware updates.
 *
 * How it works:
 *   +--------+--------+
 *   | Bank A | Bank B |
 *   | Active |  Idle   |   <-- Normal state: Bank A is running
 *   +--------+--------+
 *
 *   +--------+--------+
 *   | Bank A | Bank B |
 *   | Active |  New   |   <-- Updating: New firmware written to Bank B
 *   +--------+--------+
 *
 *   +--------+--------+
 *   | Bank A | Bank B |
 *   |  Old   | Active |   <-- After reboot: Bank B is now active
 *   +--------+--------+
 *
 * Safety guarantees:
 *   - Old firmware is preserved until new one is verified
 *   - If update fails, device boots from old bank
 *   - If new firmware fails to boot, automatic rollback occurs
 *
 * Why two banks instead of one?
 *   - Single-bank: overwrite = bricked if power fails mid-write
 *   - Dual-bank: atomic swap = never bricked
 */

#include "ota_firmware.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* Initialize dual-bank system with given memory sizes */
int ota_dualbank_init(OTA_DualBank *bank,
                      size_t bank_a_size, size_t bank_b_size) {
    if (!bank) {
        return OTA_STATUS_ERR_FLASH;
    }

    /* Allocate bank memory (simulated with malloc for learning) */
    bank->bank[OTA_BANK_A] = (uint8_t *)malloc(bank_a_size);
    bank->bank[OTA_BANK_B] = (uint8_t *)malloc(bank_b_size);

    if (!bank->bank[OTA_BANK_A] || !bank->bank[OTA_BANK_B]) {
        free(bank->bank[OTA_BANK_A]);
        free(bank->bank[OTA_BANK_B]);
        return OTA_STATUS_ERR_FLASH;
    }

    /* Initialize banks with zero */
    memset(bank->bank[OTA_BANK_A], 0, bank_a_size);
    memset(bank->bank[OTA_BANK_B], 0, bank_b_size);

    bank->bank_size[OTA_BANK_A] = bank_a_size;
    bank->bank_size[OTA_BANK_B] = bank_b_size;

    /* Start with Bank A active (simulating fresh device) */
    bank->active_bank = OTA_BANK_A;
    bank->pending_bank = OTA_BANK_B;
    bank->update_in_progress = false;
    bank->reboot_requested = false;
    bank->rollback_requested = false;

    return OTA_STATUS_OK;
}

/* Write firmware to the pending bank.
 *
 * In real firmware:
 *   1. Erase flash sector by sector
 *   2. Write each sector
 *   3. Verify written data
 *
 * Here we simulate by copying to memory.
 */
int ota_dualbank_write(OTA_DualBank *bank,
                       const OTA_FirmwareImage *image) {
    if (!bank || !image || !image->payload) {
        return OTA_STATUS_ERR_FLASH;
    }

    /* Verify pending bank has enough space */
    if (image->payload_size > bank->bank_size[bank->pending_bank]) {
        return OTA_STATUS_ERR_SIZE;
    }

    bank->update_in_progress = true;

    /* Erase pending bank (simulated by memset) */
    memset(bank->bank[bank->pending_bank], 0xFF,
           bank->bank_size[bank->pending_bank]);

    /* Write firmware header */
    memcpy(bank->bank[bank->pending_bank], &image->header,
           sizeof(OTA_FirmwareHeader));

    /* Write firmware payload */
    memcpy(bank->bank[bank->pending_bank] + sizeof(OTA_FirmwareHeader),
           image->payload, image->payload_size);

    /* Write signature after payload */
    size_t sig_offset = sizeof(OTA_FirmwareHeader) + image->payload_size;
    memcpy(bank->bank[bank->pending_bank] + sig_offset,
           image->signature, OTA_SIGNATURE_SIZE);

    bank->update_in_progress = false;
    return OTA_STATUS_OK;
}

/* Verify firmware on pending bank before activation.
 *
 * Verification steps:
 *   1. Check magic number
 *   2. Verify CRC32 checksum
 *   3. Verify SHA256 hash
 *   4. Verify RSA/ECDSA signature
 */
bool ota_dualbank_verify(OTA_DualBank *bank,
                         const OTA_FirmwareImage *image) {
    if (!bank || !image) {
        return false;
    }

    /* Step 1: Verify magic number */
    if (image->header.magic != OTA_MAGIC_NUMBER) {
        return false;
    }

    /* Step 2: Verify CRC32 checksum */
    OTA_CRC32Context crc_ctx;
    ota_crc32_init(&crc_ctx);
    uint32_t computed_crc = ota_crc32_calculate(&crc_ctx,
                                                 image->payload,
                                                 image->payload_size);
    if (computed_crc != image->header.checksum) {
        return false;
    }

    /* Step 3: Verify SHA256 hash */
    OTA_SHA256Context sha_ctx;
    ota_sha256_init(&sha_ctx);
    ota_sha256_update(&sha_ctx, image->payload, image->payload_size);
    uint8_t computed_hash[OTA_SHA256_SIZE];
    ota_sha256_final(&sha_ctx, computed_hash);
    if (memcmp(computed_hash, image->header.sha256_hash, OTA_SHA256_SIZE) != 0) {
        return false;
    }

    /* Step 4: Verify RSA/ECDSA signature */
    /* Note: In real implementation, use a proper signature verifier */
    (void)bank;
    return true;
}

/* Activate the pending bank (switch to new firmware).
 *
 * This simulates setting a boot flag that tells the bootloader
 * which bank to boot from on next reset.
 */
int ota_dualbank_activate(OTA_DualBank *bank) {
    if (!bank) {
        return OTA_STATUS_ERR_FLASH;
    }

    /* Save current active bank for potential rollback */
    uint32_t previous_bank = bank->active_bank;

    /* Switch to pending bank */
    bank->active_bank = bank->pending_bank;
    bank->reboot_requested = true;

    /* In real hardware, this would set a "safe boot" flag in RTC registers
     * or a special partition to indicate the update was successful */

    return (int)previous_bank;
}

/* Rollback to the previous bank.
 *
 * Called when:
 *   - New firmware fails to boot
 *   - Critical error detected after update
 *   - User requests rollback via OTA protocol
 */
int ota_dualbank_rollback(OTA_DualBank *bank) {
    if (!bank) {
        return OTA_STATUS_ERR_ROLLBACK;
    }

    /* Switch back to the previous bank */
    bank->active_bank = (bank->active_bank == OTA_BANK_A) ? OTA_BANK_B : OTA_BANK_A;
    bank->rollback_requested = true;

    return OTA_STATUS_OK;
}

/* Get the currently active bank */
uint32_t ota_dualbank_get_active(const OTA_DualBank *bank) {
    if (!bank) {
        return OTA_BANK_A;
    }
    return bank->active_bank;
}
