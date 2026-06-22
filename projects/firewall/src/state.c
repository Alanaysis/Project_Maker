/**
 * 状态管理模块
 *
 * 本模块负责：
 * 1. 跟踪网络连接状态
 * 2. 管理连接表
 * 3. 处理超时连接
 *
 * ⭐ 重点：理解 TCP 状态机
 *    TCP 连接有明确的状态转换：
 *    CLOSED → SYN_SENT → SYN_RECV → ESTABLISHED → FIN_WAIT → TIME_WAIT → CLOSED
 *
 * 💡 思考：为什么需要状态检测？
 *    - 无状态防火墙只检查单个包，无法判断是否属于已建立的连接
 *    - 有状态防火墙可以跟踪连接状态，更安全
 *    - 可以防止 IP 欺骗和端口扫描
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <pthread.h>

#include "state.h"

/**
 * 计算连接哈希
 *
 * 使用简单的异或哈希算法
 *
 * @param src_ip 源 IP
 * @param dst_ip 目的 IP
 * @param src_port 源端口
 * @param dst_port 目的端口
 * @param protocol 协议
 * @return 哈希值
 */
uint32_t state_hash(uint32_t src_ip, uint32_t dst_ip,
                    uint16_t src_port, uint16_t dst_port,
                    uint8_t protocol) {
    uint32_t hash = 0;

    hash ^= src_ip;
    hash ^= dst_ip;
    hash ^= ((uint32_t)src_port << 16) | dst_port;
    hash ^= protocol;

    // 使用乘法哈希使分布更均匀
    hash = hash * 2654435761U;

    return hash % CONN_TABLE_SIZE;
}

/**
 * 初始化连接表
 *
 * @return 连接表指针，失败返回 NULL
 */
connection_table_t *state_init(void) {
    connection_table_t *table;

    table = (connection_table_t *)calloc(1, sizeof(connection_table_t));
    if (!table) {
        return NULL;
    }

    // 分配连接表
    table->table = (connection_t *)calloc(CONN_TABLE_SIZE, sizeof(connection_t));
    if (!table->table) {
        free(table);
        return NULL;
    }

    table->count = 0;
    table->capacity = CONN_TABLE_SIZE;

    // 初始化互斥锁
    pthread_mutex_init(&table->lock, NULL);

    return table;
}

/**
 * 获取默认超时时间
 *
 * @param protocol 协议类型
 * @param tcp_state TCP 状态
 * @return 超时时间（秒）
 */
static time_t get_timeout(uint8_t protocol, tcp_state_t tcp_state) {
    switch (protocol) {
        case PROTO_TCP:
            if (tcp_state == TCP_STATE_ESTABLISHED) {
                return CONN_TCP_TIMEOUT;
            } else {
                return CONN_TCP_NEW_TIMEOUT;
            }
        case PROTO_UDP:
            return CONN_UDP_TIMEOUT;
        case PROTO_ICMP:
            return CONN_ICMP_TIMEOUT;
        default:
            return CONN_TCP_TIMEOUT;
    }
}

/**
 * 创建新连接
 *
 * @param pkt 数据包
 * @return 连接指针
 */
static connection_t *create_connection(const packet_t *pkt) {
    connection_t *conn;

    conn = (connection_t *)calloc(1, sizeof(connection_t));
    if (!conn) {
        return NULL;
    }

    // 设置连接标识
    conn->src_ip = pkt->src_ip;
    conn->dst_ip = pkt->dst_ip;
    conn->src_port = pkt->src_port;
    conn->dst_port = pkt->dst_port;
    conn->protocol = pkt->protocol;

    // 设置连接类型
    switch (pkt->protocol) {
        case PROTO_TCP:
            conn->type = CONN_TCP;
            break;
        case PROTO_UDP:
            conn->type = CONN_UDP;
            break;
        case PROTO_ICMP:
            conn->type = CONN_ICMP;
            break;
        default:
            conn->type = CONN_TCP;
            break;
    }

    // 设置初始状态
    conn->tcp_state = TCP_STATE_NONE;
    conn->direction = DIR_ORIGINAL;

    // 设置时间
    conn->start_time = pkt->timestamp;
    conn->last_time = pkt->timestamp;
    conn->timeout = get_timeout(pkt->protocol, conn->tcp_state);

    // 初始化统计
    conn->packets = 1;
    conn->bytes = pkt->length;

    conn->valid = 1;

    return conn;
}

