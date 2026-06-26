/*
 * dhcp.c - DHCP (Dynamic Host Configuration Protocol) client implementation
 *
 * DHCP automatically assigns IP addresses and network configuration
 * to devices on a network.
 *
 * DHCP DORA Process (DHCP DORA 流程):
 *
 *   Client                    Server
 *   ------                    ------
 *   Discover (broadcast) ---->
 *                         <---- Offer
 *   Request (broadcast) ---->
 *                         <---- Ack
 *
 *   Client now has IP configuration
 *
 * DHCP Packet Format:
 *   - Op: 1=Request, 2=Reply
 *   - HType: Hardware type (1=Ethernet)
 *   - HLen: Hardware address length (6 for Ethernet)
 *   - Xid: Transaction ID (matches request to reply)
 *   - CIAddr: Client IP (filled in later stages)
 *   - YIAddr: 'Your' IP (server-assigned IP)
 *   - SIAddr: Next server IP
 *   - GIAddr: Gateway IP (for DHCP relay)
 *   - CHAddr: Client hardware (MAC) address
 *   - Options: Variable configuration parameters
 *
 * DHCP Options:
 *   - Option 1: Subnet mask
 *   - Option 3: Router/gateway
 *   - Option 6: DNS server
 *   - Option 51: Lease time
 *   - Option 53: Message type
 *   - Option 54: Server identifier
 */

#include "embedded_net.h"
#include <string.h>
#include <stdio.h>
#include <time.h>

/* DHCP broadcast address */
#define DHCP_BROADCAST_IP 0xFFFFFFFF
#define DHCP_SERVER_PORT 67
#define DHCP_CLIENT_PORT 68

/* ============================================================================
 * DHCP Discover (DHCP Discover 消息)
 *
 * Broadcast by a client to find available DHCP servers.
 * Sent to UDP port 67 (bootps) from UDP port 68 (bootpc).
 * ============================================================================ */

int dhcp_discover(net_interface_t *iface, uint32_t xid) {
    if (!iface) return -1;

    /* Build DHCP Discover packet */
    uint8_t buf[300];
    memset(buf, 0, sizeof(buf));

    dhcp_packet_t *dhcp = (dhcp_packet_t *)buf;
    dhcp->op = DHCP_BOOT_REQUEST;
    dhcp->htype = 1;  /* Ethernet */
    dhcp->hlen = MAC_ADDR_SIZE;
    dhcp->hops = 0;
    dhcp->xid = xid;
    dhcp->secs = 0;
    dhcp->flags = htons(0x8000);  /* Broadcast flag */
    dhcp->magic_cookie = htonl(DHCP_MAGIC_COOKIE);

    /* Set client MAC address */
    memcpy(dhcp->chaddr, iface->mac.octet, MAC_ADDR_SIZE);

    /* Option: Message Type = DHCPDISCOVER (1) */
    int opt_offset = 0;
    buf[248] = 53;  /* Option type: Message Type */
    buf[249] = 1;   /* Length */
    buf[250] = DHCP_DISCOVER;  /* Value: Discover */
    buf[251] = 255; /* Option: End */
    opt_offset = 252;

    /* Option: Client Identifier */
    if (opt_offset + 2 + MAC_ADDR_SIZE < 255) {
        buf[opt_offset++] = 61;  /* Client Identifier */
        buf[opt_offset++] = MAC_ADDR_SIZE + 1;
        buf[opt_offset++] = 1;   /* Hardware type */
        memcpy(&buf[opt_offset], iface->mac.octet, MAC_ADDR_SIZE);
        opt_offset += MAC_ADDR_SIZE;
    }

    buf[opt_offset] = 255;  /* Option End */

    /* Send to DHCP server broadcast address */
    sock_addr_t dst = {
        .sin_addr = DHCP_BROADCAST_IP,
        .sin_port = htons(DHCP_SERVER_PORT),
        .sin_family = 2  /* AF_INET */
    };

    return udp_send(iface, DHCP_BROADCAST_IP, DHCP_SERVER_PORT,
                    DHCP_CLIENT_PORT, buf, opt_offset + 1);
}

/* ============================================================================
 * DHCP Request (DHCP Request 消息)
 *
 * Sent by a client to request an IP address from a specific server,
 * or to confirm an offered address.
 * ============================================================================ */

