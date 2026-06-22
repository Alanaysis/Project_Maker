/**
 * 日志模块
 *
 * 本模块负责：
 * 1. 记录防火墙运行日志
 * 2. 记录数据包日志
 * 3. 记录告警日志
 * 4. 日志轮转和管理
 *
 * ⭐ 重点：理解日志级别设计
 *    - DEBUG: 调试信息，用于开发
 *    - INFO: 一般信息，用于运行状态
 *    - WARNING: 警告信息，需要关注
 *    - ERROR: 错误信息，需要处理
 *    - ALERT: 告警信息，安全事件
 *
 * 💡 思考：如何设计高效的日志系统？
 *    - 异步写入，避免阻塞主流程
 *    - 缓冲区批量写入
 *    - 日志轮转，避免文件过大
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdarg.h>
#include <pthread.h>
#include <arpa/inet.h>

#include "logger.h"

/**
 * 获取日志级别名称
 *
 * @param level 日志级别
 * @return 级别名称字符串
 */
const char *logger_level_name(log_level_t level) {
    switch (level) {
        case LOG_DEBUG:   return "DEBUG";
        case LOG_INFO:    return "INFO";
        case LOG_WARNING: return "WARNING";
        case LOG_ERROR:   return "ERROR";
        case LOG_ALERT:   return "ALERT";
        default:          return "UNKNOWN";
    }
}

/**
 * 获取动作名称
 *
 * @param action 动作类型
 * @return 动作名称字符串
 */
const char *logger_action_name(action_t action) {
    switch (action) {
        case ACTION_ACCEPT: return "ACCEPT";
        case ACTION_DROP:   return "DROP";
        case ACTION_REJECT: return "REJECT";
        case ACTION_LOG:    return "LOG";
        default:            return "UNKNOWN";
    }
}

/**
 * 格式化时间戳
 *
 * @param timestamp 时间戳
 * @param buf 缓冲区
 * @param len 缓冲区长度
 */
void logger_format_time(time_t timestamp, char *buf, size_t len) {
    struct tm *tm_info = localtime(&timestamp);
    strftime(buf, len, "%Y-%m-%d %H:%M:%S", tm_info);
}

/**
 * 格式化 IP 地址
 *
 * @param ip IP 地址（网络字节序）
 * @param buf 缓冲区
 * @param len 缓冲区长度
 */
void logger_format_ip(uint32_t ip, char *buf, size_t len) {
    struct in_addr addr;
    addr.s_addr = ip;
    strncpy(buf, inet_ntoa(addr), len - 1);
    buf[len - 1] = '\0';
}

/**
 * 初始化日志系统
 *
 * @param config 日志配置
 * @return 日志上下文，失败返回 NULL
 */
logger_context_t *logger_init(const logger_config_t *config) {
    if (!config) {
        return NULL;
    }

    logger_context_t *ctx = (logger_context_t *)calloc(1, sizeof(logger_context_t));
    if (!ctx) {
        return NULL;
    }

    // 复制配置
    ctx->config = *config;
    if (config->filename) {
        ctx->config.filename = strdup(config->filename);
    }

    // 打开日志文件
    if (config->target == LOG_TARGET_FILE || config->target == LOG_TARGET_BOTH) {
        ctx->fp = fopen(config->filename, "a");
        if (!ctx->fp) {
            fprintf(stderr, "Warning: Cannot open log file: %s\n", config->filename);
            // 继续运行，只是不写文件
        }
    }

    // 初始化互斥锁
    pthread_mutex_init(&ctx->lock, NULL);

    ctx->count = 0;

    return ctx;
}

/**
 * 使用默认配置初始化
 *
 * @param filename 日志文件名
 * @param level 日志级别
 * @return 日志上下文，失败返回 NULL
 */
logger_context_t *logger_init_default(const char *filename, log_level_t level) {
    logger_config_t config = {
        .filename = (char *)filename,
        .level = level,
        .target = LOG_TARGET_BOTH,
        .max_size = 10 * 1024 * 1024,  // 10MB
        .rotate_count = 5
    };

    return logger_init(&config);
}

/**
 * 写入日志
 *
 * @param ctx 日志上下文
 * @param level 日志级别
 * @param fmt 格式化字符串
 * @param args 参数列表
 */
static void log_write(logger_context_t *ctx, log_level_t level, const char *fmt, va_list args) {
    if (!ctx) return;

    // 检查日志级别
    if (level < ctx->config.level) {
        return;
    }

    pthread_mutex_lock(&ctx->lock);

    // 格式化时间
    char time_str[64];
    time_t now = time(NULL);
    logger_format_time(now, time_str, sizeof(time_str));

    // 格式化日志消息
    char message[1024];
    vsnprintf(message, sizeof(message), fmt, args);

    // 输出到文件
    if (ctx->fp) {
        fprintf(ctx->fp, "[%s] [%s] %s\n", time_str, logger_level_name(level), message);
        fflush(ctx->fp);
    }

    // 输出到标准输出
    if (ctx->config.target == LOG_TARGET_STDOUT || ctx->config.target == LOG_TARGET_BOTH) {
        // 根据级别设置颜色
        const char *color = "";
        const char *reset = "\033[0m";

        switch (level) {
            case LOG_DEBUG:   color = "\033[36m"; break;  // 青色
            case LOG_INFO:    color = "\033[32m"; break;  // 绿色
            case LOG_WARNING: color = "\033[33m"; break;  // 黄色
            case LOG_ERROR:   color = "\033[31m"; break;  // 红色
            case LOG_ALERT:   color = "\033[35m"; break;  // 紫色
            default:          color = ""; break;
        }

        printf("%s[%s] [%s]%s %s\n", color, time_str, logger_level_name(level), reset, message);
    }

    ctx->count++;

    pthread_mutex_unlock(&ctx->lock);
}

