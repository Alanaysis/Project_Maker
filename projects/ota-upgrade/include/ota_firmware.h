#ifndef OTA_FIRMWARE_H
#define OTA_FIRMWARE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/*
 * ============================================================
 *  OTA Firmware Upgrade System Header
 *  ============================================================
 *
 *  This header defines the core types and interfaces for the
 *  OTA (Over-The-Air) Firmware Upgrade learning project.
 *
 *  OTA Update Flow:
 *    1. Firmware Check   - Check for available updates
 *    2. Download         - Chunked download of firmware image
 *    3. Verification     - Signature + checksum validation
 *    4. Flash Write      - Dual-bank A/B update mechanism
 *    5. Reboot           - Switch active bank and restart
 *
 *  Key Concepts:
 *    - Firmware Image Format: header + payload + signature
 *    - Chunked Transfer: download firmware in small pieces
 *    - Checksum: CRC32 for integrity, SHA256 for security
 *    - Dual-bank A/B: two partitions, switch on success
 *    - Rollback: revert to old firmware on failure
 *    - Delta Update: binary diff/patch to reduce download size
 * ============================================================
 */

/* ---- Firmware Image Header ---- */

/* Magic number to validate firmware image format */
#define OTA_MAGIC_NUMBER        0x4F544131  /* "OTA1" */

/* Maximum firmware image size: 1 MB for learning purposes */
#define OTA_MAX_FIRMWARE_SIZE   (1024 * 1024)

/* Chunk size for downloaded firmware */
#define OTA_CHUNK_SIZE          256

/* Signature sizes */
#define OTA_RSA_PUB_KEY_SIZE    256
#define OTA_SIGNATURE_SIZE      256

/* Checksum sizes */
#define OTA_CRC32_SIZE          4
#define OTA_SHA256_SIZE         32

/* Firmware status codes */
#define OTA_STATUS_OK           0
#define OTA_STATUS_ERR_MAGIC    -1
#define OTA_STATUS_ERR_CHECKSUM -2
#define OTA_STATUS_ERR_SIG      -3
#define OTA_STATUS_ERR_SIZE     -4
#define OTA_STATUS_ERR_DOWNLOAD -5
#define OTA_STATUS_ERR_FLASH    -6
#define OTA_STATUS_ERR_VERIFY   -7
#define OTA_STATUS_ERR_ROLLBACK -8

/* Bank identifiers for dual-bank A/B update */
typedef enum {
    OTA_BANK_A = 0,   /* Primary firmware partition */
    OTA_BANK_B,       /* Secondary firmware partition */
    OTA_BANK_COUNT
} ota_bank_t;

/* Firmware update states for state machine */
typedef enum {
    OTA_STATE_IDLE = 0,
    OTA_STATE_CHECKING,
    OTA_STATE_DOWNLOADING,
    OTA_STATE_VERIFYING,
    OTA_STATE_FLASHING,
    OTA_STATE_REBOOTING,
    OTA_STATE_ROLLBACK,
    OTA_STATE_COMPLETE,
    OTA_STATE_FAILED
} ota_state_t;

/* Firmware image header structure.
 *
 * Layout of a firmware image on disk/network:
 *   [OTA_FirmwareHeader][Payload Data][Signature]
 *
 * The header contains metadata about the firmware:
 *   - magic: validates the image format
 *   - version: firmware version (major.minor.patch)
 *   - checksum: CRC32 of payload
 *   - sha256_hash: SHA256 of payload (for verification)
 *   - size: payload data size in bytes
 *   - signature_size: RSA/ECDSA signature size
 *   - reserved: padding for alignment
 */
typedef struct {
    uint32_t magic;           /* Magic number: 0x4F544131 ("OTA1") */
    uint32_t version;         /* Firmware version: (major<<16)|(minor<<8)|patch */
    uint32_t checksum;        /* CRC32 checksum of payload data */
    uint8_t  sha256_hash[OTA_SHA256_SIZE];  /* SHA256 hash of payload */
    uint32_t size;            /* Size of payload data in bytes */
    uint32_t signature_size;  /* Size of RSA/ECDSA signature */
    uint8_t  reserved[16];    /* Padding for alignment */
} __attribute__((packed)) OTA_FirmwareHeader;

/* ---- CRC32 Checksum Module ---- */

typedef struct {
    uint32_t crc_table[256];  /* Precomputed CRC32 lookup table */
    bool     table_initialized;
} OTA_CRC32Context;

/* Initialize CRC32 context (call once at startup) */
void ota_crc32_init(OTA_CRC32Context *ctx);

/* Calculate CRC32 checksum of data */
uint32_t ota_crc32_calculate(const OTA_CRC32Context *ctx,
                               const uint8_t *data, size_t len);

/* ---- SHA256 Checksum Module (simplified) ---- */

typedef struct {
    uint32_t state[8];
    uint64_t bit_count;
    uint8_t  buffer[64];
} OTA_SHA256Context;

void ota_sha256_init(OTA_SHA256Context *ctx);
void ota_sha256_update(OTA_SHA256Context *ctx, const uint8_t *data, size_t len);
void ota_sha256_final(OTA_SHA256Context *ctx, uint8_t *hash);

/* ---- Signature Verification (simulated RSA/ECDSA) ---- */

typedef struct {
    uint8_t public_key[OTA_RSA_PUB_KEY_SIZE];
    uint32_t key_size;
    bool     initialized;
} OTA_SignatureVerifier;

/* Initialize the signature verifier with a public key */
void ota_sig_init(OTA_SignatureVerifier *verifier,
                  const uint8_t *public_key, uint32_t key_size);

