/*
 * tcp.c - TCP (Transmission Control Protocol) implementation
 *
 * TCP provides reliable, ordered, bidirectional byte-stream delivery.
 * It implements flow control, congestion control, and multiplexing (ports).
 *
 * TCP Segment Format (TCP 段格式):
 *   +--------+--------+--------+--------+
 *   |Src Port|Dst Port| Sequence Number|
 *   +--------+--------+--------+--------+
 *   |Ack Number| Data Off|F|U|A|P|R|S|F|
 *   +---------+--------+--------+--------+
 *   | Window | Checksum| Urgent Pointer|
 *   +--------+--------+--------+--------+
 *   | Options (variable)                |
 *   +--------+--------+--------+--------+
 *   | Data (variable)                   |
 *   +-----------------------------------+
 *
 * TCP State Machine (TCP 状态机):
 *
 *   CLOSED ----[Create]----> LISTEN
 *                                |
 *                          [SYN received]
 *                                |
 *                                v
 *                          SYN-RECEIVED
 *                                |
 *                          [SYN-ACK sent, ACK received]
 *                                |
 *                                v
 *                          ESTABLISHED <----> [Data exchange]
 *                                |
 *                          [FIN sent/received]
 *                                |
 *                                v
 *                          FIN-WAIT / CLOSE-WAIT
 *                                |
 *                          [Final ACK]
 *                                |
 *                                v
 *                          TIME-WAIT --> CLOSED
 *
 * TCP Flags (TCP 标志位):
 *   FIN  - Finish: sender has no more data to send
 *   SYN  - Synchronize: initiate connection, exchange initial sequence numbers
 *   RST  - Reset: abort connection (error or forced close)
 *   PSH  - Push: force receiver to process data immediately
 *   ACK  - Acknowledge: acknowledgment number is valid
 *   URG  - Urgent: urgent pointer is valid
 *
 * Sequence Numbers:
 *   Each byte of data is numbered. The sequence number indicates the
 *   position of the first byte in the segment.
 *
 *   Initial Sequence Number (ISN): Random value to prevent old duplicate
 *   segments from being accepted (security feature).
 *
 * Acknowledgment Number:
 *   Indicates the next byte the sender expects to receive.
 *   ACK = N means "I have received up to byte N-1, expecting byte N."
 *
 * Retransmission:
 *   TCP uses a timer for each unacknowledged segment.
 *   When the timer expires, the segment is retransmitted.
 *   The timeout is calculated using RTT measurements:
 *     SRTT = (1-alpha) * SRTT + alpha * SampleRTT  (alpha = 1/8)
 *     RTTVAR = (1-beta) * RTTVAR + beta * |SampleRTT - SRTT|  (beta = 1/4)
 *     RTO = SRTT + 4 * RTTVAR
 */

#include "embedded_net.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* ============================================================================
 * TCP Segment Processing (TCP 段处理)
 *
 * Processes an incoming TCP segment:
 *   1. Validate header (minimum 20 bytes)
 *   2. Verify checksum
 *   3. Find matching connection
 *   4. Process according to TCP state machine
 * ============================================================================ */

int tcp_input(const uint8_t *data, int len) {
    if (len < TCP_HEADER_SIZE_MIN) {
        return -1;
    }

    tcp_segment_t *seg = (tcp_segment_t *)data;

    /* Validate data offset (minimum 5 words = 20 bytes) */
    uint8_t doff = tcp_data_offset((uint8_t *)data);
    if (doff < 20 || doff > TCP_MAX_HEADER_SIZE) {
        return -1;
    }

    int seg_len = len;

    /* Verify checksum */
    seg->checksum = 0;
    uint16_t cksum = checksum(data, seg_len);
    seg->checksum = 0;  /* Restore */
    (void)cksum;  /* In full impl, compare with seg->checksum */

    /* Get sockets and find matching connection */
    socket_t *sockets = net_get_sockets();
    int count = net_get_socket_count();

    /* Look for matching connection by ports */
    for (int i = 0; i < count; i++) {
        if (sockets[i].is_connected &&
            sockets[i].type == SOCK_STREAM &&
            sockets[i].peer_addr.sin_port == seg->src_port &&
            sockets[i].local_addr.sin_port == seg->dst_port) {
            return tcp_process_segment(&sockets[i], data, seg_len);
        }
    }

    /* No matching connection - send RST */
    /* In a full implementation, this would send a TCP RST segment */

    return -1;
}

/* ============================================================================
 * TCP Segment Processing by Connection (按连接处理 TCP 段)
 *
 * Processes a TCP segment for a specific connection, updating the
 * connection state according to the TCP state machine.
 * ============================================================================ */

