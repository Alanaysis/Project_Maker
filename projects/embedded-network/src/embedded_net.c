/*
 * embedded_net.c - Core network stack implementation
 * 
 * This file implements the core functions of the embedded TCP/IP stack:
 *   - Network stack initialization
 *   - Raw packet transmission
 *   - Checksum calculation
 *   - Utility functions
 *
 * Checksum Algorithm (校验和算法):
 *   The Internet Checksum uses ones' complement arithmetic.
 *   1. Set checksum field to zero
 *   2. Sum all 16-bit words using ones' complement addition
 *   3. Fold carry bits back into the sum
 *   4. Take ones' complement of final sum
 *
 *   Example: For bytes [0x12, 0x34, 0x56, 0x78]:
 *     Word 1: 0x1234
 *     Word 2: 0x5678
 *     Sum:    0x68AC
 *     Checksum: 0x9753 (ones' complement)
 */

#include "embedded_net.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* ============================================================================
 * Global Network State (全局网络状态)
 * ============================================================================ */

static net_interface_t g_net_interface;
static socket_t g_sockets[MAX_SOCKETS];
static int g_socket_count = 0;

/* Get pointer to global network interface */
net_interface_t* net_get_interface(void) {
    return &g_net_interface;
}

/* Get pointer to sockets array */
socket_t* net_get_sockets(void) {
    return g_sockets;
}

/* Get number of active sockets */
int net_get_socket_count(void) {
    return g_socket_count;
}

/* Increment socket count */
void net_increment_socket_count(void) {
    g_socket_count++;
}

/* ============================================================================
 * Network Stack Initialization (网络栈初始化)
 * 
 * Sets up the network stack with a given interface configuration.
 * The interface must have a valid MAC address before initialization.
 * ============================================================================ */

int net_stack_init(net_interface_t *iface) {
    if (!iface) {
        return -1;
    }

    /* Copy interface configuration */
    memcpy(&g_net_interface, iface, sizeof(net_interface_t));

    /* Initialize socket table */
    memset(g_sockets, 0, sizeof(g_sockets));
    g_socket_count = 0;

    /* Mark interface as up */
    g_net_interface.is_up = 1;

    /* Clear ARP cache */
    memset(g_net_interface.arp_table, 0, sizeof(g_net_interface.arp_table));
    g_net_interface.arp_table_count = 0;

    return 0;
}

/* ============================================================================
 * Raw Packet Transmission (原始数据包传输)
 * 
 * Sends raw bytes to the network interface.
 * In a real embedded system, this would write to a network device driver.
 * In this learning implementation, it logs the packet data.
 * ============================================================================ */

int net_send(const uint8_t *data, int len) {
    if (!data || len <= 0) {
        return -1;
    }

    /* In a real implementation, this would call the device driver:
     *   device_driver_transmit(data, len);
     *
     * For this learning project, we log the transmission.
     * The data represents a complete frame ready for the link layer.
     */
    (void)data;
    (void)len;

    return len;
}

/* ============================================================================
 * Ethernet Frame Transmission (以太网帧传输)
 * 
 * Constructs and sends an Ethernet frame with the given destination MAC
 * and payload. The frame structure is:
 *   [Dst MAC (6B)][Src MAC (6B)][EtherType (2B)][Payload]
 * ============================================================================ */

int net_send_frame(const mac_addr_t *dst, uint16_t type, const uint8_t *payload, int len) {
    if (!dst || !payload || len <= 0) {
        return -1;
    }

    /* In a real implementation, this would:
     *   1. Construct the Ethernet frame header
     *   2. Call net_send() with the complete frame
     *   3. The device driver would handle physical transmission
     *
     * For learning purposes, we acknowledge the frame would be sent.
     */
    (void)dst;
    (void)type;
    (void)payload;
    (void)len;

    return len + ETHERNET_HEADER_SIZE;
}

/* ============================================================================
 * Checksum Implementation (校验和实现)
 * 
 * Internet Checksum (RFC 1071):
 * 
 * The checksum is computed over the data using ones' complement addition.
 * This is a simple error-detection scheme that catches most transmission errors.
 * 
 * Why ones' complement?
 *   - It allows the receiver to verify by summing all words (including checksum)
 *   - If the data is uncorrupted, the final sum equals 0xFFFF
 *   - It's simpler than CRC for software implementation
 *
 * Pseudo-header checksum (for ICMP/TCP/UDP):
 *   Includes source IP, destination IP, protocol, and length
 *   This ensures the packet reaches the correct protocol handler
 * ============================================================================ */

