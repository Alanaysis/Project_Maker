/**
 * 防火墙主程序
 *
 * 本文件是防火墙程序的入口点，负责：
 * 1. 解析命令行参数
 * 2. 初始化各个模块
 * 3. 启动主循环
 * 4. 处理信号和清理
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <getopt.h>
#include <syslog.h>
#include <errno.h>

#include "firewall.h"
#include "packet.h"
#include "rules.h"
#include "state.h"
#include "ids.h"
#include "logger.h"

// 全局上下文（用于信号处理）
static firewall_context_t *g_ctx = NULL;

/**
 * 信号处理函数
 *
 * 处理 SIGINT 和 SIGTERM 信号，实现优雅退出
 */
static void signal_handler(int sig) {
    (void)sig;

    if (g_ctx) {
        printf("\n[INFO] Received signal, shutting down...\n");
        g_ctx->running = 0;
    }
}

/**
 * 设置信号处理
 */
static void setup_signals(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);

    sigaction(SIGINT, &sa, NULL);   // Ctrl+C
    sigaction(SIGTERM, &sa, NULL);  // kill
    signal(SIGPIPE, SIG_IGN);       // 忽略 SIGPIPE
}

/**
 * 打印版本信息
 */
void firewall_version(void) {
    printf("%s version %s\n", FIREWALL_NAME, FIREWALL_VERSION);
    printf("A simple network firewall for learning purposes\n");
}

/**
 * 打印帮助信息
 */
void firewall_help(const char *prog_name) {
    printf("Usage: %s [OPTIONS]\n\n", prog_name);
    printf("Options:\n");
    printf("  -c, --config FILE    Configuration file path\n");
    printf("  -i, --interface IF   Network interface\n");
    printf("  -l, --log FILE       Log file path\n");
    printf("  -v, --verbose        Verbose output\n");
    printf("  -d, --daemon         Run as daemon\n");
    printf("  -h, --help           Show this help\n");
    printf("  -V, --version        Show version\n");
    printf("\nExamples:\n");
    printf("  sudo %s -i eth0 -c firewall.conf\n", prog_name);
    printf("  sudo %s -i wlan0 -v -l /var/log/firewall.log\n", prog_name);
}

/**
 * 解析命令行参数
 */
static int parse_args(int argc, char *argv[], firewall_config_t *config) {
    int opt;
    static struct option long_options[] = {
        {"config",    required_argument, 0, 'c'},
        {"interface", required_argument, 0, 'i'},
        {"log",       required_argument, 0, 'l'},
        {"verbose",   no_argument,       0, 'v'},
        {"daemon",    no_argument,       0, 'd'},
        {"help",      no_argument,       0, 'h'},
        {"version",   no_argument,       0, 'V'},
        {0, 0, 0, 0}
    };

    // 设置默认值
    config->interface = NULL;
    config->config_file = NULL;
    config->log_file = NULL;
    config->log_level = LOG_INFO;
    config->daemon_mode = 0;
    config->verbose = 0;

    while ((opt = getopt_long(argc, argv, "c:i:l:vdhV", long_options, NULL)) != -1) {
        switch (opt) {
            case 'c':
                config->config_file = strdup(optarg);
                break;
            case 'i':
                config->interface = strdup(optarg);
                break;
            case 'l':
                config->log_file = strdup(optarg);
                break;
            case 'v':
                config->verbose = 1;
                config->log_level = LOG_DEBUG;
                break;
            case 'd':
                config->daemon_mode = 1;
                break;
            case 'h':
                firewall_help(argv[0]);
                exit(0);
            case 'V':
                firewall_version();
                exit(0);
            default:
                firewall_help(argv[0]);
                return -1;
        }
    }

    // 检查必需参数
    if (!config->interface) {
        fprintf(stderr, "Error: Network interface is required (-i)\n");
        firewall_help(argv[0]);
        return -1;
    }

    return 0;
}

/**
 * 初始化防火墙上下文
 */
