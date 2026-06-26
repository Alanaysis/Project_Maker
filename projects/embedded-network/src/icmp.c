/*
 * icmp.c - ICMP (Internet Control Message Protocol) implementation
 *
 * ICMP is used for network diagnostics and error reporting.
 * It operates at the network layer (layer 3), but is considered
 * an extension of IP rather than a transport protocol.
 *
 * ICMP Message Types:
 *   - Type 0: Echo Reply (ping reply)
 *   - Type 3: Destination Unreachable
 *   - Type 8: Echo Request (ping request)
 *   - Type 11: Time Exceeded
 *
 * Ping (Echo Request/Reply):
 *   The ping utility uses ICMP Echo Request (type 8) and Echo Reply (type 0).
 *   It measures round-trip time and checks network connectivity.
 *
 *   Request:  [Type=8][Code=0][Checksum][ID=PID][Seq=N][Data]
 *   Reply:    [Type=0][Code=0][Checksum][ID=PID][Seq=N][Data]
 *
 *   The reply echoes back the exact data from the request,
 *   allowing the sender to verify data integrity.
 */

#include "embedded_net.h"
#include <string.h>
#include <stdio.h>
#include <time.h>

/* ============================================================================
 * ICMP Packet Processing (ICMP 数据包处理)
 *
 * Processes incoming ICMP packets:
 *   - Echo Request: Generate Echo Reply
 *   - Echo Reply: Log received (ping response)
 *   - Other types: Could handle errors in a full implementation
 * ============================================================================ */

int icmp_input(const uint8_t *data, int len) {
    if (len < ICMP_HEADER_SIZE) {
        return -1;
    }

    icmp_packet_t *icmp = (icmp_packet_t *)data;

    /* Verify checksum */
    icmp->checksum = 0;
    uint16_t calc_cksum = checksum(data, len);
    icmp->checksum = 0;  /* Restore original */

    if (calc_cksum != icmp->checksum) {
        return -1;  /* Checksum error */
    }

    /* Handle Echo Request (ping) */
    if (icmp->type == ICMP_ECHO_REQUEST) {
        /* Generate Echo Reply - echo back the data */
        icmp_echo_reply(data, len);
    }
    /* Echo Reply - would process timing in a full implementation */
    else if (icmp->type == ICMP_ECHO_REPLY) {
        /* In a full implementation, match identifier/sequence to pending pings */
    }

    return 0;
}

/* ============================================================================
 * ICMP Echo Request (ICMP Echo 请求 - Ping)
 *
 * Creates and sends an ICMP Echo Request packet to the target IP.
 * This is the "ping" operation.
 *
 * Packet format:
 *   [ICMP Header][Timestamp/Sequence Data]
 *
 * The identifier helps match requests to replies (usually process ID).
 * The sequence number identifies each ping in a series.
 * ============================================================================ */

int icmp_echo_request(net_interface_t *iface, uint32_t dst_ip,
                      uint16_t identifier, uint16_t seq_num) {
    if (!iface) return -1;

    /* ICMP Echo Request packet */
    uint8_t data[ICMP_HEADER_SIZE + 32];
    icmp_packet_t *icmp = (icmp_packet_t *)data;

    memset(icmp, 0, sizeof(*icmp));
    icmp->type = ICMP_ECHO_REQUEST;
    icmp->code = 0;
    icmp->identifier = htons(identifier);
    icmp->sequence = htons(seq_num);

    /* Fill data with pattern for verification */
    int data_len = sizeof(data) - ICMP_HEADER_SIZE;
    for (int i = 0; i < data_len; i++) {
        icmp->data[i] = (uint8_t)(i & 0xFF);
    }

    /* Compute ICMP checksum */
    icmp->checksum = checksum(data, ICMP_HEADER_SIZE + data_len);

    /* Send via IPv4 with protocol ICMP (1) */
    int result = ipv4_send(iface, dst_ip, IP_PROTO_ICMP, data, ICMP_HEADER_SIZE + data_len);

    return result;
}

/* ============================================================================
 * ICMP Echo Reply (ICMP Echo 回复)
 *
 * Creates and sends an ICMP Echo Reply in response to an Echo Request.
 * The reply echoes back all data from the request.
 * ============================================================================ */

int icmp_echo_reply(const uint8_t *data, int len) {
    if (len < ICMP_HEADER_SIZE) return -1;

    const icmp_packet_t *request = (const icmp_packet_t *)data;

    /* Build reply - same structure as request but type=0 */
    uint8_t reply_data[ICMP_HEADER_SIZE + 32];
    icmp_packet_t *reply = (icmp_packet_t *)reply_data;

    memset(reply, 0, sizeof(*reply));
    reply->type = ICMP_ECHO_REPLY;    /* Changed to reply */
    reply->code = 0;
    reply->identifier = request->identifier;
    reply->sequence = request->sequence;

    /* Echo back the data */
    int data_len = len - ICMP_HEADER_SIZE;
    memcpy(reply->data, request->data, data_len);

    /* Compute checksum */
    int total_len = ICMP_HEADER_SIZE + data_len;
    reply->checksum = checksum(reply_data, total_len);

    /* Get source interface */
    net_interface_t *iface = net_get_interface();
    if (!iface) return -1;

    /* In a real implementation, we'd know the source IP from the IP header
     * that delivered this packet. Here we use the interface IP. */
    return ipv4_send(iface, 0, IP_PROTO_ICMP, reply_data, total_len);
}
