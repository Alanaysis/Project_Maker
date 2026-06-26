/**
 * @file key_exchange_demo.c
 * @brief Key Exchange Demo - Demonstrates secure key storage and derivation
 *
 * This demo shows:
 *   1. Creating a master key (root of trust for key storage)
 *   2. Storing and retrieving encrypted keys
 *   3. Deriving session keys from master key
 *   4. Key rotation for security
 *
 * Embedded security concept: Key Management
 *   - Master key never leaves secure storage
 *   - Individual keys are encrypted at rest
 *   - Key rotation limits exposure from compromise
 */

#include <stdio.h>
#include <string.h>
#include "key_storage.h"
#include "sha256.h"

int main(int argc, char *argv[]) {
    (void)argc; (void)argv;

    printf("=== Embedded Security: Key Exchange Demo ===\n\n");

    /* Step 1: Initialize key storage with master key */
    printf("[1] Initializing secure key storage...\n");
    key_storage_t storage;

    /* Master key (in production, from hardware secure element) */
    uint8_t master_key[32] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
        0xF0, 0xEE, 0xDD, 0xCC, 0xBB, 0xAA, 0x99, 0x88,
        0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0x00,
        0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00, 0x11
    };

    if (!key_storage_init(&storage, master_key)) {
        printf("    [FAIL] Failed to initialize key storage\n");
        return 1;
    }
    printf("    Key storage initialized\n\n");

    /* Step 2: Store encryption keys */
    printf("[2] Storing encryption keys...\n");

    /* AES key for device-to-device communication */
    uint8_t aes_key[32] = {
        0xAB, 0xCD, 0xEF, 0x12, 0x34, 0x56, 0x78, 0x9A,
        0xBC, 0xDE, 0xF0, 0x12, 0x34, 0x56, 0x78, 0x9A,
        0xBC, 0xDE, 0xF0, 0x12, 0x34, 0x56, 0x78, 0x9A,
        0xBC, 0xDE, 0xF0, 0x12, 0x34, 0x56, 0x78, 0x9A
    };
    key_storage_store(&storage, "aes_device_key", aes_key, 32, 1);
    printf("    Stored: aes_device_key (v1)\n");

    /* HMAC key for message authentication */
    uint8_t hmac_key[32] = {
        0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
        0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00,
        0x11, 0x11, 0x22, 0x22, 0x33, 0x33, 0x44, 0x44,
        0x55, 0x55, 0x66, 0x66, 0x77, 0x77, 0x88, 0x88
    };
    key_storage_store(&storage, "hmac_auth_key", hmac_key, 32, 1);
    printf("    Stored: hmac_auth_key (v1)\n\n");

    /* Step 3: Retrieve and verify keys */
    printf("[3] Retrieving stored keys...\n");

    uint8_t retrieved_key[32];
    if (key_storage_retrieve(&storage, "aes_device_key", retrieved_key)) {
        printf("    Retrieved aes_device_key: ");
        sha256_print(retrieved_key);
    }

    if (key_storage_retrieve(&storage, "hmac_auth_key", retrieved_key)) {
        printf("    Retrieved hmac_auth_key: ");
        sha256_print(retrieved_key);
    }
    printf("\n");

    /* Step 4: Key derivation demonstration */
    printf("[4] Demonstrating key derivation...\n");

    uint8_t derived_key1[32];
    uint8_t derived_key2[32];

    derive_key(master_key, "session_encryption", 18, derived_key1);
    derive_key(master_key, "session_authentication", 22, derived_key2);

    printf("    Derived encryption key: ");
    sha256_print(derived_key1);
    printf("    Derived auth key: ");
    sha256_print(derived_key2);

    /* Verify derived keys are different */
    if (!sha256_compare(derived_key1, derived_key2)) {
        printf("    [PASS] Different labels produce different keys\n\n");
    }

    /* Step 5: Key rotation */
    printf("[5] Demonstrating key rotation...\n");

    /* Old key version */
    printf("    Key version before rotation: v1\n");

    /* New key */
    uint8_t new_aes_key[32];
    for (int i = 0; i < 32; i++) {
        new_aes_key[i] = (uint8_t)(i ^ 0xFF);
    }

    key_storage_rotate(&storage, "aes_device_key", new_aes_key, 2);
    printf("    Key version after rotation: v2\n\n");

    /* Verify rotated key */
    if (key_storage_retrieve(&storage, "aes_device_key", retrieved_key)) {
        printf("    Rotated key hash: ");
        sha256_print(retrieved_key);
    }
    printf("\n");

    /* Step 6: Key count and storage info */
    printf("[6] Key storage info:\n");
    printf("    Total keys stored: %u\n\n", key_storage_count(&storage));

    /* Step 7: Secure deletion */
    printf("[7] Deleting hmac_auth_key...\n");
    key_storage_delete(&storage, "hmac_auth_key");
    printf("    Keys remaining: %u\n\n", key_storage_count(&storage));

    /* Step 8: Secure wipe */
    printf("[8] Secure wiping all keys...\n");
    key_storage_clear(&storage);
    printf("    Keys remaining: %u\n\n", key_storage_count(&storage));

    printf("=== Key Exchange Demo Complete ===\n");
    return 0;
}
