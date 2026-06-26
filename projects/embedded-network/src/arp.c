/*
 * arp.c - ARP (Address Resolution Protocol) implementation
 *
 * ARP maps IP addresses to MAC addresses on a local network segment.
 *
 * Why ARP is needed:
 *   IP packets are routed by IP address, but Ethernet frames are delivered
 *   by MAC address. ARP bridges this gap.
 *
 * ARP Request (broadcast):
 *   "Who has IP 192.168.1.1? Tell 192.168.1.100"
 *   Sent to FF:FF:FF:FF:FF:FF (broadcast)
 *
 * ARP Reply (unicast):
 *   "192.168.1.1 is at AA:BB:CC:DD:EE:FF"
 *   Sent directly to the requester
 *
 * ARP Cache:
 *   To avoid broadcasting for every packet, devices cache ARP entries
 *   with a timeout (typically 4 hours for IPv4).
 */

#include "embedded_net.h"
#include <string.h>
#include <stdio.h>

/* ARP cache entry timeout in seconds */
#define ARP_CACHE_TIMEOUT 300

/* ============================================================================
 * ARP Packet Processing (ARP 数据包处理)
 *
 * When an ARP packet arrives, we:
 *   1. Check if it's for us (target IP matches our IP)
 *   2. Update our ARP cache with the sender's info
 *   3. If it was a request, generate a reply
 * ============================================================================ */

int arp_input(const uint8_t *frame, int len) {
    if (len < (int)(ETHERNET_HEADER_SIZE + ARP_HEADER_SIZE)) {
        return -1;
    }

    /* Skip Ethernet header */
    const arp_packet_t *arp = (const arp_packet_t *)(frame + ETHERNET_HEADER_SIZE);
    net_interface_t *iface = net_get_interface();

    /* Update ARP cache with sender information */
    /* Even if we're not the target, we learn from the sender's info */
    if (!iface) return -1;

    /* Check if this sender's IP is already in our cache */
    int found = 0;
    for (int i = 0; i < iface->arp_table_count; i++) {
        if (iface->arp_table[i] == arp->sender_ip) {
            /* Update existing entry */
            memcpy(&iface->arp_table_mac[i], &arp->sender_mac, sizeof(mac_addr_t));
            found = 1;
            break;
        }
    }

    /* Add new entry if not found */
    if (!found && iface->arp_table_count < 32) {
        iface->arp_table[iface->arp_table_count] = arp->sender_ip;
        memcpy(&iface->arp_table_mac[iface->arp_table_count],
               &arp->sender_mac, sizeof(mac_addr_t));
        iface->arp_table_count++;
    }

    /* If this is a reply, we don't need to do anything special */
    if (arp->opcode == htons(ARP_REPLY)) {
        return 0;
    }

    /* If this is a request and targets us, we reply */
    if (arp->opcode == htons(ARP_REQUEST) &&
        arp->target_ip == iface->ip_addr) {
        /* Send ARP reply */
        arp_packet_t reply;
        memset(&reply, 0, sizeof(reply));
        reply.hardware_type = htons(1);
        reply.protocol_type = htons(ETHER_TYPE_IPv4);
        reply.hardware_size = MAC_ADDR_SIZE;
        reply.protocol_size = 4;
        reply.opcode = htons(ARP_REPLY);
        reply.sender_mac = iface->mac;
        reply.sender_ip = iface->ip_addr;
        reply.target_mac = arp->sender_mac;
        reply.target_ip = arp->sender_ip;

        /* Send reply to requester's MAC */
        mac_addr_t dst;
        memcpy(&dst, &arp->sender_mac, sizeof(mac_addr_t));

        uint8_t buf[sizeof(arp_packet_t)];
        memcpy(buf, &reply, sizeof(reply));
        net_send_frame(&dst, ETHER_TYPE_ARP, buf, sizeof(arp_packet_t));
    }

    return 0;
}

/* ============================================================================
 * ARP Request (ARP 请求)
 *
 * Broadcasts an ARP request to resolve a target IP address.
 * All devices on the local network will receive this broadcast.
 * ============================================================================ */

int arp_request(net_interface_t *iface, uint32_t target_ip) {
    if (!iface) return -1;

    arp_packet_t req;
    memset(&req, 0, sizeof(req));
    req.hardware_type = htons(1);
    req.protocol_type = htons(ETHER_TYPE_IPv4);
    req.hardware_size = MAC_ADDR_SIZE;
    req.protocol_size = 4;
    req.opcode = htons(ARP_REQUEST);
    req.sender_mac = iface->mac;
    req.sender_ip = iface->ip_addr;
    req.target_mac.octet[0] = 0;  /* Unknown */
    req.target_ip = target_ip;

    /* Broadcast to all devices */
    mac_addr_t broadcast;
    broadcast.octet[0] = 0xFF;
    broadcast.octet[1] = 0xFF;
    broadcast.octet[2] = 0xFF;
    broadcast.octet[3] = 0xFF;
    broadcast.octet[4] = 0xFF;
    broadcast.octet[5] = 0xFF;

    uint8_t buf[sizeof(arp_packet_t)];
    memcpy(buf, &req, sizeof(req));
    net_send_frame(&broadcast, ETHER_TYPE_ARP, buf, sizeof(arp_packet_t));

    return 0;
}

/* ============================================================================
 * ARP Reply (ARP 回复)
 *
 * Sends a unicast ARP reply to announce or respond to an IP-to-MAC mapping.
 * ============================================================================ */

int arp_reply(net_interface_t *iface, uint32_t target_ip, const mac_addr_t *target_mac) {
    if (!iface || !target_mac) return -1;

    arp_packet_t reply;
    memset(&reply, 0, sizeof(reply));
    reply.hardware_type = htons(1);
    reply.protocol_type = htons(ETHER_TYPE_IPv4);
    reply.hardware_size = MAC_ADDR_SIZE;
    reply.protocol_size = 4;
    reply.opcode = htons(ARP_REPLY);
    reply.sender_mac = iface->mac;
    reply.sender_ip = iface->ip_addr;
    reply.target_mac = *target_mac;
    reply.target_ip = target_ip;

    uint8_t buf[sizeof(arp_packet_t)];
    memcpy(buf, &reply, sizeof(reply));
    net_send_frame(target_mac, ETHER_TYPE_ARP, buf, sizeof(arp_packet_t));

    return 0;
}

/* ============================================================================
 * ARP Cache Lookup (ARP 缓存查询)
 *
 * Searches the ARP cache for a cached MAC address for the given IP.
 * Returns 0 if found, -1 if not found.
 *
 * If the IP is on the local subnet, we must ARP for it.
 * If it's the gateway, we ARP for the gateway's IP.
 * ============================================================================ */

int arp_lookup(uint32_t ip, mac_addr_t *mac_out) {
    net_interface_t *iface = net_get_interface();
    if (!iface) return -1;

    /* Check ARP cache */
    for (int i = 0; i < iface->arp_table_count; i++) {
        if (iface->arp_table[i] == ip) {
            if (mac_out) {
                memcpy(mac_out, &iface->arp_table_mac[i], sizeof(mac_addr_t));
            }
            return 0;
        }
    }

    return -1;  /* Not found */
}
