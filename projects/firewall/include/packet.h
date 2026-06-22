#ifndef PACKET_H
#define PACKET_H

#include <stdint.h>
#include <stddef.h>
#include <time.h>

// 以太网帧头长度
#define ETH_HEADER_LEN 14

// 以太网类型
#define ETH_TYPE_IP     0x0800
#define ETH_TYPE_ARP    0x0806
#define ETH_TYPE_IPV6   0x86DD

// IP 协议号
#define IP_PROTO_ICMP   1
#define IP_PROTO_TCP    6
#define IP_PROTO_UDP    17

// TCP 标志位
#define TCP_FIN         0x01
#define TCP_SYN         0x02
#define TCP_RST         0x04
#define TCP_PSH         0x08
#define TCP_ACK         0x10
#define TCP_URG         0x20

// 以太网帧头
typedef struct {
    uint8_t  dst_mac[6];    // 目的 MAC 地址
    uint8_t  src_mac[6];    // 源 MAC 地址
    uint16_t ethertype;     // 以太网类型
} __attribute__((packed)) eth_header_t;

// IP 头部
typedef struct {
    uint8_t  ihl : 4;       // 头部长度 (单位: 4字节)
    uint8_t  version : 4;   // IP 版本
    uint8_t  tos;           // 服务类型
    uint16_t total_length;  // 总长度
    uint16_t id;            // 标识
    uint16_t flags_offset;  // 标志和片偏移
    uint8_t  ttl;           // 生存时间
    uint8_t  protocol;      // 协议类型
    uint16_t checksum;      // 校验和
    uint32_t src_ip;        // 源 IP 地址
    uint32_t dst_ip;        // 目的 IP 地址
} __attribute__((packed)) ip_header_t;

// TCP 头部
typedef struct {
    uint16_t src_port;      // 源端口
    uint16_t dst_port;      // 目的端口
    uint32_t seq;           // 序列号
    uint32_t ack;           // 确认号
    uint8_t  reserved : 4;  // 保留位
    uint8_t  data_offset : 4; // 数据偏移 (单位: 4字节)
    uint8_t  flags;         // 标志位
    uint16_t window;        // 窗口大小
    uint16_t checksum;      // 校验和
    uint16_t urgent;        // 紧急指针
} __attribute__((packed)) tcp_header_t;

// UDP 头部
typedef struct {
    uint16_t src_port;      // 源端口
    uint16_t dst_port;      // 目的端口
    uint16_t length;        // 长度
    uint16_t checksum;      // 校验和
} __attribute__((packed)) udp_header_t;

// ICMP 头部
typedef struct {
    uint8_t  type;          // 类型
    uint8_t  code;          // 代码
    uint16_t checksum;      // 校验和
    uint16_t id;            // 标识
    uint16_t sequence;      // 序列号
} __attribute__((packed)) icmp_header_t;

// 解析后的数据包
typedef struct {
    // 原始数据
    uint8_t *data;          // 原始数据指针
    size_t   length;        // 数据长度

    // 解析后的头部
    eth_header_t  *eth;     // 以太网头部
    ip_header_t   *ip;      // IP 头部
    tcp_header_t  *tcp;     // TCP 头部
    udp_header_t  *udp;     // UDP 头部
    icmp_header_t *icmp;    // ICMP 头部

    // 便捷字段
    uint8_t  protocol;      // 协议类型
    uint32_t src_ip;        // 源 IP (网络字节序)
    uint32_t dst_ip;        // 目的 IP (网络字节序)
    uint16_t src_port;      // 源端口 (主机字节序)
    uint16_t dst_port;      // 目的端口 (主机字节序)
    uint8_t  tcp_flags;     // TCP 标志
    size_t   payload_len;   // 载荷长度

    // 时间戳
    time_t timestamp;       // 捕获时间
} packet_t;

// 初始化包解析器
int packet_init(void);

// 解析数据包
int packet_parse(const uint8_t *data, size_t len, packet_t *pkt);

// 获取协议名称
const char *packet_proto_name(uint8_t protocol);

// 获取 TCP 标志字符串
const char *packet_tcp_flags_str(uint8_t flags);

// 打印包信息
void packet_print(const packet_t *pkt);

// 打印 IP 地址
void packet_print_ip(uint32_t ip, char *buf, size_t len);

// 清理资源
void packet_cleanup(void);

#endif /* PACKET_H */