uint16_t checksum(const void *data, int len) {
    const uint16_t *ptr = (const uint16_t *)data;
    uint32_t sum = 0;

    /* Sum all 16-bit words */
    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }

    /* Handle odd byte */
    if (len > 0) {
        uint16_t tmp = 0;
        *(uint8_t *)&tmp = *(const uint8_t *)ptr;
        sum += tmp;
    }

    /* Fold carry bits back into the sum */
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    /* Take ones' complement */
    return (uint16_t)~sum;
}

/* Compute pseudo-header checksum for ICMP/TCP/UDP
 * 
 * The pseudo-header includes:
 *   - Source IP address
 *   - Destination IP address
 *   - Protocol number
 *   - Protocol data length
 *
 * This ensures the packet is delivered to the correct upper-layer protocol.
 * If any IP field is corrupted, the checksum will fail.
 */
uint16_t pseudo_checksum(uint32_t src_ip, uint32_t dst_ip,
                         uint8_t protocol, uint16_t len) {
    struct {
        uint32_t src;
        uint32_t dst;
        uint8_t  zero;
        uint8_t  protocol;
        uint16_t length;
    } __attribute__((packed)) pseudo = {
        .zero = 0,
        .src = src_ip,
        .dst = dst_ip,
        .protocol = protocol,
        .length = len
    };

    return checksum(&pseudo, sizeof(pseudo));
}

/* ============================================================================
 * Utility Functions (工具函数)
 * ============================================================================ */

/* Convert IP address to dotted-decimal string */
const char* ip_to_string(uint32_t ip) {
    /* Note: In production, use a thread-safe buffer */
    static char buf[16];
    uint8_t *bytes = (uint8_t *)&ip;
    snprintf(buf, sizeof(buf), "%u.%u.%u.%u",
             bytes[0], bytes[1], bytes[2], bytes[3]);
    return buf;
}

/* Convert dotted-decimal string to IP address */
uint32_t string_to_ip(const char *str) {
    uint32_t a, b, c, d;
    if (sscanf(str, "%u.%u.%u.%u", &a, &b, &c, &d) == 4) {
        /* Return in host byte order (bytes in network order for consistency) */
        uint32_t result = 0;
        uint8_t *bytes = (uint8_t *)&result;
        bytes[0] = (uint8_t)a;
        bytes[1] = (uint8_t)b;
        bytes[2] = (uint8_t)c;
        bytes[3] = (uint8_t)d;
        return result;
    }
    return 0;
}

/* Convert 16-bit value from host to network byte order (big-endian) */
uint16_t htons(uint16_t hostshort) {
    /* On little-endian systems, swap bytes */
    uint16_t result = 0;
    uint8_t *src = (uint8_t *)&hostshort;
    uint8_t *dst = (uint8_t *)&result;
    dst[0] = src[1];
    dst[1] = src[0];
    return result;
}

/* Convert 16-bit value from network to host byte order */
uint16_t ntohs(uint16_t netshort) {
    return htons(netshort); /* Symmetric on most architectures */
}

/* Convert 32-bit value from host to network byte order */
uint32_t htonl(uint32_t hostlong) {
    uint32_t result = 0;
    uint8_t *src = (uint8_t *)&hostlong;
    uint8_t *dst = (uint8_t *)&result;
    dst[0] = src[3];
    dst[1] = src[2];
    dst[2] = src[1];
    dst[3] = src[0];
    return result;
}

/* Convert 32-bit value from network to host byte order */
uint32_t ntohl(uint32_t netlong) {
    return htonl(netlong); /* Symmetric */
}

/* Debug: Print hex dump of data */
void debug_print_hex(const char *label, const uint8_t *data, int len) {
    if (!label || !data) return;
    printf("%s (%d bytes):\n", label, len);
    for (int i = 0; i < len; i += 16) {
        printf("  %04x: ", i);
        for (int j = 0; j < 16 && (i + j) < len; j++) {
            printf("%02x ", data[i + j]);
        }
        printf("\n");
    }
}

/* Debug: Print MAC address */
void debug_print_mac(const char *label, const mac_addr_t *mac) {
    if (!label || !mac) return;
    printf("%s: %02x:%02x:%02x:%02x:%02x:%02x\n",
           label, mac->octet[0], mac->octet[1], mac->octet[2],
           mac->octet[3], mac->octet[4], mac->octet[5]);
}

/* Debug: Print IP address */
void debug_print_ip(const char *label, uint32_t ip) {
    if (!label) return;
    printf("%s: %s\n", label, ip_to_string(ip));
}
