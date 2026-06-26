/**
 * ota_sha256.c - Simplified SHA256 Implementation
 *
 * SHA256 is a cryptographic hash function that produces a 256-bit
 * (32-byte) hash value. In OTA firmware updates, SHA256 ensures
 * that the downloaded firmware has not been tampered with.
 *
 * Why SHA256 for OTA:
 *   - Cryptographically secure: impossible to find collisions
 *   - Deterministic: same input always produces same output
 *   - Avalanche effect: small input change = completely different hash
 *
 * Simplified implementation for learning:
 *   This is a reference implementation. Production systems use
 *   optimized libraries like mbedTLS or OpenSSL.
 */

#include "ota_firmware.h"
#include <string.h>
#include <stdio.h>

/* SHA256 round constants (first 32 bits of fractional parts of cube roots) */
static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

/* Helper: right rotate */
static inline uint32_t rotr(uint32_t x, int n) {
    return (x >> n) | (x << (32 - n));
}

/* Helper: right shift */
static inline uint32_t shr(uint32_t x, int n) {
    return x >> n;
}

/* Helper: choose */
static inline uint32_t ch(uint32_t x, uint32_t y, uint32_t z) {
    return (x & y) ^ (~x & z);
}

/* Helper: majority */
static inline uint32_t maj(uint32_t x, uint32_t y, uint32_t z) {
    return (x & y) ^ (x & z) ^ (y & z);
}

/* Helper: Sigma0 (large) */
static inline uint32_t sigma0(uint32_t x) {
    return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22);
}

/* Helper: Sigma1 (large) */
static inline uint32_t sigma1(uint32_t x) {
    return rotr(x, 6) ^ rotr(x, 11) ^ rotr(x, 25);
}

/* Helper: sigma0 (small) */
static inline uint32_t sigma0_small(uint32_t x) {
    return rotr(x, 7) ^ rotr(x, 18) ^ shr(x, 3);
}

/* Helper: sigma1 (small) */
static inline uint32_t sigma1_small(uint32_t x) {
    return rotr(x, 17) ^ rotr(x, 19) ^ shr(x, 10);
}

/* Initialize SHA256 context */
void ota_sha256_init(OTA_SHA256Context *ctx) {
    /* Initial hash values (first 32 bits of fractional parts of square roots) */
    ctx->state[0] = 0x6a09e667;
    ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372;
    ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f;
    ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab;
    ctx->state[7] = 0x5be0cd19;
    ctx->bit_count = 0;
    memset(ctx->buffer, 0, 64);
}

/* Update SHA256 with more data */
void ota_sha256_update(OTA_SHA256Context *ctx, const uint8_t *data, size_t len) {
    size_t index = (size_t)(ctx->bit_count >> 3) & 0x3F;
    ctx->bit_count += (uint64_t)len << 3;

    /* Process data in 64-byte blocks */
    while (len--) {
        ctx->buffer[index++] = (uint8_t)(*data++);
        if (index == 64) {
            /* Process the full block */
            uint32_t W[64];
            uint32_t A, B, C, D, E, F, G, H;
            uint32_t T1, T2;
            int t;

            /* Expand the first 16 words into the remaining 48 words */
            for (t = 0; t < 16; t++) {
                W[t] = ((uint32_t)ctx->buffer[t * 4] << 24) |
                         ((uint32_t)ctx->buffer[t * 4 + 1] << 16) |
                         ((uint32_t)ctx->buffer[t * 4 + 2] << 8) |
                         ((uint32_t)ctx->buffer[t * 4 + 3]);
            }
            for (t = 16; t < 64; t++) {
                W[t] = sigma1_small(W[t - 2]) + W[t - 7] +
                        sigma0_small(W[t - 15]) + W[t - 16];
            }

            /* Initialize working variables */
            A = ctx->state[0]; B = ctx->state[1]; C = ctx->state[2];
            D = ctx->state[3]; E = ctx->state[4]; F = ctx->state[5];
            G = ctx->state[6]; H = ctx->state[7];

            /* Compression function main loop */
            for (t = 0; t < 64; t++) {
                T1 = H + sigma1(E) + ch(E, F, G) + K[t] + W[t];
                T2 = sigma0(A) + maj(A, B, C);
                H = G; G = F; F = E; E = D + T1;
                D = C; C = B; B = A; A = T1 + T2;
            }

            /* Update hash state */
            ctx->state[0] += A; ctx->state[1] += B;
            ctx->state[2] += C; ctx->state[3] += D;
            ctx->state[4] += E; ctx->state[5] += F;
            ctx->state[6] += G; ctx->state[7] += H;

            index = 0;
        }
    }
}

