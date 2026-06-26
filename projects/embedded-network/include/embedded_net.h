/*
 * embedded-network - Embedded TCP/IP Network Stack
 * 
 * A learning project implementing a TCP/IP stack from scratch in C.
 * This project demonstrates the core concepts of network protocols
 * and helps understand how the internet works at the packet level.
 *
 * 嵌入式网络栈 - 一个从零实现的 TCP/IP 协议栈学习项目
 *
 * Architecture:
 *   Application Layer (应用层)    - Socket API, TCP/UDP interfaces
 *   Transport Layer (传输层)       - TCP state machine, UDP datagrams
 *   Internet Layer (网络层)         - IPv4, ICMP, ARP
 *   Link Layer (链路层)            - Ethernet frame handling
 *
 * Data Flow (数据流):
 *   数据封装 → 协议处理 → 网络传输 → 数据接收
 *   Encapsulation → Protocol Processing → Transmission → Reception
 */

#ifndef EMBEDDED_NET_H
#define EMBEDDED_NET_H

#include <stdint.h>
#include <stddef.h>

/* ============================================================================
 * Ethernet Frame Constants (链路层 - Link Layer)
 * 
 * Ethernet is the most common link-layer protocol.
 * Each frame has a 6-byte destination MAC, 6-byte source MAC, and 2-byte type.
 * ============================================================================ */

#define ETHERNET_HEADER_SIZE 14
#define ETHERNET_MIN_FRAME_SIZE 60
#define ETHERNET_MAX_FRAME_SIZE 1518
#define ETHERNET_CRC_SIZE 4
#define MAC_ADDR_SIZE 6

/* Ethernet frame types */
#define ETHER_TYPE_IPv4  0x0800  /* IPv4 packet */
#define ETHER_TYPE_ARP   0x0806  /* ARP request/reply */
#define ETHER_TYPE_RARP  0x8035  /* Reverse ARP */

/* Broadcast MAC address */
#define BROADCAST_MAC {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}

/* ============================================================================
 * MAC Address Structure (MAC 地址结构)
 * 
 * MAC addresses uniquely identify network interfaces at the link layer.
 * Format: XX:XX:XX:XX:XX:XX where each X is a hex digit.
 * ============================================================================ */

typedef struct {
    uint8_t octet[MAC_ADDR_SIZE];
} mac_addr_t;

/* ============================================================================
 * Ethernet Frame Structure (以太网帧结构)
 * 
 * An Ethernet frame carries data between directly connected devices.
 * Structure: [Dst MAC (6B)][Src MAC (6B)][Type (2B)][Payload (46-1500B)][CRC (4B)]
 * ============================================================================ */

typedef struct {
    mac_addr_t dst_mac;
    mac_addr_t src_mac;
    uint16_t ether_type;
    uint8_t payload[];  /* Flexible array member for variable-length payload */
} ethernet_frame_t;

/* ============================================================================
 * ARP Protocol (地址解析协议)
 * 
 * ARP maps IP addresses to MAC addresses on a local network.
 * When a device needs to send data to an IP, it first needs the MAC address.
 * 
 * ARP Request: "Who has IP x.x.x.x? Tell me, I'm at y.y.y.y" (broadcast)
 * ARP Reply:   "I have x.x.x.x, my MAC is a.a.a.a" (unicast)
 * ============================================================================ */

#define ARP_REQUEST 1
#define ARP_REPLY   2

typedef struct {
    uint16_t hardware_type;    /* 1 = Ethernet */
    uint16_t protocol_type;    /* 0x0800 = IPv4 */
    uint8_t  hardware_size;    /* 6 for Ethernet */
    uint8_t  protocol_size;    /* 4 for IPv4 */
    uint16_t opcode;           /* ARP_REQUEST or ARP_REPLY */
    mac_addr_t sender_mac;     /* Sender's MAC address */
    uint32_t  sender_ip;       /* Sender's IP address (network byte order) */
    mac_addr_t target_mac;     /* Target's MAC address */
    uint32_t  target_ip;       /* Target's IP address (network byte order) */
} arp_packet_t;

