#ifndef STATE_H
#define STATE_H

#include <stdint.h>
#include <stddef.h>
#include <time.h>
#include <pthread.h>
#include "packet.h"

// TCP 状态
typedef enum {
    TCP_STATE_NONE = 0,
    TCP_STATE_SYN_SENT,
    TCP_STATE_SYN_RECV,
    TCP_STATE_ESTABLISHED,
    TCP_STATE_FIN_WAIT,
    TCP_STATE_CLOSE_WAIT,
    TCP_STATE_LAST_ACK,
    TCP_STATE_TIME_WAIT,
    TCP_STATE_CLOSED
} tcp_state_t;

// 连接方向
typedef enum {
    DIR_ORIGINAL = 0,       // 原始方向 (客户端→服务器)
    DIR_REPLY               // 回复方向 (服务器→客户端)
} direction_t;

// 连接类型
typedef enum {
    CONN_TCP,
    CONN_UDP,
    CONN_ICMP
} conn_type_t;

// 连接记录
typedef struct {
    // 连接标识
    uint32_t src_ip;        // 源 IP
    uint32_t dst_ip;        // 目的 IP
    uint16_t src_port;      // 源端口
    uint16_t dst_port;      // 目的端口
    uint8_t  protocol;      // 协议

    // 状态信息
    conn_type_t type;       // 连接类型
    tcp_state_t tcp_state;  // TCP 状态
    direction_t direction;  // 方向

    // 统计信息
    uint32_t packets;       // 包数量
    uint64_t bytes;         // 字节数

    // 时间信息
    time_t start_time;      // 开始时间
    time_t last_time;       // 最后活动时间
    time_t timeout;         // 超时时间

    // 标志
    uint8_t valid;          // 有效标志
} connection_t;

// 连接表配置
#define CONN_TABLE_SIZE     65536
#define CONN_TCP_TIMEOUT    300     // TCP 连接超时 (秒)
#define CONN_TCP_NEW_TIMEOUT 30    // TCP 新连接超时 (秒)
#define CONN_UDP_TIMEOUT    30      // UDP 超时 (秒)
#define CONN_ICMP_TIMEOUT   10      // ICMP 超时 (秒)

// 连接表
typedef struct {
    connection_t *table;    // 连接表
    size_t count;           // 连接数量
    size_t capacity;        // 表容量
    pthread_mutex_t lock;   // 互斥锁
} connection_table_t;

// 初始化连接表
connection_table_t *state_init(void);

// 查找或创建连接
connection_t *state_lookup(connection_table_t *table, const packet_t *pkt);

// 更新连接状态
int state_update(connection_table_t *table, connection_t *conn, const packet_t *pkt);

// 清理超时连接
int state_cleanup(connection_table_t *table);

// 获取连接数量
size_t state_count(const connection_table_t *table);

// 打印连接表
void state_print(const connection_table_t *table);

// 打印连接信息
void state_print_connection(const connection_t *conn);

// 获取 TCP 状态名称
const char *state_tcp_state_name(tcp_state_t state);

// 清理所有连接
void state_cleanup_all(connection_table_t *table);

// 辅助函数：计算连接哈希
uint32_t state_hash(uint32_t src_ip, uint32_t dst_ip,
                    uint16_t src_port, uint16_t dst_port,
                    uint8_t protocol);

#endif /* STATE_H */
