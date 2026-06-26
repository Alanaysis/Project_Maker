/**
 * @file aes.c
 * @brief AES-128 Implementation (Educational)
 *
 * Implements AES block cipher per NIST FIPS 197.
 * AES uses a substitution-permutation network (SPN) structure.
 *
 * AES-128: 10 rounds, 128-bit key, 128-bit block
 * AES-192: 12 rounds, 192-bit key, 128-bit block
 * AES-256: 14 rounds, 256-bit key, 128-bit block
 *
 * Each round consists of:
 *   1. AddRoundKey: XOR state with round key
 *   2. SubBytes: Non-linear substitution using S-box
 *   3. ShiftRows: Cyclic shift of state rows
 *   4. MixColumns: Linear mixing of state columns
 *
 * Last round omits MixColumns.
 */

#include "aes.h"
#include <string.h>

/* AES S-box: 256-entry substitution table */
const uint8_t aes_sbox[256] = {
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16
};

/* Inverse S-box for decryption */
const uint8_t aes_inv_sbox[256] = {
    0x52,0x09,0x6a,0xd5,0x30,0x36,0xa5,0x38,0xbf,0x40,0xa3,0x9e,0x81,0xf3,0xd7,0xfb,
    0x7c,0xe3,0x39,0x82,0x9b,0x2f,0xff,0x87,0x34,0x8e,0x43,0x44,0xc4,0xde,0xe9,0xcb,
    0x54,0x7b,0x94,0x32,0xa6,0xc2,0x23,0x3d,0xee,0x4c,0x95,0x0b,0x42,0xfa,0xc3,0x4e,
    0x08,0x2e,0xa1,0x66,0x28,0xd9,0x24,0xb2,0x76,0x5b,0xa2,0x49,0x6d,0x8b,0xd1,0x25,
    0x72,0xf8,0xf6,0x64,0x86,0x68,0x98,0x16,0xd4,0xa4,0x5c,0xcc,0x5d,0x65,0xb6,0x92,
    0x6c,0x70,0x48,0x50,0xfd,0xed,0xb9,0xda,0x5e,0x15,0x46,0x57,0xa7,0x8d,0x9d,0x84,
    0x90,0xd8,0xab,0x00,0x8c,0xbc,0xd3,0x0a,0xf7,0xe4,0x58,0x05,0xb8,0xb3,0x45,0x06,
    0xd0,0x2c,0x1e,0x8f,0xca,0x3f,0x0f,0x02,0xc1,0xaf,0xbd,0x03,0x01,0x13,0x8a,0x6b,
    0x3a,0x91,0x11,0x41,0x4f,0x67,0xdc,0xea,0x97,0xf2,0xcf,0xce,0xf0,0xb4,0xe6,0x73,
    0x96,0xac,0x74,0x22,0xe7,0xad,0x35,0x85,0xe2,0xf9,0x37,0xe8,0x1c,0x75,0xdf,0x6e,
    0x47,0xf1,0x1a,0x71,0x1d,0x29,0xc5,0x89,0x6f,0xb7,0x62,0x0e,0xaa,0x18,0xbe,0x1b,
    0xfc,0x56,0x3e,0x4b,0xc6,0xd2,0x79,0x20,0x9a,0xdb,0xc0,0xfe,0x78,0xcd,0x5a,0xf4,
    0x1f,0xdd,0xa8,0x33,0x88,0x07,0xc7,0x31,0xb1,0x12,0x10,0x59,0x27,0x80,0xec,0x5f,
    0x60,0x51,0x7f,0xa9,0x19,0xb5,0x4a,0x0d,0x2d,0xe5,0x7a,0x9f,0x93,0xc9,0x9c,0xef,
    0xa0,0xe0,0x3b,0x4d,0xae,0x2a,0xf5,0xb0,0xc8,0xeb,0xbb,0x3c,0x83,0x53,0x99,0x61,
    0x17,0x2b,0x04,0x7e,0xba,0x77,0xd6,0x26,0xe1,0x69,0x14,0x63,0x55,0x21,0x0c,0x7d
};

