/**
 * @file test_aes.c
 * @brief Unit tests for AES-128 implementation
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "aes.h"

static int tests_run = 0;
static int tests_passed = 0;

#define TEST(name) do { printf("  TEST: %s... ", #name); tests_run++; } while(0)
#define PASS() do { printf("[PASS]\n"); tests_passed++; } while(0)
#define FAIL(msg) do { printf("[FAIL]: %s\n", msg); } while(0)
#define ASSERT(cond, msg) do { if (!(cond)) { FAIL(msg); return; } } while(0)

void test_encrypt_decrypt_roundtrip(void) {
    TEST(encrypt_decrypt_roundtrip);
    aes_context_t enc_ctx, dec_ctx;

    uint8_t key[16] = {
        0x2B, 0x7E, 0x15, 0x16, 0x28, 0xAE, 0xD2, 0xA6,
        0xAB, 0xF7, 0x15, 0x88, 0x09, 0xCF, 0x4F, 0x3C
    };

    uint8_t plaintext[16] = {
        0x32, 0x43, 0xF6, 0xA8, 0x88, 0x5A, 0x30, 0x8D,
        0x31, 0x31, 0x98, 0xA2, 0xE0, 0x37, 0x07, 0x34
    };

    uint8_t ciphertext[16], decrypted[16];

    aes_encrypt_init(&enc_ctx, key, 16);
    aes_decrypt_init(&dec_ctx, key, 16);

    aes_encrypt_block(&enc_ctx, plaintext, ciphertext);
    aes_decrypt_block(&dec_ctx, ciphertext, decrypted);

    ASSERT(memcmp(decrypted, plaintext, 16) == 0,
           "Decrypted data does not match original plaintext");
    PASS();
}

void test_key_sizes(void) {
    TEST(key_sizes);
    aes_context_t ctx;

    /* AES-128 */
    uint8_t key128[16] = {0};
    ASSERT(aes_encrypt_init(&ctx, key128, 16), "AES-128 key init failed");

    /* AES-192 */
    uint8_t key192[24] = {0};
    ASSERT(aes_encrypt_init(&ctx, key192, 24), "AES-192 key init failed");

    /* AES-256 */
    uint8_t key256[32] = {0};
    ASSERT(aes_encrypt_init(&ctx, key256, 32), "AES-256 key init failed");

    /* Invalid key size */
    uint8_t key_invalid[17] = {0};
    ASSERT(!aes_encrypt_init(&ctx, key_invalid, 17),
           "Invalid key size should be rejected");

    PASS();
}

void test_all_zeros(void) {
    TEST(all_zeros);
    aes_context_t enc_ctx, dec_ctx;

    uint8_t key[16] = {0};
    uint8_t plaintext[16] = {0};
    uint8_t ciphertext[16], decrypted[16];

    aes_encrypt_init(&enc_ctx, key, 16);
    aes_decrypt_init(&dec_ctx, key, 16);

    aes_encrypt_block(&enc_ctx, plaintext, ciphertext);

    /* Ciphertext should not be all zeros (even with zero key and plaintext) */
    ASSERT(memcmp(ciphertext, plaintext, 16) != 0,
           "Zero key + zero plaintext should produce non-zero ciphertext");

    aes_decrypt_block(&dec_ctx, ciphertext, decrypted);
    ASSERT(memcmp(decrypted, plaintext, 16) == 0,
           "Decryption of zero plaintext failed");
    PASS();
}

void test_multiple_blocks(void) {
    TEST(multiple_blocks);
    aes_context_t enc_ctx, dec_ctx;

    uint8_t key[16] = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                        0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10};

    uint8_t plaintext[32];
    uint8_t ciphertext[32], decrypted[32];

    for (int i = 0; i < 32; i++) {
        plaintext[i] = (uint8_t)i;
    }

    aes_encrypt_init(&enc_ctx, key, 16);
    aes_decrypt_init(&dec_ctx, key, 16);

    aes_encrypt_ecb(&enc_ctx, plaintext, ciphertext, 32);
    aes_decrypt_ecb(&dec_ctx, ciphertext, decrypted, 32);

    ASSERT(memcmp(decrypted, plaintext, 32) == 0,
           "Multi-block decryption mismatch");
    PASS();
}

void test_different_keys(void) {
    TEST(different_keys);
    aes_context_t enc_ctx1, enc_ctx2;
    uint8_t ciphertext1[16], ciphertext2[16];

    uint8_t key1[16] = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                         0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10};
    uint8_t key2[16] = {0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
                         0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20};

    uint8_t plaintext[16] = {0x42};

    aes_encrypt_init(&enc_ctx1, key1, 16);
    aes_encrypt_init(&enc_ctx2, key2, 16);

    aes_encrypt_block(&enc_ctx1, plaintext, ciphertext1);
    aes_encrypt_block(&enc_ctx2, plaintext, ciphertext2);

    ASSERT(memcmp(ciphertext1, ciphertext2, 16) != 0,
           "Different keys should produce different ciphertexts");
    PASS();
}

int main(void) {
    printf("=== AES-128 Unit Tests ===\n\n");

    test_encrypt_decrypt_roundtrip();
    test_key_sizes();
    test_all_zeros();
    test_multiple_blocks();
    test_different_keys();

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
