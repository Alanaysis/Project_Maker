/**
 * @file secure_boot.h
 * @brief Secure Boot Module - Firmware verification and boot chain
 *
 * Secure boot ensures that only authenticated firmware runs on an embedded device.
 * It establishes a chain of trust from the bootloader to the application.
 *
 * Security concepts demonstrated:
 * - Chain of trust: Each boot stage verifies the next
 * - Firmware integrity: SHA-256 hash verification
 * - Code signature verification: RSA-style signature check (simplified)
 */

#ifndef EMBEDDED_SECURITY_SECURE_BOOT_H
#define EMBEDDED_SECURITY_SECURE_BOOT_H

#include <stdint.h>
#include <stdbool.h>

/* Boot stage definitions - each stage verifies the next */
typedef enum {
    BOOT_STAGE_ROM_BOOTLOADER = 0,  /* Trusted ROM code (factory burned) */
    BOOT_STAGE_SECONDARY_BOOT,      /* Secondary bootloader */
    BOOT_STAGE_FIRMWARE,            /* Main application firmware */
    BOOT_STAGE_APP                  /* Application layer */
} boot_stage_t;

/* Boot verification result */
typedef enum {
    BOOT_SUCCESS = 0,
    BOOT_FAIL_HASH_MISMATCH,
    BOOT_FAIL_SIGNATURE_INVALID,
    BOOT_FAIL_STAGE_UNAUTHORIZED,
    BOOT_FAIL_CHAIN_BROKEN,
    BOOT_FAIL_TABLE_CORRUPTED
} boot_result_t;

/* Firmware header stored at the beginning of firmware image */
typedef struct {
    uint32_t magic;              /* Magic number for validation */
    uint32_t version;            /* Firmware version */
    uint32_t firmware_size;      /* Size of firmware in bytes */
    uint8_t  hash[32];          /* SHA-256 hash of firmware */
    uint8_t  signature[64];     /* Simplified RSA-style signature */
    uint32_t signature_valid:1; /* Flag indicating signature validity */
} firmware_header_t;

/* Boot chain entry - represents one stage in the boot chain */
typedef struct {
    boot_stage_t stage;
    uint32_t     base_address;
    uint32_t     size;
    uint8_t      expected_hash[32];
    bool         verified;
} boot_chain_entry_t;

/* Boot chain context */
typedef struct {
    boot_chain_entry_t entries[4];
    uint8_t            root_key[32];  /* Root of trust key */
    uint32_t           current_stage;
    boot_result_t      last_result;
} secure_boot_context_t;

/**
 * Initialize the secure boot context with root key
 * @param ctx Boot context to initialize
 * @param root_key 32-byte root key (root of trust)
 * @return BOOT_SUCCESS on success
 */
boot_result_t secure_boot_init(secure_boot_context_t *ctx, const uint8_t *root_key);

/**
 * Verify firmware header magic and basic structure
 * @param header Pointer to firmware header
 * @return true if header is structurally valid
 */
bool verify_firmware_header(const firmware_header_t *header);

/**
 * Compute SHA-256 hash of firmware data
 * @param data Pointer to firmware data
 * @param length Data length in bytes
 * @param hash Output buffer (32 bytes)
 */
void compute_firmware_hash(const uint8_t *data, uint32_t length, uint8_t *hash);

/**
 * Verify firmware hash against expected value in header
 * @param header Firmware header with expected hash
 * @param data   Firmware data to hash
 * @param length Data length
 * @return BOOT_SUCCESS if hash matches
 */
boot_result_t verify_firmware_hash(const firmware_header_t *header,
                                    const uint8_t *data, uint32_t length);

/**
 * Verify firmware signature using public key (simplified RSA-style)
 * In production, this would use proper RSA/ECC verification
 * @param header Firmware header with signature
 * @param data   Firmware data that was signed
 * @param length Data length
 * @return BOOT_SUCCESS if signature is valid
 */
boot_result_t verify_firmware_signature(const firmware_header_t *header,
                                         const uint8_t *data, uint32_t length);

/**
 * Add a boot chain entry
 * @param ctx Boot context
 * @param stage Boot stage
 * @param base_address Start address
 * @param size Size in bytes
 * @param expected_hash SHA-256 hash of this stage
 * @return BOOT_SUCCESS on success
 */
boot_result_t boot_chain_add_entry(secure_boot_context_t *ctx,
                                    boot_stage_t stage,
                                    uint32_t base_address,
                                    uint32_t size,
                                    const uint8_t *expected_hash);

/**
 * Verify the complete boot chain
 * Each stage verifies the next stage's hash
 * @param ctx Boot context
 * @return BOOT_SUCCESS if entire chain is valid
 */
boot_result_t boot_chain_verify(secure_boot_context_t *ctx);

/**
 * Execute verified firmware (jump to firmware entry point)
 * In real systems, this would set PC to firmware entry point
 * @param ctx Boot context
 * @param firmware_data Pointer to verified firmware
 * @return BOOT_SUCCESS if jump prepared
 */
boot_result_t boot_execute_firmware(secure_boot_context_t *ctx,
                                     const uint8_t *firmware_data);

/**
 * Get human-readable string for boot result
 * @param result Boot result code
 * @return String description
 */
const char *boot_result_str(boot_result_t result);

#endif /* EMBEDDED_SECURITY_SECURE_BOOT_H */
