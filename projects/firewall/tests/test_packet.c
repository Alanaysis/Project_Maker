/**
 * 包解析模块测试
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "packet.h"

// 测试计数器
static int tests_passed = 0;
static int tests_failed = 0;

// 测试宏
#define TEST(name) \
    printf("Running test: %s... ", name); \
    tests_passed++;  // 临时增加，失败时会减少

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
 * 测试协议名称
 */
void test_proto_name(void) {
    TEST("protocol_name");

    ASSERT(strcmp(packet_proto_name(IP_PROTO_TCP), "TCP") == 0, "TCP name");
    ASSERT(strcmp(packet_proto_name(IP_PROTO_UDP), "UDP") == 0, "UDP name");
    ASSERT(strcmp(packet_proto_name(IP_PROTO_ICMP), "ICMP") == 0, "ICMP name");
    ASSERT(strcmp(packet_proto_name(99), "UNKNOWN") == 0, "Unknown name");

    TEST_SUCCESS();
}

/**
 * 测试 TCP 标志字符串
 */
void test_tcp_flags(void) {
    TEST("tcp_flags");

    ASSERT(strcmp(packet_tcp_flags_str(TCP_SYN), "S") == 0, "SYN flag");
    ASSERT(strcmp(packet_tcp_flags_str(TCP_ACK), "A") == 0, "ACK flag");
    ASSERT(strcmp(packet_tcp_flags_str(TCP_SYN | TCP_ACK), "SA") == 0, "SYN+ACK flags");
    ASSERT(strcmp(packet_tcp_flags_str(TCP_FIN | TCP_ACK), "FA") == 0, "FIN+ACK flags");
    ASSERT(strcmp(packet_tcp_flags_str(0), "") == 0, "No flags");

    TEST_SUCCESS();
}

/**
 * 测试 IP 地址格式化
 */
void test_ip_format(void) {
    TEST("ip_format");

    char buf[INET_ADDRSTRLEN];

    // 测试 192.168.1.1
    uint32_t ip1 = 0xC0A80101;  // 192.168.1.1 (大端序)
    packet_print_ip(ip1, buf, sizeof(buf));
    ASSERT(strcmp(buf, "192.168.1.1") == 0, "IP format");

    // 测试 10.0.0.1
    uint32_t ip2 = 0x0A000001;  // 10.0.0.1
    packet_print_ip(ip2, buf, sizeof(buf));
    ASSERT(strcmp(buf, "10.0.0.1") == 0, "IP format 2");

    TEST_SUCCESS();
}

/**
 * 测试包解析（模拟数据）
 */
void test_packet_parse(void) {
    TEST("packet_parse");

    // 注意：这里需要构造有效的以太网帧数据
    // 实际测试中应该使用真实的网络数据包

    // 这里只测试空数据的情况
    packet_t pkt;
    uint8_t data[64];
    memset(data, 0, sizeof(data));

    // 测试空数据
    ASSERT(packet_parse(NULL, 0, &pkt) == -1, "Null data");
    ASSERT(packet_parse(data, 0, &pkt) == -1, "Zero length");

    TEST_SUCCESS();
}

/**
 * 主函数
 */
int main(void) {
    printf("=== Packet Parser Tests ===\n\n");

    // 运行测试
    test_proto_name();
    test_tcp_flags();
    test_ip_format();
    test_packet_parse();

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