#define ARP_HEADER_SIZE 28

/* ============================================================================
 * IPv4 Protocol (互联网协议版本4)
 * 
 * IPv4 is the primary network layer protocol of the internet.
 * Each packet contains source/destination IP addresses and routing info.
 * 
 * Key fields:
 *   - Version (4 bits): IP version (4)
 *   - IHL (4 bits): Header length in 32-bit words
 *   - Total Length: Entire packet size including header
 *   - Identification: Unique packet identifier for fragmentation
 *   - Flags: Fragment control flags
 *   - TTL: Time to live - decremented each hop, packet discarded at 0
 *   - Protocol: Upper layer protocol (6=TCP, 17=UDP, 1=ICMP)
 *   - Header Checksum: Error detection for header only
 * ============================================================================ */

#define IPv4_HEADER_SIZE 20
#define IPv4_MAX_PACKET_SIZE 65535
#define IPv4_MAX_TTL 255

/* IPv4 version and IHL combined (version 4, 20-byte header = 5 * 4 bytes) */
#define IPv4_VERSION_IHL 0x45

/* Protocol numbers */
#define IP_PROTO_ICMP 1
#define IP_PROTO_TCP  6
#define IP_PROTO_UDP  17

/* IPv4 flags */
#define IP_FLAG_DF 0x4000  /* Don't Fragment */

typedef struct {
    uint8_t  version_ihl;     /* Version (4 bits) + IHL (4 bits) */
    uint8_t  dscp_ecn;        /* Differentiated Services / ECN */
    uint16_t total_length;    /* Total length of packet in bytes */
    uint16_t identification;  /* Identification field */
    uint16_t flags_fragment;  /* Flags + Fragment offset */
    uint8_t  ttl;             /* Time to live */
    uint8_t  protocol;        /* Upper layer protocol */
    uint16_t header_checksum; /* Header checksum */
    uint32_t src_ip;          /* Source IP address (network byte order) */
    uint32_t dst_ip;          /* Destination IP address (network byte order) */
    /* Options follow if IHL > 5 */
} ipv4_header_t;

/* ============================================================================
 * ICMP Protocol (互联网控制消息协议)
 * 
 * ICMP is used for network diagnostics and error reporting.
 * Ping uses ICMP Echo Request (type 8) and Echo Reply (type 0).
 * 
 * Ping flow:
 *   Host A -> ICMP Echo Request -> Host B
 *   Host B -> ICMP Echo Reply   -> Host A
 *   Round-trip time = Reply time - Request time
 * ============================================================================ */

#define ICMP_ECHO_REPLY     0
#define ICMP_ECHO_REQUEST   8
#define ICMP_HEADER_SIZE    8

typedef struct {
    uint8_t  type;        /* ICMP message type (0=reply, 8=request) */
    uint8_t  code;        /* ICMP code (always 0 for echo) */
    uint16_t checksum;    /* ICMP checksum */
    uint16_t identifier;  /* Identifier (usually PID) */
    uint16_t sequence;    /* Sequence number */
    uint8_t  data[];      /* Echo data (variable length) */
} icmp_packet_t;

/* ============================================================================
 * UDP Protocol (用户数据报协议)
 * 
 * UDP is a connectionless, unreliable transport protocol.
 * It adds multiplexing (ports) to IP datagrams with minimal overhead.
 * 
 * UDP header (8 bytes):
 *   - Source Port: 2 bytes
 *   - Destination Port: 2 bytes
 *   - Length: 2 bytes (UDP header + data)
 *   - Checksum: 2 bytes (optional in IPv4)
 * ============================================================================ */

#define UDP_HEADER_SIZE 8
#define UDP_MIN_PACKET_SIZE 28  /* Ethernet + IP + UDP + 1 byte payload */

typedef struct {
    uint16_t src_port;      /* Source port number */
    uint16_t dst_port;      /* Destination port number */
    uint16_t length;        /* UDP datagram length */
    uint16_t checksum;      /* UDP checksum */
    uint8_t  data[];        /* Payload data */
} udp_header_t;

