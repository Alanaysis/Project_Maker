/*
 * ping_demo.c - ICMP Ping Demo
 *
 * Demonstrates ICMP Echo Request/Reply (ping) functionality.
 * This is the most fundamental network diagnostic tool.
 *
 * How ping works:
 *   1. Client sends ICMP Echo Request to target IP
 *   2. Target receives request and echoes it back as Echo Reply
 *   3. Client measures round-trip time
 *
 * This demo simulates the ping process by:
 *   - Creating an ICMP Echo Request packet
 *   - Showing the packet structure
 *   - Demonstrating checksum calculation
 *
 * Learning objectives:
 *   - Understand ICMP message types
 *   - See how ping packets are structured
 *   - Learn about ICMP checksum calculation
 */

#include "embedded_net.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Demo configuration */
#define PING_IDENTIFIER 12345
#define PING_SEQ_NUM    1
#define PING_DATA_SIZE  32
#define PING_TARGET_IP  "192.168.1.1"

/* Simulated network interface for demo */
static net_interface_t demo_iface;

/* ============================================================================
 * Initialize demo network interface
 * ============================================================================ */

static void init_demo_interface(void) {
    memset(&demo_iface, 0, sizeof(demo_iface));

    /* Set local MAC address (in real system, this comes from hardware) */
    demo_iface.mac.octet[0] = 0x00;
    demo_iface.mac.octet[1] = 0x1A;
    demo_iface.mac.octet[2] = 0x2B;
    demo_iface.mac.octet[3] = 0x3C;
    demo_iface.mac.octet[4] = 0x4D;
    demo_iface.mac.octet[5] = 0x5E;

    /* Set local IP address */
    demo_iface.ip_addr = string_to_ip("192.168.1.100");

    /* Set subnet mask (255.255.255.0) */
    demo_iface.subnet_mask = string_to_ip("255.255.255.0");

    /* Set gateway */
    demo_iface.gateway = string_to_ip("192.168.1.1");

    /* Set DNS server */
    demo_iface.dns_server = string_to_ip("8.8.8.8");

    demo_iface.is_up = 1;
    demo_iface.has_ip = 1;
}

/* ============================================================================
 * Demo: Build ICMP Echo Request packet
 *
 * Shows the exact byte layout of an ICMP Echo Request.
 * ============================================================================ */

static void demo_build_echo_request(void) {
    printf("\n=== ICMP Echo Request Packet Structure ===\n");
    printf("Target: %s\n", PING_TARGET_IP);
    printf("Identifier: %d\n", PING_IDENTIFIER);
    printf("Sequence: %d\n\n", PING_SEQ_NUM);

    /* Build ICMP Echo Request */
    uint8_t data[ICMP_HEADER_SIZE + PING_DATA_SIZE];
    icmp_packet_t *icmp = (icmp_packet_t *)data;

    memset(icmp, 0, sizeof(*icmp));
    icmp->type = ICMP_ECHO_REQUEST;
    icmp->code = 0;
    icmp->identifier = htons(PING_IDENTIFIER);
    icmp->sequence = htons(PING_SEQ_NUM);

    /* Fill with pattern */
    for (int i = 0; i < PING_DATA_SIZE; i++) {
        icmp->data[i] = (uint8_t)(i & 0xFF);
    }

    /* Compute checksum */
    icmp->checksum = checksum(data, ICMP_HEADER_SIZE + PING_DATA_SIZE);

    /* Print packet structure */
    printf("ICMP Header:\n");
    printf("  Type:        %d (Echo Request)\n", icmp->type);
    printf("  Code:        %d\n", icmp->code);
    printf("  Checksum:    0x%04X\n", icmp->checksum);
    printf("  Identifier:  %d\n", ntohs(icmp->identifier));
    printf("  Sequence:    %d\n", ntohs(icmp->sequence));
    printf("  Data Size:   %d bytes\n", PING_DATA_SIZE);

    /* Show hex dump */
    printf("\nPacket hex dump:\n");
    debug_print_hex("ICMP Packet", data, ICMP_HEADER_SIZE + PING_DATA_SIZE);
}

/* ============================================================================
 * Demo: Verify ICMP checksum
 *
 * Demonstrates that the checksum verification works correctly.
 * ============================================================================ */

static void demo_checksum_verification(void) {
    printf("\n=== ICMP Checksum Verification ===\n");

    /* Build a simple packet */
    uint8_t data[] = {0x08, 0x00, 0x00, 0x00, 0x12, 0x34, 0x56, 0x78};
    uint16_t cksum = checksum(data, sizeof(data));

    printf("Data: ");
    for (int i = 0; i < (int)sizeof(data); i++) {
        printf("%02x ", data[i]);
    }
    printf("\n");
    printf("Checksum: 0x%04X\n", cksum);

    /* Now verify - set checksum in data and verify sum is correct */
    uint16_t *cksum_ptr = (uint16_t *)&data[2];
    uint16_t original = *cksum_ptr;
    *cksum_ptr = cksum;

    uint16_t verify = checksum(data, sizeof(data));
    printf("After inserting checksum:\n");
    printf("Verification sum: 0x%04X (should be 0x%04X for valid checksum)\n",
           verify, 0x0000);

    /* Restore */
    *cksum_ptr = original;
}