/**
 * 查找连接
 *
 * 使用哈希表和线性探测法
 *
 * @param table 连接表
 * @param pkt 数据包
 * @return 连接指针，未找到返回 NULL
 */
connection_t *state_lookup(connection_table_t *table, const packet_t *pkt) {
    if (!table || !pkt) {
        return NULL;
    }

    uint32_t hash = state_hash(pkt->src_ip, pkt->dst_ip,
                               pkt->src_port, pkt->dst_port,
                               pkt->protocol);

    pthread_mutex_lock(&table->lock);

    // 线性探测
    uint32_t index = hash;
    while (table->table[index].valid) {
        connection_t *conn = &table->table[index];

        // 检查是否匹配（正向）
        if (conn->src_ip == pkt->src_ip &&
            conn->dst_ip == pkt->dst_ip &&
            conn->src_port == pkt->src_port &&
            conn->dst_port == pkt->dst_port &&
            conn->protocol == pkt->protocol) {
            pthread_mutex_unlock(&table->lock);
            return conn;
        }

        // 检查是否匹配（反向）
        if (conn->src_ip == pkt->dst_ip &&
            conn->dst_ip == pkt->src_ip &&
            conn->src_port == pkt->dst_port &&
            conn->dst_port == pkt->src_port &&
            conn->protocol == pkt->protocol) {
            // 标记为回复方向
            pkt->tcp_flags;  // 避免编译警告
            pthread_mutex_unlock(&table->lock);
            return conn;
        }

        // 移动到下一个位置
        index = (index + 1) % table->capacity;

        // 防止无限循环
        if (index == hash) {
            break;
        }
    }

    pthread_mutex_unlock(&table->lock);
    return NULL;
}

/**
 * 添加连接到表中
 *
 * @param table 连接表
 * @param conn 连接
 * @return 0 成功，-1 失败
 */
static int add_connection(connection_table_t *table, connection_t *conn) {
    if (!table || !conn) {
        return -1;
    }

    // 检查表是否已满
    if (table->count >= table->capacity * 0.8) {
        // 表已满，需要清理
        state_cleanup(table);
    }

    uint32_t hash = state_hash(conn->src_ip, conn->dst_ip,
                               conn->src_port, conn->dst_port,
                               conn->protocol);

    // 线性探测找空位
    uint32_t index = hash;
    while (table->table[index].valid) {
        index = (index + 1) % table->capacity;
        if (index == hash) {
            return -1;  // 表已满
        }
    }

    // 复制连接
    table->table[index] = *conn;
    table->count++;

    return 0;
}

/**
 * 更新 TCP 状态
 *
 * ⭐ 重点：理解 TCP 状态机
 *
 * TCP 状态转换：
 * CLOSED → SYN_SENT (客户端发送 SYN)
 * SYN_SENT → SYN_RECV (服务器收到 SYN)
 * SYN_RECV → ESTABLISHED (客户端收到 SYN+ACK)
 * ESTABLISHED → FIN_WAIT (一方发送 FIN)
 * FIN_WAIT → TIME_WAIT (收到 ACK)
 * TIME_WAIT → CLOSED (超时)
 *
 * @param conn 连接
 * @param pkt 数据包
 */
