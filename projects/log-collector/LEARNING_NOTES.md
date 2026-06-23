# Log Collector - 学习笔记

## 项目概述

实现一个分布式日志收集系统，掌握日志架构、日志解析和日志聚合的核心概念。

## 学习目标

1. 理解日志架构
2. 掌握日志解析
3. 学会日志聚合

## 核心概念

### 1. 日志架构

日志系统的核心循环：日志产生 -> 采集 -> 传输 -> 存储 -> 查询

#### 日志采集

日志采集是日志系统的入口。常见的采集方式：
- **文件采集**：监听日志文件，读取新增内容
- **Syslog**：通过 syslog 协议接收日志
- **Agent**：在每个节点部署日志 Agent
- **SDK**：应用内嵌日志 SDK

本项目实现了文件采集，支持从文件和 stdin 读取日志。

#### 日志传输

日志传输需要考虑：
- **可靠性**：不丢失日志
- **顺序性**：保持日志顺序
- **缓冲**：生产者和消费者速度不匹配时的缓冲

本项目使用 Go channel 作为传输通道，提供了内置的缓冲机制。

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

#### 解析策略

本项目实现了自动检测格式的策略：
1. 尝试 JSON 解析
2. 尝试 Logfmt 解析
3. 尝试 Common 格式解析
4. 兜底：整行作为消息

### 3. 日志聚合

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

## 实现细节

### 并发模型

使用 Go 的 goroutine 和 channel 实现并发：
- Collector 在独立 goroutine 中读取日志
- Parser 在主 goroutine 中处理
- Channel 提供缓冲和同步

### 内存管理

- 使用 `sync.RWMutex` 保护共享数据
- 使用索引避免全表扫描
- 限制缓冲区大小防止内存溢出

### 错误处理

- 解析失败的日志行降级为 UNKNOWN 级别
- 文件打开失败记录错误但不中断
- 空行自动跳过

## 与其他系统的对比

| 特性 | 本项目 | ELK Stack | Fluentd |
|------|--------|-----------|---------|
| 语言 | Go | Java/Elasticsearch | Ruby/C |
| 存储 | 内存 | Elasticsearch | 可插拔 |
| 查询 | 简单 DSL | Lucene | 标签过滤 |
| 规模 | 单机学习 | 生产级 | 生产级 |
| 复杂度 | 低 | 高 | 中 |

## 下一步学习

1. **添加持久化**：将日志写入文件或数据库
2. **网络传输**：支持 TCP/UDP 接收日志
3. **分布式架构**：多节点日志聚合
4. **日志轮转**：自动清理旧日志
5. **告警规则**：基于日志内容触发告警

## 参考资源

- [The Log: What every software engineer should know](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying)
- [Structured Logging](https://www.dataset.com/blog/the-10-commandments-of-logging/)
- [Logfmt](https://brandur.org/logfmt)
