/**
 * example_firmware_verify.c - Firmware Verification Demo
 *
 * This example demonstrates different verification methods used in OTA:
 *   1. CRC32 checksum: fast integrity check
 *   2. SHA256 hash: cryptographic integrity verification
 *   3. RSA/ECDSA signature: authenticity verification
 *   4. Combined verification: all checks together
 *
 * Learning objectives:
 *   - Understand why multiple verification layers exist
 *   - See the performance vs security tradeoff
 *   - Verify tampered firmware is detected
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ota_firmware.h"

static const uint8_t private_key[32] = {
    0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE,
    0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,
    0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
    0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00
};

/* Hex dump helper */
static void hex_dump(const char *label, const uint8_t *data, size_t len) {
    printf("  %s:", label);
    for (size_t i = 0; i < len && i < 16; i++) {
        printf(" %02X", data[i]);
    }
    if (len > 16) printf(" ...");
    printf("\n");
}

int main(void) {
    printf("============================================================\n");
    printf("  Firmware Verification Demo\n");
    printf("============================================================\n\n");

    /* Create test firmware */
    uint8_t payload[512];
    for (int i = 0; i < 512; i++) payload[i] = (uint8_t)(i * 3 + 17);

    OTA_FirmwareImage image;
    ota_image_create(&image, 0x020000, payload, 512, private_key);

    printf("Original firmware:\n");
    printf("  Version: %d.%d.%d\n",
           (image.header.version >> 16) & 0xFF,
           (image.header.version >> 8) & 0xFF,
            image.header.version & 0xFF);
    printf("  CRC32: 0x%08X\n", image.header.checksum);
    hex_dump("  SHA256", image.header.sha256_hash, 8);

    /* Generate public key */
    uint8_t public_key[256];
    for (int i = 0; i < 256; i++) {
        public_key[i] = (uint8_t)(private_key[i % 32] * 37 + i * 23 + 1);
    }

    /* === Test 1: CRC32 Verification === */
    printf("\n--- Test 1: CRC32 Verification ---\n");
    OTA_CRC32Context crc_ctx;
    ota_crc32_init(&crc_ctx);
    uint32_t crc = ota_crc32_calculate(&crc_ctx, image.payload, image.payload_size);
    printf("  Computed CRC32: 0x%08X\n", crc);
    printf("  Stored CRC32:   0x%08X\n", image.header.checksum);
    printf("  Match: %s\n", crc == image.header.checksum ? "YES" : "NO");

    /* === Test 2: SHA256 Verification === */
    printf("\n--- Test 2: SHA256 Verification ---\n");
    OTA_SHA256Context sha_ctx;
    ota_sha256_init(&sha_ctx);
    ota_sha256_update(&sha_ctx, image.payload, image.payload_size);
    uint8_t computed_hash[OTA_SHA256_SIZE];
    ota_sha256_final(&sha_ctx, computed_hash);
    printf("  Computed SHA256: ");
    for (int i = 0; i < 8; i++) printf("%02X", computed_hash[i]);
    printf("...\n");
    printf("  Stored SHA256:   ");
    for (int i = 0; i < 8; i++) printf("%02X", image.header.sha256_hash[i]);
    printf("...\n");
    printf("  Match: %s\n",
           memcmp(computed_hash, image.header.sha256_hash, OTA_SHA256_SIZE) == 0
           ? "YES" : "NO");

    /* === Test 3: Signature Verification === */
    printf("\n--- Test 3: Signature Verification ---\n");
    OTA_SignatureVerifier verifier;
    ota_sig_init(&verifier, public_key, 256);
    bool sig_ok = ota_sig_verify(&verifier, image.payload,
                                  image.payload_size, image.signature);
    printf("  Signature valid: %s\n", sig_ok ? "YES" : "NO");

    /* === Test 4: Tampered Data Detection === */
    printf("\n--- Test 4: Tampered Data Detection ---\n");
    uint8_t tampered_payload[512];
    memcpy(tampered_payload, image.payload, 512);
    tampered_payload[100] ^= 0xFF;  /* Flip bits in the middle */

    uint32_t tampered_crc = ota_crc32_calculate(&crc_ctx,
                                                  tampered_payload, 512);
    printf("  Original CRC32:  0x%08X\n", image.header.checksum);
    printf("  Tampered CRC32:  0x%08X\n", tampered_crc);
    printf("  CRC32 detects tampering: %s\n",
           tampered_crc != image.header.checksum ? "YES" : "NO");

    OTA_SHA256Context sha2;
    ota_sha256_init(&sha2);
    ota_sha256_update(&sha2, tampered_payload, 512);
    uint8_t tampered_hash[OTA_SHA256_SIZE];
    ota_sha256_final(&sha2, tampered_hash);
    int hash_diff = memcmp(tampered_hash, image.header.sha256_hash, OTA_SHA256_SIZE);
    printf("  SHA256 detects tampering: %s\n",
           hash_diff != 0 ? "YES" : "NO");
    printf("  (Avalanche effect: even 1-bit change = completely different hash)\n");

    /* === Test 5: Invalid Signature Detection === */
    printf("\n--- Test 5: Invalid Signature Detection ---\n");
    /* Create a fake signature */
    uint8_t fake_sig[OTA_SIGNATURE_SIZE];
    memset(fake_sig, 0xAA, OTA_SIGNATURE_SIZE);
    bool fake_ok = ota_sig_verify(&verifier, image.payload,
                                   image.payload_size, fake_sig);
    printf("  Fake signature accepted: %s\n", fake_ok ? "YES (BAD!)" : "NO (GOOD!)");

    printf("\n============================================================\n");
    printf("  Verification Summary\n");
    printf("============================================================\n");
    printf("  CRC32  - Fast integrity check (detects accidental corruption)\n");
    printf("  SHA256 - Cryptographic integrity (detects intentional tampering)\n");
    printf("  RSA    - Authenticity (verifies firmware comes from trusted source)\n");
    printf("  All three together = secure OTA update\n");
    printf("============================================================\n");

    ota_image_destroy(&image);
    return 0;
}