/* Verify signature of data (simulated for learning purposes) */
bool ota_sig_verify(const OTA_SignatureVerifier *verifier,
                    const uint8_t *data, size_t data_len,
                    const uint8_t *signature);

/* Simulate signing data with a private key (for testing) */
bool ota_sig_sign(const uint8_t *data, size_t data_len,
                  const uint8_t *private_key, uint8_t *signature);

/* ---- Chunked Download Module ---- */

typedef struct {
    uint8_t  buffer[OTA_CHUNK_SIZE];  /* Download chunk buffer */
    size_t   offset;                  /* Current position in chunk */
    size_t   total_downloaded;        /* Total bytes downloaded */
    size_t   total_expected;          /* Expected total size */
    bool     complete;                /* Download complete flag */
    int      error_code;              /* Last error code */
} OTA_DownloadState;

/* Initialize download state */
void ota_download_init(OTA_DownloadState *state, size_t expected_size);

/* Simulate receiving a chunk of firmware data */
int ota_download_chunk(OTA_DownloadState *state,
                       const uint8_t *chunk, size_t chunk_size);

/* Check download progress */
float ota_download_progress(const OTA_DownloadState *state);

/* ---- Firmware Image Builder ---- */

typedef struct {
    OTA_FirmwareHeader header;
    uint8_t *payload;
    size_t payload_size;
    uint8_t signature[OTA_SIGNATURE_SIZE];
    size_t signature_size;
} OTA_FirmwareImage;

/* Create a new firmware image with the given payload */
int ota_image_create(OTA_FirmwareImage *image,
                     uint32_t version,
                     const uint8_t *payload, size_t payload_size,
                     const uint8_t *private_key);

/* Free firmware image resources */
void ota_image_destroy(OTA_FirmwareImage *image);

/* Serialize firmware image to buffer */
int ota_image_serialize(const OTA_FirmwareImage *image,
                        uint8_t *buffer, size_t buffer_size);

/* Deserialize firmware image from buffer */
int ota_image_deserialize(OTA_FirmwareImage *image,
                          const uint8_t *buffer, size_t buffer_size);

/* ---- Dual-bank A/B Update Module ---- */

typedef struct {
    uint8_t *bank[OTA_BANK_COUNT];    /* Bank memory buffers */
    size_t   bank_size[OTA_BANK_COUNT]; /* Bank sizes */
    uint32_t active_bank;             /* Currently active bank (0=A, 1=B) */
    uint32_t pending_bank;            /* Bank with pending update */
    bool     update_in_progress;      /* Update operation in progress */
    bool     reboot_requested;        /* Reboot to switch banks */
    bool     rollback_requested;      /* Rollback to previous bank */
} OTA_DualBank;

/* Initialize dual-bank system with given memory sizes */
int ota_dualbank_init(OTA_DualBank *bank,
                      size_t bank_a_size, size_t bank_b_size);

/* Write firmware to the pending bank */
int ota_dualbank_write(OTA_DualBank *bank,
                       const OTA_FirmwareImage *image);

/* Verify firmware on pending bank before activation */
bool ota_dualbank_verify(OTA_DualBank *bank,
                         const OTA_FirmwareImage *image);

/* Activate the pending bank (switch to new firmware) */
int ota_dualbank_activate(OTA_DualBank *bank);

/* Rollback to the previous bank */
int ota_dualbank_rollback(OTA_DualBank *bank);

/* Get current active bank */
uint32_t ota_dualbank_get_active(const OTA_DualBank *bank);

/* ---- Delta Update Module ---- */

/* Delta header for binary patch format */
typedef struct {
    uint32_t source_version;  /* Version of the original firmware */
    uint32_t target_version;  /* Version after patch application */
    uint32_t patch_size;      /* Size of the patch data */
    uint32_t original_checksum; /* CRC32 of original firmware */
    uint32_t target_checksum;   /* CRC32 of target firmware */
} OTA_DeltaHeader;

/* Apply delta patch to original firmware to create new firmware */
int ota_delta_apply(const uint8_t *original, size_t original_size,
                    const uint8_t *patch, size_t patch_size,
                    uint8_t *target, size_t *target_size);

/* Generate delta patch from two firmware images */
int ota_delta_create(const uint8_t *old_firmware, size_t old_size,
                     const uint8_t *new_firmware, size_t new_size,
                     uint8_t *patch, size_t *patch_size);

/* ---- Bootloader Simulation ---- */

typedef struct {
    uint32_t current_bank;
    uint32_t last_boot_bank;
    uint32_t boot_count;
    bool     secure_boot_enabled;
    uint8_t  boot_signature[OTA_SHA256_SIZE];
    bool     boot_verified;
} OTA_Bootloader;

/* Initialize bootloader */
void ota_bootloader_init(OTA_Bootloader *bl);

/* Simulate boot process with verification */
bool ota_bootloader_boot(OTA_Bootloader *bl,
                         const OTA_DualBank *dualbank);

/* Check if firmware needs update */
bool ota_bootloader_needs_update(const OTA_Bootloader *bl,
                                  uint32_t new_version);

/* ---- OTA State Machine ---- */

typedef struct {
    ota_state_t current_state;
    ota_state_t last_state;
    uint32_t    error_code;
    float       progress;
    uint32_t    start_time;
    uint32_t    end_time;
} OTA_StateMachine;

void ota_state_machine_init(OTA_StateMachine *sm);
void ota_state_machine_set_state(OTA_StateMachine *sm, ota_state_t state);
const char *ota_state_to_string(ota_state_t state);

#endif /* OTA_FIRMWARE_H */
