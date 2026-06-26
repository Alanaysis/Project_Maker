/**
 * ota_download.c - Chunked Firmware Download Module
 *
 * In real OTA systems, firmware is downloaded over HTTP/HTTPS in chunks.
 * This module simulates chunked transfer for learning purposes.
 *
 * Why chunked download?
 *   - Large firmware images (MBs) can't be loaded into memory at once
 *   - Chunks allow progress tracking and resume capability
 *   - Each chunk can be verified before continuing
 *   - Memory-constrained devices benefit from small buffers
 *
 * Download flow:
 *   1. Receive download URL and expected size
 *   2. Request chunks sequentially
 *   3. Verify each chunk's integrity
 *   4. Combine chunks into complete firmware image
 *   5. Verify final image integrity
 */

#include "ota_firmware.h"
#include <string.h>
#include <stdio.h>

/* Initialize download state */
void ota_download_init(OTA_DownloadState *state, size_t expected_size) {
    memset(state, 0, sizeof(OTA_DownloadState));
    state->total_expected = expected_size;
    state->complete = false;
    state->error_code = OTA_STATUS_OK;
}

/* Simulate receiving a chunk of firmware data.
 *
 * In a real OTA system, this would:
 *   1. Make an HTTP range request: Range: bytes=start-end
 *   2. Receive the chunk data from the server
 *   3. Verify chunk integrity (optional HMAC per chunk)
 *   4. Write to flash memory at the correct offset
 *
 * Here we simulate by copying data into our buffer.
 */
int ota_download_chunk(OTA_DownloadState *state,
                       const uint8_t *chunk, size_t chunk_size) {
    if (!state || !chunk) {
        return OTA_STATUS_ERR_DOWNLOAD;
    }

    /* Check if download is already complete */
    if (state->complete) {
        return OTA_STATUS_OK;
    }

    /* Check if this chunk would exceed expected size */
    if (state->total_downloaded + chunk_size > state->total_expected) {
        state->error_code = OTA_STATUS_ERR_SIZE;
        return OTA_STATUS_ERR_SIZE;
    }

    /* Simulate writing chunk to buffer at current offset */
    memcpy(state->buffer + state->offset, chunk, chunk_size);
    state->offset += chunk_size;
    state->total_downloaded += chunk_size;

    /* Check if download is complete */
    if (state->total_downloaded >= state->total_expected) {
        state->complete = true;
    }

    return OTA_STATUS_OK;
}

/* Get download progress as a percentage (0.0 to 1.0) */
float ota_download_progress(const OTA_DownloadState *state) {
    if (!state || state->total_expected == 0) {
        return 0.0f;
    }
    return (float)state->total_downloaded / (float)state->total_expected;
}