/**
 * 记录日志
 *
 * @param ctx 日志上下文
 * @param level 日志级别
 * @param fmt 格式化字符串
 */
void logger_log(logger_context_t *ctx, log_level_t level, const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    log_write(ctx, level, fmt, args);
    va_end(args);
}

/**
 * 记录包日志
 *
 * 格式：
 * [时间戳] [动作] [协议] [源IP:端口] → [目的IP:端口] [长度] [规则ID]
 *
 * @param ctx 日志上下文
 * @param pkt 数据包
 * @param action 动作
 * @param rule_id 规则 ID
 */
void logger_packet(logger_context_t *ctx, const packet_t *pkt, action_t action, uint32_t rule_id) {
    if (!ctx || !pkt) return;

    char src_ip[INET_ADDRSTRLEN];
    char dst_ip[INET_ADDRSTRLEN];

    logger_format_ip(pkt->src_ip, src_ip, sizeof(src_ip));
    logger_format_ip(pkt->dst_ip, dst_ip, sizeof(dst_ip));

    if (pkt->protocol == PROTO_TCP || pkt->protocol == PROTO_UDP) {
        logger_log(ctx, LOG_INFO, "[%s] [%s] %s:%d → %s:%d len=%zu rule=%u",
                  logger_action_name(action),
                  packet_proto_name(pkt->protocol),
                  src_ip, pkt->src_port,
                  dst_ip, pkt->dst_port,
                  pkt->length,
                  rule_id);
    } else {
        logger_log(ctx, LOG_INFO, "[%s] [%s] %s → %s len=%zu rule=%u",
                  logger_action_name(action),
                  packet_proto_name(pkt->protocol),
                  src_ip, dst_ip,
                  pkt->length,
                  rule_id);
    }
}

/**
 * 记录告警
 *
 * @param ctx 日志上下文
 * @param alert 告警
 */
void logger_alert(logger_context_t *ctx, const alert_t *alert) {
    if (!ctx || !alert) return;

    char src_ip[INET_ADDRSTRLEN];
    char dst_ip[INET_ADDRSTRLEN];

    logger_format_ip(alert->src_ip, src_ip, sizeof(src_ip));
    logger_format_ip(alert->dst_ip, dst_ip, sizeof(dst_ip));

    logger_log(ctx, LOG_ALERT, "[%s] %s:%d → %s:%d %s",
              ids_alert_type_name(alert->type),
              src_ip, alert->src_port,
              dst_ip, alert->dst_port,
              alert->description);
}

/**
 * 记录连接状态变化
 *
 * @param ctx 日志上下文
 * @param conn 连接
 * @param event 事件
 */
void logger_connection(logger_context_t *ctx, const connection_t *conn, const char *event) {
    if (!ctx || !conn) return;

    char src_ip[INET_ADDRSTRLEN];
    char dst_ip[INET_ADDRSTRLEN];

    logger_format_ip(conn->src_ip, src_ip, sizeof(src_ip));
    logger_format_ip(conn->dst_ip, dst_ip, sizeof(dst_ip));

    logger_log(ctx, LOG_DEBUG, "[CONN] [%s] %s:%d → %s:%d [%s] [%s]",
              event,
              src_ip, conn->src_port,
              dst_ip, conn->dst_port,
              packet_proto_name(conn->protocol),
              state_tcp_state_name(conn->tcp_state));
}

/**
 * 设置日志级别
 *
 * @param ctx 日志上下文
 * @param level 日志级别
 */
void logger_set_level(logger_context_t *ctx, log_level_t level) {
    if (ctx) {
        ctx->config.level = level;
    }
}

/**
 * 获取日志计数
 *
 * @param ctx 日志上下文
 * @return 日志计数
 */
uint64_t logger_count(const logger_context_t *ctx) {
    return ctx ? ctx->count : 0;
}

/**
 * 刷新日志
 *
 * @param ctx 日志上下文
 */
void logger_flush(logger_context_t *ctx) {
    if (!ctx) return;

    pthread_mutex_lock(&ctx->lock);

    if (ctx->fp) {
        fflush(ctx->fp);
    }

    pthread_mutex_unlock(&ctx->lock);
}

/**
 * 清理资源
 *
 * @param ctx 日志上下文
 */
void logger_cleanup(logger_context_t *ctx) {
    if (!ctx) return;

    // 刷新缓冲区
    logger_flush(ctx);

    // 关闭文件
    if (ctx->fp) {
        fclose(ctx->fp);
    }

    // 释放配置字符串
    free(ctx->config.filename);

    // 销毁互斥锁
    pthread_mutex_destroy(&ctx->lock);

    // 释放上下文
    free(ctx);
}
