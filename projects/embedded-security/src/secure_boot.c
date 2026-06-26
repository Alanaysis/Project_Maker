/**
 * @file secure_boot.c
 * @brief Secure Boot Implementation
 *
 * Implements a chain-of-trust boot process for embedded systems.
 * Each boot stage verifies the next stage before execution.
 *
 * Boot chain:
 *   ROM Bootstrap (trusted, factory-burned)
 *       -> Secondary Bootloader (verified by ROM)
 *           -> Firmware (verified by bootloader)
 *               -> Application (verified by firmware)
 */

#include "secure_boot.h"
#include "sha256.h"
#include <string.h>
#include <stdio.h>

/* Magic number for firmware validation */
#define FIRMWARE_MAGIC 0x53424F4F  /* "SB OO" */

/* Simplified key verification (educational - not real crypto) */
#define VERIFY_KEY_SIZE 32

/* Root key used for signature verification in this educational implementation */
static const uint8_t default_verify_key[VERIFY_KEY_SIZE] = {
    0xAB, 0xCD, 0xEF, 0x01, 0x23, 0x45, 0x67, 0x89,
    0xAB, 0xCD, 0xEF, 0x01, 0x23, 0x45, 0x67, 0x89,
    0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,
    0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0
};

boot_result_t secure_boot_init(secure_boot_context_t *ctx, const uint8_t *root_key) {
    if (!ctx || !root_key) return BOOT_FAIL_TABLE_CORRUPTED;

    memset(ctx, 0, sizeof(secure_boot_context_t));

    /* Copy root key (root of trust) */
    memcpy(ctx->root_key, root_key, 32);

    /* Initialize boot chain entries */
    ctx->entries[BOOT_STAGE_ROM_BOOTLOADER].stage = BOOT_STAGE_ROM_BOOTLOADER;
    ctx->entries[BOOT_STAGE_ROM_BOOTLOADER].base_address = 0x00000000;
    ctx->entries[BOOT_STAGE_ROM_BOOTLOADER].size = 0x10000;
    ctx->entries[BOOT_STAGE_ROM_BOOTLOADER].verified = true;

    ctx->current_stage = BOOT_STAGE_ROM_BOOTLOADER;
    ctx->last_result = BOOT_SUCCESS;

    return BOOT_SUCCESS;
}

bool verify_firmware_header(const firmware_header_t *header) {
    if (!header) return false;
    /* Check magic number */
    return header->magic == FIRMWARE_MAGIC;
}

void compute_firmware_hash(const uint8_t *data, uint32_t length, uint8_t *hash) {
    sha256_hash(data, length, hash);
}

boot_result_t verify_firmware_hash(const firmware_header_t *header,
                                    const uint8_t *data, uint32_t length) {
    if (!header || !data) return BOOT_FAIL_HASH_MISMATCH;

    uint8_t computed[32];
    compute_firmware_hash(data, length, computed);

    if (sha256_compare(computed, header->hash)) {
        return BOOT_SUCCESS;
    }
    return BOOT_FAIL_HASH_MISMATCH;
}

/* Simplified signature verification for educational purposes */
/* In production, use RSA-2048, ECDSA-P256, or Ed25519 */
boot_result_t verify_firmware_signature(const firmware_header_t *header,
                                         const uint8_t *data, uint32_t length) {
    if (!header || !data) return BOOT_FAIL_SIGNATURE_INVALID;
    if (!header->signature_valid) return BOOT_FAIL_SIGNATURE_INVALID;

    /* Compute hash of firmware */
    uint8_t firmware_hash[32];
    compute_firmware_hash(data, length, firmware_hash);

    /* Simplified verification:
     * In real systems, this would:
     * 1. Decrypt the signature with the public key
     * 2. Compare with computed hash
     * Here we use a simplified check for demonstration */
    uint8_t verify_data[64];
    memcpy(verify_data, firmware_hash, 32);
    memcpy(verify_data + 32, default_verify_key, 32);

    uint8_t verify_hash[32];
    sha256_hash(verify_data, 64, verify_hash);

    /* Check if signature matches (educational simplified check) */
    for (int i = 0; i < 16; i++) {
        if (header->signature[i] != verify_hash[i]) {
            return BOOT_FAIL_SIGNATURE_INVALID;
        }
    }

    return BOOT_SUCCESS;
}

