/**
 * 包解析模块
 *
 * 本模块负责解析网络数据包的各个层次：
 * - 以太网帧
 * - IP 头部
 * - TCP 头部
 * - UDP 头部
 * - ICMP 头部
 *
 * ⭐ 重点：理解网络字节序（大端序）和主机字节序的转换
 * 💡 思考：为什么需要校验和？如何处理分片？
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <time.h>

#include "packet.h"

/**
 * 初始化包解析器
 *
 * @return 0 成功，-1 失败
 */
int packet_init(void) {
    // 目前不需要初始化
    // 未来可以添加全局配置
    return 0;
}

/**
 * 解析以太网帧头
 *
 * 以太网帧结构：
 * +-------------------+-------------------+---------+
 * | 目的 MAC (6字节)  | 源 MAC (6字节)    | 类型    |
 * +-------------------+-------------------+---------+
 *
 * @param data 原始数据
 * @param len 数据长度
 * @param pkt 解析后的数据包
 * @return 0 成功，-1 失败
 */
static int parse_ethernet(const uint8_t *data, size_t len, packet_t *pkt) {
    if (len < ETH_HEADER_LEN) {
        return -1;
    }

    pkt->eth = (eth_header_t *)data;

    // 注意：ethertype 是网络字节序，需要转换
    // 但这里我们只检查类型，不使用数值，所以可以不转换
    return 0;
}

/**
 * 解析 IP 头部
 *
 * IP 头部结构：
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |Version|  IHL  |Type of Service|          Total Length         |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |         Identification        |Flags|      Fragment Offset    |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |  Time to Live |    Protocol   |         Header Checksum       |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |                       Source Address                          |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |                    Destination Address                        |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 * ⭐ 重点：理解 IHL（Internet Header Length）字段
 *    IHL 表示 IP 头部的长度，单位是 4 字节
 *    最小值是 5（20 字节），最大值是 15（60 字节）
 *
 * @param data 原始数据
 * @param len 数据长度
 * @param pkt 解析后的数据包
 * @return 0 成功，-1 失败
 */
static int parse_ip(const uint8_t *data, size_t len, packet_t *pkt) {
    if (len < sizeof(ip_header_t)) {
        return -1;
    }

    pkt->ip = (ip_header_t *)data;

    // ⭐ 验证 IP 版本
    if (pkt->ip->version != 4) {
        return -1;  // 只支持 IPv4
    }

    // ⭐ 计算 IP 头部长度
    uint8_t ip_header_len = pkt->ip->ihl * 4;
    if (ip_header_len < sizeof(ip_header_t) || ip_header_len > len) {
        return -1;
    }

    // ⭐ 验证总长度
    uint16_t total_length = ntohs(pkt->ip->total_length);
    if (total_length > len) {
        return -1;
    }

    // 提取便捷字段
    pkt->protocol = pkt->ip->protocol;
    pkt->src_ip = pkt->ip->src_ip;  // 保持网络字节序
    pkt->dst_ip = pkt->ip->dst_ip;

    return 0;
}

/**
 * 解析 TCP 头部
 *
 * TCP 头部结构：
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |          Source Port          |       Destination Port        |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |                        Sequence Number                        |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |                    Acknowledgment Number                      |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |  Data |       |C|E|U|A|P|R|S|F|                               |
 * | Offset| Rsrvd |W|C|R|C|S|S|Y|I|            Window             |
 * |       |       |R|E|G|K|H|T|N|N|                               |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |           Checksum            |         Urgent Pointer        |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 * ⭐ 重点：理解 TCP 标志位
 *    SYN - 同步序列号，用于建立连接
 *    ACK - 确认号有效
 *    FIN - 发送方完成发送
 *    RST - 重置连接
 *    PSH - 推送数据
 *    URG - 紧急指针有效
 *
 * @param data 原始数据
 * @param len 数据长度
 * @param pkt 解析后的数据包
 * @return 0 成功，-1 失败
 */