static void update_tcp_state(connection_t *conn, const packet_t *pkt) {
    uint8_t flags = pkt->tcp_flags;

    switch (conn->tcp_state) {
        case TCP_STATE_NONE:
            if (flags & TCP_SYN) {
                conn->tcp_state = TCP_STATE_SYN_SENT;
            }
            break;

        case TCP_STATE_SYN_SENT:
            if ((flags & TCP_SYN) && (flags & TCP_ACK)) {
                conn->tcp_state = TCP_STATE_SYN_RECV;
            } else if (flags & TCP_RST) {
                conn->tcp_state = TCP_STATE_CLOSED;
            }
            break;

        case TCP_STATE_SYN_RECV:
            if (flags & TCP_ACK) {
                conn->tcp_state = TCP_STATE_ESTABLISHED;
            } else if (flags & TCP_RST) {
                conn->tcp_state = TCP_STATE_CLOSED;
            }
            break;

        case TCP_STATE_ESTABLISHED:
            if (flags & TCP_FIN) {
                conn->tcp_state = TCP_STATE_FIN_WAIT;
            } else if (flags & TCP_RST) {
                conn->tcp_state = TCP_STATE_CLOSED;
            }
            break;

        case TCP_STATE_FIN_WAIT:
            if (flags & TCP_ACK) {
                conn->tcp_state = TCP_STATE_TIME_WAIT;
            } else if (flags & TCP_RST) {
                conn->tcp_state = TCP_STATE_CLOSED;
            }
            break;

        case TCP_STATE_TIME_WAIT:
            // 等待超时
            break;

        case TCP_STATE_CLOSED:
            // 已关闭
            break;

        default:
            break;
    }

    // 更新超时时间
    conn->timeout = get_timeout(conn->protocol, conn->tcp_state);
}

/**
 * 查找或创建连接
 *
 * @param table 连接表
 * @param pkt 数据包
 * @return 连接指针，失败返回 NULL
 */
connection_t *state_lookup_or_create(connection_table_t *table, const packet_t *pkt) {
    connection_t *conn;

    if (!table || !pkt) {
        return NULL;
    }

    pthread_mutex_lock(&table->lock);

    // 先查找（内联查找逻辑，避免在锁外查找导致 TOCTOU 竞态）
    uint32_t hash = state_hash(pkt->src_ip, pkt->dst_ip,
                               pkt->src_port, pkt->dst_port,
                               pkt->protocol);

    uint32_t index = hash;
    while (table->table[index].valid) {
        conn = &table->table[index];

        // 正向匹配
        if (conn->src_ip == pkt->src_ip &&
            conn->dst_ip == pkt->dst_ip &&
            conn->src_port == pkt->src_port &&
            conn->dst_port == pkt->dst_port &&
            conn->protocol == pkt->protocol) {
            pthread_mutex_unlock(&table->lock);
            return conn;
        }

        // 反向匹配
        if (conn->src_ip == pkt->dst_ip &&
            conn->dst_ip == pkt->src_ip &&
            conn->src_port == pkt->dst_port &&
            conn->dst_port == pkt->src_port &&
            conn->protocol == pkt->protocol) {
            pthread_mutex_unlock(&table->lock);
            return conn;
        }

        index = (index + 1) % table->capacity;
    }

    // 未找到，创建新连接
    conn = create_connection(pkt);
    if (!conn) {
        pthread_mutex_unlock(&table->lock);
        return NULL;
    }

    // 添加到表中（已在锁内，无需再次加锁）
    if (add_connection(table, conn) != 0) {
        pthread_mutex_unlock(&table->lock);
        free(conn);
        return NULL;
    }

    pthread_mutex_unlock(&table->lock);

    return conn;
}

/**
 * 更新连接状态
 *
 * @param table 连接表
 * @param conn 连接
 * @param pkt 数据包
 * @return 0 成功，-1 失败
 */
