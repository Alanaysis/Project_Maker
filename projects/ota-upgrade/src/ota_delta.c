/**
 * ota_delta.c - Delta Update (Binary Diff/Patch) Module
 *
 * Delta update reduces OTA bandwidth by sending only the differences
 * between the old and new firmware instead of the full new firmware.
 *
 * Why delta updates?
 *   - Firmware images can be 1-10 MB
 *   - Between versions, only small portions change
 *   - A 100-byte patch can update a 1 MB firmware
 *   - Saves bandwidth, time, and device battery
 *
 * Delta update algorithm (simplified bsdiff-like):
 *   1. Find common blocks between old and new firmware
 *   2. Record which blocks to keep, which to delete
 *   3. Record new data to insert
 *   4. Patch = (keep/delete instructions) + (new data)
 *
 * Real-world delta tools:
 *   - bsdiff/bspatch: widely used in Android OTA
 *   - xdelta: another popular binary diff tool
 *   - musl-delta: lightweight delta for embedded
 */

#include "ota_firmware.h"
#include <string.h>
#include <stdio.h>

/*
 * Apply delta patch to original firmware.
 *
 * Patch format (simplified):
 *   [DeltaHeader][CopyCommands][InsertData]
 *
 * CopyCommands format:
 *   Each command: [length: 4 bytes]
 *   Meaning: copy 'length' bytes from original at current position
 *
 * Insert marker: [0xFFFFFFFF: 4 bytes][insert_len: 4 bytes][data...]
 */
int ota_delta_apply(const uint8_t *original, size_t original_size,
                    const uint8_t *patch, size_t patch_size,
                    uint8_t *target, size_t *target_size) {
    if (!original || !patch || !target || !target_size) {
        return OTA_STATUS_ERR_VERIFY;
    }

    /* Parse delta header */
    if (patch_size < sizeof(OTA_DeltaHeader)) {
        return OTA_STATUS_ERR_VERIFY;
    }

    OTA_DeltaHeader *delta = (OTA_DeltaHeader *)patch;

    /* Validate checksums */
    OTA_CRC32Context crc_ctx;
    ota_crc32_init(&crc_ctx);
    uint32_t orig_crc = ota_crc32_calculate(&crc_ctx, original, original_size);
    if (orig_crc != delta->original_checksum) {
        return OTA_STATUS_ERR_VERIFY;
    }

    /* Apply patch */
    size_t orig_pos = 0;
    size_t target_pos = 0;
    size_t cmd_offset = sizeof(OTA_DeltaHeader);

    while (orig_pos < original_size && cmd_offset + 4 <= patch_size) {
        /* Read copy command: [length] */
        uint32_t copy_length = 0;
        memcpy(&copy_length, patch + cmd_offset, 4);
        cmd_offset += 4;

        /* If length is 0xFFFFFFFF, this is insert-only marker */
        if (copy_length == 0xFFFFFFFF) {
            /* Read insert length */
            uint32_t insert_len = 0;
            if (cmd_offset + 4 > patch_size) return OTA_STATUS_ERR_VERIFY;
            memcpy(&insert_len, patch + cmd_offset, 4);
            cmd_offset += 4;

            /* Insert data */
            if (cmd_offset + insert_len > patch_size) return OTA_STATUS_ERR_VERIFY;
            if (target_pos + insert_len > OTA_MAX_FIRMWARE_SIZE) {
                return OTA_STATUS_ERR_SIZE;
            }
            memcpy(target + target_pos, patch + cmd_offset, insert_len);
            target_pos += insert_len;
            cmd_offset += insert_len;
            break;
        }

        /* Copy from original at current position */
        if (orig_pos + copy_length > original_size) {
            return OTA_STATUS_ERR_VERIFY;
        }
        memcpy(target + target_pos, original + orig_pos, copy_length);
        target_pos += copy_length;
        orig_pos += copy_length;
    }

    /* Copy remaining original data */
    if (orig_pos < original_size) {
        size_t remaining = original_size - orig_pos;
        memcpy(target + target_pos, original + orig_pos, remaining);
        target_pos += remaining;
    }

    *target_size = target_pos;
    return OTA_STATUS_OK;
}

/*
 * Generate delta patch from two firmware images.
 *
 * This finds differences between old and new firmware and creates
 * a patch that can transform the old firmware into the new one.
 *
 * Simplified algorithm for learning:
 *   1. Walk through both firmware byte by byte
 *   2. When bytes match: emit copy command (length)
 *   3. When bytes differ: emit insert marker + new byte(s)
 *   4. At end: emit copy for remaining
 */
int ota_delta_create(const uint8_t *old_fw, size_t old_size,
                     const uint8_t *new_fw, size_t new_size,
                     uint8_t *patch, size_t *patch_size) {
    if (!old_fw || !new_fw || !patch || !patch_size) {
        return OTA_STATUS_ERR_VERIFY;
    }

    OTA_DeltaHeader *delta = (OTA_DeltaHeader *)patch;

    /* Compute checksums */
    OTA_CRC32Context crc_ctx;
    ota_crc32_init(&crc_ctx);
    delta->source_version = 0;
    delta->target_version = 0;
    delta->original_checksum = ota_crc32_calculate(&crc_ctx, old_fw, old_size);
    delta->target_checksum = ota_crc32_calculate(&crc_ctx, new_fw, new_size);

    size_t pos = sizeof(OTA_DeltaHeader);
    size_t old_pos = 0;
    size_t new_pos = 0;

    /* Walk through both firmware, find matching and differing regions */
    while (old_pos < old_size && new_pos < new_size) {
        /* Find matching run */
        size_t match_start = old_pos;
        while (old_pos < old_size && new_pos < new_size &&
               old_fw[old_pos] == new_fw[new_pos]) {
            old_pos++;
            new_pos++;
        }
        size_t match_len = old_pos - match_start;

        /* Emit copy command for matching region */
        if (match_len > 0) {
            memcpy(patch + pos, &match_len, 4);
            pos += 4;
        }

        /* Find differing run */
        size_t diff_start = new_pos;
        while (old_pos < old_size && new_pos < new_size &&
               old_fw[old_pos] != new_fw[new_pos]) {
            old_pos++;
            new_pos++;
        }
        size_t diff_len = new_pos - diff_start;

        /* Emit insert marker + new data */
        if (diff_len > 0) {
            uint32_t insert_marker = 0xFFFFFFFF;
            memcpy(patch + pos, &insert_marker, 4);
            pos += 4;
            memcpy(patch + pos, &diff_len, 4);
            pos += 4;
            memcpy(patch + pos, new_fw + diff_start, diff_len);
            pos += diff_len;
        }
    }

    /* Copy remaining old data */
    if (old_pos < old_size) {
        size_t remaining = old_size - old_pos;
        memcpy(patch + pos, &remaining, 4);
        pos += 4;
    }

    *patch_size = pos;
    return OTA_STATUS_OK;
}
