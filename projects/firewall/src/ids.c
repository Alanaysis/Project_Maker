/**
 * 入侵检测模块
 *
 * 本模块负责：
 * 1. 检测 SYN Flood 攻击
 * 2. 检测端口扫描
 * 3. 检测异常数据包
 * 4. 生成告警
 *
 * ⭐ 重点：理解入侵检测的基本原理
 *    - 基于阈值的检测：统计异常行为
 *    - 基于规则的检测：匹配已知攻击模式
 *    - 基于异常的检测：偏离正常行为
 *
 * 💡 思考：如何降低误报率？
 *    - 设置合理的阈值
 *    - 考虑时间窗口
 *    - 结合多个指标
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "ids.h"

// 默认统计容量
#define DEFAULT_STATS_CAPACITY 1024
#define DEFAULT_ALERT_CAPACITY 256

/**
 * 初始化 IDS
 *
 * @return IDS 上下文，失败返回 NULL
 */
ids_context_t *ids_init(void) {
    ids_context_t *ctx;

    ctx = (ids_context_t *)calloc(1, sizeof(ids_context_t));
    if (!ctx) {
        return NULL;
    }

    // 初始化互斥锁
    if (pthread_mutex_init(&ctx->stats_mutex, NULL) != 0) {
        free(ctx);
        return NULL;
    }
    if (pthread_mutex_init(&ctx->alert_mutex, NULL) != 0) {
        pthread_mutex_destroy(&ctx->stats_mutex);
        free(ctx);
        return NULL;
    }

    // 设置默认配置
    ids_set_default_config(ctx);

    // 分配统计数组
    ctx->stats_capacity = DEFAULT_STATS_CAPACITY;

    ctx->syn_stats = (rate_stat_t *)calloc(ctx->stats_capacity, sizeof(rate_stat_t));
    if (!ctx->syn_stats) {
        pthread_mutex_destroy(&ctx->alert_mutex);
        pthread_mutex_destroy(&ctx->stats_mutex);
        free(ctx);
        return NULL;
    }

    ctx->scan_stats = (scan_stat_t *)calloc(ctx->stats_capacity, sizeof(scan_stat_t));
    if (!ctx->scan_stats) {
        free(ctx->syn_stats);
        pthread_mutex_destroy(&ctx->alert_mutex);
        pthread_mutex_destroy(&ctx->stats_mutex);
        free(ctx);
        return NULL;
    }

    ctx->icmp_stats = (rate_stat_t *)calloc(ctx->stats_capacity, sizeof(rate_stat_t));
    if (!ctx->icmp_stats) {
        free(ctx->scan_stats);
        free(ctx->syn_stats);
        pthread_mutex_destroy(&ctx->alert_mutex);
        pthread_mutex_destroy(&ctx->stats_mutex);
        free(ctx);
        return NULL;
    }

    ctx->udp_stats = (rate_stat_t *)calloc(ctx->stats_capacity, sizeof(rate_stat_t));
    if (!ctx->udp_stats) {
        free(ctx->icmp_stats);
        free(ctx->scan_stats);
        free(ctx->syn_stats);
        pthread_mutex_destroy(&ctx->alert_mutex);
        pthread_mutex_destroy(&ctx->stats_mutex);
        free(ctx);
        return NULL;
    }

    // 分配告警数组
    ctx->alert_capacity = DEFAULT_ALERT_CAPACITY;
    ctx->alerts = (alert_t *)calloc(ctx->alert_capacity, sizeof(alert_t));
    if (!ctx->alerts) {
        free(ctx->udp_stats);
        free(ctx->icmp_stats);
        free(ctx->scan_stats);
        free(ctx->syn_stats);
        pthread_mutex_destroy(&ctx->alert_mutex);
        pthread_mutex_destroy(&ctx->stats_mutex);
        free(ctx);
        return NULL;
    }

    ctx->alert_count = 0;

    return ctx;
}

/**
 * 设置默认配置
 *
 * @param ctx IDS 上下文
 */
void ids_set_default_config(ids_context_t *ctx) {
    if (!ctx) return;

    ctx->config.syn_flood_threshold = IDS_DEFAULT_SYN_FLOOD_THRESHOLD;
    ctx->config.port_scan_threshold = IDS_DEFAULT_PORT_SCAN_THRESHOLD;
    ctx->config.pkt_size_min = IDS_DEFAULT_PKT_SIZE_MIN;
    ctx->config.pkt_size_max = IDS_DEFAULT_PKT_SIZE_MAX;
    ctx->config.icmp_flood_threshold = IDS_DEFAULT_ICMP_FLOOD_THRESHOLD;
    ctx->config.udp_flood_threshold = IDS_DEFAULT_UDP_FLOOD_THRESHOLD;
}

