/**
 * @file auth_demo.c
 * @brief Authentication Demo - Demonstrates challenge-response and HMAC
 *
 * This demo shows:
 *   1. Challenge-response authentication flow
 *   2. HMAC message authentication
 *   3. Session management and replay protection
 *   4. Tamper detection
 *
 * Embedded security concept: Authentication
 *   - Challenge-response proves identity without sharing secrets
 *   - HMAC ensures message integrity and authenticity
 *   - Nonces prevent replay attacks
 */

#include <stdio.h>
#include <string.h>
#include "authentication.h"
#include "sha256.h"

/* Shared secret between two devices (would be from key exchange) */
static const uint8_t shared_secret[32] = {
    0xAB, 0xCD, 0xEF, 0x01, 0x23, 0x45, 0x67, 0x89,
    0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,
    0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
    0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00
};

int main(int argc, char *argv[]) {
    (void)argc; (void)argv;

    printf("=== Embedded Security: Authentication Demo ===\n\n");

    /* Part 1: Challenge-Response Authentication */
    printf("[Part 1] Challenge-Response Authentication\n");
    printf("-------------------------------------------\n\n");

    auth_session_t session;

    /* Server generates challenge */
    printf("  [Server] Generating challenge...\n");
    auth_start_session(&session, shared_secret, 32);
    printf("    Challenge: ");
    sha256_print(session.challenge);

    /* Client computes response */
    printf("\n  [Client] Computing HMAC response...\n");
    auth_compute_response(&session, shared_secret, 32);
    printf("    Response: ");
    sha256_print(session.response);

    /* Server verifies response */
    printf("\n  [Server] Verifying response...\n");
    if (auth_verify_response(&session, shared_secret, 32, session.response)) {
        printf("    [PASS] Authentication successful!\n\n");
    } else {
        printf("    [FAIL] Authentication failed!\n\n");
    }

    /* Part 2: Replay Attack Prevention */
    printf("[Part 2] Replay Attack Prevention\n");
    printf("-----------------------------------\n\n");

    /* Generate new challenge (simulates fresh authentication) */
    auth_reset_session(&session);
    auth_start_session(&session, shared_secret, 32);
    auth_compute_response(&session, shared_secret, 32);

    printf("  New challenge:  ");
    sha256_print(session.challenge);

    auth_reset_session(&session);
    auth_start_session(&session, shared_secret, 32);
    auth_compute_response(&session, shared_secret, 32);

    printf("  New response:   ");
    sha256_print(session.response);
    printf("\n  [PASS] Different challenges produce different responses\n\n");

    /* Part 3: HMAC Message Authentication */
    printf("[Part 3] HMAC Message Authentication\n");
    printf("--------------------------------------\n\n");

    /* Message to authenticate */
    const char *message = "Device configuration update v1.2.3";
    uint32_t msg_len = (uint32_t)strlen(message);

    printf("  Message: \"%s\"\n", message);
    printf("  Message length: %u bytes\n\n", msg_len);

    /* Compute HMAC */
    uint8_t hmac_tag[32];
    hmac_context hmac_ctx;
    hmac_init(&hmac_ctx, shared_secret, 32);
    hmac_update(&hmac_ctx, (const uint8_t *)message, msg_len);
    hmac_final(&hmac_ctx, hmac_tag);

    printf("  HMAC tag: ");
    sha256_print(hmac_tag);

    /* Verify HMAC */
    printf("\n  [Server] Verifying HMAC...\n");
    if (verify_hmac(shared_secret, 32,
                    (const uint8_t *)message, msg_len, hmac_tag)) {
        printf("  [PASS] Message integrity verified!\n\n");
    } else {
        printf("  [FAIL] HMAC verification failed!\n\n");
    }

    /* Part 4: Tamper Detection */
    printf("[Part 4] Tamper Detection\n");
    printf("-------------------------\n\n");

    /* Tamper with message */
    char tampered_msg[128];
    strncpy(tampered_msg, message, sizeof(tampered_msg) - 1);
    tampered_msg[sizeof(tampered_msg) - 1] = '\0';
    tampered_msg[10] ^= 0xFF;  /* Flip some bits */

    printf("  Original:  \"%s\"\n", message);
    printf("  Tampered:  \"%s\"\n", tampered_msg);

    /* Verify tampered message */
    printf("\n  [Server] Verifying tampered message...\n");
    if (verify_hmac(shared_secret, 32,
                    (const uint8_t *)tampered_msg, strlen(tampered_msg), hmac_tag)) {
        printf("  [FAIL] Tamper not detected!\n\n");
    } else {
        printf("  [PASS] Tamper detected! HMAC mismatch!\n\n");
    }

    /* Part 5: Session Management */
    printf("[Part 5] Session Management\n");
    printf("---------------------------\n\n");

    /* Multiple authentication rounds */
    printf("  Performing multiple authentication rounds...\n");
    for (int round = 1; round <= 3; round++) {
        auth_reset_session(&session);
        auth_start_session(&session, shared_secret, 32);
        auth_compute_response(&session, shared_secret, 32);

        if (auth_verify_response(&session, shared_secret, 32, session.response)) {
            printf("    Round %d: [PASS] Authentication successful\n", round);
        } else {
            printf("    Round %d: [FAIL] Authentication failed\n", round);
        }
    }

    /* Wrong key verification */
    printf("\n  Testing with wrong key...\n");
    uint8_t wrong_secret[32];
    for (int i = 0; i < 32; i++) {
        wrong_secret[i] = (uint8_t)(shared_secret[i] ^ 0xFF);
    }

    auth_reset_session(&session);
    auth_start_session(&session, shared_secret, 32);
    auth_compute_response(&session, shared_secret, 32);

    if (auth_verify_response(&session, wrong_secret, 32, session.response)) {
        printf("  [FAIL] Wrong key accepted!\n\n");
    } else {
        printf("  [PASS] Wrong key rejected!\n\n");
    }

    printf("=== Authentication Demo Complete ===\n");
    return 0;
}
