/**
 * test_firmware_image.c - Firmware Image Unit Tests
 *
 * Tests for firmware image creation, serialization, and deserialization.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ota_firmware.h"

static int tests_run = 0;
static int tests_passed = 0;

#define TEST(name) do { \
    printf("  TEST: %s ... ", #name); \
    tests_run++; \
    if (test_##name()) { \
        tests_passed++; \
        printf("PASS\n"); \
    } else { \
        printf("FAIL\n"); \
    } \
} while(0)

static const uint8_t private_key[32] = {
    0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE,
    0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,
    0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
    0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00
};

/* Test firmware image creation */
static int test_image_create(void) {
    OTA_FirmwareImage image;
    uint8_t payload[] = "Hello OTA World!";
    int ret = ota_image_create(&image, 0x010203, payload, sizeof(payload) - 1, private_key);
    return ret == OTA_STATUS_OK && image.header.magic == OTA_MAGIC_NUMBER
           && image.payload_size == sizeof(payload) - 1;
}

/* Test firmware image magic number */
static int test_image_magic(void) {
    OTA_FirmwareImage image;
    uint8_t payload[] = "test";
    ota_image_create(&image, 0x010000, payload, 4, private_key);
    return image.header.magic == OTA_MAGIC_NUMBER;
}

/* Test firmware image version encoding */
static int test_image_version(void) {
    OTA_FirmwareImage image;
    uint8_t payload[] = "test";
    ota_image_create(&image, 0x020304, payload, 4, private_key);
    return image.header.version == 0x020304;
}

/* Test firmware image CRC32 */
static int test_image_crc32(void) {
    OTA_FirmwareImage image;
    uint8_t payload[64];
    for (int i = 0; i < 64; i++) payload[i] = (uint8_t)i;
    ota_image_create(&image, 0x010000, payload, 64, private_key);
    /* Verify CRC32 is correct */
    OTA_CRC32Context ctx;
    ota_crc32_init(&ctx);
    uint32_t computed = ota_crc32_calculate(&ctx, image.payload, image.payload_size);
    return computed == image.header.checksum;
}

/* Test firmware image SHA256 */
static int test_image_sha256(void) {
    OTA_FirmwareImage image;
    uint8_t payload[] = "SHA256 test data";
    ota_image_create(&image, 0x010000, payload, sizeof(payload) - 1, private_key);
    /* Verify SHA256 is correct */
    OTA_SHA256Context ctx;
    ota_sha256_init(&ctx);
    ota_sha256_update(&ctx, image.payload, image.payload_size);
    uint8_t computed[OTA_SHA256_SIZE];
    ota_sha256_final(&ctx, computed);
    return memcmp(computed, image.header.sha256_hash, OTA_SHA256_SIZE) == 0;
}

/* Test firmware image serialization */
static int test_image_serialize(void) {
    OTA_FirmwareImage image;
    uint8_t payload[] = "Serialize test";
    ota_image_create(&image, 0x010000, payload, sizeof(payload) - 1, private_key);
    uint8_t buffer[2048];
    int ret = ota_image_serialize(&image, buffer, sizeof(buffer));
    return ret == OTA_STATUS_OK && buffer[0] != 0;
}

/* Test firmware image deserialization */
static int test_image_deserialize(void) {
    OTA_FirmwareImage image1, image2;
    uint8_t payload[] = "Deserialize test data";
    ota_image_create(&image1, 0x010000, payload, sizeof(payload) - 1, private_key);

    uint8_t buffer[2048];
    ota_image_serialize(&image1, buffer, sizeof(buffer));
    int ret = ota_image_deserialize(&image2, buffer, sizeof(buffer));

    int ok = (ret == OTA_STATUS_OK && image2.header.magic == OTA_MAGIC_NUMBER
              && image2.payload_size == image1.payload_size
              && memcmp(image2.payload, image1.payload, image1.payload_size) == 0);

    ota_image_destroy(&image2);
    return ok;
}

/* Test firmware image too large */
static int test_image_too_large(void) {
    OTA_FirmwareImage image;
    uint8_t *payload = (uint8_t *)malloc(OTA_MAX_FIRMWARE_SIZE + 1);
    int ret = ota_image_create(&image, 0x010000, payload,
                               OTA_MAX_FIRMWARE_SIZE + 1, private_key);
    free(payload);
    return ret == OTA_STATUS_ERR_SIZE;
}

/* Test firmware image null handling */
static int test_image_null(void) {
    OTA_FirmwareImage image;
    uint8_t payload[] = "test";
    int ret = ota_image_create(NULL, 0x010000, payload, 4, private_key);
    return ret != OTA_STATUS_OK;
}

/* Test firmware image destroy */
static int test_image_destroy(void) {
    OTA_FirmwareImage image;
    uint8_t payload[] = "destroy test";
    ota_image_create(&image, 0x010000, payload, sizeof(payload) - 1, private_key);
    ota_image_destroy(&image);
    return image.payload == NULL;
}

/* Test firmware image signature */
static int test_image_signature(void) {
    OTA_FirmwareImage image;
    uint8_t payload[] = "signature test";
    ota_image_create(&image, 0x010000, payload, sizeof(payload) - 1, private_key);
    return image.signature_size == OTA_SIGNATURE_SIZE;
}

int main(void) {
    printf("============================================================\n");
    printf("  Firmware Image Unit Tests\n");
    printf("============================================================\n\n");

    TEST(image_create);
    TEST(image_magic);
    TEST(image_version);
    TEST(image_crc32);
    TEST(image_sha256);
    TEST(image_serialize);
    TEST(image_deserialize);
    TEST(image_too_large);
    TEST(image_null);
    TEST(image_destroy);
    TEST(image_signature);

    printf("\n============================================================\n");
    printf("  Results: %d/%d tests passed\n", tests_passed, tests_run);
    printf("============================================================\n");

    return (tests_passed == tests_run) ? 0 : 1;
}