/* ============================================================================
 * Demo: IPv4 header structure
 *
 * Shows how an IPv4 packet is structured.
 * ============================================================================ */

static void demo_ipv4_header(void) {
    printf("\n=== IPv4 Header Structure ===\n");

    ipv4_header_t hdr;
    memset(&hdr, 0, sizeof(hdr));

    /* Build a sample IPv4 header */
    hdr.version_ihl = IPv4_VERSION_IHL;
    hdr.dscp_ecn = 0;
    hdr.total_length = htons(IPv4_HEADER_SIZE + 32);
    hdr.identification = 0x1234;
    hdr.flags_fragment = htons(IP_FLAG_DF);
    hdr.ttl = 64;
    hdr.protocol = IP_PROTO_ICMP;
    hdr.src_ip = string_to_ip("192.168.1.100");
    hdr.dst_ip = string_to_ip("192.168.1.1");

    /* Compute checksum */
    hdr.header_checksum = checksum((uint8_t *)&hdr, IPv4_HEADER_SIZE);

    printf("Version:     %d\n", (hdr.version_ihl >> 4) & 0x0F);
    printf("IHL:         %d (%d bytes)\n", hdr.version_ihl & 0x0F, (hdr.version_ihl & 0x0F) * 4);
    printf("Total Length: %d bytes\n", ntohs(hdr.total_length));
    printf("Identification: 0x%04X\n", ntohs(hdr.identification));
    printf("TTL:         %d\n", hdr.ttl);
    printf("Protocol:    %d (ICMP)\n", hdr.protocol);
    printf("Source IP:   %s\n", ip_to_string(hdr.src_ip));
    printf("Dest IP:     %s\n", ip_to_string(hdr.dst_ip));
    printf("Checksum:    0x%04X\n", ntohs(hdr.header_checksum));

    /* Verify checksum */
    hdr.header_checksum = 0;
    uint16_t verify = checksum((uint8_t *)&hdr, IPv4_HEADER_SIZE);
    hdr.header_checksum = checksum((uint8_t *)&hdr, IPv4_HEADER_SIZE);
    printf("Checksum verification: %s\n",
           verify == hdr.header_checksum ? "PASS" : "FAIL");
}

/* ============================================================================
 * Demo: ARP packet structure
 *
 * Shows how an ARP request is structured.
 * ============================================================================ */

static void demo_arp_packet(void) {
    printf("\n=== ARP Request Packet Structure ===\n");

    arp_packet_t arp;
    memset(&arp, 0, sizeof(arp));

    arp.hardware_type = htons(1);
    arp.protocol_type = htons(ETHER_TYPE_IPv4);
    arp.hardware_size = MAC_ADDR_SIZE;
    arp.protocol_size = 4;
    arp.opcode = htons(ARP_REQUEST);

    /* Sender (us) */
    arp.sender_mac.octet[0] = 0x00;
    arp.sender_mac.octet[1] = 0x1A;
    arp.sender_mac.octet[2] = 0x2B;
    arp.sender_mac.octet[3] = 0x3C;
    arp.sender_mac.octet[4] = 0x4D;
    arp.sender_mac.octet[5] = 0x5E;
    arp.sender_ip = string_to_ip("192.168.1.100");

    /* Target (broadcast) */
    arp.target_ip = string_to_ip("192.168.1.1");

    printf("Hardware Type:   %d (Ethernet)\n", ntohs(arp.hardware_type));
    printf("Protocol Type:   0x%04X (IPv4)\n", ntohs(arp.protocol_type));
    printf("Hardware Size:   %d\n", arp.hardware_size);
    printf("Protocol Size:   %d\n", arp.protocol_size);
    printf("Opcode:          %d (Request)\n", ntohs(arp.opcode));
    printf("Sender MAC:      ");
    debug_print_mac("", &arp.sender_mac);
    printf("Sender IP:       %s\n", ip_to_string(arp.sender_ip));
    printf("Target IP:       %s\n", ip_to_string(arp.target_ip));
}

/* ============================================================================
 * Main demo driver
 * ============================================================================ */

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    printf("========================================\n");
    printf("  ICMP Ping Demo - embedded-network\n");
    printf("========================================\n");

    /* Initialize demo interface */
    init_demo_interface();
    net_stack_init(&demo_iface);

    printf("\nLocal Interface:\n");
    debug_print_mac("MAC Address", &demo_iface.mac);
    printf("IP Address:    %s\n", ip_to_string(demo_iface.ip_addr));
    printf("Subnet Mask:   %s\n", ip_to_string(demo_iface.subnet_mask));
    printf("Gateway:       %s\n", ip_to_string(demo_iface.gateway));
    printf("DNS:           %s\n", ip_to_string(demo_iface.dns_server));

    /* Run demos */
    demo_build_echo_request();
    demo_checksum_verification();
    demo_ipv4_header();
    demo_arp_packet();

    printf("\n========================================\n");
    printf("  Demo Complete!\n");
    printf("========================================\n");

    return 0;
}