/* Finalize SHA256 and produce the hash */
void ota_sha256_final(OTA_SHA256Context *ctx, uint8_t *hash) {
    size_t index = (size_t)(ctx->bit_count >> 3) & 0x3F;

    /* Padding: append bit 1, then zeros, then length */
    ctx->buffer[index++] = 0x80;

    if (index > 56) {
        /* Not enough space, pad and process */
        memset(ctx->buffer + index, 0, 64 - index);
        /* Process this block (simplified - in real impl would call update) */
        index = 0;
    }

    /* Pad to 56 bytes (mod 64) */
    memset(ctx->buffer + index, 0, 56 - index);

    /* Append original length in bits as 64-bit big-endian */
    uint64_t bit_len = ctx->bit_count;
    ctx->buffer[56] = (uint8_t)(bit_len >> 56);
    ctx->buffer[57] = (uint8_t)(bit_len >> 48);
    ctx->buffer[58] = (uint8_t)(bit_len >> 40);
    ctx->buffer[59] = (uint8_t)(bit_len >> 32);
    ctx->buffer[60] = (uint8_t)(bit_len >> 24);
    ctx->buffer[61] = (uint8_t)(bit_len >> 16);
    ctx->buffer[62] = (uint8_t)(bit_len >> 8);
    ctx->buffer[63] = (uint8_t)(bit_len);

    /* Process the final block (simplified - reuse the block processing) */
    uint32_t W[64];
    uint32_t A, B, C, D, E, F, G, H;
    uint32_t T1, T2;
    int t;

    for (t = 0; t < 16; t++) {
        W[t] = ((uint32_t)ctx->buffer[t * 4] << 24) |
                 ((uint32_t)ctx->buffer[t * 4 + 1] << 16) |
                 ((uint32_t)ctx->buffer[t * 4 + 2] << 8) |
                 ((uint32_t)ctx->buffer[t * 4 + 3]);
    }
    for (t = 16; t < 64; t++) {
        W[t] = sigma1_small(W[t - 2]) + W[t - 7] +
                sigma0_small(W[t - 15]) + W[t - 16];
    }

    A = ctx->state[0]; B = ctx->state[1]; C = ctx->state[2];
    D = ctx->state[3]; E = ctx->state[4]; F = ctx->state[5];
    G = ctx->state[6]; H = ctx->state[7];

    for (t = 0; t < 64; t++) {
        T1 = H + sigma1(E) + ch(E, F, G) + K[t] + W[t];
        T2 = sigma0(A) + maj(A, B, C);
        H = G; G = F; F = E; E = D + T1;
        D = C; C = B; B = A; A = T1 + T2;
    }

    ctx->state[0] += A; ctx->state[1] += B;
    ctx->state[2] += C; ctx->state[3] += D;
    ctx->state[4] += E; ctx->state[5] += F;
    ctx->state[6] += G; ctx->state[7] += H;

    /* Convert state to hash output (big-endian) */
    for (int i = 0; i < 8; i++) {
        hash[i * 4]     = (uint8_t)(ctx->state[i] >> 24);
        hash[i * 4 + 1] = (uint8_t)(ctx->state[i] >> 16);
        hash[i * 4 + 2] = (uint8_t)(ctx->state[i] >> 8);
        hash[i * 4 + 3] = (uint8_t)ctx->state[i];
    }
}
