/*
 * udp_demo.c - UDP Demo
 *
 * Demonstrates UDP datagram communication.
 *
 * UDP vs TCP (UDP 与 TCP 对比):
 *
 *   Feature          TCP                    UDP
 *   --------         ----                   ----
 *   Connection       Yes (3-way handshake)  No
 *   Reliability      Yes (ACK + retransmit) No
 *   Ordering         Yes                    No
 *   Flow Control     Yes (window)           No
 *   Congestion Ctrl  Yes                    No
 *   Header Overhead  20+ bytes              8 bytes
 *   Speed            Slower                 Faster
 *   Use Cases        Web, email, file transfer DNS, streaming, VoIP
 *
 * UDP Header (8 bytes minimum):
 *   +--------+--------+--------+--------+
 *   |Src Port|Dst Port| Length | Checksum|
 *   +--------+--------+--------+--------+
 *
 *   Length: UDP header (8) + data
 *   Checksum: Optional in IPv4, mandatory in IPv6
 *
 * Why use UDP?
 *   - Low latency (no handshake, no ACK overhead)
 *   - Small header (8 bytes vs 20+ for TCP)
 *   - Broadcast/multicast support
 *   - Application can handle reliability if needed
 *
 * Common UDP protocols:
 *   - DNS (port 53)
 *   - DHCP (ports 67/68)
 *   - SNMP (port 161)
 *   - TFTP (port 69)
 *   - NTP (port 123)
 */

#include "embedded_net.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Demo configuration */
#define SERVER_PORT 5000
#define CLIENT_PORT 5001
#define SERVER_IP   "192.168.1.1"
#define CLIENT_IP   "192.168.1.100"
#define SAMPLE_MSG  "Hello UDP World!"

/* Simulated network interface */
static net_interface_t demo_iface;

/* ============================================================================
 * Initialize demo interface
 * ============================================================================ */

static void init_demo_interface(void) {
    memset(&demo_iface, 0, sizeof(demo_iface));

    demo_iface.mac.octet[0] = 0x00;
    demo_iface.mac.octet[1] = 0x1A;
    demo_iface.mac.octet[2] = 0x2B;
    demo_iface.mac.octet[3] = 0x3C;
    demo_iface.mac.octet[4] = 0x4D;
    demo_iface.mac.octet[5] = 0x5E;

    demo_iface.ip_addr = string_to_ip(CLIENT_IP);
    demo_iface.subnet_mask = string_to_ip("255.255.255.0");
    demo_iface.gateway = string_to_ip("192.168.1.1");
    demo_iface.dns_server = string_to_ip("8.8.8.8");
    demo_iface.is_up = 1;
    demo_iface.has_ip = 1;
}

/* ============================================================================
 * Demo: UDP Datagram Structure
 *
 * Shows the exact byte layout of a UDP datagram.
 * ============================================================================ */

static void demo_udp_datagram(void) {
    printf("\n=== UDP Datagram Structure ===\n\n");

    /* Build UDP datagram */
    uint8_t data[UDP_HEADER_SIZE + sizeof(SAMPLE_MSG)];
    udp_header_t *udp = (udp_header_t *)data;

    memset(udp, 0, sizeof(*udp));

    /* Set UDP header fields */
    udp->src_port = htons(CLIENT_PORT);
    udp->dst_port = htons(SERVER_PORT);
    udp->length = htons(UDP_HEADER_SIZE + sizeof(SAMPLE_MSG) - 1);

    /* Copy payload */
    memcpy(data + UDP_HEADER_SIZE, SAMPLE_MSG, sizeof(SAMPLE_MSG) - 1);

    /* Compute checksum */
    uint32_t pseudo[3];
    pseudo[0] = (uint32_t)htonl(demo_iface.ip_addr);
    pseudo[1] = (uint32_t)htonl(string_to_ip(SERVER_IP));
    pseudo[2] = (uint32_t)((1 << 24) | (IP_PROTO_UDP << 16) | udp->length);

    udp->checksum = checksum((uint8_t *)pseudo, 12);
    udp->checksum = checksum(data, udp->length);

    /* Print structure */
    printf("UDP Header:\n");
    printf("  Source Port:   %d\n", ntohs(udp->src_port));
    printf("  Dest Port:     %d\n", ntohs(udp->dst_port));
    printf("  Length:        %d bytes\n", ntohs(udp->length));
    printf("  Checksum:      0x%04X\n", ntohs(udp->checksum));
    printf("  Payload:       '%s' (%d bytes)\n",
           (char*)(data + UDP_HEADER_SIZE),
           (int)strlen((char*)(data + UDP_HEADER_SIZE)));

    /* Show hex dump */
    printf("\nUDP Datagram hex dump:\n");
    debug_print_hex("UDP", data, udp->length);
}