/* ============================================================================
 * TCP Protocol (传输控制协议)
 * 
 * TCP provides reliable, ordered, bidirectional byte-stream delivery.
 * 
 * TCP State Machine (TCP 状态机):
 * 
 *   LISTEN ----[SYN-RCV]----> SYN-SENT ----[SYN-ACK]--> SYN-RCV
 *                                                      |
 *   [FIN-WAIT-2] <--- FIN --- ESTABLISHED --- [ACK] ---
 *       |                     |
 *   [TIME-WAIT] -----------> CLOSE-WAIT ---> CLOSING ---> LAST-ACK
 *       |                        |
 *     (2MSL)                  CLOSED
 * 
 * TCP Flags (TCP 标志位):
 *   SYN (Synchronize) - Start connection, exchange initial sequence numbers
 *   ACK (Acknowledge) - Acknowledge received data
 *   FIN (Finish)      - Close connection gracefully
 *   RST (Reset)       - Abort connection immediately
 *   PSH (Push)        - Force receiver to process data immediately
 *   URG (Urgent)      - Urgent data pointer is valid
 * ============================================================================ */

#define TCP_HEADER_SIZE_MIN 20
#define TCP_MAX_OPTIONS_SIZE 40
#define TCP_MAX_HEADER_SIZE (TCP_HEADER_SIZE_MIN + TCP_MAX_OPTIONS_SIZE)

/* TCP flag bits */
#define TCP_FLAG_FIN 0x01
#define TCP_FLAG_SYN 0x02
#define TCP_FLAG_RST 0x04
#define TCP_FLAG_PSH 0x08
#define TCP_FLAG_ACK 0x10
#define TCP_FLAG_URG 0x20

/* TCP states (TCP 状态) */
typedef enum {
    TCP_CLOSED,
    TCP_LISTEN,
    TCP_SYN_SENT,
    TCP_SYN_RECEIVED,
    TCP_ESTABLISHED,
    TCP_FIN_WAIT_1,
    TCP_FIN_WAIT_2,
    TCP_CLOSE_WAIT,
    TCP_CLOSING,
    TCP_LAST_ACK,
    TCP_TIME_WAIT
} tcp_state_t;

/* TCP connection configuration */
#define TCP_DEFAULT_MSS 1460
#define TCP_DEFAULT_SRTT 500      /* Smoothed RTT in ms */
#define TCP_DEFAULT_RTO 1000       /* Retransmission timeout in ms */
#define TCP_MAX_RETRANSMISSIONS 4  /* Maximum retransmission attempts */
#define TCP_WINDOW_SIZE 65535      /* Maximum window size */

/* TCP segment structure */
typedef struct {
    uint16_t src_port;          /* Source port */
    uint16_t dst_port;          /* Destination port */
    uint32_t seq_num;           /* Sequence number */
    uint32_t ack_num;           /* Acknowledgment number */
    uint8_t  data_offset_flags; /* Data offset (4 bits) + reserved (6 bits) + flags (6 bits) */
    uint16_t window;            /* Window size */
    uint16_t checksum;          /* TCP checksum */
    uint16_t urgent_pointer;    /* Urgent pointer */
    uint8_t  options[TCP_MAX_OPTIONS_SIZE];  /* Options (padding to 20-byte minimum) */
    uint8_t  payload[];         /* TCP segment payload */
} tcp_segment_t;

/* Get TCP header length from data_offset_flags */
static inline uint8_t tcp_data_offset(const uint8_t *flags) {
    uint8_t doff = (*flags >> 4) & 0x0F;
    return doff * 4;
}

/* Get TCP flags from data_offset_flags */
static inline uint8_t tcp_flags(const uint8_t *flags) {
    return *flags & 0x3F;
}