/**
 * 加载 IDS 配置
 *
 * @param ctx IDS 上下文
 * @param filename 配置文件名
 * @return 0 成功，-1 失败
 */
int ids_load_config(ids_context_t *ctx, const char *filename) {
    if (!ctx || !filename) {
        return -1;
    }

    FILE *fp = fopen(filename, "r");
    if (!fp) {
        return -1;
    }

    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        // 跳过注释和空行
        if (line[0] == '#' || line[0] == '\n') {
            continue;
        }

        char key[64];
        int value;

        if (sscanf(line, "%63s = %d", key, &value) == 2) {
            if (strcmp(key, "syn_flood_threshold") == 0) {
                ctx->config.syn_flood_threshold = value;
            } else if (strcmp(key, "port_scan_threshold") == 0) {
                ctx->config.port_scan_threshold = value;
            } else if (strcmp(key, "pkt_size_min") == 0) {
                ctx->config.pkt_size_min = value;
            } else if (strcmp(key, "pkt_size_max") == 0) {
                ctx->config.pkt_size_max = value;
            } else if (strcmp(key, "icmp_flood_threshold") == 0) {
                ctx->config.icmp_flood_threshold = value;
            } else if (strcmp(key, "udp_flood_threshold") == 0) {
                ctx->config.udp_flood_threshold = value;
            }
        }
    }

    fclose(fp);
    return 0;
}

/**
 * 获取或创建速率统计条目
 *
 * @param stats 统计数组
 * @param capacity 数组容量
 * @param ip IP 地址
 * @return 统计条目指针
 */
static rate_stat_t *get_rate_stat(rate_stat_t *stats, size_t capacity, uint32_t ip) {
    // 查找现有条目
    for (size_t i = 0; i < capacity; i++) {
        if (stats[i].active && stats[i].ip == ip) {
            return &stats[i];
        }
    }

    // 创建新条目
    for (size_t i = 0; i < capacity; i++) {
        if (!stats[i].active) {
            stats[i].ip = ip;
            stats[i].window_start = time(NULL);
            stats[i].count = 0;
            stats[i].active = 1;
            return &stats[i];
        }
    }

    return NULL;
}

/**
 * 获取或创建扫描统计条目
 *
 * @param stats 统计数组
 * @param capacity 数组容量
 * @param ip IP 地址
 * @return 统计条目指针
 */
static scan_stat_t *get_scan_stat(scan_stat_t *stats, size_t capacity, uint32_t ip) {
    // 查找现有条目
    for (size_t i = 0; i < capacity; i++) {
        if (stats[i].active && stats[i].src_ip == ip) {
            return &stats[i];
        }
    }

    // 创建新条目
    for (size_t i = 0; i < capacity; i++) {
        if (!stats[i].active) {
            stats[i].src_ip = ip;
            stats[i].port_count = 0;
            stats[i].window_start = time(NULL);
            stats[i].active = 1;
            return &stats[i];
        }
    }

    return NULL;
}

/**
 * 添加告警
 *
 * @param ctx IDS 上下文
 * @param type 告警类型
 * @param pkt 数据包
 * @param desc 描述
 * @return 0 成功，-1 失败
 */
int ids_add_alert(ids_context_t *ctx, alert_type_t type, const packet_t *pkt, const char *desc) {
    if (!ctx || !pkt) {
        return -1;
    }

    pthread_mutex_lock(&ctx->alert_mutex);

    // 检查告警数组是否已满
    if (ctx->alert_count >= ctx->alert_capacity) {
        // 扩展数组
        size_t new_capacity = ctx->alert_capacity * 2;
        alert_t *new_alerts = (alert_t *)realloc(ctx->alerts, new_capacity * sizeof(alert_t));
        if (!new_alerts) {
            pthread_mutex_unlock(&ctx->alert_mutex);
            return -1;
        }
        ctx->alerts = new_alerts;
        ctx->alert_capacity = new_capacity;
    }

    // 添加告警
    alert_t *alert = &ctx->alerts[ctx->alert_count];
    alert->type = type;
    alert->timestamp = pkt->timestamp;
    alert->src_ip = pkt->src_ip;
    alert->dst_ip = pkt->dst_ip;
    alert->src_port = pkt->src_port;
    alert->dst_port = pkt->dst_port;
    alert->protocol = pkt->protocol;

    if (desc) {
        strncpy(alert->description, desc, sizeof(alert->description) - 1);
        alert->description[sizeof(alert->description) - 1] = '\0';
    }

    ctx->alert_count++;

    pthread_mutex_unlock(&ctx->alert_mutex);

    return 0;
}