/* ============================================================================
 * Demo: UDP vs TCP comparison
 * ============================================================================ */

static void demo_udp_vs_tcp(void) {
    printf("\n=== UDP vs TCP Comparison ===\n\n");

    printf("                    TCP                    UDP\n");
    printf("  ---------------  -------------------  -------------------\n");
    printf("  Header Size      20+ bytes             8 bytes\n");
    printf("  Connection       Yes (3-way handshake) No\n");
    printf("  Reliability      Yes                   No\n");
    printf("  Ordering         Yes                   No\n");
    printf("  Flow Control     Window-based          None\n");
    printf("  Congestion Ctrl  Yes                   None\n");
    printf("  Broadcast        No                    Yes\n");
    printf("  Multicast        No                    Yes\n");
    printf("  Latency          Higher (overhead)     Lower\n");
    printf("  Throughput       Good                  Excellent\n");
    printf("  ---------------  -------------------  -------------------\n");

    printf("\nWhen to use UDP:\n");
    printf("  - DNS queries (need fast response)\n");
    printf("  - Streaming media (loss is acceptable)\n");
    printf("  - Real-time games (latency is critical)\n");
    printf("  - DHCP (pre-IP configuration)\n");
    printf("  - Simple request/response protocols\n");

    printf("\nWhen to use TCP:\n");
    printf("  - Web browsing (HTTP/HTTPS)\n");
    printf("  - File transfer (FTP, SFTP)\n");
    printf("  - Email (SMTP, IMAP, POP3)\n");
    printf("  - Database connections\n");
    printf("  - Any data where reliability is critical\n");
}

/* ============================================================================
 * Demo: UDP Checksum Calculation
 *
 * Shows how the UDP checksum is computed over the pseudo-header,
 * UDP header, and data.
 * ============================================================================ */

static void demo_udp_checksum(void) {
    printf("\n=== UDP Checksum Calculation ===\n\n");

    const char *msg = "Test";
    int data_len = strlen(msg);
    int total_len = UDP_HEADER_SIZE + data_len;

    /* Build pseudo-header */
    uint32_t src_ip = demo_iface.ip_addr;
    uint32_t dst_ip = string_to_ip(SERVER_IP);

    printf("Pseudo-header:\n");
    printf("  Source IP:     %s\n", ip_to_string(src_ip));
    printf("  Dest IP:       %s\n", ip_to_string(dst_ip));
    printf("  Protocol:      %d (UDP)\n", IP_PROTO_UDP);
    printf("  Length:        %d\n", total_len);

    /* Build UDP header + data */
    uint8_t buf[UDP_HEADER_SIZE + 64];
    udp_header_t *udp = (udp_header_t *)buf;
    udp->src_port = htons(CLIENT_PORT);
    udp->dst_port = htons(SERVER_PORT);
    udp->length = htons(total_len);
    udp->checksum = 0;  /* Zero before checksum */

    memcpy(buf + UDP_HEADER_SIZE, msg, data_len);

    /* Compute checksum */
    uint16_t cksum = checksum((uint8_t *)&src_ip, 8);  /* Src IP */
    cksum = checksum((uint8_t *)&dst_ip, 4);            /* Dst IP */
    uint8_t proto = IP_PROTO_UDP;
    cksum = checksum(&proto, 1);
    uint16_t zero = 0;
    cksum = checksum(&zero, 1);
    cksum = checksum(buf, total_len);

    udp->checksum = cksum;

    printf("\nUDP Header + Data:\n");
    debug_print_hex("UDP+Data", buf, total_len);

    printf("\nFinal Checksum: 0x%04X\n", ntohs(udp->checksum));
    printf("Verification: 0x%04X (should be 0x0000 for valid checksum)\n",
           checksum(buf, total_len));
}

/* ============================================================================
 * Main demo driver
 * ============================================================================ */

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    printf("========================================\n");
    printf("  UDP Demo - embedded-network\n");
    printf("========================================\n");

    init_demo_interface();
    net_stack_init(&demo_iface);

    printf("\nLocal Interface:\n");
    debug_print_mac("MAC Address", &demo_iface.mac);
    printf("IP Address:    %s\n", ip_to_string(demo_iface.ip_addr));

    /* Run demos */
    demo_udp_datagram();
    demo_udp_vs_tcp();
    demo_udp_checksum();

    printf("\n========================================\n");
    printf("  Demo Complete!\n");
    printf("========================================\n");

    return 0;
}
