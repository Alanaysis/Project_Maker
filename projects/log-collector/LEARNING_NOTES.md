# Log Collector - 学习笔记

## 项目概述

实现一个分布式日志收集系统，掌握日志架构、日志解析、日志过滤和日志聚合的核心概念。

## 学习目标

1. 理解日志架构
2. 掌握日志解析（含正则解析）
3. 学会日志过滤
4. 学会日志聚合
5. 理解网络传输

## 核心概念

### 1. 日志架构

日志系统的核心循环：日志产生 -> 采集 -> 传输 -> 解析 -> 过滤 -> 存储 -> 查询

#### 日志采集

日志采集是日志系统的入口。常见的采集方式：
- **文件采集**：监听日志文件，读取新增内容
- **文件监控**：持续监控文件变化（tail -f）
- **网络采集**：通过 TCP/UDP 接收日志
- **Syslog**：通过 syslog 协议接收日志
- **Agent**：在每个节点部署日志 Agent
- **SDK**：应用内嵌日志 SDK

本项目实现了文件采集、文件监控和 TCP/UDP 网络接收。

#### 日志传输

日志传输需要考虑：
- **可靠性**：不丢失日志
- **顺序性**：保持日志顺序
- **缓冲**：生产者和消费者速度不匹配时的缓冲
- **协议选择**：TCP（可靠）vs UDP（高性能）

本项目使用 Go channel 作为内部传输通道，TCP/UDP 作为网络传输。

#### 日志存储

日志存储的选择：
- **文件系统**：简单直接，适合小规模
- **Elasticsearch**：全文搜索，适合大规模
- **ClickHouse**：列式存储，适合分析查询
- **时序数据库**：如 InfluxDB，适合时间序列数据

本项目使用内存存储，演示了索引的设计思路。

### 2. 日志解析

#### 结构化日志 vs 非结构化日志

**非结构化日志**：
```
2024-01-15 10:30:00 [INFO] Application started successfully
```
- 人类可读
- 难以机器解析
- 需要正则表达式匹配

**结构化日志**：
```json
{"level":"info","msg":"server started","ts":"2024-01-01T12:00:00Z"}
```
- 机器友好
- 易于解析和查询
- 支持任意字段

#### 常见日志格式

1. **JSON**：最流行的结构化日志格式
2. **Logfmt**：Go 生态常用的 key=value 格式
3. **Common Log Format**：Apache/Nginx 使用的格式
4. **Syslog**：系统日志标准格式
5. **自定义格式**：使用正则表达式定义

#### 解析策略

本项目实现了自动检测格式的策略：
1. 尝试 JSON 解析
2. 尝试 Logfmt 解析
3. 尝试 Common 格式解析
4. 兜底：整行作为消息

#### 正则解析

正则解析器使用命名捕获组映射到字段：
```go
pattern := `^(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<msg>.+)$`
```

内置模式：Apache、Syslog、Generic、Access。

### 3. 日志过滤

#### 过滤策略

- **级别过滤**：按日志级别过滤，只保留 >= 指定级别的日志
- **关键词过滤**：按关键词匹配，支持包含/排除模式
- **正则过滤**：按正则表达式匹配，支持复杂模式
- **来源过滤**：按日志来源过滤

#### 组合过滤

- **Chain（AND）**：所有过滤器都匹配才通过
- **MatchAny（OR）**：任一过滤器匹配就通过

#### 过滤器接口

```go
type Filter interface {
    Match(entry Entry) bool
}
```

使用接口模式，支持自定义过滤器。

### 4. 日志聚合

#### 索引设计

为了快速查询，需要建立索引：
- **时间索引**：按时间排序，支持时间范围查询
- **级别索引**：按日志级别分组，快速筛选错误日志
- **来源索引**：按来源文件分组，快速定位特定服务

#### 查询语言

本项目实现了一个简单的查询 DSL：
```
level:error source:app.log after:2024-01-01
```

生产级系统通常支持更复杂的查询：
- Elasticsearch: Lucene 查询语法
- Splunk: SPL (Search Processing Language)
- KQL: Kusto Query Language

### 5. 网络传输

#### TCP 传输

- **可靠传输**：保证数据不丢失
- **面向连接**：需要建立连接
- **适合**：重要日志，需要保证送达

#### UDP 传输

- **无连接**：不需要建立连接
- **高性能**：没有连接开销
- **可能丢包**：不适合重要日志
- **适合**：高频日志，允许少量丢失

#### 文件输出

- **轮转**：按大小或时间轮转日志文件
- **压缩**：旧日志文件可以压缩
- **清理**：自动清理过期日志

## 实现细节

### 并发模型

使用 Go 的 goroutine 和 channel 实现并发：
- Collector 在独立 goroutine 中读取日志
- Tailer 在独立 goroutine 中监控文件
- TCP/UDP 在独立 goroutine 中接收连接
- Parser 和 Filter 在主 goroutine 中处理
- Channel 提供缓冲和同步

### 内存管理

- 使用 `sync.RWMutex` 保护共享数据
- 使用索引避免全表扫描
- 限制缓冲区大小防止内存溢出
- 正则表达式预编译避免重复编译

### 错误处理

- 解析失败的日志行降级为 UNKNOWN 级别
- 文件打开失败记录错误但不中断
- 空行自动跳过
- 网络断开记录错误，继续接受其他连接
- 过滤器错误跳过无效过滤器，记录警告

## 与其他系统的对比

| 特性 | 本项目 | ELK Stack | Fluentd |
|------|--------|-----------|---------|
| 语言 | Go | Java/Elasticsearch | Ruby/C |
| 存储 | 内存 | Elasticsearch | 可插拔 |
| 查询 | 简单 DSL | Lucene | 标签过滤 |
| 规模 | 单机学习 | 生产级 | 生产级 |
| 复杂度 | 低 | 高 | 中 |
| 网络 | TCP/UDP | HTTP | 多种协议 |
| 过滤 | 级别/关键词/正则 | 查询过滤 | 标签过滤 |

## 下一步学习

1. **添加持久化**：将日志写入文件或数据库
2. **Kafka 集成**：支持 Kafka 消息队列
3. **分布式架构**：多节点日志聚合
4. **日志轮转**：自动清理旧日志
5. **告警规则**：基于日志内容触发告警
6. **Web UI**：添加 Web 界面进行查询
7. **指标收集**：从日志中提取指标

## 参考资源

- [The Log: What every software engineer should know](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying)
- [Structured Logging](https://www.dataset.com/blog/the-10-commandments-of-logging/)
- [Logfmt](https://brandur.org/logfmt)
- [Go Concurrency Patterns](https://go.dev/blog/pipelines)
- [Regular Expressions in Go](https://pkg.go.dev/regexp)
