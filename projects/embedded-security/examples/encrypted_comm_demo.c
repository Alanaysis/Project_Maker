/**
 * @file encrypted_comm_demo.c
 * @brief Encrypted Communication Demo - Demonstrates AES encryption and TLS simulation
 *
 * This demo shows:
 *   1. AES block cipher encryption/decryption
 *   2. AES-128 encryption of messages
 *   3. TLS handshake simulation
 *   4. Encrypted channel communication
 *
 * Embedded security concept: Confidentiality
 *   - AES-128 provides strong encryption
 *   - TLS provides both confidentiality and integrity
 *   - Keys are derived from shared secrets
 */

#include <stdio.h>
#include <string.h>
#include "aes.h"
#include "tls_sim.h"
#include "secure_channel.h"
#include "rng.h"

int main(int argc, char *argv[]) {
    (void)argc; (void)argv;

    printf("=== Embedded Security: Encrypted Communication Demo ===\n\n");

    /* Part 1: AES Encryption Demo */
    printf("[Part 1] AES-128 Encryption Demo\n");
    printf("-----------------------------------\n\n");

    /* Initialize AES with a 128-bit key */
    uint8_t aes_key[16] = {
        0x2B, 0x7E, 0x15, 0x16, 0x28, 0xAE, 0xD2, 0xA6,
        0xAB, 0xF7, 0x15, 0x88, 0x09, 0xCF, 0x4F, 0x3C
    };

    aes_context_t enc_ctx, dec_ctx;
    aes_encrypt_init(&enc_ctx, aes_key, 16);
    aes_decrypt_init(&dec_ctx, aes_key, 16);

    /* Encrypt a message */
    const char *plaintext = "Hello, Embedded Security!";
    uint8_t ciphertext[128];
    uint8_t decrypted[128];

    printf("  Plaintext:  \"%s\"\n", plaintext);
    printf("  Plaintext length: %zu bytes\n\n", strlen(plaintext));

    /* Pad plaintext to 16-byte boundary */
    uint32_t msg_len = (uint32_t)strlen(plaintext);
    uint32_t padded_len = (msg_len + 15) / 16 * 16;

    aes_encrypt_ecb(&enc_ctx, (const uint8_t *)plaintext, ciphertext, padded_len);

    printf("  Ciphertext (hex): ");
    for (uint32_t i = 0; i < padded_len; i++) {
        printf("%02x", ciphertext[i]);
    }
    printf("\n\n");

    /* Decrypt */
    aes_decrypt_ecb(&dec_ctx, ciphertext, decrypted, padded_len);
    decrypted[msg_len] = '\0';

    printf("  Decrypted:  \"%s\"\n", decrypted);

    if (strcmp(plaintext, (char *)decrypted) == 0) {
        printf("  [PASS] Decryption successful!\n\n");
    } else {
        printf("  [FAIL] Decryption mismatch!\n\n");
    }

    /* Part 2: TLS Handshake Simulation */
    printf("[Part 2] TLS Handshake Simulation\n");
    printf("-----------------------------------\n\n");

    tls_context_t tls_ctx;
    memset(&tls_ctx, 0, sizeof(tls_context_t));

    /* Supported cipher suites */
    uint16_t ciphers[] = {
        TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
        TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA,
        TLS_RSA_WITH_AES_128_CBC_SHA
    };

    /* Client generates ClientHello */
    printf("  Client -> ServerHello\n");
    tls_generate_client_hello(&tls_ctx, ciphers, 3);
    printf("    Cipher suites offered: %d\n", tls_ctx.client_hello.num_ciphers);
    for (uint8_t i = 0; i < tls_ctx.client_hello.num_ciphers; i++) {
        printf("      - %s\n", tls_cipher_suite_str(tls_ctx.client_hello.cipher_suites[i]));
    }
    printf("\n");

    /* Server responds with ServerHello */
    printf("  Server -> ClientHello\n");
    tls_process_client_hello(&tls_ctx);
    tls_process_server_hello(&tls_ctx);
    printf("    Selected cipher: %s\n", tls_cipher_suite_str(tls_ctx.cipher_suite));
    printf("    State: %s\n\n", tls_state_str(tls_ctx.state));

    /* Complete handshake */
    printf("  Completing handshake...\n");
    if (tls_handshake_complete(&tls_ctx)) {
        printf("    [PASS] Handshake completed!\n");
        printf("    State: %s\n", tls_state_str(tls_ctx.state));
        printf("    Client write key: ");
        for (int i = 0; i < 16; i++) {
            printf("%02x", tls_ctx.keys.client_write_key[i]);
        }
        printf("\n");
        printf("    Server write key: ");
        for (int i = 0; i < 16; i++) {
            printf("%02x", tls_ctx.keys.server_write_key[i]);
        }
        printf("\n\n");
    }

    /* Part 3: Encrypted Channel Communication */
    printf("[Part 3] Encrypted Channel Communication\n");
    printf("-----------------------------------\n\n");

    channel_manager_t mgr;
    channel_manager_init(&mgr);

    /* Create and open channel */
    uint32_t ch_id;
    secure_channel_t *ch = channel_create(&mgr, &ch_id);
    if (ch) {
        printf("  Channel created: ID=%u\n", ch_id);

        if (channel_open(ch)) {
            printf("  [PASS] Channel opened\n\n");

            /* Send encrypted message */
            const char *msg = "Secure message for embedded device!";
            uint32_t sent = channel_send(ch, (const uint8_t *)msg, (uint32_t)strlen(msg));
            printf("  Sent: %u bytes\n", sent);

            /* Set up receive buffer for demo */
            memcpy(ch->rx_buffer, (const uint8_t *)msg, strlen(msg));
            ch->rx_len = (uint32_t)strlen(msg);

            /* Receive and decrypt */
            uint8_t recv_buf[256];
            uint32_t received = channel_receive(ch, recv_buf, sizeof(recv_buf));
            recv_buf[received] = '\0';

            printf("  Received: \"%s\"\n", (char *)recv_buf);

            if (strcmp((char *)recv_buf, msg) == 0) {
                printf("  [PASS] Message received correctly!\n\n");
            }
        }

        channel_close(ch);
        channel_destroy(&mgr, ch_id);
    }

    printf("\n=== Encrypted Communication Demo Complete ===\n");
    return 0;
}
