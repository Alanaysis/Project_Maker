/**
 * @file secure_channel.c
 * @brief Secure Channel Management Implementation
 *
 * Manages secure communication channels between embedded devices.
 * Provides channel lifecycle management and secure message framing.
 *
 * Channel lifecycle:
 *   1. Create: Allocate channel resources
 *   2. Open: Perform TLS handshake
 *   3. Send/Receive: Encrypted communication
 *   4. Close: Teardown and cleanup
 */

#include "secure_channel.h"
#include <string.h>
#include <stdio.h>

void channel_manager_init(channel_manager_t *mgr) {
    if (!mgr) return;

    memset(mgr, 0, sizeof(channel_manager_t));
    mgr->next_channel_id = 1;
}

secure_channel_t *channel_create(channel_manager_t *mgr, uint32_t *channel_id) {
    if (!mgr) return NULL;

    /* Find free slot */
    for (int i = 0; i < MAX_CHANNELS; i++) {
        if (!mgr->channels[i].active) {
            secure_channel_t *ch = &mgr->channels[i];
            memset(ch, 0, sizeof(secure_channel_t));
            ch->channel_id = mgr->next_channel_id++;
            ch->state = CHANNEL_CLOSED;
            ch->active = true;
            ch->created_at = 0; /* Would use RTC in production */
            ch->last_active = ch->created_at;

            if (channel_id) *channel_id = ch->channel_id;
            return ch;
        }
    }

    return NULL; /* No free slots */
}

bool channel_open(secure_channel_t *ch) {
    if (!ch) return false;

    /* Supported cipher suites (ECDHE-RSA-AES128-GCM-SHA256 preferred) */
    uint16_t ciphers[] = {
        TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
        TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA,
        TLS_RSA_WITH_AES_128_CBC_SHA
    };

    /* Generate client hello */
    tls_generate_client_hello(&ch->tls_ctx, ciphers, 3);

    /* Process server hello (simulated) */
    tls_process_client_hello(&ch->tls_ctx);
    tls_process_server_hello(&ch->tls_ctx);

    /* Complete handshake */
    if (!tls_handshake_complete(&ch->tls_ctx)) {
        ch->state = CHANNEL_ERROR;
        return false;
    }

    ch->state = CHANNEL_OPEN;
    ch->msg_count = 0;
    return true;
}

uint32_t channel_send(secure_channel_t *ch, const uint8_t *data, uint32_t len) {
    if (!ch || ch->state != CHANNEL_OPEN) return 0;
    if (!data || len == 0) return 0;
    if (len > CHANNEL_BUF_SIZE) return 0;

    /* Encrypt data */
    if (ch->tls_ctx.state == TLS_STATE_ESTABLISHED) {
        tls_encrypt(&ch->tls_ctx, data, ch->tx_buffer, len);
    } else {
        /* No encryption (pre-handshake) */
        memcpy(ch->tx_buffer, data, len);
    }

    ch->tx_len = len;
    ch->msg_count++;
    ch->last_active = ch->created_at; /* Would use real timestamp */

    return len;
}

uint32_t channel_receive(secure_channel_t *ch, uint8_t *output, uint32_t max_len) {
    if (!ch || ch->state != CHANNEL_OPEN) return 0;
    if (!output || max_len == 0) return 0;

    /* Decrypt data */
    if (ch->tls_ctx.state == TLS_STATE_ESTABLISHED && ch->rx_len > 0) {
        tls_decrypt(&ch->tls_ctx, ch->rx_buffer, output, ch->rx_len);
    } else {
        memcpy(output, ch->rx_buffer, ch->rx_len);
    }

    ch->msg_count++;
    ch->last_active = ch->created_at; /* Would use real timestamp */

    return ch->rx_len;
}

void channel_close(secure_channel_t *ch) {
    if (!ch) return;

    ch->state = CHANNEL_CLOSING;
    ch->rx_len = 0;
    ch->tx_len = 0;
}

bool channel_destroy(channel_manager_t *mgr, uint32_t channel_id) {
    if (!mgr) return false;

    for (int i = 0; i < MAX_CHANNELS; i++) {
        if (mgr->channels[i].active &&
            mgr->channels[i].channel_id == channel_id) {
            memset(&mgr->channels[i], 0, sizeof(secure_channel_t));
            mgr->channels[i].active = false;
            return true;
        }
    }

    return false;
}

secure_channel_t *channel_get_by_id(channel_manager_t *mgr, uint32_t channel_id) {
    if (!mgr) return NULL;

    for (int i = 0; i < MAX_CHANNELS; i++) {
        if (mgr->channels[i].active &&
            mgr->channels[i].channel_id == channel_id) {
            return &mgr->channels[i];
        }
    }

    return NULL;
}

bool channel_is_valid(secure_channel_t *ch, uint32_t max_idle_ms) {
    if (!ch || !ch->active) return false;
    if (ch->state != CHANNEL_OPEN) return false;

    /* Check idle time (would use real timestamp in production) */
    (void)max_idle_ms;
    return true;
}

uint32_t channel_active_count(channel_manager_t *mgr) {
    if (!mgr) return 0;

    uint32_t count = 0;
    for (int i = 0; i < MAX_CHANNELS; i++) {
        if (mgr->channels[i].active && mgr->channels[i].state == CHANNEL_OPEN) {
            count++;
        }
    }
    return count;
}

void channel_manager_reset(channel_manager_t *mgr) {
    if (!mgr) return;

    memset(mgr, 0, sizeof(channel_manager_t));
    mgr->next_channel_id = 1;
}
