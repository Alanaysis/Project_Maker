#ifndef LOGGER_H
#define LOGGER_H

#include <stdint.h>
#include <stdarg.h>
#include "packet.h"
#include "firewall.h"
#include "ids.h"

// 日志输出目标
typedef enum {
    LOG_TARGET_FILE = 0,    // 文件
    LOG_TARGET_STDOUT,      // 标准输出
    LOG_TARGET_SYSLOG,      // syslog
    LOG_TARGET_BOTH         // 文件和标准输出
} log_target_t;

// 日志配置
typedef struct {
    char *filename;         // 日志文件名
    log_level_t level;      // 日志级别
    log_target_t target;    // 输出目标
    int max_size;           // 最大文件大小 (字节)
    int rotate_count;       // 轮转文件数量
} logger_config_t;

// 日志上下文
typedef struct {
    logger_config_t config; // 配置
    FILE *fp;               // 文件指针
    pthread_mutex_t lock;   // 互斥锁
    uint64_t count;         // 日志计数
} logger_context_t;

// 初始化日志系统
logger_context_t *logger_init(const logger_config_t *config);

// 使用默认配置初始化
logger_context_t *logger_init_default(const char *filename, log_level_t level);

// 记录日志
void logger_log(logger_context_t *ctx, log_level_t level, const char *fmt, ...);

// 记录包日志
void logger_packet(logger_context_t *ctx, const packet_t *pkt, action_t action, uint32_t rule_id);

// 记录告警
void logger_alert(logger_context_t *ctx, const alert_t *alert);

// 记录连接状态变化
void logger_connection(logger_context_t *ctx, const connection_t *conn, const char *event);

// 设置日志级别
void logger_set_level(logger_context_t *ctx, log_level_t level);

// 获取日志计数
uint64_t logger_count(const logger_context_t *ctx);

// 刷新日志
void logger_flush(logger_context_t *ctx);

// 清理资源
void logger_cleanup(logger_context_t *ctx);

// 辅助函数：获取日志级别名称
const char *logger_level_name(log_level_t level);

// 辅助函数：获取动作名称
const char *logger_action_name(action_t action);

// 辅助函数：格式化时间戳
void logger_format_time(time_t timestamp, char *buf, size_t len);

// 辅助函数：格式化 IP 地址
void logger_format_ip(uint32_t ip, char *buf, size_t len);

#endif /* LOGGER_H */
