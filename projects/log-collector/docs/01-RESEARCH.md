# 01 - 调研：日志收集系统

## 什么是日志收集系统

日志收集系统是一种基础设施组件，负责从多个来源采集日志数据，进行解析、转换、过滤、存储，并提供查询能力。

## 核心组件

### 1. 日志源（Log Sources）

- **应用日志**：应用程序输出的日志
- **系统日志**：操作系统日志（syslog）
- **访问日志**：Web 服务器访问日志
- **错误日志**：错误和异常日志
- **审计日志**：安全审计日志
- **网络日志**：通过 TCP/UDP 接收的日志

### 2. 采集器（Collector）

采集器负责从日志源读取日志。常见实现：
- **Filebeat**：Elastic 的轻量级采集器
- **Fluentd**：CNCF 的日志收集器
- **Promtail**：Grafana Loki 的采集器
- **Vector**：Rust 实现的高性能采集器

采集方式：
- **文件读取**：一次性读取日志文件
- **文件监控**：持续监控文件变化（tail -f）
- **网络接收**：通过 TCP/UDP 接收日志
- **Syslog**：通过 syslog 协议接收

### 3. 解析器（Parser）

解析器将原始日志行转换为结构化数据：
- **JSON 解析**：解析 JSON 格式日志
- **Logfmt 解析**：解析 key=value 格式
- **正则解析**：使用正则表达式自定义解析
- **自动检测**：自动识别日志格式

### 4. 过滤器（Filter）

过滤器根据条件筛选日志：
- **级别过滤**：按日志级别过滤
- **关键词过滤**：按关键词匹配过滤
- **正则过滤**：按正则表达式过滤
- **来源过滤**：按日志来源过滤
- **组合过滤**：AND/OR 逻辑组合

### 5. 传输通道（Transport）

- **Kafka**：高吞吐量消息队列
- **Redis Pub/Sub**：轻量级消息传递
- **TCP/UDP**：网络传输协议
- **gRPC/HTTP**：直接传输
- **Channel**：进程内传输（本项目使用）

### 6. 存储（Storage）

- **Elasticsearch**：全文搜索和分析
- **ClickHouse**：列式分析数据库
- **Loki**：Grafana 的日志系统
- **文件系统**：简单的文件存储

### 7. 查询引擎（Query Engine）

- **Kibana**：Elasticsearch 的可视化工具
- **Grafana**：通用可视化平台
- **SQL**：结构化查询语言
- **自定义 DSL**：领域特定查询语言

## 日志格式标准

### Syslog (RFC 5424)

```
<165>1 2024-01-15T10:30:00.000Z myhost myapp 1234 - - Hello World
```

### JSON

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "message": "Hello World",
  "service": "myapp",
  "trace_id": "abc123"
}
```

### Logfmt

```
ts=2024-01-15T10:30:00Z level=info msg="Hello World" service=myapp trace_id=abc123
```

### Common Log Format

```
2024-01-15 10:30:00 [INFO] Application started successfully
```

### Apache Combined Log Format

```
192.168.1.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
```

## 性能考虑

- **吞吐量**：每秒处理的日志行数
- **延迟**：从日志产生到可查询的时间
- **内存使用**：缓冲区和索引的内存占用
- **磁盘 I/O**：写入存储的 I/O 开销
- **网络带宽**：网络传输的带宽消耗

## 竞品分析

| 系统 | 语言 | 特点 |
|------|------|------|
| ELK Stack | Java | 功能全面，资源消耗大 |
| Loki + Grafana | Go | 轻量级，标签索引 |
| Fluentd | Ruby | 插件丰富，CNCF 项目 |
| Vector | Rust | 高性能，Rust 生态 |
| Splunk | C++ | 企业级，商业产品 |

## 本项目实现范围

本项目实现了以下核心功能：
1. **日志采集**：文件读取、文件监控（tail）、TCP/UDP 网络接收
2. **日志解析**：JSON、Logfmt、Common、自定义正则
3. **日志过滤**：级别过滤、关键词过滤、正则过滤、组合过滤
4. **日志传输**：TCP/UDP 接收、文件输出（带轮转）
5. **日志存储**：内存存储，带索引
6. **日志查询**：高级查询 DSL、交互式查询
