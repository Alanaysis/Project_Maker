/**
 * ota_image.c - Firmware Image Builder and Serializer
 *
 * The firmware image format is the core data structure for OTA updates.
 * It contains the header, payload, and signature.
 *
 * Firmware Image Layout:
 *   +------------------+-------------------+------------------+
 *   | OTA_FirmwareHeader |    Payload Data   |  RSA Signature   |
 *   |     (64 bytes)     |   (variable size) |   (256 bytes)    |
 *   +------------------+-------------------+------------------+
 *
 * Header fields:
 *   - magic: validates image format (0x4F544131 = "OTA1")
 *   - version: firmware version encoded as (major<<16)|(minor<<8)|patch
 *   - checksum: CRC32 of payload for fast integrity check
 *   - sha256_hash: SHA256 of payload for cryptographic verification
 *   - size: payload size in bytes
 *   - signature_size: RSA/ECDSA signature size
 */

#include "ota_firmware.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* Create a new firmware image with payload, compute checksums and signature */
int ota_image_create(OTA_FirmwareImage *image,
                     uint32_t version,
                     const uint8_t *payload, size_t payload_size,
                     const uint8_t *private_key) {
    if (!image || !payload || !private_key) {
        return OTA_STATUS_ERR_SIZE;
    }

    if (payload_size > OTA_MAX_FIRMWARE_SIZE) {
        return OTA_STATUS_ERR_SIZE;
    }

    /* Zero out the image structure */
    memset(image, 0, sizeof(OTA_FirmwareImage));

    /* Set header fields */
    image->header.magic = OTA_MAGIC_NUMBER;
    image->header.version = version;
    image->header.size = (uint32_t)payload_size;
    image->header.signature_size = OTA_SIGNATURE_SIZE;

    /* Compute CRC32 checksum of payload */
    OTA_CRC32Context crc_ctx;
    ota_crc32_init(&crc_ctx);
    image->header.checksum = ota_crc32_calculate(&crc_ctx, payload, payload_size);

    /* Compute SHA256 hash of payload */
    OTA_SHA256Context sha_ctx;
    ota_sha256_init(&sha_ctx);
    ota_sha256_update(&sha_ctx, payload, payload_size);
    ota_sha256_final(&sha_ctx, image->header.sha256_hash);

    /* Allocate payload buffer */
    image->payload = (uint8_t *)malloc(payload_size);
    if (!image->payload) {
        return OTA_STATUS_ERR_FLASH;
    }
    memcpy(image->payload, payload, payload_size);
    image->payload_size = payload_size;

    /* Sign the payload with private key */
    ota_sig_sign(payload, payload_size, private_key, image->signature);
    image->signature_size = OTA_SIGNATURE_SIZE;

    return OTA_STATUS_OK;
}

/* Free firmware image resources */
void ota_image_destroy(OTA_FirmwareImage *image) {
    if (image && image->payload) {
        free(image->payload);
        image->payload = NULL;
        image->payload_size = 0;
    }
}

/* Serialize firmware image to a contiguous buffer.
 *
 * Output format: [Header][Payload][Signature]
 * This is the format that would be transmitted over the network.
 */
int ota_image_serialize(const OTA_FirmwareImage *image,
                        uint8_t *buffer, size_t buffer_size) {
    if (!image || !buffer) {
        return OTA_STATUS_ERR_FLASH;
    }

    size_t total_size = sizeof(OTA_FirmwareHeader) +
                        image->payload_size +
                        OTA_SIGNATURE_SIZE;

    if (buffer_size < total_size) {
        return OTA_STATUS_ERR_SIZE;
    }

    size_t offset = 0;

    /* Copy header */
    memcpy(buffer + offset, &image->header, sizeof(OTA_FirmwareHeader));
    offset += sizeof(OTA_FirmwareHeader);

    /* Copy payload */
    memcpy(buffer + offset, image->payload, image->payload_size);
    offset += image->payload_size;

    /* Copy signature */
    memcpy(buffer + offset, image->signature, OTA_SIGNATURE_SIZE);
    offset += OTA_SIGNATURE_SIZE;

    return OTA_STATUS_OK;
}

/* Deserialize firmware image from buffer.
 *
 * Input format: [Header][Payload][Signature]
 * This is the format received from the OTA server.
 */
int ota_image_deserialize(OTA_FirmwareImage *image,
                          const uint8_t *buffer, size_t buffer_size) {
    if (!image || !buffer) {
        return OTA_STATUS_ERR_FLASH;
    }

    size_t min_size = sizeof(OTA_FirmwareHeader) + OTA_SIGNATURE_SIZE;
    if (buffer_size < min_size) {
        return OTA_STATUS_ERR_SIZE;
    }

    size_t offset = 0;

    /* Copy header */
    memcpy(&image->header, buffer + offset, sizeof(OTA_FirmwareHeader));
    offset += sizeof(OTA_FirmwareHeader);

    /* Validate magic number */
    if (image->header.magic != OTA_MAGIC_NUMBER) {
        return OTA_STATUS_ERR_MAGIC;
    }

    /* Validate payload size */
    if (image->header.size > OTA_MAX_FIRMWARE_SIZE) {
        return OTA_STATUS_ERR_SIZE;
    }

    /* Allocate and copy payload */
    image->payload = (uint8_t *)malloc(image->header.size);
    if (!image->payload) {
        return OTA_STATUS_ERR_FLASH;
    }
    memcpy(image->payload, buffer + offset, image->header.size);
    image->payload_size = image->header.size;
    offset += image->header.size;

    /* Copy signature */
    memcpy(image->signature, buffer + offset, OTA_SIGNATURE_SIZE);
    image->signature_size = OTA_SIGNATURE_SIZE;

    return OTA_STATUS_OK;
}