/* Round constants for key expansion */
const uint8_t aes_rcon[11] = {
    0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36
};

/* AES block cipher state structure helpers */
void aes_bytes_to_state(const uint8_t *bytes, aes_state_t *state) {
    /* AES uses column-major order */
    for (int i = 0; i < 16; i++) {
        state->bytes[i] = bytes[i];
    }
}

void aes_state_to_bytes(const aes_state_t *state, uint8_t *bytes) {
    for (int i = 0; i < 16; i++) {
        bytes[i] = state->bytes[i];
    }
}

void aes_xor_block(const uint8_t *a, const uint8_t *b, uint8_t *result) {
    for (int i = 0; i < AES_BLOCK_SIZE; i++) {
        result[i] = a[i] ^ b[i];
    }
}

/* Galois field (GF(2^8)) multiplication for MixColumns */
static uint8_t gf_mul(uint8_t a, uint8_t b) {
    uint8_t p = 0;
    for (int i = 0; i < 8; i++) {
        if (b & 1) p ^= a;
        uint8_t hi = a & 0x80;
        a = (a << 1) & 0xFF;
        if (hi) a ^= 0x1b;  /* AES irreducible polynomial */
        b >>= 1;
    }
    return p;
}

/* AES key expansion (key schedule) */
static void aes_key_expansion(const uint8_t *key, int key_len,
                               uint32_t *expanded_key, int *rounds) {
    int nk, nr, n;
    if (key_len == 16) { nk = 4; nr = 10; }
    else if (key_len == 24) { nk = 6; nr = 12; }
    else { nk = 8; nr = 14; }
    *rounds = nr;

    /* Copy key into first nk words */
    for (int i = 0; i < nk; i++) {
        expanded_key[i] = ((uint32_t)key[4*i] << 24) |
                          ((uint32_t)key[4*i+1] << 16) |
                          ((uint32_t)key[4*i+2] << 8) |
                          ((uint32_t)key[4*i+3]);
    }

    /* Expand key */
    for (int i = nk; i < 4 * (nr + 1); i++) {
        uint32_t temp = expanded_key[i - 1];

        if (i % nk == 0) {
            /* RotWord: cyclic shift left */
            temp = ((temp << 8) | (temp >> 24)) & 0xFFFFFFFF;
            /* SubWord: S-box substitution */
            temp = ((uint32_t)aes_sbox[(temp >> 24) & 0xFF] << 24) |
                   ((uint32_t)aes_sbox[(temp >> 16) & 0xFF] << 16) |
                   ((uint32_t)aes_sbox[(temp >> 8) & 0xFF] << 8) |
                   ((uint32_t)aes_sbox[temp & 0xFF]);
            /* XOR with round constant */
            temp ^= ((uint32_t)aes_rcon[i / nk] << 24);
        } else if (nk > 6 && i % nk == 4) {
            /* SubWord for AES-256 */
            temp = ((uint32_t)aes_sbox[(temp >> 24) & 0xFF] << 24) |
                   ((uint32_t)aes_sbox[(temp >> 16) & 0xFF] << 16) |
                   ((uint32_t)aes_sbox[(temp >> 8) & 0xFF] << 8) |
                   ((uint32_t)aes_sbox[temp & 0xFF]);
        }

        expanded_key[i] = expanded_key[i - nk] ^ temp;
    }
}

/* AddRoundKey: XOR state with round key */
static void add_round_key(aes_state_t *state, const uint32_t *round_key) {
    for (int col = 0; col < 4; col++) {
        uint32_t rk = round_key[col];
        for (int row = 0; row < 4; row++) {
            int idx = col * 4 + row;
            state->bytes[idx] ^= (uint8_t)((rk >> (24 - row * 8)) & 0xFF);
        }
    }
}

/* SubBytes: Apply S-box substitution */
static void sub_bytes(aes_state_t *state) {
    for (int i = 0; i < 16; i++) {
        state->bytes[i] = aes_sbox[state->bytes[i]];
    }
}

