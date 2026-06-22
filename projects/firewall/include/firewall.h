#ifndef FIREWALL_H
#define FIREWALL_H

#include <stdint.h>
#include <stddef.h>
#include <time.h>

// 版本信息
#define FIREWALL_VERSION "1.0.0"
#define FIREWALL_NAME "SimpleFirewall"

// 错误码
typedef enum {
    FW_OK = 0,
    FW_ERR_NOMEM,
    FW_ERR_INVAL,
    FW_ERR_NOT_FOUND,
    FW_ERR_PERM,
    FW_ERR_IO,
    FW_ERR_PARSE,
    FW_ERR_NET,
    FW_ERR_FULL,
    FW_ERR_TIMEOUT
} fw_error_t;

// 日志级别
typedef enum {
    LOG_DEBUG,
    LOG_INFO,
    LOG_WARNING,
    LOG_ERROR,
    LOG_ALERT
} log_level_t;

// 动作类型
typedef enum {
    ACTION_ACCEPT,
    ACTION_DROP,
    ACTION_REJECT,
    ACTION_LOG
} action_t;

// 协议类型
typedef enum {
    PROTO_ALL = 0,
    PROTO_TCP = 6,
    PROTO_UDP = 17,
    PROTO_ICMP = 1
} protocol_t;

// 配置结构
typedef struct {
    char *interface;        // 网络接口
    char *config_file;      // 配置文件路径
    char *log_file;         // 日志文件路径
    log_level_t log_level;  // 日志级别
    int daemon_mode;        // 后台运行模式
    int verbose;            // 详细输出
} firewall_config_t;

// 防火墙上文
typedef struct {
    firewall_config_t config;

    // 各模块上下文
    void *rules;            // 规则引擎
    void *state;            // 状态管理
    void *ids;              // 入侵检测
    void *logger;           // 日志系统

    // 运行状态
    int running;            // 运行标志
    uint64_t packet_count;  // 包计数
    time_t start_time;      // 启动时间
} firewall_context_t;

// 初始化防火墙
firewall_context_t *firewall_init(const firewall_config_t *config);

// 启动防火墙
int firewall_start(firewall_context_t *ctx);

// 停止防火墙
void firewall_stop(firewall_context_t *ctx);

// 清理资源
void firewall_cleanup(firewall_context_t *ctx);

// 获取统计信息
void firewall_stats(const firewall_context_t *ctx);

// 打印版本信息
void firewall_version(void);

// 打印帮助信息
void firewall_help(const char *prog_name);

#endif /* FIREWALL_H */