/**
 * 检测 SYN Flood 攻击
 *
 * SYN Flood 攻击原理：
 * 1. 攻击者发送大量 SYN 包
 * 2. 服务器为每个 SYN 分配资源
 * 3. 服务器资源耗尽
 *
 * 检测方法：
 * 统计每秒 SYN 包数量，超过阈值则告警
 *
 * @param ctx IDS 上下文
 * @param pkt 数据包
 * @return 1 检测到攻击，0 正常
 */
int ids_detect_syn_flood(ids_context_t *ctx, const packet_t *pkt) {
    if (!ctx || !pkt) {
        return 0;
    }

    // 只检测 TCP SYN 包
    if (pkt->protocol != PROTO_TCP || !(pkt->tcp_flags & TCP_SYN)) {
        return 0;
    }

    pthread_mutex_lock(&ctx->stats_mutex);

    // 获取速率统计
    rate_stat_t *stat = get_rate_stat(ctx->syn_stats, ctx->stats_capacity, pkt->src_ip);
    if (!stat) {
        pthread_mutex_unlock(&ctx->stats_mutex);
        return 0;
    }

    time_t now = pkt->timestamp;

    // 检查时间窗口（1秒）
    if (difftime(now, stat->window_start) >= 1) {
        // 重置窗口
        stat->window_start = now;
        stat->count = 0;
    }

    stat->count++;
    uint32_t count = stat->count;

    pthread_mutex_unlock(&ctx->stats_mutex);

    // 检查是否超过阈值
    if (count > ctx->config.syn_flood_threshold) {
        char desc[256];
        snprintf(desc, sizeof(desc), "SYN Flood detected: %d SYN packets in 1 second",
                count);
        ids_add_alert(ctx, ALERT_SYN_FLOOD, pkt, desc);
        return 1;
    }

    return 0;
}

/**
 * 检测端口扫描
 *
 * 端口扫描原理：
 * 攻击者尝试连接多个端口，寻找开放的服务
 *
 * 检测方法：
 * 统计每分钟访问的不同端口数，超过阈值则告警
 *
 * @param ctx IDS 上下文
 * @param pkt 数据包
 * @return 1 检测到扫描，0 正常
 */
int ids_detect_port_scan(ids_context_t *ctx, const packet_t *pkt) {
    if (!ctx || !pkt) {
        return 0;
    }

    // 只检测 TCP 和 UDP
    if (pkt->protocol != PROTO_TCP && pkt->protocol != PROTO_UDP) {
        return 0;
    }

    pthread_mutex_lock(&ctx->stats_mutex);

    // 获取扫描统计
    scan_stat_t *stat = get_scan_stat(ctx->scan_stats, ctx->stats_capacity, pkt->src_ip);
    if (!stat) {
        pthread_mutex_unlock(&ctx->stats_mutex);
        return 0;
    }

    time_t now = pkt->timestamp;

    // 检查时间窗口（60秒）
    if (difftime(now, stat->window_start) >= 60) {
        // 重置窗口
        stat->window_start = now;
        stat->port_count = 0;
    }

    // 检查端口是否已记录
    int found = 0;
    for (uint32_t i = 0; i < stat->port_count; i++) {
        if (stat->ports[i] == pkt->dst_port) {
            found = 1;
            break;
        }
    }

    // 记录新端口
    if (!found && stat->port_count < 256) {
        stat->ports[stat->port_count++] = pkt->dst_port;
    }

    uint32_t port_count = stat->port_count;

    pthread_mutex_unlock(&ctx->stats_mutex);

    // 检查是否超过阈值
    if (port_count > ctx->config.port_scan_threshold) {
        char desc[256];
        snprintf(desc, sizeof(desc), "Port scan detected: %d ports scanned in 60 seconds",
                port_count);
        ids_add_alert(ctx, ALERT_PORT_SCAN, pkt, desc);
        return 1;
    }

    return 0;
}

/**
 * 检测异常数据包
 *
 * 异常检测：
 * - 包大小异常（过大或过小）
 * - TTL 异常
 * - 标志位异常
 *
 * @param ctx IDS 上下文
 * @param pkt 数据包
 * @return 1 检测到异常，0 正常
 */