/* ShiftRows: Cyclic row shifts */
static void shift_rows(aes_state_t *state) {
    uint8_t temp[4];

    /* Row 1: shift left by 1 */
    temp[0] = state->bytes[4]; temp[1] = state->bytes[5];
    temp[2] = state->bytes[6]; temp[3] = state->bytes[7];
    state->bytes[4] = temp[1]; state->bytes[5] = temp[2];
    state->bytes[6] = temp[3]; state->bytes[7] = temp[0];

    /* Row 2: shift left by 2 */
    temp[0] = state->bytes[8]; temp[1] = state->bytes[9];
    temp[2] = state->bytes[10]; temp[3] = state->bytes[11];
    state->bytes[8] = temp[2]; state->bytes[9] = temp[3];
    state->bytes[10] = temp[0]; state->bytes[11] = temp[1];

    /* Row 3: shift left by 3 */
    temp[0] = state->bytes[12]; temp[1] = state->bytes[13];
    temp[2] = state->bytes[14]; temp[3] = state->bytes[15];
    state->bytes[12] = temp[3]; state->bytes[13] = temp[0];
    state->bytes[14] = temp[1]; state->bytes[15] = temp[2];
}

/* MixColumns: Linear mixing operation */
static void mix_columns(aes_state_t *state) {
    for (int col = 0; col < 4; col++) {
        uint8_t s0 = state->bytes[col * 4];
        uint8_t s1 = state->bytes[col * 4 + 1];
        uint8_t s2 = state->bytes[col * 4 + 2];
        uint8_t s3 = state->bytes[col * 4 + 3];

        state->bytes[col * 4]     = gf_mul(2, s0) ^ gf_mul(3, s1) ^ s2 ^ s3;
        state->bytes[col * 4 + 1] = s0 ^ gf_mul(2, s1) ^ gf_mul(3, s2) ^ s3;
        state->bytes[col * 4 + 2] = s0 ^ s1 ^ gf_mul(2, s2) ^ gf_mul(3, s3);
        state->bytes[col * 4 + 3] = gf_mul(3, s0) ^ s1 ^ s2 ^ gf_mul(2, s3);
    }
}

/* Inverse operations for decryption */
static void inv_sub_bytes(aes_state_t *state) {
    for (int i = 0; i < 16; i++) {
        state->bytes[i] = aes_inv_sbox[state->bytes[i]];
    }
}

static void inv_shift_rows(aes_state_t *state) {
    uint8_t temp[4];

    /* Row 1: shift right by 1 */
    temp[0] = state->bytes[4]; temp[1] = state->bytes[5];
    temp[2] = state->bytes[6]; temp[3] = state->bytes[7];
    state->bytes[4] = temp[3]; state->bytes[5] = temp[0];
    state->bytes[6] = temp[1]; state->bytes[7] = temp[2];

    /* Row 2: shift right by 2 */
    temp[0] = state->bytes[8]; temp[1] = state->bytes[9];
    temp[2] = state->bytes[10]; temp[3] = state->bytes[11];
    state->bytes[8] = temp[2]; state->bytes[9] = temp[3];
    state->bytes[10] = temp[0]; state->bytes[11] = temp[1];

    /* Row 3: shift right by 3 */
    temp[0] = state->bytes[12]; temp[1] = state->bytes[13];
    temp[2] = state->bytes[14]; temp[3] = state->bytes[15];
    state->bytes[12] = temp[1]; state->bytes[13] = temp[2];
    state->bytes[14] = temp[3]; state->bytes[15] = temp[0];
}