/* ============================================================================
 * Socket API (套接字 API)
 * 
 * The Socket API provides a standardized interface for network communication.
 * It abstracts the underlying protocol details into a file-descriptor-like model.
 * 
 * Socket types:
 *   - SOCK_STREAM: TCP - reliable, ordered, connection-oriented
 *   - SOCK_DGRAM:  UDP - datagram, unordered, connectionless
 * 
 * Socket workflow (套接字工作流):
 *   Server: socket() -> bind() -> listen() -> accept() -> recv()/send() -> close()
 *   Client: socket() -> connect() -> send()/recv() -> close()
 * ============================================================================ */

#define MAX_SOCKETS 8
#define SOCKET_INVALID -1
#define SOMAXCONN 128
#define SOCK_STREAM 1
#define SOCK_DGRAM  2

/* Socket address structure (simplified IPv4) */
typedef struct {
    uint32_t sin_addr;      /* IP address (network byte order) */
    uint16_t sin_port;      /* Port number (network byte order) */
    uint8_t  sin_family;    /* Address family (AF_INET = 2) */
} sock_addr_t;

/* Socket structure */
typedef struct socket {
    int                  fd;            /* Socket file descriptor */
    int                  type;          /* SOCK_STREAM or SOCK_DGRAM */
    tcp_state_t        state;         /* TCP state for stream sockets */
    sock_addr_t        local_addr;    /* Local address */
    sock_addr_t        peer_addr;     /* Peer address */
    uint8_t            rbuf[4096];    /* Receive buffer */
    int                rbuf_len;      /* Received data length */
    int                rbuf_offset;   /* Read offset in buffer */
    uint32_t           snd_seq;       /* Send sequence number */
    uint32_t           rcv_seq;       /* Receive sequence number */
    uint32_t           snd_una;       /* Send unacknowledged (first unacked) */
    uint16_t           window;        /* Advertised window */
    int                mss;           /* Maximum segment size */
    int                is_bound;      /* Whether socket is bound */
    int                is_listening;  /* Whether socket is listening */
    int                is_connected;  /* Whether socket is connected */
    void              (*handler)(void *arg); /* Event callback */
    void              *handler_arg;   /* Callback argument */
    uint32_t           srtt;          /* Smoothed round-trip time (ms * 16) */
    uint32_t           rttvar;        /* RTT variance */
    uint32_t           retransmit_to; /* Next retransmission timestamp */
    int                retransmit_cnt; /* Retransmission count */
} socket_t;

/* ============================================================================
 * DHCP Protocol (动态主机配置协议)
 * 
 * DHCP automatically assigns IP addresses to devices on a network.
 * 
 * DHCP flow (DORA - Discover, Offer, Request, Acknowledge):
 *   1. Discover: Client broadcasts "I need an IP" (UDP 67->68)
 *   2. Offer:   Server responds "I offer IP x.x.x.x"
 *   3. Request: Client broadcasts "I accept IP x.x.x.x"
 *   4. Ack:     Server confirms "IP x.x.x.x is yours"
 * ============================================================================ */

#define DHCP_DISCOVER  1
#define DHCP_OFFER     2
#define DHCP_REQUEST   3
#define DHCP_DECLINE   4
#define DHCP_ACK       5
#define DHCP_NAK       6
#define DHCP_RELEASE   7

#define DHCP_BOOT_REQUEST  1
#define DHCP_BOOT_REPLY    2

#define DHCP_MAGIC_COOKIE 0x63825363UL
#define DHCP_OPTION_END   255
#define DHCP_OPTION_PAD   0
#define DHCP_OPTION_SUBNET_MASK 1
#define DHCP_OPTION_ROUTER      3
#define DHCP_OPTION_DNS         6
#define DHCP_OPTION_REQUESTED_IP 50
#define DHCP_OPTION_LEASE_TIME  51
#define DHCP_OPTION_MSG_TYPE    53
#define DHCP_OPTION_SERVER_ID   54
#define DHCP_OPTION_CLIENT_ID   61
#define DHCP_OPTION_MAX_LEN     10

