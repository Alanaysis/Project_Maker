# 技术设计文档

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户空间应用                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    防火墙主程序                      │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────┐ │   │
│  │  │ 包捕获  │→│ 规则    │→│ 状态    │→│ 日志  │ │   │
│  │  │ 模块    │  │ 匹配    │  │ 检测    │  │ 记录  │ │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └───────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↕ libnetfilter_queue               │
├─────────────────────────────────────────────────────────────┤
│                      内核空间                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Netfilter 框架                    │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │              NFQUEUE 目标                    │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
firewall/
├── main.c              # 主程序入口，初始化和主循环
├── packet.c/h          # 数据包解析
├── rules.c/h           # 规则引擎
├── state.c/h           # 状态管理
├── ids.c/h             # 入侵检测
└── logger.c/h          # 日志模块
```

### 1.3 数据流

```
                     ┌─────────────┐
                     │   网络接口   │
                     └──────┬──────┘
                            ↓
                     ┌─────────────┐
                     │  Netfilter  │
                     │  NFQUEUE    │
                     └──────┬──────┘
                            ↓
                     ┌─────────────┐
                     │  包捕获模块  │
                     │  (packet.c) │
                     └──────┬──────┘
                            ↓
                     ┌─────────────┐
                     │  包解析模块  │
                     │  (packet.c) │
                     └──────┬──────┘
                            ↓
                     ┌─────────────┐
                     │  规则匹配    │
                     │  (rules.c)  │
                     └──────┬──────┘
                            ↓
                     ┌─────────────┐
                     │  状态检测    │
                     │  (state.c)  │
                     └──────┬──────┘
                            ↓
                     ┌─────────────┐
                     │  入侵检测    │
                     │  (ids.c)    │
                     └──────┬──────┘
                            ↓
                     ┌─────────────┐
                     │  日志记录    │
                     │  (logger.c) │
                     └──────┬──────┘
                            ↓
                     ┌─────────────┐
                     │  动作执行    │
                     │  ACCEPT/DROP│
                     └─────────────┘
```

## 2. 数据结构设计

### 2.1 数据包结构

```c
// include/packet.h

// IP 头部结构
typedef struct {
    uint8_t  version;       // IP 版本 (4)
    uint8_t  ihl;           // 头部长度 (单位: 4字节)
    uint8_t  tos;           // 服务类型
    uint16_t total_length;  // 总长度
    uint16_t id;            // 标识
    uint16_t flags_offset;  // 标志和片偏移
    uint8_t  ttl;           // 生存时间
    uint8_t  protocol;      // 协议类型
    uint16_t checksum;      // 校验和
    uint32_t src_ip;        // 源 IP 地址
    uint32_t dst_ip;        // 目的 IP 地址
} ip_header_t;

// TCP 头部结构
typedef struct {
    uint16_t src_port;      // 源端口
    uint16_t dst_port;      // 目的端口
    uint32_t seq;           // 序列号
    uint32_t ack;           // 确认号
    uint8_t  data_offset;   // 数据偏移
    uint8_t  flags;         // 标志位
    uint16_t window;        // 窗口大小
    uint16_t checksum;      // 校验和
    uint16_t urgent;        // 紧急指针
} tcp_header_t;

// UDP 头部结构
typedef struct {
    uint16_t src_port;      // 源端口
    uint16_t dst_port;      // 目的端口
    uint16_t length;        // 长度
    uint16_t checksum;      // 校验和
} udp_header_t;

// ICMP 头部结构
typedef struct {
    uint8_t  type;          // 类型
    uint8_t  code;          // 代码
    uint16_t checksum;      // 校验和
    uint16_t id;            // 标识
    uint16_t sequence;      // 序列号
} icmp_header_t;

// 解析后的数据包
typedef struct {
    // 原始数据
    uint8_t *data;          // 原始数据指针
    size_t   length;        // 数据长度

    // 解析后的头部
    ip_header_t  *ip;       // IP 头部
    tcp_header_t *tcp;      // TCP 头部
    udp_header_t *udp;      // UDP 头部
    icmp_header_t *icmp;    // ICMP 头部

    // 便捷字段
    uint8_t  protocol;      // 协议类型
    uint32_t src_ip;        // 源 IP
    uint32_t dst_ip;        // 目的 IP
    uint16_t src_port;      // 源端口
    uint16_t dst_port;      // 目的端口
    uint8_t  tcp_flags;     // TCP 标志

    // 时间戳
    time_t timestamp;       // 捕获时间
} packet_t;
```

### 2.2 规则结构

```c
// include/rules.h