static void inv_mix_columns(aes_state_t *state) {
    for (int col = 0; col < 4; col++) {
        uint8_t s0 = state->bytes[col * 4];
        uint8_t s1 = state->bytes[col * 4 + 1];
        uint8_t s2 = state->bytes[col * 4 + 2];
        uint8_t s3 = state->bytes[col * 4 + 3];

        state->bytes[col * 4]     = gf_mul(14, s0) ^ gf_mul(11, s1) ^ gf_mul(13, s2) ^ gf_mul(9, s3);
        state->bytes[col * 4 + 1] = gf_mul(9, s0) ^ gf_mul(14, s1) ^ gf_mul(11, s2) ^ gf_mul(13, s3);
        state->bytes[col * 4 + 2] = gf_mul(13, s0) ^ gf_mul(9, s1) ^ gf_mul(14, s2) ^ gf_mul(11, s3);
        state->bytes[col * 4 + 3] = gf_mul(11, s0) ^ gf_mul(13, s1) ^ gf_mul(9, s2) ^ gf_mul(14, s3);
    }
}

bool aes_encrypt_init(aes_context_t *ctx, const uint8_t *key, int key_len) {
    if (!ctx || !key) return false;
    if (key_len != 16 && key_len != 24 && key_len != 32) return false;

    memset(ctx, 0, sizeof(aes_context_t));
    aes_key_expansion(key, key_len, ctx->expanded_key, &ctx->rounds);
    return true;
}

bool aes_decrypt_init(aes_context_t *ctx, const uint8_t *key, int key_len) {
    /* Same key expansion for decryption (just use different round order) */
    return aes_encrypt_init(ctx, key, key_len);
}

void aes_encrypt_block(const aes_context_t *ctx,
                       const uint8_t *plaintext,
                       uint8_t *ciphertext) {
    aes_state_t state;
    aes_bytes_to_state(plaintext, &state);

    /* Initial round key addition */
    add_round_key(&state, ctx->expanded_key);

    /* Main rounds (1 to rounds-1) */
    for (int round = 1; round < ctx->rounds; round++) {
        sub_bytes(&state);
        shift_rows(&state);
        mix_columns(&state);
        add_round_key(&state, ctx->expanded_key + 4 * round);
    }

    /* Final round (no MixColumns) */
    sub_bytes(&state);
    shift_rows(&state);
    add_round_key(&state, ctx->expanded_key + 4 * ctx->rounds);

    aes_state_to_bytes(&state, ciphertext);
}

void aes_decrypt_block(const aes_context_t *ctx,
                       const uint8_t *ciphertext,
                       uint8_t *plaintext) {
    aes_state_t state;
    aes_bytes_to_state(ciphertext, &state);

    /* Initial round key addition (last round key first) */
    add_round_key(&state, ctx->expanded_key + 4 * ctx->rounds);

    /* Main rounds in reverse (rounds-1 to 1) */
    for (int round = ctx->rounds - 1; round >= 1; round--) {
        inv_shift_rows(&state);
        inv_sub_bytes(&state);
        add_round_key(&state, ctx->expanded_key + 4 * round);
        inv_mix_columns(&state);
    }

    /* Final round (no InvMixColumns) */
    inv_shift_rows(&state);
    inv_sub_bytes(&state);
    add_round_key(&state, ctx->expanded_key);

    aes_state_to_bytes(&state, plaintext);
}

void aes_encrypt_ecb(const aes_context_t *ctx,
                     const uint8_t *input,
                     uint8_t *output,
                     uint32_t length) {
    if (!ctx || !input || !output || length % AES_BLOCK_SIZE != 0) return;

    for (uint32_t i = 0; i < length; i += AES_BLOCK_SIZE) {
        aes_encrypt_block(ctx, input + i, output + i);
    }
}

void aes_decrypt_ecb(const aes_context_t *ctx,
                     const uint8_t *input,
                     uint8_t *output,
                     uint32_t length) {
    if (!ctx || !input || !output || length % AES_BLOCK_SIZE != 0) return;

    for (uint32_t i = 0; i < length; i += AES_BLOCK_SIZE) {
        aes_decrypt_block(ctx, input + i, output + i);
    }
}

const char *aes_mode_str(int mode) {
    switch (mode) {
        case 0: return "ECB";
        case 1: return "CBC";
        case 2: return "CTR";
        case 3: return "GCM";
        default: return "Unknown";
    }
}
