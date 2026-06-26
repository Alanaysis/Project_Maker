/**
 * @file test_key_storage.c
 * @brief Unit tests for key storage module
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "key_storage.h"
#include "sha256.h"

static int tests_run = 0;
static int tests_passed = 0;

#define TEST(name) do { printf("  TEST: %s... ", #name); tests_run++; } while(0)
#define PASS() do { printf("[PASS]\n"); tests_passed++; } while(0)
#define FAIL(msg) do { printf("[FAIL]: %s\n", msg); } while(0)
#define ASSERT(cond, msg) do { if (!(cond)) { FAIL(msg); return; } } while(0)

void test_store_and_retrieve(void) {
    TEST(store_and_retrieve);
    key_storage_t storage;
    uint8_t master_key[32] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
                                0xF0, 0xEE, 0xDD, 0xCC, 0xBB, 0xAA, 0x99, 0x88,
                                0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0x00,
                                0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00, 0x11};

    key_storage_init(&storage, master_key);

    uint8_t test_key[32] = {0xAB, 0xCD, 0xEF, 0x12, 0x34, 0x56, 0x78, 0x9A,
                              0xBC, 0xDE, 0xF0, 0x12, 0x34, 0x56, 0x78, 0x9A,
                              0xBC, 0xDE, 0xF0, 0x12, 0x34, 0x56, 0x78, 0x9A,
                              0xBC, 0xDE, 0xF0, 0x12, 0x34, 0x56, 0x78, 0x9A};

    ASSERT(key_storage_store(&storage, "test_key", test_key, 32, 1),
           "Key store should succeed");

    uint8_t retrieved[32];
    ASSERT(key_storage_retrieve(&storage, "test_key", retrieved),
           "Key retrieve should succeed");

    ASSERT(memcmp(retrieved, test_key, 32) == 0,
           "Retrieved key should match stored key");
    PASS();
}

void test_key_not_found(void) {
    TEST(key_not_found);
    key_storage_t storage;
    uint8_t master_key[32] = {0x01};

    key_storage_init(&storage, master_key);

    uint8_t retrieved[32];
    ASSERT(!key_storage_retrieve(&storage, "nonexistent", retrieved),
           "Nonexistent key should not be retrieved");
    PASS();
}

void test_key_delete(void) {
    TEST(key_delete);
    key_storage_t storage;
    uint8_t master_key[32] = {0x02};

    key_storage_init(&storage, master_key);

    uint8_t test_key[32] = {0x42};
    key_storage_store(&storage, "del_key", test_key, 1, 1);

    ASSERT(key_storage_delete(&storage, "del_key"),
           "Key delete should succeed");

    uint8_t retrieved[32];
    ASSERT(!key_storage_retrieve(&storage, "del_key", retrieved),
           "Deleted key should not be retrieved");
    PASS();
}

void test_key_rotation(void) {
    TEST(key_rotation);
    key_storage_t storage;
    uint8_t master_key[32] = {0x03};

    key_storage_init(&storage, master_key);

    uint8_t old_key[32] = {0x11};
    uint8_t new_key[32] = {0x22};

    key_storage_store(&storage, "rot_key", old_key, 1, 1);

    ASSERT(key_storage_rotate(&storage, "rot_key", new_key, 2),
           "Key rotation should succeed");

    uint8_t retrieved[32];
    ASSERT(key_storage_retrieve(&storage, "rot_key", retrieved),
           "Rotated key should be retrievable");

    ASSERT(memcmp(retrieved, new_key, 32) == 0,
           "Retrieved key should match new key after rotation");
    PASS();
}

void test_key_count(void) {
    TEST(key_count);
    key_storage_t storage;
    uint8_t master_key[32] = {0x04};

    key_storage_init(&storage, master_key);

    ASSERT(key_storage_count(&storage) == 0,
           "Initial key count should be 0");

    uint8_t key[32] = {0x42};
    key_storage_store(&storage, "key1", key, 1, 1);
    key_storage_store(&storage, "key2", key, 1, 1);
    key_storage_store(&storage, "key3", key, 1, 1);

    ASSERT(key_storage_count(&storage) >= 3,
           "Key count should be at least 3");
    PASS();
}

void test_secure_clear(void) {
    TEST(secure_clear);
    key_storage_t storage;
    uint8_t master_key[32] = {0x05};

    key_storage_init(&storage, master_key);

    uint8_t key[32] = {0x42};
    key_storage_store(&storage, "clear_key", key, 1, 1);

    ASSERT(key_storage_count(&storage) > 0, "Key should be stored");

    key_storage_clear(&storage);

    ASSERT(key_storage_count(&storage) == 0,
           "Key count should be 0 after clear");
    PASS();
}

void test_init_failure(void) {
    TEST(init_failure);
    key_storage_t storage;

    ASSERT(!key_storage_init(&storage, NULL),
           "Init with NULL master key should fail");
    PASS();
}

int main(void) {
    printf("=== Key Storage Unit Tests ===\n\n");

    test_store_and_retrieve();
    test_key_not_found();
    test_key_delete();
    test_key_rotation();
    test_key_count();
    test_secure_clear();
    test_init_failure();

    printf("\n--- Results ---\n");
    printf("  Passed: %d / %d\n", tests_passed, tests_run);

    if (tests_passed == tests_run) {
        printf("  [ALL TESTS PASSED]\n");
        return 0;
    } else {
        printf("  [SOME TESTS FAILED]\n");
        return 1;
    }
}