static int parse_tcp(const uint8_t *data, size_t len, packet_t *pkt) {
    if (len < sizeof(tcp_header_t)) {
        return -1;
    }

    pkt->tcp = (tcp_header_t *)data;

    // ⭐ 计算 TCP 头部长度
    uint8_t tcp_header_len = pkt->tcp->data_offset * 4;
    if (tcp_header_len < sizeof(tcp_header_t) || tcp_header_len > len) {
        return -1;
    }

    // 提取便捷字段
    pkt->src_port = ntohs(pkt->tcp->src_port);
    pkt->dst_port = ntohs(pkt->tcp->dst_port);
    pkt->tcp_flags = pkt->tcp->flags;

    // 计算载荷长度
    pkt->payload_len = len - tcp_header_len;

    return 0;
}

/**
 * 解析 UDP 头部
 *
 * UDP 头部结构：
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |          Source Port          |       Destination Port        |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |            Length             |           Checksum            |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 * 💡 思考：UDP 和 TCP 的主要区别是什么？
 *    - UDP 是无连接的，TCP 是面向连接的
 *    - UDP 不保证可靠性，TCP 保证可靠性
 *    - UDP 没有流量控制，TCP 有流量控制
 *
 * @param data 原始数据
 * @param len 数据长度
 * @param pkt 解析后的数据包
 * @return 0 成功，-1 失败
 */
static int parse_udp(const uint8_t *data, size_t len, packet_t *pkt) {
    if (len < sizeof(udp_header_t)) {
        return -1;
    }

    pkt->udp = (udp_header_t *)data;

    // 提取便捷字段
    pkt->src_port = ntohs(pkt->udp->src_port);
    pkt->dst_port = ntohs(pkt->udp->dst_port);

    // 计算载荷长度
    pkt->payload_len = ntohs(pkt->udp->length) - sizeof(udp_header_t);

    return 0;
}

/**
 * 解析 ICMP 头部
 *
 * ICMP 头部结构：
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |     Type      |      Code     |          Checksum             |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |           Identifier          |        Sequence Number        |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *
 * 常见 ICMP 类型：
 * - Type 0: Echo Reply (ping 回复)
 * - Type 3: Destination Unreachable
 * - Type 8: Echo Request (ping 请求)
 * - Type 11: Time Exceeded
 *
 * @param data 原始数据
 * @param len 数据长度
 * @param pkt 解析后的数据包
 * @return 0 成功，-1 失败
 */
static int parse_icmp(const uint8_t *data, size_t len, packet_t *pkt) {
    if (len < sizeof(icmp_header_t)) {
        return -1;
    }

    pkt->icmp = (icmp_header_t *)data;

    // ICMP 没有端口概念，设置为 0
    pkt->src_port = 0;
    pkt->dst_port = 0;

    // 计算载荷长度
    pkt->payload_len = len - sizeof(icmp_header_t);

    return 0;
}

/**
 * 解析数据包
 *
 * 解析流程：
 * 1. 解析以太网帧
 * 2. 解析 IP 头部
 * 3. 根据协议类型解析传输层头部
 *
 * @param data 原始数据
 * @param len 数据长度
 * @param pkt 解析后的数据包
 * @return 0 成功，-1 失败
 */
