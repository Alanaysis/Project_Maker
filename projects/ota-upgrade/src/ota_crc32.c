/**
 * ota_crc32.c - CRC32 Checksum Implementation
 *
 * CRC32 (Cyclic Redundancy Check) is a widely used checksum algorithm
 * for detecting accidental changes to data. In OTA firmware updates,
 * CRC32 provides fast integrity verification.
 *
 * How CRC32 works:
 *   1. A 32-bit polynomial (0xEDB88320 - reversed form of CRC-32/ISO 3309)
 *      is used as the divisor
 *   2. Data bytes are processed one at a time
 *   3. The remainder after division becomes the checksum
 *
 * In real OTA systems:
 *   - CRC32 is used for quick integrity checks
 *   - SHA256 is used for cryptographic verification
 *   - Both together provide performance + security
 */

#include "ota_firmware.h"
#include <stdio.h>
#include <string.h>

/* CRC-32 polynomial (reversed bit order) */
#define CRC32_POLYNOMIAL  0xEDB88320

/* Initialize the CRC32 lookup table.
 *
 * The lookup table precomputes the CRC32 value for all 256 possible
 * byte values, making the actual checksum calculation much faster.
 * This is called "table-driven" CRC32 implementation.
 */
void ota_crc32_init(OTA_CRC32Context *ctx) {
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t crc = i;
        for (int j = 0; j < 8; j++) {
            if (crc & 1) {
                crc = (crc >> 1) ^ CRC32_POLYNOMIAL;
            } else {
                crc >>= 1;
            }
        }
        ctx->crc_table[i] = crc;
    }
    ctx->table_initialized = true;
}

/* Calculate CRC32 checksum of data.
 *
 * Processing:
 *   1. Start with CRC value 0xFFFFFFFF (initial value)
 *   2. For each byte, XOR with lower byte of CRC, look up table
 *   3. Final CRC is XORed with 0xFFFFFFFF (output reflection)
 *
 * Time complexity: O(n) where n = data length
 * Space complexity: O(1) - table is fixed 256 entries
 */
uint32_t ota_crc32_calculate(const OTA_CRC32Context *ctx,
                              const uint8_t *data, size_t len) {
    if (!ctx->table_initialized) {
        return 0;
    }

    uint32_t crc = 0xFFFFFFFF;

    for (size_t i = 0; i < len; i++) {
        uint8_t index = (uint8_t)(crc ^ data[i]) & 0xFF;
        crc = (crc >> 8) ^ ctx->crc_table[index];
    }

    return crc ^ 0xFFFFFFFF;
}