int state_update(connection_table_t *table, connection_t *conn, const packet_t *pkt) {
    if (!table || !conn || !pkt) {
        return -1;
    }

    pthread_mutex_lock(&table->lock);

    // 更新统计信息
    conn->packets++;
    conn->bytes += pkt->length;
    conn->last_time = pkt->timestamp;

    // 更新方向
    if (conn->src_ip == pkt->src_ip && conn->src_port == pkt->src_port) {
        conn->direction = DIR_ORIGINAL;
    } else {
        conn->direction = DIR_REPLY;
    }

    // 更新 TCP 状态
    if (pkt->protocol == PROTO_TCP && pkt->tcp) {
        update_tcp_state(conn, pkt);
    }

    pthread_mutex_unlock(&table->lock);

    return 0;
}

/**
 * 清理超时连接
 *
 * @param table 连接表
 * @return 清理的连接数量
 */
int state_cleanup(connection_table_t *table) {
    if (!table) {
        return 0;
    }

    int cleaned = 0;
    time_t now = time(NULL);

    pthread_mutex_lock(&table->lock);

    for (size_t i = 0; i < table->capacity; i++) {
        connection_t *conn = &table->table[i];

        if (!conn->valid) {
            continue;
        }

        // 检查是否超时
        if (difftime(now, conn->last_time) > conn->timeout) {
            // 标记为无效
            conn->valid = 0;
            table->count--;
            cleaned++;
        }
    }

    pthread_mutex_unlock(&table->lock);

    return cleaned;
}

/**
 * 获取连接数量
 *
 * @param table 连接表
 * @return 连接数量
 */
size_t state_count(const connection_table_t *table) {
    return table ? table->count : 0;
}

/**
 * 获取 TCP 状态名称
 *
 * @param state TCP 状态
 * @return 状态名称字符串
 */
const char *state_tcp_state_name(tcp_state_t state) {
    switch (state) {
        case TCP_STATE_NONE:        return "NONE";
        case TCP_STATE_SYN_SENT:    return "SYN_SENT";
        case TCP_STATE_SYN_RECV:    return "SYN_RECV";
        case TCP_STATE_ESTABLISHED: return "ESTABLISHED";
        case TCP_STATE_FIN_WAIT:    return "FIN_WAIT";
        case TCP_STATE_CLOSE_WAIT:  return "CLOSE_WAIT";
        case TCP_STATE_LAST_ACK:    return "LAST_ACK";
        case TCP_STATE_TIME_WAIT:   return "TIME_WAIT";
        case TCP_STATE_CLOSED:      return "CLOSED";
        default:                    return "UNKNOWN";
    }
}

/**
 * 打印连接信息
 *
 * @param conn 连接
 */
void state_print_connection(const connection_t *conn) {
    if (!conn) return;

    char src_ip[INET_ADDRSTRLEN];
    char dst_ip[INET_ADDRSTRLEN];
    struct in_addr addr;

    addr.s_addr = conn->src_ip;
    strcpy(src_ip, inet_ntoa(addr));

    addr.s_addr = conn->dst_ip;
    strcpy(dst_ip, inet_ntoa(addr));

    printf("%s:%d → %s:%d [%s] [%s] pkts=%u bytes=%lu\n",
           src_ip, conn->src_port,
           dst_ip, conn->dst_port,
           packet_proto_name(conn->protocol),
           state_tcp_state_name(conn->tcp_state),
           conn->packets,
           conn->bytes);
}

/**
 * 打印连接表
 *
 * @param table 连接表
 */
void state_print(const connection_table_t *table) {
    if (!table) return;

    printf("\n=== Connection Table ===\n");
    printf("Active connections: %zu / %zu\n", table->count, table->capacity);
    printf("\n");

    for (size_t i = 0; i < table->capacity; i++) {
        if (table->table[i].valid) {
            state_print_connection(&table->table[i]);
        }
    }

    printf("========================\n\n");
}

/**
 * 清理所有连接
 *
 * @param table 连接表
 */
void state_cleanup_all(connection_table_t *table) {
    if (!table) return;

    pthread_mutex_lock(&table->lock);

    free(table->table);
    table->table = NULL;
    table->count = 0;
    table->capacity = 0;

    pthread_mutex_unlock(&table->lock);

    pthread_mutex_destroy(&table->lock);
    free(table);
}
