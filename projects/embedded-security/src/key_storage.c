/**
 * @file key_storage.c
 * @brief Secure Key Storage Implementation
 *
 * Provides secure storage for cryptographic keys in embedded systems.
 * Keys are encrypted with a master key before storage.
 *
 * Key storage architecture:
 *   Master Key (root of trust)
 *       -> Key Derivation Function
 *           -> Individual Key Encryption
 *               -> Integrity Hash (detect tampering)
 */

#include "key_storage.h"
#include "sha256.h"
#include <string.h>
#include <stdio.h>

/* Key entry magic for validation */
#define KEY_ENTRY_MAGIC 0x4B455931  /* "KEY1" */

/* Simple XOR-based key encryption (educational - use AES-CTR in production) */
void encrypt_key(const key_storage_t *storage, const uint8_t *plaintext,
                 uint32_t plaintext_len, uint8_t *ciphertext) {
    if (!storage || !storage->master_key_set || !plaintext || !ciphertext) return;

    uint8_t derived_key[32];
    derive_key(storage->master_key, "key_encrypt", 11, derived_key);

    /* XOR encryption with derived key (repeating) */
    for (uint32_t i = 0; i < plaintext_len; i++) {
        ciphertext[i] = plaintext[i] ^ derived_key[i % 32];
    }
}

void decrypt_key(const key_storage_t *storage, const uint8_t *ciphertext,
                 uint32_t ciphertext_len, uint8_t *plaintext) {
    /* XOR decryption is the same as encryption */
    encrypt_key(storage, ciphertext, ciphertext_len, plaintext);
}

void derive_key(const uint8_t *master_key, const char *label,
                uint32_t label_len, uint8_t *derived_key) {
    /* Simple key derivation: SHA-256(master_key || label)
     * In production, use HKDF or PBKDF2 */
    uint8_t input[MASTER_KEY_SIZE + 64];
    memcpy(input, master_key, MASTER_KEY_SIZE);
    memcpy(input + MASTER_KEY_SIZE, label, label_len);

    sha256_hash(input, MASTER_KEY_SIZE + label_len, derived_key);
}

void compute_key_integrity_hash(const uint8_t *data, uint32_t data_len,
                                 uint8_t *hash) {
    sha256_hash(data, data_len, hash);
}

bool key_storage_init(key_storage_t *storage, const uint8_t *master_key) {
    if (!storage || !master_key) return false;

    memset(storage, 0, sizeof(key_storage_t));
    memcpy(storage->master_key, master_key, MASTER_KEY_SIZE);
    storage->master_key_set = true;
    storage->count = 0;

    return true;
}

bool key_storage_store(key_storage_t *storage, const char *name,
                       const uint8_t *key, uint32_t key_length,
                       uint32_t version) {
    if (!storage || !name || !key || !storage->master_key_set) return false;
    if (key_length > 32) return false;
    if (storage->count >= MAX_KEY_ENTRIES) return false;

    /* Find existing entry or allocate new */
    int slot = -1;
    for (int i = 0; i < MAX_KEY_ENTRIES; i++) {
        if (!storage->entries[i].valid) {
            slot = i;
            break;
        }
        if (strcmp(storage->entries[i].name, name) == 0) {
            slot = i;
            break;
        }
    }

    if (slot == -1) return false;

    key_entry_t *entry = &storage->entries[slot];

    /* Store entry */
    strncpy(entry->name, name, MAX_KEY_NAME_LEN - 1);
    entry->name[MAX_KEY_NAME_LEN - 1] = '\0';

    /* Encrypt key before storage */
    uint8_t encrypted_key[32];
    encrypt_key(storage, key, key_length, encrypted_key);
    memcpy(entry->key, encrypted_key, 32);
    entry->key_length = key_length;
    entry->version = version;
    entry->created_at = 0; /* Would use RTC in production */
    entry->valid = true;

    /* Compute integrity hash of encrypted key */
    compute_key_integrity_hash(entry->key, entry->key_length, entry->integrity_hash);

    /* Update count if new entry */
    if (slot >= (int)storage->count) {
        storage->count = slot + 1;
    }

    return true;
}

bool key_storage_retrieve(const key_storage_t *storage, const char *name,
                          uint8_t *key) {
    if (!storage || !name || !key || !storage->master_key_set) return false;

    /* Find entry */
    const key_entry_t *entry = NULL;
    for (int i = 0; i < MAX_KEY_ENTRIES; i++) {
        if (storage->entries[i].valid &&
            strcmp(storage->entries[i].name, name) == 0) {
            entry = &storage->entries[i];
            break;
        }
    }

    if (!entry) return false;

    /* Verify integrity */
    uint8_t computed_hash[32];
    compute_key_integrity_hash(entry->key, entry->key_length, computed_hash);
    if (!sha256_compare(computed_hash, entry->integrity_hash)) {
        fprintf(stderr, "Key integrity check failed for: %s\n", name);
        return false;
    }

    /* Decrypt key */
    decrypt_key(storage, entry->key, entry->key_length, key);

    return true;
}

bool key_storage_delete(key_storage_t *storage, const char *name) {
    if (!storage || !name || !storage->master_key_set) return false;

    for (int i = 0; i < MAX_KEY_ENTRIES; i++) {
        if (storage->entries[i].valid &&
            strcmp(storage->entries[i].name, name) == 0) {
            /* Secure erase: zero out key material */
            memset(&storage->entries[i], 0, sizeof(key_entry_t));
            storage->entries[i].valid = false;
            return true;
        }
    }

    return false;
}

bool key_storage_rotate(key_storage_t *storage, const char *name,
                        const uint8_t *new_key, uint32_t new_version) {
    if (!storage || !name || !new_key || !storage->master_key_set) return false;

    for (int i = 0; i < MAX_KEY_ENTRIES; i++) {
        if (storage->entries[i].valid &&
            strcmp(storage->entries[i].name, name) == 0) {
            /* Store new version */
            return key_storage_store(storage, name, new_key, 32, new_version);
        }
    }

    return false;
}

uint32_t key_storage_count(const key_storage_t *storage) {
    if (!storage) return 0;
    return storage->count;
}

void key_storage_clear(key_storage_t *storage) {
    if (!storage) return;

    /* Secure erase all entries */
    for (int i = 0; i < MAX_KEY_ENTRIES; i++) {
        memset(&storage->entries[i], 0, sizeof(key_entry_t));
        storage->entries[i].valid = false;
    }
    storage->count = 0;
}
