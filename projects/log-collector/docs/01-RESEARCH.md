# 01 - 调研：日志收集系统

## 什么是日志收集系统

日志收集系统是一种基础设施组件，负责从多个来源采集日志数据，进行解析、转换、存储，并提供查询能力。

## 核心组件

### 1. 日志源（Log Sources）

- **应用日志**：应用程序输出的日志
- **系统日志**：操作系统日志（syslog）
- **访问日志**：Web 服务器访问日志
- **错误日志**：错误和异常日志
- **审计日志**：安全审计日志

### 2. 采集器（Collector）

采集器负责从日志源读取日志。常见实现：
- **Filebeat**：Elastic 的轻量级采集器
- **Fluentd**：CNCF 的日志收集器
- **Promtail**：Grafana Loki 的采集器
- **Vector**：Rust 实现的高性能采集器

### 3. 传输通道（Transport）

- **Kafka**：高吞吐量消息队列
- **Redis Pub/Sub**：轻量级消息传递
- **gRPC/HTTP**：直接传输
- **Channel**：进程内传输（本项目使用）

### 4. 存储（Storage）

- **Elasticsearch**：全文搜索和分析
- **ClickHouse**：列式分析数据库
- **Loki**：Grafana 的日志系统
- **文件系统**：简单的文件存储

### 5. 查询引擎（Query Engine）

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

## 性能考虑

- **吞吐量**：每秒处理的日志行数
- **延迟**：从日志产生到可查询的时间
- **内存使用**：缓冲区和索引的内存占用
- **磁盘 I/O**：写入存储的 I/O 开销

## 竞品分析

| 系统 | 语言 | 特点 |
|------|------|------|
| ELK Stack | Java | 功能全面，资源消耗大 |
| Loki + Grafana | Go | 轻量级，标签索引 |
| Fluentd | Ruby | 插件丰富，CNCF 项目 |
| Vector | Rust | 高性能，Rust 生态 |
| Splunk | C++ | 企业级，商业产品 |
