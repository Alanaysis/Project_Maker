#ifndef IDS_H
#define IDS_H

#include <stdint.h>
#include <stddef.h>
#include <time.h>
#include "packet.h"

// 告警类型
typedef enum {
    ALERT_SYN_FLOOD = 0,    // SYN Flood 攻击
    ALERT_PORT_SCAN,        // 端口扫描
    ALERT_ANOMALY_PKT,      // 异常包
    ALERT_RATE_EXCEEDED,    // 速率超限
    ALERT_ICMP_FLOOD,       // ICMP Flood
    ALERT_UDP_FLOOD         // UDP Flood
} alert_type_t;

// 告警记录
typedef struct {
    alert_type_t type;      // 告警类型
    time_t timestamp;       // 时间戳
    uint32_t src_ip;        // 源 IP
    uint32_t dst_ip;        // 目的 IP
    uint16_t src_port;      // 源端口
    uint16_t dst_port;      // 目的端口
    uint8_t  protocol;      // 协议
    char description[256];  // 描述
} alert_t;

// 速率统计条目
typedef struct {
    uint32_t ip;            // IP 地址
    time_t window_start;    // 窗口开始时间
    uint32_t count;         // 计数
    uint8_t  active;        // 活动标志
} rate_stat_t;

// 端口扫描统计
typedef struct {
    uint32_t src_ip;        // 源 IP
    uint16_t ports[256];    // 访问的端口列表
    uint32_t port_count;    // 端口数量
    time_t window_start;    // 窗口开始时间
    uint8_t  active;        // 活动标志
} scan_stat_t;

// IDS 配置
typedef struct {
    uint32_t syn_flood_threshold;   // SYN Flood 阈值 (包/秒)
    uint32_t port_scan_threshold;   // 端口扫描阈值 (端口/分钟)
    uint32_t pkt_size_min;          // 最小包大小
    uint32_t pkt_size_max;          // 最大包大小
    uint32_t icmp_flood_threshold;  // ICMP Flood 阈值
    uint32_t udp_flood_threshold;   // UDP Flood 阈值
} ids_config_t;

// IDS 上下文
typedef struct {
    ids_config_t config;    // 配置

    // 统计数据
    rate_stat_t *syn_stats;     // SYN 统计
    scan_stat_t *scan_stats;    // 扫描统计
    rate_stat_t *icmp_stats;    // ICMP 统计
    rate_stat_t *udp_stats;     // UDP 统计
    size_t stats_capacity;      // 统计容量

    // 告警列表
    alert_t *alerts;            // 告警数组
    size_t alert_count;         // 告警数量
    size_t alert_capacity;      // 告警容量
} ids_context_t;

// 默认配置
#define IDS_DEFAULT_SYN_FLOOD_THRESHOLD     100     // 100 SYN/秒
#define IDS_DEFAULT_PORT_SCAN_THRESHOLD     20      // 20 端口/分钟
#define IDS_DEFAULT_PKT_SIZE_MIN            20      // 最小 20 字节
#define IDS_DEFAULT_PKT_SIZE_MAX            1500    // 最大 1500 字节
#define IDS_DEFAULT_ICMP_FLOOD_THRESHOLD    50      // 50 ICMP/秒
#define IDS_DEFAULT_UDP_FLOOD_THRESHOLD     1000    // 1000 UDP/秒

// 初始化 IDS
ids_context_t *ids_init(void);

// 加载 IDS 配置
int ids_load_config(ids_context_t *ctx, const char *filename);

// 设置默认配置
void ids_set_default_config(ids_context_t *ctx);

// 检测数据包
int ids_detect(ids_context_t *ctx, const packet_t *pkt);

// 获取告警数量
size_t ids_alert_count(const ids_context_t *ctx);

// 获取告警
int ids_get_alerts(ids_context_t *ctx, alert_t *alerts, size_t max_count);

// 打印告警
void ids_print_alerts(const ids_context_t *ctx);

// 清理资源
void ids_cleanup(ids_context_t *ctx);

// 内部检测函数
int ids_detect_syn_flood(ids_context_t *ctx, const packet_t *pkt);
int ids_detect_port_scan(ids_context_t *ctx, const packet_t *pkt);
int ids_detect_anomaly(ids_context_t *ctx, const packet_t *pkt);
int ids_detect_icmp_flood(ids_context_t *ctx, const packet_t *pkt);
int ids_detect_udp_flood(ids_context_t *ctx, const packet_t *pkt);

// 辅助函数：添加告警
int ids_add_alert(ids_context_t *ctx, alert_type_t type, const packet_t *pkt, const char *desc);

// 辅助函数：获取告警类型名称
const char *ids_alert_type_name(alert_type_t type);

#endif /* IDS_H */