// 动作类型
typedef enum {
    ACTION_ACCEPT,          // 允许
    ACTION_DROP,            // 丢弃
    ACTION_REJECT,          // 拒绝
    ACTION_LOG              // 仅记录
} action_t;

// 协议类型
typedef enum {
    PROTO_ALL = 0,          // 所有协议
    PROTO_TCP = 6,          // TCP
    PROTO_UDP = 17,         // UDP
    PROTO_ICMP = 1          // ICMP
} protocol_t;

// 规则结构
typedef struct {
    uint32_t id;            // 规则 ID

    // 匹配条件
    uint32_t src_ip;        // 源 IP (0 表示任意)
    uint32_t src_mask;      // 源 IP 掩码
    uint32_t dst_ip;        // 目的 IP
    uint32_t dst_mask;      // 目的 IP 掩码
    uint16_t src_port;      // 源端口 (0 表示任意)
    uint16_t dst_port;      // 目的端口
    uint8_t  protocol;      // 协议类型

    // 状态匹配
    uint8_t  match_state;   // 是否匹配状态
    uint8_t  state_flags;   // 状态标志

    // 动作
    action_t action;        // 动作类型

    // 日志
    uint8_t  log;           // 是否记录日志
} rule_t;

// 规则链
typedef struct {
    rule_t *rules;          // 规则数组
    size_t  count;          // 规则数量
    size_t  capacity;       // 规则容量
    action_t default_action; // 默认动作
} rule_chain_t;
```

### 2.3 连接状态结构

```c
// include/state.h

// TCP 状态
typedef enum {
    TCP_STATE_NONE,
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
    DIR_ORIGINAL,           // 原始方向 (客户端→服务器)
    DIR_REPLY               // 回复方向 (服务器→客户端)
} direction_t;

// 连接记录
typedef struct {
    // 连接标识
    uint32_t src_ip;        // 源 IP
    uint32_t dst_ip;        // 目的 IP
    uint16_t src_port;      // 源端口
    uint16_t dst_port;      // 目的端口
    uint8_t  protocol;      // 协议

    // 状态信息
    tcp_state_t tcp_state;  // TCP 状态
    direction_t direction;  // 方向

    // 统计信息
    uint32_t packets;       // 包数量
    uint64_t bytes;         // 字节数

    // 时间信息
    time_t start_time;      // 开始时间
    time_t last_time;       // 最后活动时间
    time_t timeout;         // 超时时间
} connection_t;

// 连接表
#define CONN_TABLE_SIZE 65536

typedef struct {
    connection_t *table;    // 连接表
    size_t count;           // 连接数量
    size_t capacity;        // 表容量
    pthread_mutex_t lock;   // 互斥锁
} connection_table_t;
```

### 2.4 入侵检测结构

```c
// include/ids.h

// 告警类型
typedef enum {
    ALERT_SYN_FLOOD,        // SYN Flood 攻击
    ALERT_PORT_SCAN,        // 端口扫描
    ALERT_ANOMALY_PKT,      // 异常包
    ALERT_RATE_EXCEEDED     // 速率超限
} alert_type_t;

// 告警记录
typedef struct {
    alert_type_t type;      // 告警类型
    time_t timestamp;       // 时间戳
    uint32_t src_ip;        // 源 IP
    uint32_t dst_ip;        // 目的 IP
    char description[256];  // 描述
} alert_t;

// 速率统计
typedef struct {
    uint32_t src_ip;        // 源 IP
    time_t window_start;    // 窗口开始时间
    uint32_t count;         // 计数
} rate_stat_t;

// IDS 上下文
typedef struct {
    // 阈值配置
    uint32_t syn_flood_threshold;   // SYN Flood 阈值 (包/秒)
    uint32_t port_scan_threshold;   // 端口扫描阈值 (端口/分钟)
    uint32_t pkt_size_min;          // 最小包大小
    uint32_t pkt_size_max;          // 最大包大小

    // 统计数据
    rate_stat_t *syn_stats;         // SYN 统计
    rate_stat_t *scan_stats;        // 扫描统计
    size_t stats_capacity;

    // 告警列表
    alert_t *alerts;                // 告警数组
    size_t alert_count;
    size_t alert_capacity;
} ids_context_t;
```

## 3. 接口设计

### 3.1 包解析接口

```c
// include/packet.h

