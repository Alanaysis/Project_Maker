# 开发手册

## 1. 环境搭建

### 1.1 系统要求

- **操作系统**：Linux (推荐 Ubuntu 20.04+)
- **内核版本**：>= 3.10
- **编译器**：GCC >= 7.0
- **权限**：root 权限（运行时）

### 1.2 依赖安装

**Ubuntu/Debian**：
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    libnetfilter-queue-dev \
    libpcap-dev \
    pkg-config
```

**CentOS/RHEL**：
```bash
sudo yum install -y \
    gcc \
    make \
    libnetfilter_queue-devel \
    libpcap-devel \
    pkgconfig
```

**Arch Linux**：
```bash
sudo pacman -S \
    base-devel \
    libnetfilter_queue \
    libpcap
```

### 1.3 验证环境

```bash
# 检查编译器
gcc --version

# 检查依赖
pkg-config --libs libnetfilter_queue
pkg-config --libs libpcap

# 检查内核版本
uname -r
```

## 2. 项目构建

### 2.1 编译

```bash
# 进入项目目录
cd projects/firewall

# 编译
make

# 编译并显示所有警告
make CFLAGS="-Wall -Wextra -g"

# 清理编译文件
make clean
```

### 2.2 Makefile 解释

```makefile
# 编译器
CC = gcc

# 编译选项
CFLAGS = -Wall -Wextra -g -O2
LDFLAGS = -lnetfilter_queue -lpcap