firewall_context_t *firewall_init(const firewall_config_t *config) {
    firewall_context_t *ctx;

    // 分配上下文
    ctx = (firewall_context_t *)calloc(1, sizeof(firewall_context_t));
    if (!ctx) {
        fprintf(stderr, "Error: Failed to allocate context\n");
        return NULL;
    }

    // 复制配置
    ctx->config = *config;
    if (config->interface) ctx->config.interface = strdup(config->interface);
    if (config->config_file) ctx->config.config_file = strdup(config->config_file);
    if (config->log_file) ctx->config.log_file = strdup(config->log_file);

    // 初始化日志系统
    logger_config_t log_config = {
        .filename = ctx->config.log_file ? ctx->config.log_file : "/var/log/firewall.log",
        .level = ctx->config.log_level,
        .target = ctx->config.daemon_mode ? LOG_TARGET_FILE : LOG_TARGET_BOTH,
        .max_size = 10 * 1024 * 1024,  // 10MB
        .rotate_count = 5
    };
    ctx->logger = logger_init(&log_config);
    if (!ctx->logger) {
        fprintf(stderr, "Error: Failed to initialize logger\n");
        free(ctx);
        return NULL;
    }

    // 初始化规则引擎
    ctx->rules = rules_init();
    if (!ctx->rules) {
        fprintf(stderr, "Error: Failed to initialize rules engine\n");
        logger_cleanup(ctx->logger);
        free(ctx);
        return NULL;
    }

    // 加载规则文件
    if (ctx->config.config_file) {
        if (rules_load(ctx->rules, ctx->config.config_file) != 0) {
            fprintf(stderr, "Warning: Failed to load config file, using default rules\n");
        }
    }

    // 初始化状态管理
    ctx->state = state_init();
    if (!ctx->state) {
        fprintf(stderr, "Error: Failed to initialize state management\n");
        rules_cleanup(ctx->rules);
        logger_cleanup(ctx->logger);
        free(ctx);
        return NULL;
    }

    // 初始化入侵检测
    ctx->ids = ids_init();
    if (!ctx->ids) {
        fprintf(stderr, "Error: Failed to initialize IDS\n");
        state_cleanup_all(ctx->state);
        rules_cleanup(ctx->rules);
        logger_cleanup(ctx->logger);
        free(ctx);
        return NULL;
    }

    // 初始化运行状态
    ctx->running = 1;
    ctx->packet_count = 0;
    ctx->start_time = time(NULL);

    return ctx;
}

/**
 * 启动防火墙
 *
 * 这是防火墙的主循环，负责：
 * 1. 捕获数据包
 * 2. 解析数据包
 * 3. 匹配规则
 * 4. 检测入侵
 * 5. 执行动作
 * 6. 记录日志
 */
int firewall_start(firewall_context_t *ctx) {
    // 注意：这是一个简化的实现
    // 实际的防火墙需要使用 libnetfilter_queue 来拦截数据包
    // 这里我们使用 libpcap 来捕获和分析数据包

    printf("[INFO] Starting %s on interface %s\n", FIREWALL_NAME, ctx->config.interface);
    logger_log(ctx->logger, LOG_INFO, "Firewall started on interface %s", ctx->config.interface);

    // 打印规则信息
    rules_print(ctx->rules);

    printf("[INFO] Firewall is running. Press Ctrl+C to stop.\n");

    // 主循环（简化版本，实际应使用 libnetfilter_queue）
    while (ctx->running) {
        // 模拟数据包处理
        // 实际实现应该：
        // 1. 使用 nfq_open() 打开队列
        // 2. 使用 nfq_create_queue() 创建队列
        // 3. 设置回调函数处理数据包
        // 4. 在回调函数中执行包过滤逻辑

        sleep(1);

        // 定期清理超时连接
        state_cleanup(ctx->state);
    }

    return 0;
}

/**
 * 停止防火墙
 */
void firewall_stop(firewall_context_t *ctx) {
    if (ctx) {
        ctx->running = 0;
        printf("[INFO] Stopping firewall...\n");
        logger_log(ctx->logger, LOG_INFO, "Firewall stopping");
    }
}

/**
 * 获取统计信息
 */
void firewall_stats(const firewall_context_t *ctx) {
    if (!ctx) return;

    time_t now = time(NULL);
    double uptime = difftime(now, ctx->start_time);

    printf("\n=== Firewall Statistics ===\n");
    printf("Uptime: %.0f seconds\n", uptime);
    printf("Packets processed: %lu\n", ctx->packet_count);
    printf("Active connections: %lu\n", state_count(ctx->state));
    printf("Alerts: %lu\n", ids_alert_count(ctx->ids));
    printf("===========================\n");
}

/**
 * 清理防火墙资源
 */
void firewall_cleanup(firewall_context_t *ctx) {
    if (!ctx) return;

    printf("[INFO] Cleaning up...\n");

    // 打印最终统计
    firewall_stats(ctx);

    // 清理各模块
    if (ctx->ids) {
        ids_cleanup(ctx->ids);
    }
    if (ctx->state) {
        state_cleanup_all(ctx->state);
    }
    if (ctx->rules) {
        rules_cleanup(ctx->rules);
    }
    if (ctx->logger) {
        logger_log(ctx->logger, LOG_INFO, "Firewall stopped");
        logger_cleanup(ctx->logger);
    }

    // 释放配置字符串
    free(ctx->config.interface);
    free(ctx->config.config_file);
    free(ctx->config.log_file);

    // 释放上下文
    free(ctx);
}

/**
 * 主函数
 */
int main(int argc, char *argv[]) {
    firewall_config_t config;

    // 解析命令行参数
    if (parse_args(argc, argv, &config) != 0) {
        return 1;
    }

    // 设置信号处理
    setup_signals();

    // 初始化防火墙
    g_ctx = firewall_init(&config);
    if (!g_ctx) {
        fprintf(stderr, "Error: Failed to initialize firewall\n");
        return 1;
    }

    // 启动防火墙
    int ret = firewall_start(g_ctx);

    // 清理资源
    firewall_cleanup(g_ctx);
    g_ctx = NULL;

    return ret;
}