int packet_parse(const uint8_t *data, size_t len, packet_t *pkt) {
    if (!data || !pkt || len == 0) {
        return -1;
    }

    // 清空数据包结构
    memset(pkt, 0, sizeof(packet_t));

    // 保存原始数据
    pkt->data = (uint8_t *)data;
    pkt->length = len;
    pkt->timestamp = time(NULL);

    // 解析以太网帧
    if (parse_ethernet(data, len, pkt) != 0) {
        return -1;
    }

    // 检查是否是 IP 包
    uint16_t ethertype = ntohs(pkt->eth->ethertype);
    if (ethertype != ETH_TYPE_IP) {
        return -1;  // 只处理 IPv4
    }

    // 跳过以太网头部
    const uint8_t *ip_data = data + ETH_HEADER_LEN;
    size_t ip_len = len - ETH_HEADER_LEN;

    // 解析 IP 头部
    if (parse_ip(ip_data, ip_len, pkt) != 0) {
        return -1;
    }

    // 计算 IP 头部长度
    uint8_t ip_header_len = pkt->ip->ihl * 4;

    // 跳过 IP 头部
    const uint8_t *transport_data = ip_data + ip_header_len;
    size_t transport_len = ip_len - ip_header_len;

    // 根据协议类型解析传输层头部
    switch (pkt->protocol) {
        case IP_PROTO_TCP:
            if (parse_tcp(transport_data, transport_len, pkt) != 0) {
                return -1;
            }
            break;

        case IP_PROTO_UDP:
            if (parse_udp(transport_data, transport_len, pkt) != 0) {
                return -1;
            }
            break;

        case IP_PROTO_ICMP:
            if (parse_icmp(transport_data, transport_len, pkt) != 0) {
                return -1;
            }
            break;

        default:
            // 不支持的协议
            pkt->payload_len = transport_len;
            break;
    }

    return 0;
}

/**
 * 获取协议名称
 *
 * @param protocol 协议号
 * @return 协议名称字符串
 */
const char *packet_proto_name(uint8_t protocol) {
    switch (protocol) {
        case IP_PROTO_TCP:  return "TCP";
        case IP_PROTO_UDP:  return "UDP";
        case IP_PROTO_ICMP: return "ICMP";
        default:            return "UNKNOWN";
    }
}

/**
 * 获取 TCP 标志字符串
 *
 * @param flags TCP 标志位
 * @return 标志字符串
 */
const char *packet_tcp_flags_str(uint8_t flags) {
    static char buf[32];
    int pos = 0;

    if (flags & TCP_SYN) buf[pos++] = 'S';
    if (flags & TCP_ACK) buf[pos++] = 'A';
    if (flags & TCP_FIN) buf[pos++] = 'F';
    if (flags & TCP_RST) buf[pos++] = 'R';
    if (flags & TCP_PSH) buf[pos++] = 'P';
    if (flags & TCP_URG) buf[pos++] = 'U';
    buf[pos] = '\0';

    return buf;
}

/**
 * 打印 IP 地址
 *
 * ⭐ 重点：理解网络字节序
 *    IP 地址在网络中以大端序存储
 *    使用 inet_ntoa() 进行转换
 *
 * @param ip IP 地址（网络字节序）
 * @param buf 缓冲区
 * @param len 缓冲区长度
 */
void packet_print_ip(uint32_t ip, char *buf, size_t len) {
    struct in_addr addr;
    addr.s_addr = ip;
    strncpy(buf, inet_ntoa(addr), len - 1);
    buf[len - 1] = '\0';
}

/**
 * 打印包信息
 *
 * @param pkt 数据包
 */
void packet_print(const packet_t *pkt) {
    if (!pkt) return;

    char src_ip[INET_ADDRSTRLEN];
    char dst_ip[INET_ADDRSTRLEN];
    char time_str[64];
    struct tm *tm_info;

    // 格式化时间
    tm_info = localtime(&pkt->timestamp);
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_info);

    // 格式化 IP 地址
    packet_print_ip(pkt->src_ip, src_ip, sizeof(src_ip));
    packet_print_ip(pkt->dst_ip, dst_ip, sizeof(dst_ip));

    // 打印包信息
    printf("[%s] ", time_str);
    printf("%s ", packet_proto_name(pkt->protocol));

    if (pkt->protocol == IP_PROTO_TCP || pkt->protocol == IP_PROTO_UDP) {
        printf("%s:%d → %s:%d", src_ip, pkt->src_port, dst_ip, pkt->dst_port);
    } else {
        printf("%s → %s", src_ip, dst_ip);
    }

    if (pkt->protocol == IP_PROTO_TCP) {
        printf(" [%s]", packet_tcp_flags_str(pkt->tcp_flags));
    }

    printf(" len=%zu", pkt->length);
    printf("\n");
}

/**
 * 清理资源
 */
void packet_cleanup(void) {
    // 目前不需要清理
}
