/**
 * 简单过滤示例
 *
 * 本示例演示如何使用防火墙库进行简单的数据包过滤
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>

#include "firewall.h"
#include "packet.h"
#include "rules.h"
#include "state.h"
#include "logger.h"

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
 * 主函数
 */
int main(void) {
    printf("=== Simple Firewall Filter Example ===\n\n");

    // 初始化规则引擎
    rule_chain_t *rules = rules_init();
    if (!rules) {
        fprintf(stderr, "Failed to initialize rules engine\n");
        return 1;
    }

    // 添加规则
    rule_t rule1 = {
        .id = 1,
        .protocol = PROTO_TCP,
        .dst_port = 80,
        .action = ACTION_ACCEPT,
        .log = 1
    };
    rules_add(rules, &rule1);

    rule_t rule2 = {
        .id = 2,
        .protocol = PROTO_TCP,
        .dst_port = 22,
        .action = ACTION_DROP,
        .log = 1
    };
    rules_add(rules, &rule2);

    rule_t rule3 = {
        .id = 3,
        .protocol = PROTO_UDP,
        .dst_port = 53,
        .action = ACTION_ACCEPT,
        .log = 1
    };
    rules_add(rules, &rule3);

    // 打印规则
    rules_print(rules);

    // 测试数据包
    printf("Testing packet filtering...\n\n");

    // 测试 1: HTTP 流量（应该允许）
    packet_t pkt1;
    create_test_packet(&pkt1, "192.168.1.100", 12345, "8.8.8.8", 80, PROTO_TCP, TCP_SYN);

    rule_t *matched1 = rules_match(rules, &pkt1);
    if (matched1) {
        printf("Test 1 (HTTP): Rule %d matched - %s\n",
               matched1->id,
               matched1->action == ACTION_ACCEPT ? "ACCEPT" : "DROP");
    } else {
        printf("Test 1 (HTTP): No rule matched - DROP (default)\n");
    }

    // 测试 2: SSH 流量（应该拒绝）
    packet_t pkt2;
    create_test_packet(&pkt2, "192.168.1.100", 12346, "192.168.1.1", 22, PROTO_TCP, TCP_SYN);

    rule_t *matched2 = rules_match(rules, &pkt2);
    if (matched2) {
        printf("Test 2 (SSH):  Rule %d matched - %s\n",
               matched2->id,
               matched2->action == ACTION_ACCEPT ? "ACCEPT" : "DROP");
    } else {
        printf("Test 2 (SSH):  No rule matched - DROP (default)\n");
    }

    // 测试 3: DNS 流量（应该允许）
    packet_t pkt3;
    create_test_packet(&pkt3, "192.168.1.100", 12347, "8.8.8.8", 53, PROTO_UDP, 0);

    rule_t *matched3 = rules_match(rules, &pkt3);
    if (matched3) {
        printf("Test 3 (DNS):  Rule %d matched - %s\n",
               matched3->id,
               matched3->action == ACTION_ACCEPT ? "ACCEPT" : "DROP");
    } else {
        printf("Test 3 (DNS):  No rule matched - DROP (default)\n");
    }

    // 测试 4: 其他流量（应该拒绝）
    packet_t pkt4;
    create_test_packet(&pkt4, "192.168.1.100", 12348, "10.0.0.1", 8080, PROTO_TCP, TCP_SYN);

    rule_t *matched4 = rules_match(rules, &pkt4);
    if (matched4) {
        printf("Test 4 (Other): Rule %d matched - %s\n",
               matched4->id,
               matched4->action == ACTION_ACCEPT ? "ACCEPT" : "DROP");
    } else {
        printf("Test 4 (Other): No rule matched - DROP (default)\n");
    }

    printf("\n=== Example Complete ===\n");

    // 清理
    rules_cleanup(rules);

    return 0;
}