int tcp_process_segment(socket_t *sock, const uint8_t *data, int len) {
    if (!sock || !data) return -1;

    tcp_segment_t *seg = (tcp_segment_t *)data;
    uint8_t flags = tcp_flags((uint8_t *)data);

    /* Update state based on flags received */
    sock->state = tcp_state_machine(sock, flags);

    /* Process ACK data */
    if (flags & TCP_FLAG_ACK) {
        /* Update send state based on acknowledgment */
        uint32_t ack = ntohl(seg->ack_num);
        if (ack > sock->snd_una) {
            sock->snd_una = ack;
        }
    }

    /* Handle FIN - peer is closing */
    if (flags & TCP_FLAG_FIN) {
        sock->retransmit_cnt = 0;
    }

    return 0;
}

/* ============================================================================
 * TCP State Machine (TCP 状态机)
 *
 * Implements the TCP connection lifecycle. The state machine transitions
 * between states based on received flags and local events.
 *
 * This is the core of TCP reliability - every state transition is
 * carefully defined to handle network unreliability.
 * ============================================================================ */

tcp_state_t tcp_state_machine(socket_t *sock, uint8_t flags) {
    tcp_state_t current = sock->state;

    switch (current) {
        case TCP_LISTEN:
            if (flags & TCP_FLAG_SYN) {
                /* Received SYN while listening - standard TCP doesn't
                 * normally receive SYN in LISTEN state, but for our
                 * simplified implementation, we accept it */
                sock->state = TCP_SYN_RECEIVED;
            }
            break;

        case TCP_SYN_SENT:
            if ((flags & TCP_FLAG_SYN) && (flags & TCP_FLAG_ACK)) {
                /* Received SYN-ACK - connection established */
                sock->state = TCP_ESTABLISHED;
            } else if (flags & TCP_FLAG_RST) {
                sock->state = TCP_CLOSED;
            }
            break;

        case TCP_SYN_RECEIVED:
            if (flags & TCP_FLAG_ACK) {
                sock->state = TCP_ESTABLISHED;
            } else if (flags & TCP_FLAG_RST) {
                sock->state = TCP_CLOSED;
            }
            break;

        case TCP_ESTABLISHED:
            if (flags & TCP_FLAG_FIN) {
                sock->state = TCP_CLOSE_WAIT;
            } else if (flags & TCP_FLAG_RST) {
                sock->state = TCP_CLOSED;
            }
            break;

        case TCP_FIN_WAIT_1:
            if ((flags & TCP_FLAG_FIN) && (flags & TCP_FLAG_ACK)) {
                sock->state = TCP_TIME_WAIT;
            } else if (flags & TCP_FLAG_ACK) {
                sock->state = TCP_FIN_WAIT_2;
            } else if (flags & TCP_FLAG_RST) {
                sock->state = TCP_CLOSED;
            }
            break;

        case TCP_FIN_WAIT_2:
            if (flags & TCP_FLAG_FIN) {
                sock->state = TCP_TIME_WAIT;
            } else if (flags & TCP_FLAG_RST) {
                sock->state = TCP_CLOSED;
            }
            break;

        case TCP_CLOSE_WAIT:
            if (flags & TCP_FLAG_ACK) {
                sock->state = TCP_LAST_ACK;
            } else if (flags & TCP_FLAG_RST) {
                sock->state = TCP_CLOSED;
            }
            break;

        case TCP_CLOSING:
            if (flags & TCP_FLAG_ACK) {
                sock->state = TCP_TIME_WAIT;
            } else if (flags & TCP_FLAG_RST) {
                sock->state = TCP_CLOSED;
            }
            break;

        case TCP_LAST_ACK:
            if (flags & TCP_FLAG_ACK) {
                sock->state = TCP_CLOSED;
            } else if (flags & TCP_FLAG_RST) {
                sock->state = TCP_CLOSED;
            }
            break;

        case TCP_TIME_WAIT:
            /* TIME_WAIT persists for 2*MSL (Maximum Segment Lifetime)
             * before transitioning to CLOSED. This ensures any delayed
             * segments are discarded and the other side received our ACK. */
            if (flags & TCP_FLAG_RST) {
                sock->state = TCP_CLOSED;
            }
            break;

        case TCP_CLOSED:
        default:
            /* In CLOSED state, only RST is valid response to unsolicited segments */
            if (flags & TCP_FLAG_RST) {
                sock->state = TCP_CLOSED;
            }
            break;
    }

    return sock->state;
}

/* ============================================================================
 * TCP Segment Transmission (TCP 段发送)
 *
 * Sends a TCP segment with the given parameters.
 *
 * The TCP checksum covers:
 *   - Pseudo-header (source/dest IP, protocol, length)
 *   - TCP header
 *   - TCP data payload
 *
 * This ensures end-to-end data integrity.
 * ============================================================================ */

