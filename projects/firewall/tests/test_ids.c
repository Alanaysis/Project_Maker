/**
 * 入侵检测系统测试
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <arpa/inet.h>

#include "ids.h"
#include "packet.h"

// 测试计数器
static int tests_passed = 0;
static int tests_failed = 0;

// 测试宏
#define TEST(name) \
    printf("Running test: %s... ", name); \
    tests_passed++;

#define ASSERT(cond, msg) \
    if (!(cond)) { \
        printf("FAILED: %s\n", msg); \
        tests_failed++; \
        tests_passed--; \
        return; \
    }

#define TEST_SUCCESS() \
    printf("PASSED\n");

/**
 * 创建测试数据包
 */
static void create_test_packet(packet_t *pkt, const char *src_ip, uint16_t src_port,
                               const char *dst_ip, uint16_t dst_port,
                               uint8_t protocol, uint8_t tcp_flags) {
    memset(pkt, 0, sizeof(packet_t));

    struct in_addr addr;

    inet_pton(AF_INET, src_ip, &addr);
    pkt->src_ip = addr.s_addr;

    inet_pton(AF_INET, dst_ip, &addr);
    pkt->dst_ip = addr.s_addr;

    pkt->src_port = src_port;
    pkt->dst_port = dst_port;
    pkt->protocol = protocol;
    pkt->tcp_flags = tcp_flags;
    pkt->timestamp = time(NULL);
    pkt->length = 64;
}

/**
 * 测试 IDS 初始化
 */
void test_ids_init(void) {
    TEST("ids_init");

    ids_context_t *ctx = ids_init();
    ASSERT(ctx != NULL, "Init failed");
    ASSERT(ctx->alert_count == 0, "Initial alert count");
    ASSERT(ctx->config.syn_flood_threshold == IDS_DEFAULT_SYN_FLOOD_THRESHOLD, "Default threshold");

    ids_cleanup(ctx);
    TEST_SUCCESS();
}

/**
 * 测试告警类型名称
 */
void test_alert_type_name(void) {
    TEST("alert_type_name");

    ASSERT(strcmp(ids_alert_type_name(ALERT_SYN_FLOOD), "SYN_FLOOD") == 0, "SYN_FLOOD");
    ASSERT(strcmp(ids_alert_type_name(ALERT_PORT_SCAN), "PORT_SCAN") == 0, "PORT_SCAN");
    ASSERT(strcmp(ids_alert_type_name(ALERT_ANOMALY_PKT), "ANOMALY_PKT") == 0, "ANOMALY_PKT");

    TEST_SUCCESS();
}

/**
 * 测试异常包检测
 */
void test_anomaly_detection(void) {
    TEST("anomaly_detection");

    ids_context_t *ctx = ids_init();
    ASSERT(ctx != NULL, "Init failed");

    // 测试正常包
    packet_t pkt;
    create_test_packet(&pkt, "192.168.1.1", 12345, "192.168.1.2", 80, PROTO_TCP, TCP_SYN);
    pkt.length = 64;
    ASSERT(ids_detect_anomaly(ctx, &pkt) == 0, "Normal packet");

    // 测试异常小包
    pkt.length = 10;
    ASSERT(ids_detect_anomaly(ctx, &pkt) == 1, "Small packet");

    // 测试异常大包
    pkt.length = 2000;
    ASSERT(ids_detect_anomaly(ctx, &pkt) == 1, "Large packet");

    ids_cleanup(ctx);
    TEST_SUCCESS();
}

/**
 * 测试 SYN Flood 检测
 */
void test_syn_flood_detection(void) {
    TEST("syn_flood_detection");

    ids_context_t *ctx = ids_init();
    ASSERT(ctx != NULL, "Init failed");

    // 设置低阈值用于测试
    ctx->config.syn_flood_threshold = 5;

    packet_t pkt;
    create_test_packet(&pkt, "192.168.1.1", 12345, "192.168.1.2", 80, PROTO_TCP, TCP_SYN);

    // 发送多个 SYN 包
    for (int i = 0; i < 4; i++) {
        ASSERT(ids_detect_syn_flood(ctx, &pkt) == 0, "Below threshold");
    }

    // 超过阈值
    ASSERT(ids_detect_syn_flood(ctx, &pkt) == 1, "Above threshold");

    ids_cleanup(ctx);
    TEST_SUCCESS();
}

/**
 * 测试端口扫描检测
 */
void test_port_scan_detection(void) {
    TEST("port_scan_detection");

    ids_context_t *ctx = ids_init();
    ASSERT(ctx != NULL, "Init failed");

    // 设置低阈值用于测试
    ctx->config.port_scan_threshold = 5;

    packet_t pkt;
    create_test_packet(&pkt, "192.168.1.1", 12345, "192.168.1.2", 0, PROTO_TCP, TCP_SYN);

    // 访问不同端口
    for (uint16_t port = 1; port <= 4; port++) {
        pkt.dst_port = port;
        ASSERT(ids_detect_port_scan(ctx, &pkt) == 0, "Below threshold");
    }

    // 超过阈值
    pkt.dst_port = 6;
    ASSERT(ids_detect_port_scan(ctx, &pkt) == 1, "Above threshold");

    ids_cleanup(ctx);
    TEST_SUCCESS();
}

/**
 * 测试告警计数
 */
void test_alert_count(void) {
    TEST("alert_count");

    ids_context_t *ctx = ids_init();
    ASSERT(ctx != NULL, "Init failed");

    ASSERT(ids_alert_count(ctx) == 0, "Initial count");

    // 触发告警
    packet_t pkt;
    create_test_packet(&pkt, "192.168.1.1", 12345, "192.168.1.2", 80, PROTO_TCP, TCP_SYN);
    pkt.length = 10;  // 异常小包
    ids_detect_anomaly(ctx, &pkt);

    ASSERT(ids_alert_count(ctx) > 0, "Alerts detected");

    ids_cleanup(ctx);
    TEST_SUCCESS();
}

/**
 * 主函数
 */
int main(void) {
    printf("=== IDS Tests ===\n\n");

    // 运行测试
    test_ids_init();
    test_alert_type_name();
    test_anomaly_detection();
    test_syn_flood_detection();
    test_port_scan_detection();
    test_alert_count();

    // 打印结果
    printf("\n=== Test Results ===\n");
    printf("Passed: %d\n", tests_passed);
    printf("Failed: %d\n", tests_failed);
    printf("Total:  %d\n", tests_passed + tests_failed);

    if (tests_failed > 0) {
        printf("\nSome tests FAILED!\n");
        return 1;
    }

    printf("\nAll tests PASSED!\n");
    return 0;
}