int ids_detect_anomaly(ids_context_t *ctx, const packet_t *pkt) {
    if (!ctx || !pkt) {
        return 0;
    }

    // 检查包大小
    if (pkt->length < ctx->config.pkt_size_min) {
        char desc[256];
        snprintf(desc, sizeof(desc), "Anomaly: Packet too small (%zu bytes)", pkt->length);
        ids_add_alert(ctx, ALERT_ANOMALY_PKT, pkt, desc);
        return 1;
    }

    if (pkt->length > ctx->config.pkt_size_max) {
        char desc[256];
        snprintf(desc, sizeof(desc), "Anomaly: Packet too large (%zu bytes)", pkt->length);
        ids_add_alert(ctx, ALERT_ANOMALY_PKT, pkt, desc);
        return 1;
    }

    // 检查 TCP 标志位异常
    if (pkt->protocol == PROTO_TCP && pkt->tcp) {
        // SYN + FIN 同时设置是异常的
        if ((pkt->tcp_flags & TCP_SYN) && (pkt->tcp_flags & TCP_FIN)) {
            char desc[256];
            snprintf(desc, sizeof(desc), "Anomaly: SYN+FIN flags set");
            ids_add_alert(ctx, ALERT_ANOMALY_PKT, pkt, desc);
            return 1;
        }

        // 所有标志位都设置是异常的
        if (pkt->tcp_flags == 0x3F) {
            char desc[256];
            snprintf(desc, sizeof(desc), "Anomaly: All TCP flags set (XMAS scan)");
            ids_add_alert(ctx, ALERT_ANOMALY_PKT, pkt, desc);
            return 1;
        }

        // 没有标志位是异常的（NULL scan）
        if (pkt->tcp_flags == 0) {
            char desc[256];
            snprintf(desc, sizeof(desc), "Anomaly: No TCP flags set (NULL scan)");
            ids_add_alert(ctx, ALERT_ANOMALY_PKT, pkt, desc);
            return 1;
        }
    }

    return 0;
}

/**
 * 检测 ICMP Flood
 *
 * @param ctx IDS 上下文
 * @param pkt 数据包
 * @return 1 检测到攻击，0 正常
 */
int ids_detect_icmp_flood(ids_context_t *ctx, const packet_t *pkt) {
    if (!ctx || !pkt) {
        return 0;
    }

    // 只检测 ICMP
    if (pkt->protocol != PROTO_ICMP) {
        return 0;
    }

    pthread_mutex_lock(&ctx->stats_mutex);

    // 获取速率统计
    rate_stat_t *stat = get_rate_stat(ctx->icmp_stats, ctx->stats_capacity, pkt->src_ip);
    if (!stat) {
        pthread_mutex_unlock(&ctx->stats_mutex);
        return 0;
    }

    time_t now = pkt->timestamp;

    // 检查时间窗口（1秒）
    if (difftime(now, stat->window_start) >= 1) {
        stat->window_start = now;
        stat->count = 0;
    }

    stat->count++;
    uint32_t count = stat->count;

    pthread_mutex_unlock(&ctx->stats_mutex);

    // 检查是否超过阈值
    if (count > ctx->config.icmp_flood_threshold) {
        char desc[256];
        snprintf(desc, sizeof(desc), "ICMP Flood detected: %d ICMP packets in 1 second",
                count);
        ids_add_alert(ctx, ALERT_ICMP_FLOOD, pkt, desc);
        return 1;
    }

    return 0;
}

/**
 * 检测 UDP Flood
 *
 * @param ctx IDS 上下文
 * @param pkt 数据包
 * @return 1 检测到攻击，0 正常
 */
int ids_detect_udp_flood(ids_context_t *ctx, const packet_t *pkt) {
    if (!ctx || !pkt) {
        return 0;
    }

    // 只检测 UDP
    if (pkt->protocol != PROTO_UDP) {
        return 0;
    }

    pthread_mutex_lock(&ctx->stats_mutex);

    // 获取速率统计
    rate_stat_t *stat = get_rate_stat(ctx->udp_stats, ctx->stats_capacity, pkt->src_ip);
    if (!stat) {
        pthread_mutex_unlock(&ctx->stats_mutex);
        return 0;
    }

    time_t now = pkt->timestamp;

    // 检查时间窗口（1秒）
    if (difftime(now, stat->window_start) >= 1) {
        stat->window_start = now;
        stat->count = 0;
    }

    stat->count++;
    uint32_t count = stat->count;

    pthread_mutex_unlock(&ctx->stats_mutex);

    // 检查是否超过阈值
    if (count > ctx->config.udp_flood_threshold) {
        char desc[256];
        snprintf(desc, sizeof(desc), "UDP Flood detected: %d UDP packets in 1 second",
                count);
        ids_add_alert(ctx, ALERT_UDP_FLOOD, pkt, desc);
        return 1;
    }

    return 0;
}