# 源文件
SRCDIR = src
SRCS = $(wildcard $(SRCDIR)/*.c)
OBJS = $(SRCS:.c=.o)

# 目标
TARGET = build/firewall

# 编译规则
$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o $@ $(LDFLAGS)

# 清理
clean:
	rm -f $(OBJS) $(TARGET)
```

### 2.3 编译选项说明

| 选项 | 说明 |
|------|------|
| `-Wall` | 显示所有警告 |
| `-Wextra` | 额外警告 |
| `-g` | 调试信息 |
| `-O2` | 优化级别 2 |
| `-DDEBUG` | 调试模式 |

## 3. 核心模块解析

### 3.1 包解析模块 (packet.c)

**功能**：解析网络数据包的各个层次

**关键函数**：
```c
// 解析以太网帧
int parse_ethernet(const uint8_t *data, size_t len, packet_t *pkt);

// 解析 IP 头部
int parse_ip(const uint8_t *data, size_t len, packet_t *pkt);

// 解析 TCP 头部
int parse_tcp(const uint8_t *data, size_t len, packet_t *pkt);

// 解析 UDP 头部
int parse_udp(const uint8_t *data, size_t len, packet_t *pkt);

// 解析 ICMP 头部
int parse_icmp(const uint8_t *data, size_t len, packet_t *pkt);
```

**学习要点**：
- ⭐ 理解网络字节序（大端序）
- ⭐ 理解头部长度计算
- 💡 为什么需要校验和验证？

### 3.2 规则引擎模块 (rules.c)

**功能**：加载和匹配过滤规则

**关键函数**：
```c
// 加载规则文件
int rules_load(rule_chain_t *chain, const char *filename);

// 匹配规则
rule_t *rules_match(rule_chain_t *chain, const packet_t *pkt);

// 添加规则
int rules_add(rule_chain_t *chain, const rule_t *rule);
```

**规则格式**：
```
# 注释
ACTION PROTOCOL [条件...]

# 示例
ACCEPT tcp dst_port 80
DROP tcp src_ip 192.168.1.100
ACCEPT tcp ESTABLISHED
```

**学习要点**：
- ⭐ 理解规则匹配顺序
- ⭐ 理解 CIDR 表示法
- 💡 如何优化规则匹配性能？

### 3.3 状态管理模块 (state.c)

**功能**：跟踪网络连接状态

**关键函数**：
```c
// 初始化连接表
connection_table_t *state_init(void);

// 查找连接
connection_t *state_lookup(connection_table_t *table, const packet_t *pkt);

// 更新连接状态
int state_update(connection_table_t *table, connection_t *conn, const packet_t *pkt);

// 清理超时连接
int state_cleanup(connection_table_t *table);
```

**TCP 状态机**：
```
    CLOSED
      ↓ SYN
    SYN_SENT
      ↓ SYN+ACK
    SYN_RECV
      ↓ ACK
  ESTABLISHED
      ↓ FIN
    FIN_WAIT
      ↓ ACK
    TIME_WAIT
      ↓ 超时
    CLOSED
```

**学习要点**：
- ⭐ 理解 TCP 三次握手
- ⭐ 理解 TCP 四次挥手
- 💡 为什么需要 TIME_WAIT 状态？

### 3.4 入侵检测模块 (ids.c)

**功能**：检测异常网络行为

**关键函数**：
```c
// 检测 SYN Flood
int detect_syn_flood(ids_context_t *ctx, const packet_t *pkt);

// 检测端口扫描
int detect_port_scan(ids_context_t *ctx, const packet_t *pkt);

// 检测异常包
int detect_anomaly(ids_context_t *ctx, const packet_t *pkt);
```

**检测算法**：
```c
// SYN Flood 检测
// 统计每秒 SYN 包数量，超过阈值则告警
if (syn_count_per_second > threshold) {
    alert(SYN_FLOOD, src_ip);
}
```

**学习要点**：
- ⭐ 理解 SYN Flood 攻击原理
- ⭐ 理解速率限制算法
- 💡 如何降低误报率？

### 3.5 日志模块 (logger.c)

**功能**：记录防火墙运行日志

**关键函数**：
```c
// 初始化日志系统
int logger_init(const char *filename, log_level_t level);

// 记录日志
void logger_log(log_level_t level, const char *fmt, ...);

// 记录包日志
void logger_packet(const packet_t *pkt, action_t action, uint32_t rule_id);

// 记录告警
void logger_alert(const alert_t *alert);
```

**日志级别**：
```c
typedef enum {
    LOG_DEBUG,      // 调试信息
    LOG_INFO,       // 一般信息
    LOG_WARNING,    // 警告
    LOG_ERROR,      // 错误
    LOG_ALERT       // 告警
} log_level_t;
```

**学习要点**：
- ⭐ 理解日志级别设计
- 💡 如何设计高效的日志系统？

## 4. 调试技巧

### 4.1 使用 GDB 调试

```bash
# 编译时添加调试信息
make CFLAGS="-g -O0"

# 启动 GDB
sudo gdb ./build/firewall

# 常用 GDB 命令
(gdb) break main          # 设置断点
(gdb) run -c config.conf  # 运行程序
(gdb) next                # 单步执行
(gdb) print pkt           # 打印变量
(gdb) backtrace           # 查看调用栈
(gdb) quit                # 退出
```

### 4.2 使用 Valgrind 检测内存问题

```bash
# 检测内存泄漏
sudo valgrind --leak-check=full ./build/firewall -c config.conf

# 输出示例
==12345== LEAK SUMMARY:
==12345==    definitely lost: 0 bytes in 0 blocks
==12345==    indirectly lost: 0 bytes in 0 blocks
==12345==      possibly lost: 0 bytes in 0 blocks
==12345==    still reachable: 1,024 bytes in 1 blocks
==12345==         suppressed: 0 bytes in 0 blocks
```

### 4.3 使用 tcpdump 验证

```bash
# 在另一个终端捕获流量
sudo tcpdump -i eth0 -n

# 过滤特定流量
sudo tcpdump -i eth0 tcp port 80
```

### 4.4 使用 Wireshark 分析

```bash
# 捕获流量到文件
sudo tcpdump -i eth0 -w capture.pcap

# 使用 Wireshark 打开
wireshark capture.pcap
```

## 5. 测试方法

### 5.1 单元测试

```bash
# 编译测试
make test

# 运行所有测试
./build/test_all

# 运行特定测试
./build/test_packet
./build/test_rules
./build/test_state
```

### 5.2 集成测试

```bash
# 启动防火墙
sudo ./build/firewall -c test.conf &

# 发送测试流量
curl http://example.com
ssh localhost

# 检查日志
tail -f /var/log/firewall.log
```

### 5.3 性能测试

```bash
# 使用 hping3 发送大量包
sudo hping3 -S -p 80 --flood 192.168.1.1

# 监控性能
top -p $(pgrep firewall)
```

## 6. 常见问题

### 6.1 权限问题

**问题**：`Permission denied`

**解决**：
```bash
sudo ./build/firewall -c config.conf
```

### 6.2 依赖缺失

**问题**：`libnetfilter_queue not found`

**解决**：
```bash
sudo apt-get install libnetfilter-queue-dev
```

### 6.3 内核模块缺失

**问题**：`nf_queue: no such module`

**解决**：
```bash
sudo modprobe nfnetlink_queue
sudo modprobe nf_conntrack
```

### 6.4 防火墙规则冲突

**问题**：iptables 规则冲突

**解决**：
```bash
# 查看现有规则
sudo iptables -L -n

# 清空规则（谨慎操作）
sudo iptables -F
```

## 7. 开发规范

### 7.1 代码风格

- 使用 4 空格缩进
- 函数名使用小写下划线
- 常量使用大写下划线
- 结构体使用 typedef

### 7.2 注释规范

```c
/**
 * 函数功能描述
 *
 * @param 参数1 参数说明
 * @param 参数2 参数说明
 * @return 返回值说明
 */
int function_name(int param1, int param2);
```

### 7.3 提交规范

```
<类型>(<范围>): <描述>

# 示例
feat(rules): add CIDR support
fix(state): fix memory leak
docs(readme): update installation guide
```

## 8. 部署指南

### 8.1 生产环境部署

```bash
# 1. 编译发布版本
make CFLAGS="-O2 -DNDEBUG"

# 2. 安装到系统
sudo make install

# 3. 创建配置文件
sudo cp configs/default.conf /etc/firewall/firewall.conf

# 4. 创建 systemd 服务
sudo cp firewall.service /etc/systemd/system/

# 5. 启动服务
sudo systemctl start firewall
sudo systemctl enable firewall
```

### 8.2 systemd 服务文件

```ini
[Unit]
Description=Firewall Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/firewall -c /etc/firewall/firewall.conf
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 9. 扩展开发

### 9.1 添加新协议

1. 在 `packet.h` 中定义协议头部结构
2. 在 `packet.c` 中添加解析函数
3. 在 `rules.c` 中添加匹配逻辑

### 9.2 添加新检测规则

1. 在 `ids.h` 中定义告警类型
2. 在 `ids.c` 中实现检测算法
3. 在配置文件中添加阈值配置

### 9.3 添加新日志后端

1. 在 `logger.h` 中定义接口
2. 实现新的日志输出模块
3. 在配置文件中启用

## 10. 学习资源

### 10.1 网络协议

- [RFC 791 - Internet Protocol](https://tools.ietf.org/html/rfc791)
- [RFC 793 - Transmission Control Protocol](https://tools.ietf.org/html/rfc793)
- [RFC 768 - User Datagram Protocol](https://tools.ietf.org/html/rfc768)

### 10.2 Netfilter

- [Netfilter 官方文档](https://www.netfilter.org/documentation.html)
- [libnetfilter_queue API](https://netfilter.org/projects/libnetfilter_queue/doxygen/)

### 10.3 防火墙

- [Linux Firewalls](https://www.booleanworld.com/depth-guide-iptables-linux-firewall/)
- [iptables 指南](https://www.frozentux.net/iptables-tutorial/)

### 10.4 C 语言

- [C Programming Language](https://en.wikipedia.org/wiki/The_C_Programming_Language)
- [Advanced Programming in the UNIX Environment](https://en.wikipedia.org/wiki/Advanced_Programming_in_the_Unix_Environment)