// 初始化包解析器
int packet_init(void);

// 解析数据包
int packet_parse(const uint8_t *data, size_t len, packet_t *pkt);

// 获取协议名称
const char *packet_proto_name(uint8_t protocol);

// 打印包信息
void packet_print(const packet_t *pkt);

// 清理资源
void packet_cleanup(void);
```

### 3.2 规则引擎接口

```c
// include/rules.h

// 初始化规则引擎
rule_chain_t *rules_init(void);

// 加载规则文件
int rules_load(rule_chain_t *chain, const char *filename);

// 添加规则
int rules_add(rule_chain_t *chain, const rule_t *rule);

// 匹配规则
rule_t *rules_match(rule_chain_t *chain, const packet_t *pkt);

// 打印规则
void rules_print(const rule_chain_t *chain);

// 清理资源
void rules_cleanup(rule_chain_t *chain);
```

### 3.3 状态管理接口

```c
// include/state.h

// 初始化连接表
connection_table_t *state_init(void);

// 查找或创建连接
connection_t *state_lookup(connection_table_t *table, const packet_t *pkt);

// 更新连接状态
int state_update(connection_table_t *table, connection_t *conn, const packet_t *pkt);

// 清理超时连接
int state_cleanup(connection_table_t *table);

// 打印连接表
void state_print(const connection_table_t *table);

// 清理资源
void state_cleanup_all(connection_table_t *table);
```

### 3.4 入侵检测接口

```c
// include/ids.h

// 初始化 IDS
ids_context_t *ids_init(void);

// 加载 IDS 配置
int ids_load_config(ids_context_t *ctx, const char *filename);

// 检测数据包
int ids_detect(ids_context_t *ctx, const packet_t *pkt);

// 获取告警
int ids_get_alerts(ids_context_t *ctx, alert_t *alerts, size_t max_count);

// 清理资源
void ids_cleanup(ids_context_t *ctx);
```

### 3.5 日志接口

```c
// include/logger.h

// 日志级别
typedef enum {
    LOG_DEBUG,
    LOG_INFO,
    LOG_WARNING,
    LOG_ERROR,
    LOG_ALERT
} log_level_t;

// 初始化日志系统
int logger_init(const char *filename, log_level_t level);

// 记录日志
void logger_log(log_level_t level, const char *fmt, ...);

// 记录包日志
void logger_packet(const packet_t *pkt, action_t action, uint32_t rule_id);

// 记录告警
void logger_alert(const alert_t *alert);

// 清理资源
void logger_cleanup(void);
```

## 4. 核心算法

### 4.1 规则匹配算法

```c
// 简单的线性匹配算法
rule_t *rules_match(rule_chain_t *chain, const packet_t *pkt) {
    for (size_t i = 0; i < chain->count; i++) {
        rule_t *rule = &chain->rules[i];

        // 检查协议
        if (rule->protocol != PROTO_ALL &&
            rule->protocol != pkt->protocol) {
            continue;
        }

        // 检查源 IP
        if (rule->src_ip != 0 &&
            (pkt->src_ip & rule->src_mask) != (rule->src_ip & rule->src_mask)) {
            continue;
        }

        // 检查目的 IP
        if (rule->dst_ip != 0 &&
            (pkt->dst_ip & rule->dst_mask) != (rule->dst_ip & rule->dst_mask)) {
            continue;
        }

        // 检查源端口
        if (rule->src_port != 0 && rule->src_port != pkt->src_port) {
            continue;
        }

        // 检查目的端口
        if (rule->dst_port != 0 && rule->dst_port != pkt->dst_port) {
            continue;
        }

        // 规则匹配
        return rule;
    }

    // 返回默认动作
    return NULL;
}
```

### 4.2 TCP 状态机

```c
// TCP 状态转换
tcp_state_t tcp_next_state(tcp_state_t current, uint8_t flags) {
    switch (current) {
        case TCP_STATE_NONE:
            if (flags & TCP_SYN) {
                return TCP_STATE_SYN_SENT;
            }
            break;

        case TCP_STATE_SYN_SENT:
            if ((flags & TCP_SYN) && (flags & TCP_ACK)) {
                return TCP_STATE_SYN_RECV;
            }
            break;

        case TCP_STATE_SYN_RECV:
            if (flags & TCP_ACK) {
                return TCP_STATE_ESTABLISHED;
            }
            break;

        case TCP_STATE_ESTABLISHED:
            if (flags & TCP_FIN) {
                return TCP_STATE_FIN_WAIT;
            }
            break;

        case TCP_STATE_FIN_WAIT:
            if (flags & TCP_ACK) {
                return TCP_STATE_TIME_WAIT;
            }
            break;

        case TCP_STATE_TIME_WAIT:
            // 超时后关闭
            break;

        default:
            break;
    }
    return current;
}
```

### 4.3 连接表查找算法

```c
// 基于哈希的连接表查找
uint32_t conn_hash(uint32_t src_ip, uint32_t dst_ip,
                   uint16_t src_port, uint16_t dst_port,
                   uint8_t protocol) {
    uint32_t hash = 0;
    hash ^= src_ip;
    hash ^= dst_ip;
    hash ^= (src_port << 16) | dst_port;
    hash ^= protocol;
    return hash % CONN_TABLE_SIZE;
}