/**
 * 检测数据包
 *
 * 运行所有检测函数
 *
 * @param ctx IDS 上下文
 * @param pkt 数据包
 * @return 1 检测到异常，0 正常
 */
int ids_detect(ids_context_t *ctx, const packet_t *pkt) {
    if (!ctx || !pkt) {
        return 0;
    }

    int detected = 0;

    // 运行所有检测
    if (ids_detect_syn_flood(ctx, pkt)) detected = 1;
    if (ids_detect_port_scan(ctx, pkt)) detected = 1;
    if (ids_detect_anomaly(ctx, pkt)) detected = 1;
    if (ids_detect_icmp_flood(ctx, pkt)) detected = 1;
    if (ids_detect_udp_flood(ctx, pkt)) detected = 1;

    return detected;
}

/**
 * 获取告警数量
 *
 * @param ctx IDS 上下文
 * @return 告警数量
 */
size_t ids_alert_count(const ids_context_t *ctx) {
    if (!ctx) return 0;

    pthread_mutex_lock(&ctx->alert_mutex);
    size_t count = ctx->alert_count;
    pthread_mutex_unlock(&ctx->alert_mutex);

    return count;
}

/**
 * 获取告警
 *
 * @param ctx IDS 上下文
 * @param alerts 告警数组
 * @param max_count 最大数量
 * @return 实际获取的告警数量
 */
int ids_get_alerts(ids_context_t *ctx, alert_t *alerts, size_t max_count) {
    if (!ctx || !alerts) {
        return 0;
    }

    pthread_mutex_lock(&ctx->alert_mutex);

    size_t count = ctx->alert_count < max_count ? ctx->alert_count : max_count;
    memcpy(alerts, ctx->alerts, count * sizeof(alert_t));

    pthread_mutex_unlock(&ctx->alert_mutex);

    return count;
}

/**
 * 获取告警类型名称
 *
 * @param type 告警类型
 * @return 类型名称字符串
 */
const char *ids_alert_type_name(alert_type_t type) {
    switch (type) {
        case ALERT_SYN_FLOOD:    return "SYN_FLOOD";
        case ALERT_PORT_SCAN:    return "PORT_SCAN";
        case ALERT_ANOMALY_PKT:  return "ANOMALY_PKT";
        case ALERT_RATE_EXCEEDED: return "RATE_EXCEEDED";
        case ALERT_ICMP_FLOOD:   return "ICMP_FLOOD";
        case ALERT_UDP_FLOOD:    return "UDP_FLOOD";
        default:                 return "UNKNOWN";
    }
}

/**
 * 打印告警
 *
 * @param ctx IDS 上下文
 */
void ids_print_alerts(const ids_context_t *ctx) {
    if (!ctx) return;

    pthread_mutex_lock(&ctx->alert_mutex);

    printf("\n=== Intrusion Detection Alerts ===\n");
    printf("Total alerts: %zu\n", ctx->alert_count);
    printf("\n");

    for (size_t i = 0; i < ctx->alert_count; i++) {
        const alert_t *alert = &ctx->alerts[i];
        char time_str[64];
        char src_ip[INET_ADDRSTRLEN];
        char dst_ip[INET_ADDRSTRLEN];
        struct tm *tm_info;
        struct in_addr addr;

        // 格式化时间
        tm_info = localtime(&alert->timestamp);
        strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_info);

        // 格式化 IP 地址
        addr.s_addr = alert->src_ip;
        strcpy(src_ip, inet_ntoa(addr));

        addr.s_addr = alert->dst_ip;
        strcpy(dst_ip, inet_ntoa(addr));

        printf("[%s] [%s] %s:%d → %s:%d %s\n",
               time_str,
               ids_alert_type_name(alert->type),
               src_ip, alert->src_port,
               dst_ip, alert->dst_port,
               alert->description);
    }

    printf("===================================\n\n");

    pthread_mutex_unlock(&ctx->alert_mutex);
}

/**
 * 清理资源
 *
 * @param ctx IDS 上下文
 */
void ids_cleanup(ids_context_t *ctx) {
    if (!ctx) return;

    free(ctx->syn_stats);
    free(ctx->scan_stats);
    free(ctx->icmp_stats);
    free(ctx->udp_stats);
    free(ctx->alerts);
    pthread_mutex_destroy(&ctx->alert_mutex);
    pthread_mutex_destroy(&ctx->stats_mutex);
    free(ctx);
}