typedef struct {
    uint8_t  op;              /* Message type: 1=bootrequest, 2=bootreply */
    uint8_t  htype;           /* Hardware type (1=Ethernet) */
    uint8_t  hlen;            /* Hardware address length */
    uint8_t  hops;            /* Hop count */
    uint32_t xid;             /* Transaction ID */
    uint16_t secs;            /* Elapsed time */
    uint16_t flags;           /* Flags */
    uint32_t ciaddr;          /* Client IP address */
    uint32_t yiaddr;          /* 'Your' (client) IP address */
    uint32_t siaddr;          /* Next server IP address */
    uint32_t giaddr;          /* Gateway IP address */
    uint8_t  chaddr[16];      /* Client hardware address */
    uint8_t  sname[64];       /* Server host name */
    uint8_t  file[128];       /* Boot file name */
    uint32_t magic_cookie;    /* DHCP magic cookie */
    uint8_t  options[DHCP_OPTION_MAX_LEN * 64]; /* Options */
} dhcp_packet_t;

/* ============================================================================
 * Network Interface (网络接口)
 * 
 * Represents a network interface with its configuration.
 * ============================================================================ */

typedef struct {
    mac_addr_t       mac;           /* Interface MAC address */
    uint32_t         ip_addr;       /* IP address (network byte order) */
    uint32_t         subnet_mask;   /* Subnet mask */
    uint32_t         gateway;       /* Default gateway */
    uint32_t         dns_server;    /* DNS server address */
    int              is_up;         /* Interface status */
    int              has_ip;        /* Whether IP is configured */
    int              dhcp_enabled;  /* Whether DHCP is enabled */
    /* ARP cache */
    uint32_t         arp_table[32]; /* Cached IP addresses */
    mac_addr_t       arp_table_mac[32];
    uint8_t          arp_table_count;
} net_interface_t;

/* ============================================================================
 * Core Functions (核心函数)
 * ============================================================================ */

/* Get pointer to global network interface */
net_interface_t* net_get_interface(void);

/* Get pointer to sockets array */
socket_t* net_get_sockets(void);

/* Get number of active sockets */
int net_get_socket_count(void);

/* Increment socket count */
void net_increment_socket_count(void);

/* Initialize the network stack */
int net_stack_init(net_interface_t *iface);

/* Send raw bytes on the interface */
int net_send(const uint8_t *data, int len);

/* Send Ethernet frame */
int net_send_frame(const mac_addr_t *dst, uint16_t type, const uint8_t *payload, int len);

/* ============================================================================
 * Checksum Calculation (校验和计算)
 * 
 * The Internet Checksum is used by IP, ICMP, TCP, and UDP.
 * 
 * Algorithm:
 *   1. Set checksum field to 0
 *   2. Compute sum of all 16-bit words using ones' complement addition
 *   3. Add any carry bits back into the sum
 *   4. Take ones' complement of the result
 * 
 * This detects accidental corruption in transmission.
 * ============================================================================ */

/* Compute Internet checksum */
uint16_t checksum(const void *data, int len);

/* Compute pseudo-header checksum for ICMP/TCP/UDP */
uint16_t pseudo_checksum(uint32_t src_ip, uint32_t dst_ip, 
                         uint8_t protocol, uint16_t len);

/* ============================================================================
 * ARP Functions (ARP 函数)
 * ============================================================================ */

/* Process incoming ARP packet */
int arp_input(const uint8_t *frame, int len);

/* Send ARP request to resolve IP to MAC */
int arp_request(net_interface_t *iface, uint32_t target_ip);

/* Send ARP reply */
int arp_reply(net_interface_t *iface, uint32_t target_ip, const mac_addr_t *target_mac);

/* Lookup MAC address for an IP in ARP cache */
int arp_lookup(uint32_t ip, mac_addr_t *mac_out);

/* ============================================================================
 * IPv4 Functions (IPv4 函数)
 * ============================================================================ */

/* Process incoming IPv4 packet */
int ipv4_input(const uint8_t *data, int len);

/* Create and send IPv4 packet */
int ipv4_send(net_interface_t *iface, uint32_t dst_ip, uint8_t protocol,
              const uint8_t *payload, int payload_len);