connection_t *state_lookup(connection_table_t *table, const packet_t *pkt) {
    uint32_t index = conn_hash(pkt->src_ip, pkt->dst_ip,
                               pkt->src_port, pkt->dst_port,
                               pkt->protocol);

    // 线性探测
    while (table->table[index].src_ip != 0) {
        connection_t *conn = &table->table[index];

        // 检查是否匹配
        if (conn->src_ip == pkt->src_ip &&
            conn->dst_ip == pkt->dst_ip &&
            conn->src_port == pkt->src_port &&
            conn->dst_port == pkt->dst_port &&
            conn->protocol == pkt->protocol) {
            return conn;
        }

        index = (index + 1) % table->capacity;
    }

    return NULL;  // 未找到
}
```

## 5. 错误处理设计

### 5.1 错误码定义

```c
// include/common.h

typedef enum {
    FW_OK = 0,              // 成功
    FW_ERR_NOMEM,           // 内存不足
    FW_ERR_INVAL,           // 无效参数
    FW_ERR_NOT_FOUND,       // 未找到
    FW_ERR_PERM,            // 权限不足
    FW_ERR_IO,              // I/O 错误
    FW_ERR_PARSE,           // 解析错误
    FW_ERR_NET,             // 网络错误
    FW_ERR_FULL,            // 表已满
    FW_ERR_TIMEOUT          // 超时
} fw_error_t;
```

### 5.2 错误处理策略

- **内存不足**：记录日志，尝试清理后重试
- **权限不足**：提示用户使用 root 权限
- **配置错误**：记录错误位置，退出程序
- **网络错误**：记录日志，继续运行

## 6. 性能优化设计

### 6.1 优化策略

1. **规则预编译**：将规则编译为内部表示，避免重复解析
2. **连接表缓存**：使用哈希表加速连接查找
3. **批量处理**：批量处理数据包，减少系统调用
4. **内存池**：预分配内存，减少 malloc/free

### 6.2 性能指标

| 指标 | 目标值 |
|------|--------|
| 包处理延迟 | < 1ms |
| 吞吐量 | > 10,000 包/秒 |
| 内存使用 | < 50MB |
| 连接表容量 | 65,536 |

## 7. 扩展性设计

### 7.1 插件接口

```c
// 未来的插件接口设计
typedef struct {
    const char *name;
    int (*init)(void);
    int (*process)(packet_t *pkt);
    void (*cleanup)(void);
} plugin_t;
```

### 7.2 可扩展点

- 新增协议支持
- 新增检测规则
- 新增日志后端
- 新增告警方式

## 8. 安全考虑

### 8.1 权限管理
- 必须以 root 权限运行
- 可以使用 capabilities 精细控制

### 8.2 防御措施
- 防止规则注入
- 防止日志洪水
- 防止资源耗尽

### 8.3 审计日志
- 记录所有配置变更
- 记录所有告警事件
- 日志不可篡改
