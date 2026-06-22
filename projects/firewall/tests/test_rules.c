/**
 * 规则引擎测试
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <arpa/inet.h>

#include "rules.h"

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
 * 测试 CIDR 解析
 */
void test_cidr_parse(void) {
    TEST("cidr_parse");

    uint32_t ip, mask;

    // 测试 192.168.1.0/24
    ASSERT(rules_parse_cidr("192.168.1.0/24", &ip, &mask) == 0, "Parse CIDR");
    struct in_addr addr;
    addr.s_addr = ip;
    ASSERT(strcmp(inet_ntoa(addr), "192.168.1.0") == 0, "IP address");

    // 测试精确 IP
    ASSERT(rules_parse_cidr("10.0.0.1", &ip, &mask) == 0, "Parse exact IP");
    addr.s_addr = ip;
    ASSERT(strcmp(inet_ntoa(addr), "10.0.0.1") == 0, "Exact IP");

    // 测试无效输入
    ASSERT(rules_parse_cidr("invalid", &ip, &mask) == -1, "Invalid input");

    TEST_SUCCESS();
}

/**
 * 测试端口解析
 */
void test_port_parse(void) {
    TEST("port_parse");

    uint16_t port;

    ASSERT(rules_parse_port("80", &port) == 0, "Parse port 80");
    ASSERT(port == 80, "Port value");

    ASSERT(rules_parse_port("443", &port) == 0, "Parse port 443");
    ASSERT(port == 443, "Port value 443");

    ASSERT(rules_parse_port("65535", &port) == 0, "Parse max port");
    ASSERT(port == 65535, "Max port value");

    // 测试无效输入
    ASSERT(rules_parse_port("invalid", &port) == -1, "Invalid port");
    ASSERT(rules_parse_port("70000", &port) == -1, "Port out of range");

    TEST_SUCCESS();
}

/**
 * 测试协议解析
 */
void test_protocol_parse(void) {
    TEST("protocol_parse");

    uint8_t protocol;

    ASSERT(rules_parse_protocol("tcp", &protocol) == 0, "Parse TCP");
    ASSERT(protocol == PROTO_TCP, "TCP value");

    ASSERT(rules_parse_protocol("UDP", &protocol) == 0, "Parse UDP");
    ASSERT(protocol == PROTO_UDP, "UDP value");

    ASSERT(rules_parse_protocol("icmp", &protocol) == 0, "Parse ICMP");
    ASSERT(protocol == PROTO_ICMP, "ICMP value");

    ASSERT(rules_parse_protocol("all", &protocol) == 0, "Parse all");
    ASSERT(protocol == PROTO_ALL, "All value");

    // 测试无效输入
    ASSERT(rules_parse_protocol("invalid", &protocol) == -1, "Invalid protocol");

    TEST_SUCCESS();
}

/**
 * 测试规则初始化
 */
void test_rules_init(void) {
    TEST("rules_init");

    rule_chain_t *chain = rules_init();
    ASSERT(chain != NULL, "Init failed");
    ASSERT(chain->count == 0, "Initial count");
    ASSERT(chain->default_action == ACTION_DROP, "Default action");

    rules_cleanup(chain);
    TEST_SUCCESS();
}

/**
 * 测试规则添加
 */
void test_rules_add(void) {
    TEST("rules_add");

    rule_chain_t *chain = rules_init();
    ASSERT(chain != NULL, "Init failed");

    // 添加规则
    rule_t rule1 = {
        .id = 1,
        .protocol = PROTO_TCP,
        .dst_port = 80,
        .action = ACTION_ACCEPT
    };

    ASSERT(rules_add(chain, &rule1) == 0, "Add rule 1");
    ASSERT(chain->count == 1, "Count after add");

    // 添加更多规则
    rule_t rule2 = {
        .id = 2,
        .protocol = PROTO_UDP,
        .dst_port = 53,
        .action = ACTION_ACCEPT
    };

    ASSERT(rules_add(chain, &rule2) == 0, "Add rule 2");
    ASSERT(chain->count == 2, "Count after add 2");

    rules_cleanup(chain);
    TEST_SUCCESS();
}

/**
 * 测试规则匹配
 */
void test_rules_match(void) {
    TEST("rules_match");

    rule_chain_t *chain = rules_init();
    ASSERT(chain != NULL, "Init failed");

    // 添加规则
    rule_t rule1 = {
        .id = 1,
        .protocol = PROTO_TCP,
        .dst_port = 80,
        .action = ACTION_ACCEPT
    };
    rules_add(chain, &rule1);

    rule_t rule2 = {
        .id = 2,
        .protocol = PROTO_UDP,
        .dst_port = 53,
        .action = ACTION_ACCEPT
    };
    rules_add(chain, &rule2);

    // 创建测试数据包
    packet_t pkt;
    memset(&pkt, 0, sizeof(pkt));

    // 测试匹配
    pkt.protocol = PROTO_TCP;
    pkt.dst_port = 80;
    rule_t *matched = rules_match(chain, &pkt);
    ASSERT(matched != NULL, "Should match");
    ASSERT(matched->id == 1, "Rule ID");

    // 测试不匹配
    pkt.protocol = PROTO_TCP;
    pkt.dst_port = 22;
    matched = rules_match(chain, &pkt);
    ASSERT(matched == NULL, "Should not match");

    rules_cleanup(chain);
    TEST_SUCCESS();
}

/**
 * 测试规则删除
 */
void test_rules_delete(void) {
    TEST("rules_delete");

    rule_chain_t *chain = rules_init();
    ASSERT(chain != NULL, "Init failed");

    // 添加规则
    rule_t rule1 = { .id = 1, .protocol = PROTO_TCP, .dst_port = 80, .action = ACTION_ACCEPT };
    rule_t rule2 = { .id = 2, .protocol = PROTO_UDP, .dst_port = 53, .action = ACTION_ACCEPT };
    rule_t rule3 = { .id = 3, .protocol = PROTO_ICMP, .action = ACTION_ACCEPT };

    rules_add(chain, &rule1);
    rules_add(chain, &rule2);
    rules_add(chain, &rule3);

    ASSERT(chain->count == 3, "Initial count");

    // 删除规则
    ASSERT(rules_delete(chain, 2) == 0, "Delete rule");
    ASSERT(chain->count == 2, "Count after delete");

    // 验证删除的规则不可匹配
    packet_t pkt;
    memset(&pkt, 0, sizeof(pkt));
    pkt.protocol = PROTO_UDP;
    pkt.dst_port = 53;
    rule_t *matched = rules_match(chain, &pkt);
    ASSERT(matched == NULL, "Deleted rule should not match");

    rules_cleanup(chain);
    TEST_SUCCESS();
}

/**
 * 主函数
 */
int main(void) {
    printf("=== Rules Engine Tests ===\n\n");

    // 运行测试
    test_cidr_parse();
    test_port_parse();
    test_protocol_parse();
    test_rules_init();
    test_rules_add();
    test_rules_match();
    test_rules_delete();

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