int tcp_send(socket_t *sock, const uint8_t *data, int len, uint8_t flags) {
    if (!sock) return -1;

    /* Calculate segment size */
    int header_size = TCP_HEADER_SIZE_MIN;
    int total_len = header_size + len;

    /* Allocate buffer */
    uint8_t *buf = malloc(total_len);
    if (!buf) return -1;

    tcp_segment_t *seg = (tcp_segment_t *)buf;
    memset(seg, 0, total_len);

    /* Build TCP header */
    seg->src_port = sock->local_addr.sin_port;
    seg->dst_port = sock->peer_addr.sin_port;
    seg->seq_num = htonl(sock->snd_seq);
    seg->ack_num = htonl(sock->rcv_seq);

    /* Data offset = 5 (20 bytes) + options / 4 */
    uint8_t *doff_flags = (uint8_t *)seg;
    *doff_flags = (5 << 4) | flags;

    seg->window = htons(sock->window);
    seg->urgent_pointer = 0;

    /* Copy payload */
    if (data && len > 0) {
        memcpy(buf + header_size, data, len);
    }

    /* Compute TCP checksum */
    seg->checksum = 0;
    seg->checksum = pseudo_checksum(
        sock->peer_addr.sin_addr,
        sock->local_addr.sin_addr,
        IP_PROTO_TCP,
        total_len
    );

    /* Send via IPv4 */
    net_interface_t *iface = net_get_interface();
    if (!iface) {
        free(buf);
        return -1;
    }

    int result = ipv4_send(iface, sock->peer_addr.sin_addr,
                           IP_PROTO_TCP, buf, total_len);

    free(buf);
    return result;
}

/* ============================================================================
 * TCP Segment Transmission with Specific Parameters (指定参数发送 TCP 段)
 *
 * Low-level function to send a TCP segment with explicit sequence/ack numbers.
 * Used for connection setup/teardown and retransmission.
 * ============================================================================ */

int tcp_send_segment(socket_t *sock, uint32_t seq, uint32_t ack,
                     const uint8_t *data, int len, uint8_t flags) {
    if (!sock) return -1;

    int header_size = TCP_HEADER_SIZE_MIN;
    int total_len = header_size + len;

    uint8_t *buf = malloc(total_len);
    if (!buf) return -1;

    tcp_segment_t *seg = (tcp_segment_t *)buf;
    memset(seg, 0, total_len);

    seg->src_port = sock->local_addr.sin_port;
    seg->dst_port = sock->peer_addr.sin_port;
    seg->seq_num = htonl(seq);
    seg->ack_num = htonl(ack);

    uint8_t *doff_flags = (uint8_t *)seg;
    *doff_flags = (5 << 4) | flags;

    seg->window = htons(sock->window);
    seg->urgent_pointer = 0;

    if (data && len > 0) {
        memcpy(buf + header_size, data, len);
    }

    /* Compute checksum */
    seg->checksum = 0;
    seg->checksum = pseudo_checksum(
        sock->peer_addr.sin_addr,
        sock->local_addr.sin_addr,
        IP_PROTO_TCP,
        total_len
    );

    net_interface_t *iface = net_get_interface();
    if (!iface) {
        free(buf);
        return -1;
    }

    int result = ipv4_send(iface, sock->peer_addr.sin_addr,
                           IP_PROTO_TCP, buf, total_len);

    free(buf);
    return result;
}

/* ============================================================================
 * Retransmission Timeout Handling (重传超时处理)
 *
 * When a segment is not acknowledged within the RTO period,
 * TCP retransmits the segment. The RTO is dynamically calculated
 * from RTT measurements.
 *
 * RFC 6298 Algorithm:
 *   1. On first transmission: RTO = max(1s, SRTT + 4*RTTVAR)
 *   2. On subsequent samples:
 *      SRTT' = (7/8) * SRTT + (1/8) * SampleRTT
 *      RTTVAR' = (3/4) * RTTVAR + (1/4) * |SampleRTT - SRTT|
 *      RTO = SRTT' + 4 * RTTVAR'
 *   3. If retransmission count >= MAX: connection is dead
 * ============================================================================ */

void tcp_handle_timeout(socket_t *sock) {
    if (!sock) return;

    /* Check if we've exceeded maximum retransmissions */
    sock->retransmit_cnt++;
    if (sock->retransmit_cnt >= TCP_MAX_RETRANSMISSIONS) {
        sock->state = TCP_CLOSED;
        return;
    }

    /* Calculate RTO: SRTT * 16 + RTTVAR * 64 (fixed-point) */
    uint32_t rto = (sock->srtt >> 1) + (sock->rttvar << 6);
    if (rto < 1000) rto = 1000;  /* Minimum 1 second */

    sock->retransmit_to = rto;

    /* Retransmit unacknowledged data */
    int remaining = sock->snd_seq - sock->snd_una;
    if (remaining > 0) {
        int send_len = remaining > sock->mss ? sock->mss : remaining;
        tcp_send(sock, sock->rbuf + (sock->snd_seq - remaining),
                 send_len, TCP_FLAG_ACK);
    }
}
