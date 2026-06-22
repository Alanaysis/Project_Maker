/**
 * 状态管理测试
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <arpa/inet.h>
#include <unistd.h>

#include "state.h"

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
 * 测试哈希函数
 */
void test_hash(void) {
    TEST("hash_function");

    // 测试相同输入产生相同哈希
    uint32_t hash1 = state_hash(0xC0A80101, 0xC0A80102, 12345, 80, PROTO_TCP);
    uint32_t hash2 = state_hash(0xC0A80101, 0xC0A80102, 12345, 80, PROTO_TCP);
    ASSERT(hash1 == hash2, "Same input same hash");

    // 测试不同输入产生不同哈希
    uint32_t hash3 = state_hash(0xC0A80101, 0xC0A80102, 12346, 80, PROTO_TCP);
    ASSERT(hash1 != hash3, "Different input different hash");

    // 测试哈希值在范围内
    ASSERT(hash1 < CONN_TABLE_SIZE, "Hash in range");

    TEST_SUCCESS();
}

/**
 * 测试连接表初始化
 */
void test_state_init(void) {
    TEST("state_init");

    connection_table_t *table = state_init();
    ASSERT(table != NULL, "Init failed");
    ASSERT(table->count == 0, "Initial count");
    ASSERT(table->capacity == CONN_TABLE_SIZE, "Capacity");

    state_cleanup_all(table);
    TEST_SUCCESS();
}

/**
 * 测试连接查找
 */
void test_state_lookup(void) {
    TEST("state_lookup");

    connection_table_t *table = state_init();
    ASSERT(table != NULL, "Init failed");

    // 创建测试数据包
    packet_t pkt;
    memset(&pkt, 0, sizeof(pkt));
    pkt.src_ip = 0xC0A80101;  // 192.168.1.1
    pkt.dst_ip = 0xC0A80102;  // 192.168.1.2
    pkt.src_port = 12345;
    pkt.dst_port = 80;
    pkt.protocol = PROTO_TCP;
    pkt.timestamp = time(NULL);

    // 查找不存在的连接
    connection_t *conn = state_lookup(table, &pkt);
    ASSERT(conn == NULL, "Should not find");

    state_cleanup_all(table);
    TEST_SUCCESS();
}

/**
 * 测试 TCP 状态名称
 */
void test_tcp_state_name(void) {
    TEST("tcp_state_name");

    ASSERT(strcmp(state_tcp_state_name(TCP_STATE_NONE), "NONE") == 0, "NONE");
    ASSERT(strcmp(state_tcp_state_name(TCP_STATE_SYN_SENT), "SYN_SENT") == 0, "SYN_SENT");
    ASSERT(strcmp(state_tcp_state_name(TCP_STATE_SYN_RECV), "SYN_RECV") == 0, "SYN_RECV");
    ASSERT(strcmp(state_tcp_state_name(TCP_STATE_ESTABLISHED), "ESTABLISHED") == 0, "ESTABLISHED");
    ASSERT(strcmp(state_tcp_state_name(TCP_STATE_FIN_WAIT), "FIN_WAIT") == 0, "FIN_WAIT");
    ASSERT(strcmp(state_tcp_state_name(TCP_STATE_TIME_WAIT), "TIME_WAIT") == 0, "TIME_WAIT");
    ASSERT(strcmp(state_tcp_state_name(TCP_STATE_CLOSED), "CLOSED") == 0, "CLOSED");

    TEST_SUCCESS();
}

/**
 * 测试连接计数
 */
void test_state_count(void) {
    TEST("state_count");

    connection_table_t *table = state_init();
    ASSERT(table != NULL, "Init failed");

    ASSERT(state_count(table) == 0, "Initial count");
    ASSERT(state_count(NULL) == 0, "NULL table");

    state_cleanup_all(table);
    TEST_SUCCESS();
}

/**
 * 主函数
 */
int main(void) {
    printf("=== State Management Tests ===\n\n");

    // 运行测试
    test_hash();
    test_state_init();
    test_state_lookup();
    test_tcp_state_name();
    test_state_count();

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