boot_result_t boot_chain_add_entry(secure_boot_context_t *ctx,
                                    boot_stage_t stage,
                                    uint32_t base_address,
                                    uint32_t size,
                                    const uint8_t *expected_hash) {
    if (!ctx || !expected_hash || stage >= BOOT_STAGE_APP) {
        return BOOT_FAIL_TABLE_CORRUPTED;
    }

    ctx->entries[stage].stage = stage;
    ctx->entries[stage].base_address = base_address;
    ctx->entries[stage].size = size;
    memcpy(ctx->entries[stage].expected_hash, expected_hash, 32);
    ctx->entries[stage].verified = false;

    return BOOT_SUCCESS;
}

boot_result_t boot_chain_verify(secure_boot_context_t *ctx) {
    if (!ctx) return BOOT_FAIL_TABLE_CORRUPTED;

    boot_result_t result = BOOT_SUCCESS;

    /* Verify each stage in the boot chain */
    for (int stage = BOOT_STAGE_ROM_BOOTLOADER + 1;
         stage < BOOT_STAGE_APP; stage++) {

        /* ROM bootloader is always trusted */
        if (stage == BOOT_STAGE_ROM_BOOTLOADER) {
            ctx->entries[stage].verified = true;
            continue;
        }

        /* Previous stage must be verified first */
        if (!ctx->entries[stage - 1].verified) {
            result = BOOT_FAIL_CHAIN_BROKEN;
            break;
        }

        /* In a real system, we would:
         * 1. Read the next stage from flash/memory
         * 2. Compute its hash
         * 3. Compare with expected_hash
         * 4. Verify signature if present */

        /* For demonstration, mark as verified if hash is set */
        bool hash_valid = true;
        for (int i = 0; i < 32; i++) {
            if (ctx->entries[stage].expected_hash[i] != 0) {
                hash_valid = false;
                break;
            }
        }

        if (hash_valid) {
            result = BOOT_FAIL_HASH_MISMATCH;
            break;
        }

        ctx->entries[stage].verified = true;
        ctx->current_stage = (boot_stage_t)stage;
    }

    ctx->last_result = result;
    return result;
}

boot_result_t boot_execute_firmware(secure_boot_context_t *ctx,
                                     const uint8_t *firmware_data) {
    if (!ctx || !firmware_data) return BOOT_FAIL_STAGE_UNAUTHORIZED;

    /* Verify firmware before execution */
    boot_result_t result = boot_chain_verify(ctx);
    if (result != BOOT_SUCCESS) {
        return result;
    }

    /* In a real embedded system, this would:
     * 1. Set the program counter to firmware entry point
     * 2. Initialize stack pointer
     * 3. Jump to firmware entry point
     *
     * For simulation, we just confirm the firmware is ready */

    ctx->current_stage = BOOT_STAGE_FIRMWARE;
    ctx->last_result = BOOT_SUCCESS;
    return BOOT_SUCCESS;
}

const char *boot_result_str(boot_result_t result) {
    switch (result) {
        case BOOT_SUCCESS:              return "Boot success";
        case BOOT_FAIL_HASH_MISMATCH:   return "Hash mismatch";
        case BOOT_FAIL_SIGNATURE_INVALID: return "Invalid signature";
        case BOOT_FAIL_STAGE_UNAUTHORIZED: return "Unauthorized stage";
        case BOOT_FAIL_CHAIN_BROKEN:    return "Chain broken";
        case BOOT_FAIL_TABLE_CORRUPTED: return "Table corrupted";
        default:                        return "Unknown";
    }
}