int dhcp_request(net_interface_t *iface, uint32_t xid,
                 uint32_t server_ip, uint32_t requested_ip) {
    if (!iface) return -1;

    uint8_t buf[300];
    memset(buf, 0, sizeof(buf));

    dhcp_packet_t *dhcp = (dhcp_packet_t *)buf;
    dhcp->op = DHCP_BOOT_REQUEST;
    dhcp->htype = 1;
    dhcp->hlen = MAC_ADDR_SIZE;
    dhcp->hops = 0;
    dhcp->xid = xid;
    dhcp->secs = 0;
    dhcp->flags = htons(0x8000);
    dhcp->magic_cookie = htonl(DHCP_MAGIC_COOKIE);

    /* Set client MAC */
    memcpy(dhcp->chaddr, iface->mac.octet, MAC_ADDR_SIZE);

    /* If we have a requested IP, set it */
    if (requested_ip != 0) {
        dhcp->ciaddr = requested_ip;
    }

    int opt_offset = 0;

    /* Option: Message Type = DHCPREQUEST (3) */
    buf[248] = 53;
    buf[249] = 1;
    buf[250] = DHCP_REQUEST;
    buf[251] = 255;
    opt_offset = 252;

    /* Option: Server Identifier */
    if (server_ip != 0) {
        buf[opt_offset++] = 54;  /* Server Identifier */
        buf[opt_offset++] = 4;
        uint8_t *ip_bytes = (uint8_t *)&server_ip;
        buf[opt_offset++] = ip_bytes[0];
        buf[opt_offset++] = ip_bytes[1];
        buf[opt_offset++] = ip_bytes[2];
        buf[opt_offset++] = ip_bytes[3];
    }

    /* Option: Requested IP Address */
    if (requested_ip != 0) {
        buf[opt_offset++] = 50;  /* Requested IP */
        buf[opt_offset++] = 4;
        uint8_t *ip_bytes = (uint8_t *)&requested_ip;
        buf[opt_offset++] = ip_bytes[0];
        buf[opt_offset++] = ip_bytes[1];
        buf[opt_offset++] = ip_bytes[2];
        buf[opt_offset++] = ip_bytes[3];
    }

    /* Option: Client Identifier */
    buf[opt_offset++] = 61;
    buf[opt_offset++] = MAC_ADDR_SIZE + 1;
    buf[opt_offset++] = 1;
    memcpy(&buf[opt_offset], iface->mac.octet, MAC_ADDR_SIZE);
    opt_offset += MAC_ADDR_SIZE;

    buf[opt_offset] = 255;  /* Option End */

    /* Send to DHCP server */
    uint32_t dest = (server_ip != 0) ? server_ip : DHCP_BROADCAST_IP;
    return udp_send(iface, dest, DHCP_SERVER_PORT,
                    DHCP_CLIENT_PORT, buf, opt_offset + 1);
}

/* ============================================================================
 * DHCP Options Parser (DHCP 选项解析器)
 *
 * Parses DHCP options to extract network configuration.
 * Options are stored as: [Type (1B)][Length (1B)][Value (N B)]
 * Terminated by Option 255 (End). Option 0 (Pad) is skipped.
 * ============================================================================ */

int dhcp_parse_options(const uint8_t *options, int len, net_interface_t *iface) {
    if (!options || len <= 0 || !iface) return -1;

    int offset = 0;
    while (offset < len) {
        uint8_t option = options[offset];

        if (option == 255) {
            break;  /* Option End */
        }

        if (option == 0) {
            offset++;  /* Option Pad - skip */
            continue;
        }

        if (offset + 1 >= len) break;  /* Incomplete option */

        uint8_t opt_len = options[offset + 1];
        if (offset + 2 + opt_len > len) break;  /* Out of bounds */

        const uint8_t *opt_val = &options[offset + 2];

        switch (option) {
            case 1:  /* Subnet Mask */
                if (opt_len == 4) {
                    iface->subnet_mask = (opt_val[0] << 24) |
                                         (opt_val[1] << 16) |
                                         (opt_val[2] << 8) |
                                         opt_val[3];
                }
                break;

            case 3:  /* Router/Gateway */
                if (opt_len == 4) {
                    iface->gateway = (opt_val[0] << 24) |
                                     (opt_val[1] << 16) |
                                     (opt_val[2] << 8) |
                                     opt_val[3];
                }
                break;

            case 6:  /* DNS Server */
                if (opt_len == 4) {
                    iface->dns_server = (opt_val[0] << 24) |
                                        (opt_val[1] << 16) |
                                        (opt_val[2] << 8) |
                                        opt_val[3];
                }
                break;

            case 51: /* Lease Time */
                if (opt_len == 4) {
                    uint32_t lease = (opt_val[0] << 24) |
                                     (opt_val[1] << 16) |
                                     (opt_val[2] << 8) |
                                     opt_val[3];
                    (void)lease;  /* Could store lease expiry */
                }
                break;

            default:
                break;
        }

        offset += 2 + opt_len;
    }

    return 0;
}