/* ============================================================================
 * ICMP Functions (ICMP 函数)
 * ============================================================================ */

/* Process incoming ICMP packet */
int icmp_input(const uint8_t *data, int len);

/* Send ICMP Echo Request (ping) */
int icmp_echo_request(net_interface_t *iface, uint32_t dst_ip, 
                      uint16_t identifier, uint16_t seq_num);

/* Send ICMP Echo Reply */
int icmp_echo_reply(const uint8_t *data, int len);

/* ============================================================================
 * UDP Functions (UDP 函数)
 * ============================================================================ */

/* Process incoming UDP datagram */
int udp_input(const uint8_t *data, int len);

/* Send UDP datagram */
int udp_send(net_interface_t *iface, uint32_t dst_ip, uint16_t dst_port,
             uint16_t src_port, const uint8_t *data, int len);

/* ============================================================================
 * TCP Functions (TCP 函数)
 * ============================================================================ */

/* Process incoming TCP segment */
int tcp_input(const uint8_t *data, int len);

/* Process TCP segment by connection */
int tcp_process_segment(socket_t *sock, const uint8_t *data, int len);

/* Handle TCP state machine */
tcp_state_t tcp_state_machine(socket_t *sock, uint8_t flags);

/* Send TCP segment */
int tcp_send(socket_t *sock, const uint8_t *data, int len, uint8_t flags);

/* Send TCP segment with specific flags */
int tcp_send_segment(socket_t *sock, uint32_t seq, uint32_t ack,
                     const uint8_t *data, int len, uint8_t flags);

/* Retransmission timeout handling */
void tcp_handle_timeout(socket_t *sock);

/* ============================================================================
 * Socket API Functions (套接字 API 函数)
 * ============================================================================ */

/* Create a socket */
int socket_create(int type);

/* Bind socket to local address */
int socket_bind(int fd, const sock_addr_t *addr);

/* Listen for connections (TCP) */
int socket_listen(int fd, int backlog);

/* Accept incoming connection (TCP) */
int socket_accept(int fd, sock_addr_t *addr);

/* Connect to remote address (TCP) */
int socket_connect(int fd, const sock_addr_t *addr);

/* Send data */
int socket_send(int fd, const void *buf, int len);

/* Send data to specific address (UDP) */
int socket_sendto(int fd, const void *buf, int len, const sock_addr_t *addr);

/* Receive data */
int socket_recv(int fd, void *buf, int len);

/* Receive data from specific address (UDP) */
int socket_recvfrom(int fd, void *buf, int len, sock_addr_t *addr);

/* Close socket */
int socket_close(int fd);

/* ============================================================================
 * DHCP Functions (DHCP 函数)
 * ============================================================================ */

/* Send DHCP discover message */
int dhcp_discover(net_interface_t *iface, uint32_t xid);

/* Send DHCP request message */
int dhcp_request(net_interface_t *iface, uint32_t xid, 
                 uint32_t server_ip, uint32_t requested_ip);

/* Parse DHCP options */
int dhcp_parse_options(const uint8_t *options, int len, net_interface_t *iface);

/* ============================================================================
 * Utility Functions (工具函数)
 * ============================================================================ */

/* Convert IP address to string */
const char* ip_to_string(uint32_t ip);

/* Convert string to IP address (simplified) */
uint32_t string_to_ip(const char *str);

/* Convert port to network byte order */
uint16_t htons(uint16_t hostshort);

/* Convert port from network byte order */
uint16_t ntohs(uint16_t netshort);

/* Convert IP from host to network byte order */
uint32_t htonl(uint32_t hostlong);

/* Convert IP from network to host byte order */
uint32_t ntohl(uint32_t netlong);

/* Debug printing */
void debug_print_hex(const char *label, const uint8_t *data, int len);
void debug_print_mac(const char *label, const mac_addr_t *mac);
void debug_print_ip(const char *label, uint32_t ip);

#endif /* EMBEDDED_NET_H */
