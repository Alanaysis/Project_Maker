/**
 * @file secure_channel.h
 * @brief Secure Channel Management Module
 *
 * Manages secure communication channels between embedded devices.
 * Provides channel lifecycle management and secure message framing.
 *
 * Security concepts:
 * - Secure channel: Encrypted communication session
 * - Message integrity: Ensuring messages are not tampered
 * - Channel lifecycle: Creation, use, and teardown of secure sessions
 */

#ifndef EMBEDDED_SECURITY_SECURE_CHANNEL_H
#define EMBEDDED_SECURITY_SECURE_CHANNEL_H

#include <stdint.h>
#include <stdbool.h>
#include "tls_sim.h"

#define MAX_CHANNELS   8
#define CHANNEL_BUF_SIZE 256
#define MAX_MSG_SIZE   2048

/* Channel state */
typedef enum {
    CHANNEL_CLOSED = 0,
    CHANNEL_OPENING,
    CHANNEL_OPEN,
    CHANNEL_CLOSING,
    CHANNEL_ERROR
} channel_state_t;

/* Channel direction */
typedef enum {
    CHANNEL_DIR_TX = 0,
    CHANNEL_DIR_RX
} channel_direction_t;

/* Secure channel entry */
typedef struct {
    uint32_t    channel_id;
    channel_state_t state;
    tls_context_t tls_ctx;
    uint8_t     rx_buffer[CHANNEL_BUF_SIZE];
    uint8_t     tx_buffer[CHANNEL_BUF_SIZE];
    uint32_t    rx_len;
    uint32_t    tx_len;
    uint32_t    created_at;
    uint32_t    last_active;
    uint32_t    msg_count;
    bool        active;
} secure_channel_t;

/* Channel manager */
typedef struct {
    secure_channel_t channels[MAX_CHANNELS];
    uint32_t         next_channel_id;
} channel_manager_t;

/**
 * Initialize channel manager
 * @param mgr Channel manager
 */
void channel_manager_init(channel_manager_t *mgr);

/**
 * Create a new secure channel
 * @param mgr Channel manager
 * @param channel_id Output channel ID
 * @return Pointer to created channel, NULL on failure
 */
secure_channel_t *channel_create(channel_manager_t *mgr, uint32_t *channel_id);

/**
 * Open a channel (perform handshake)
 * @param ch Secure channel
 * @return true if channel opened successfully
 */
bool channel_open(secure_channel_t *ch);

/**
 * Send data through secure channel
 * @param ch Secure channel
 * @param data Data to send
 * @param len Data length
 * @return bytes sent, 0 on failure
 */
uint32_t channel_send(secure_channel_t *ch, const uint8_t *data, uint32_t len);

/**
 * Receive data from secure channel
 * @param ch Secure channel
 * @param output Output buffer
 * @param max_len Maximum output length
 * @return bytes received
 */
uint32_t channel_receive(secure_channel_t *ch, uint8_t *output, uint32_t max_len);

/**
 * Close a secure channel
 * @param ch Secure channel
 */
void channel_close(secure_channel_t *ch);

/**
 * Destroy a channel and free resources
 * @param mgr Channel manager
 * @param channel_id Channel to destroy
 * @return true if channel was destroyed
 */
bool channel_destroy(channel_manager_t *mgr, uint32_t channel_id);

/**
 * Get channel by ID
 * @param mgr Channel manager
 * @param channel_id Channel ID
 * @return Pointer to channel, NULL if not found
 */
secure_channel_t *channel_get_by_id(channel_manager_t *mgr, uint32_t channel_id);

/**
 * Check if channel is still valid (not expired)
 * @param ch Secure channel
 * @param max_idle_ms Maximum idle time in milliseconds
 * @return true if channel is active
 */
bool channel_is_valid(secure_channel_t *ch, uint32_t max_idle_ms);

/**
 * Get active channel count
 * @param mgr Channel manager
 * @return Number of active channels
 */
uint32_t channel_active_count(channel_manager_t *mgr);

/**
 * Reset all channels
 * @param mgr Channel manager
 */
void channel_manager_reset(channel_manager_t *mgr);

#endif /* EMBEDDED_SECURITY_SECURE_CHANNEL_H */
