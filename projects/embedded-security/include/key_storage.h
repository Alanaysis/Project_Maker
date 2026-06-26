/**
 * @file key_storage.h
 * @brief Secure Key Storage Module
 *
 * Provides secure storage for cryptographic keys in embedded systems.
 * Demonstrates hash-based and encrypted key storage schemes.
 *
 * Security concepts:
 * - Key derivation: Deriving keys from master key using KDF
 * - Key encryption: Storing keys encrypted at rest
 * - Hash-based lookup: Efficient key retrieval using hash tables
 */

#ifndef EMBEDDED_SECURITY_KEY_STORAGE_H
#define EMBEDDED_SECURITY_KEY_STORAGE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define MAX_KEY_ENTRIES    32
#define MAX_KEY_NAME_LEN   32
#define MASTER_KEY_SIZE    32
#define KEY_DERIVATION_SIZE 32
#define XOR_BLOCK_SIZE     16

/* Key entry stored in secure storage */
typedef struct {
    char     name[MAX_KEY_NAME_LEN];
    uint8_t  key[32];              /* Encrypted key material */
    uint32_t key_length;
    uint32_t version;              /* Key version for rotation */
    uint32_t created_at;           /* Creation timestamp */
    uint8_t  integrity_hash[32];   /* HMAC of key data for integrity */
    bool     valid;
} key_entry_t;

/* Key storage context */
typedef struct {
    key_entry_t entries[MAX_KEY_ENTRIES];
    uint32_t    count;
    uint8_t     master_key[MASTER_KEY_SIZE];
    bool        master_key_set;
} key_storage_t;

/**
 * Initialize key storage with master key
 * The master key is the root of trust for all stored keys
 * @param storage Key storage context
 * @param master_key 32-byte master key
 * @return true on success
 */
bool key_storage_init(key_storage_t *storage, const uint8_t *master_key);

/**
 * Derive a key from master key using simple KDF
 * In production, use HKDF or PBKDF2
 * @param master_key Master key
 * @param label Key derivation label/context
 * @param label_len Label length
 * @param derived_key Output derived key (32 bytes)
 */
void derive_key(const uint8_t *master_key, const char *label,
                uint32_t label_len, uint8_t *derived_key);

/**
 * Encrypt a key using master key (XOR-based encryption)
 * In production, use AES-CTR or AES-GCM mode
 * @param storage Key storage context
 * @param plaintext Key to encrypt
 * @param plaintext_len Key length
 * @param ciphertext Output encrypted key
 */
void encrypt_key(const key_storage_t *storage, const uint8_t *plaintext,
                 uint32_t plaintext_len, uint8_t *ciphertext);

/**
 * Decrypt a key using master key
 * @param storage Key storage context
 * @param ciphertext Encrypted key
 * @param ciphertext_len Encrypted length
 * @param plaintext Output decrypted key
 */
void decrypt_key(const key_storage_t *storage, const uint8_t *ciphertext,
                 uint32_t ciphertext_len, uint8_t *plaintext);

/**
 * Compute integrity hash for key entry
 * @param data Key data
 * @param data_len Data length
 * @param hash Output hash (32 bytes)
 */
void compute_key_integrity_hash(const uint8_t *data, uint32_t data_len,
                                 uint8_t *hash);

/**
 * Store a key in secure storage
 * Key is encrypted with master key before storage
 * @param storage Key storage context
 * @param name Key name/identifier
 * @param key Key material (up to 32 bytes)
 * @param key_length Key length
 * @param version Key version
 * @return true on success
 */
bool key_storage_store(key_storage_t *storage, const char *name,
                       const uint8_t *key, uint32_t key_length,
                       uint32_t version);

/**
 * Retrieve and decrypt a key from storage
 * @param storage Key storage context
 * @param name Key name/identifier
 * @param key Output decrypted key buffer (must be >= 32 bytes)
 * @return true if key found and decrypted successfully
 */
bool key_storage_retrieve(const key_storage_t *storage, const char *name,
                          uint8_t *key);

/**
 * Delete a key from storage
 * @param storage Key storage context
 * @param name Key name/identifier
 * @return true if key was deleted
 */
bool key_storage_delete(key_storage_t *storage, const char *name);

/**
 * Rotate a key (update to new version)
 * @param storage Key storage context
 * @param name Key name/identifier
 * @param new_key New key material
 * @param new_version New version number
 * @return true on success
 */
bool key_storage_rotate(key_storage_t *storage, const char *name,
                        const uint8_t *new_key, uint32_t new_version);

/**
 * Get key count in storage
 * @param storage Key storage context
 * @return Number of stored keys
 */
uint32_t key_storage_count(const key_storage_t *storage);

/**
 * Clear all keys from storage (secure erase)
 * @param storage Key storage context
 */
void key_storage_clear(key_storage_t *storage);

#endif /* EMBEDDED_SECURITY_KEY_STORAGE_H */
