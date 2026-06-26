/*
 * ipv4.c - IPv4 packet handling implementation
 *
 * IPv4 (Internet Protocol version 4) is the network layer protocol that
 * provides packet switching and routing across interconnected networks.
 *
 * IPv4 Header Structure (IPv4 头部结构):
 *   - Version (4 bits): Must be 4
 *   - IHL (4 bits): Header length in 32-bit words (usually 5 = 20 bytes)
 *   - DSCP/ECN (8 bits): Differentiated services / Explicit congestion notification
 *   - Total Length (16 bits): Header + data (max 65535)
 *   - Identification (16 bits): For fragment reassembly
 *   - Flags/Fragment Offset (16 bits): Fragment control
 *   - TTL (8 bits): Time to live - decremented by each router
 *   - Protocol (8 bits): Upper layer protocol (6=TCP, 17=UDP, 1=ICMP)
 *   - Header Checksum (16 bits): Error check for header only
 *   - Source IP (32 bits): Sender address
 *   - Destination IP (32 bits): Receiver address
 *   - Options (variable): Optional fields (usually none)
 *
 * Key Concepts:
 *   - Fragmentation: Large packets are split at MTU boundaries
 *   - TTL: Prevents packets from looping forever
 *   - Checksum: Only protects the header, not the data
 */

#include "embedded_net.h"
#include <string.h>
#include <stdio.h>

/* ============================================================================
 * IPv4 Packet Processing (IPv4 数据包处理)
 *
 * When an IPv4 packet arrives:
 *   1. Validate the packet (checksum, length)
 *   2. Check destination IP
 *   3. Decrement TTL
 *   4. Pass to upper-layer protocol handler
 * ============================================================================ */

int ipv4_input(const uint8_t *data, int len) {
    if (len < (int)IPv4_HEADER_SIZE) {
        return -1;
    }

    const ipv4_header_t *hdr = (const ipv4_header_t *)data;

    /* Validate version and header length */
    uint8_t version = (hdr->version_ihl >> 4) & 0x0F;
    uint8_t ihl = hdr->version_ihl & 0x0F;

    if (version != 4) {
        return -1;  /* Not IPv4 */
    }

    if (ihl < 5) {
        return -1;  /* Header too short */
    }

    int header_len = ihl * 4;
    if (len < header_len) {
        return -1;
    }

    /* Verify header checksum */
    ipv4_header_t temp_hdr;
    memcpy(&temp_hdr, hdr, sizeof(temp_hdr));
    temp_hdr.header_checksum = 0;

    uint16_t calc_checksum = checksum(&temp_hdr, header_len);
    if (calc_checksum != hdr->header_checksum) {
        return -1;  /* Checksum error */
    }

    int total_len = ntohs(hdr->total_length);
    if (total_len > len) {
        return -1;  /* Truncated packet */
    }

    /* Check TTL */
    if (hdr->ttl <= 0) {
        return -1;  /* TTL expired */
    }

    /* Get payload pointer (skip IP header) */
    const uint8_t *payload = data + header_len;
    int payload_len = total_len - header_len;

    /* Dispatch to upper-layer protocol */
    switch (hdr->protocol) {
        case IP_PROTO_ICMP:
            return icmp_input(payload, payload_len);
        case IP_PROTO_UDP:
            return udp_input(payload, payload_len);
        case IP_PROTO_TCP:
            return tcp_input(payload, payload_len);
        default:
            return -1;  /* Unsupported protocol */
    }
}

/* ============================================================================
 * IPv4 Packet Creation and Transmission (IPv4 数据包创建与发送)
 *
 * Creates an IPv4 packet with the given payload and sends it through
 * the network stack.
 *
 * Steps:
 *   1. Build IPv4 header
 *   2. Compute header checksum
 *   3. Find destination MAC (via ARP)
 *   4. Encapsulate in Ethernet frame
 *   5. Transmit
 * ============================================================================ */

int ipv4_send(net_interface_t *iface, uint32_t dst_ip, uint8_t protocol,
              const uint8_t *payload, int payload_len) {
    if (!iface || !payload || payload_len <= 0) {
        return -1;
    }

    /* Need space for IPv4 header + payload */
    int total_len = IPv4_HEADER_SIZE + payload_len;
    uint8_t *buf = malloc(total_len);
    if (!buf) return -1;

    ipv4_header_t *hdr = (ipv4_header_t *)buf;
    memset(hdr, 0, sizeof(*hdr));

    /* Build IPv4 header */
    hdr->version_ihl = IPv4_VERSION_IHL;  /* Version 4, 20-byte header */
    hdr->dscp_ecn = 0;
    hdr->total_length = htons(total_len);
    hdr->identification = 0;
    hdr->flags_fragment = htons(IP_FLAG_DF);  /* Don't fragment */
    hdr->ttl = IPv4_MAX_TTL;
    hdr->protocol = protocol;

    /* Set IP addresses (network byte order) */
    hdr->src_ip = iface->ip_addr;
    hdr->dst_ip = dst_ip;

    /* Compute header checksum */
    hdr->header_checksum = 0;
    hdr->header_checksum = checksum(buf, IPv4_HEADER_SIZE);

    /* Find destination MAC address */
    mac_addr_t dst_mac;
    int need_arp = 0;

    /* Check if destination is on local subnet */
    uint32_t dst_subnet = dst_ip & iface->subnet_mask;
    uint32_t local_subnet = iface->ip_addr & iface->subnet_mask;

    if (dst_subnet != local_subnet) {
        /* Destination is off-subnet, use gateway */
        if (iface->gateway != 0) {
            if (arp_lookup(iface->gateway, &dst_mac) == 0) {
                /* Gateway in cache, use it */
            } else {
                need_arp = 1;
            }
        } else {
            need_arp = 1;
        }
    } else {
        /* Destination is on local subnet */
        if (dst_ip == iface->ip_addr) {
            /* Sending to self */
            dst_mac.octet[0] = iface->mac.octet[0];
            dst_mac.octet[1] = iface->mac.octet[1];
            dst_mac.octet[2] = iface->mac.octet[2];
            dst_mac.octet[3] = iface->mac.octet[3];
            dst_mac.octet[4] = iface->mac.octet[4];
            dst_mac.octet[5] = iface->mac.octet[5];
        } else if (arp_lookup(dst_ip, &dst_mac) == 0) {
            /* In ARP cache */
        } else {
            need_arp = 1;
        }
    }

    if (need_arp) {
        free(buf);
        return -2;  /* Need ARP resolution */
    }

    /* Copy payload */
    memcpy(buf + IPv4_HEADER_SIZE, payload, payload_len);

    /* Build Ethernet frame and send */
    ethernet_frame_t *frame = (ethernet_frame_t *)malloc(
        ETHERNET_HEADER_SIZE + total_len);
    if (!frame) {
        free(buf);
        return -1;
    }

    memcpy(frame->dst_mac.octet, dst_mac.octet, MAC_ADDR_SIZE);
    memcpy(frame->src_mac.octet, iface->mac.octet, MAC_ADDR_SIZE);
    frame->ether_type = htons(ETHER_TYPE_IPv4);
    memcpy(frame->payload, buf, total_len);

    int result = net_send_frame(&dst_mac, ETHER_TYPE_IPv4,
                                (uint8_t *)frame,
                                ETHERNET_HEADER_SIZE + total_len);

    free(buf);
    free(frame);

    return result;
}
