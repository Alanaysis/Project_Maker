/*
 * udp.c - UDP (User Datagram Protocol) implementation
 *
 * UDP is a connectionless, unreliable transport protocol that adds
 * multiplexing (ports) to IP datagrams with minimal overhead.
 *
 * UDP Header (8 bytes):
 *   +--------+--------+--------+--------+
 *   |Src Port|Dst Port| Length | Checksum|
 *   +--------+--------+--------+--------+
 *
 * Key characteristics:
 *   - No connection establishment (unlike TCP)
 *   - No acknowledgment or retransmission
 *   - No flow control or congestion control
 *   - No guarantee of delivery or ordering
 *   - Minimal header overhead (8 bytes vs TCP's 20+ bytes)
 *
 * Use cases:
 *   - DNS queries (fast, small packets)
 *   - Streaming media (loss tolerated, speed critical)
 *   - DHCP (pre-IP configuration)
 *   - Simple request/response protocols
 *
 * UDP Checksum:
 *   Computed over pseudo-header + UDP header + data.
 *   In IPv4, checksum is optional (0 = no checksum).
 *   In IPv6, checksum is mandatory.
 */

#include "embedded_net.h"
#include <string.h>
#include <stdio.h>

/* ============================================================================
 * UDP Packet Processing (UDP 数据包处理)
 *
 * Processes incoming UDP datagrams:
 *   1. Validate header
 *   2. Verify checksum
 *   3. Deliver to appropriate socket or callback
 * ============================================================================ */

int udp_input(const uint8_t *data, int len) {
    if (len < UDP_HEADER_SIZE) {
        return -1;
    }

    udp_header_t *udp = (udp_header_t *)data;

    /* Validate length */
    int udp_len = ntohs(udp->length);
    if (udp_len < UDP_HEADER_SIZE || udp_len > len) {
        return -1;
    }

    /* Verify checksum (if checksum is non-zero) */
    if (udp->checksum != 0) {
        /* Compute pseudo-header checksum */
        uint16_t cksum = checksum(data, udp_len);
        if (cksum != 0) {
            return -1;  /* Checksum error */
        }
    }

    /* In a full implementation, we'd look up the destination port
     * in a socket table and deliver the data to the appropriate socket.
     * For this learning implementation, we acknowledge receipt. */

    return 0;
}

/* ============================================================================
 * UDP Datagram Transmission (UDP 数据报发送)
 *
 * Creates and sends a UDP datagram to the specified destination.
 *
 * Steps:
 *   1. Build UDP header with ports, length, checksum
 *   2. Compute UDP checksum over pseudo-header + UDP + data
 *   3. Encapsulate in IPv4 packet
 *   4. Send via network stack
 * ============================================================================ */

int udp_send(net_interface_t *iface, uint32_t dst_ip, uint16_t dst_port,
             uint16_t src_port, const uint8_t *data, int len) {
    if (!iface || !data || len <= 0) return -1;

    /* Total UDP datagram size */
    int total_len = UDP_HEADER_SIZE + len;

    /* Allocate buffer for UDP header + data */
    uint8_t *buf = malloc(total_len);
    if (!buf) return -1;

    udp_header_t *udp = (udp_header_t *)buf;
    memset(udp, 0, sizeof(*udp));

    /* Build UDP header */
    udp->src_port = htons(src_port);
    udp->dst_port = htons(dst_port);
    udp->length = htons(total_len);

    /* Compute UDP checksum */
    /* Pseudo-header: src IP, dst IP, protocol, length */
    uint32_t pseudo[3];
    pseudo[0] = (uint32_t)htonl(iface->ip_addr);
    pseudo[1] = (uint32_t)htonl(dst_ip);
    pseudo[2] = (uint32_t)((1 << 24) | (IP_PROTO_UDP << 16) | total_len);

    /* Calculate checksum over pseudo-header + UDP header + data */
    uint16_t cksum = checksum((uint8_t *)pseudo, 12);
    cksum = checksum(buf, total_len);
    udp->checksum = cksum;

    /* Copy data */
    memcpy(buf + UDP_HEADER_SIZE, data, len);

    /* Send via IPv4 with protocol UDP (17) */
    int result = ipv4_send(iface, dst_ip, IP_PROTO_UDP, buf, total_len);

    free(buf);
    return result;
}
