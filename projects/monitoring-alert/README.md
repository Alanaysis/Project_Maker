# 监控告警系统

一个学习型的监控告警系统实现，帮助理解监控指标、时序数据存储和告警规则引擎。

## 项目概述

本项目实现了一个完整的监控告警系统，包含指标采集、时序数据存储、告警规则引擎和通知发送四个核心模块。通过这个项目，可以深入理解：

- 监控系统的核心概念和架构
- 时序数据的特点和存储方式
- 告警规则的评估逻辑
- 多通道通知的实现

## 学习目标

- **理解监控指标**：掌握 Counter、Gauge、Histogram 等指标类型
- **掌握时序数据**：学习时序数据的存储、查询和聚合
- **学会告警规则**：理解告警规则的定义、评估和状态管理

## 技术栈

- **主语言**：Go 1.22+
- **测试框架**：Go testing + testify
- **存储**：内存时序数据库
- **通知**：支持日志、Webhook、邮件、Slack 等多种通知方式

## 项目结构

```
monitoring-alert/
├── cmd/
│   └── server/
│       └── main.go                    # 服务器入口
├── configs/
│   └── config.toml                    # 配置文件
├── docs/
│   ├── 01-RESEARCH.md                 # 市场调研
│   ├── 02-ARCHITECTURE.md             # 架构设计
│   ├── 03-IMPLEMENTATION.md           # 实现细节
│   ├── 04-TESTING.md                  # 测试策略
│   └── 05-DEVELOPMENT.md             # 开发日志
├── internal/
│   ├── model/
│   │   ├── metric.go                  # 指标模型
│   │   └── alert.go                   # 告警模型
│   ├── collector/
│   │   └── collector.go               # 指标采集器
│   ├── storage/
│   │   └── tsdb.go                    # 时序数据库
│   ├── alert/
│   │   └── engine.go                  # 告警规则引擎
│   └── notifier/
│       └── notifier.go                # 通知器
├── test/
│   ├── model_test.go                  # 模型测试
│   ├── collector_test.go              # 采集器测试
│   ├── storage_test.go                # 存储测试
│   ├── alert_test.go                  # 告警引擎测试
│   └── notifier_test.go              # 通知器测试
├── go.mod                             # Go 模块定义
├── LEARNING_NOTES.md                  # 学习笔记
└── README.md                          # 项目文档
```

## 快速开始

### 环境要求

- Go 1.22 或更高版本
- Git

### 安装依赖

```bash
cd projects/monitoring-alert
go mod tidy
```

### 运行测试

```bash
# 运行所有测试
go test ./test/...

# 运行特定测试
go test ./test/... -run TestMetricCreation

# 运行测试并显示覆盖率
go test ./test/... -cover

# 运行竞态检测
go test ./test/... -race
```

### 启动系统

```bash
go run cmd/server/main.go
```

## 核心概念

### 1. 监控指标

监控系统使用三种基本指标类型：

- **Counter（计数器）**：只增不减，用于统计请求数、错误数等
- **Gauge（仪表盘）**：可增可减，用于表示温度、内存使用率等
- **Histogram（直方图）**：用于统计分布，如请求延迟分布

### 2. 时序数据

时序数据是按时间顺序记录的数据序列，具有以下特点：

- **时间戳**：每个数据点都有精确的时间戳
- **标签**：通过标签区分不同的数据源
- **高效存储**：使用压缩算法减少存储空间
- **快速查询**：支持按时间范围和标签查询

### 3. 告警规则

告警规则定义了何时触发告警：

```
metric_name operator threshold [for duration]
```

示例：
- `cpu_usage > 80`：CPU 使用率超过 80% 时触发
- `memory_usage >= 90 for 5m`：内存使用率持续 5 分钟超过 90% 时触发

支持的操作符：`>`, `>=`, `<`, `<=`, `==`, `!=`

### 4. 通知机制

系统支持多种通知方式：

- **日志通知**：输出到控制台
- **Webhook 通知**：发送 HTTP 请求
- **邮件通知**：发送电子邮件
- **Slack 通知**：发送 Slack 消息
- **多通道通知**：同时发送到多个渠道
- **节流通知**：限制通知频率

## API 接口

### 指标采集

```go
// 创建采集器
collector := collector.NewSystemCollector(5 * time.Second)

// 启动采集
collector.Start(ctx)

// 手动采集
metrics, err := collector.Collect()
```

### 时序存储

```go
// 创建时序数据库
db := storage.NewMemoryTSDB(24 * time.Hour)

// 写入指标
db.Write(metric)

// 查询数据
ts, err := db.Read("cpu_usage", labels, start, end)

// 获取最新值
value, ok := db.GetLatest("cpu_usage", labels)
```

### 告警规则

```go
// 创建规则评估器
evaluator := alert.NewRuleEvaluator(db)

// 添加规则
rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
evaluator.AddRule(rule)

// 评估规则
alerts, err := evaluator.Evaluate()
```

### 通知发送

```go
// 创建通知器
logNotifier := notifier.NewLogNotifier(100)
webhookNotifier := notifier.NewWebhookNotifier("http://example.com/webhook", 100)

// 创建告警管理器
manager := alert.NewAlertManager(evaluator, 1000)
manager.AddNotifier(logNotifier)
manager.AddNotifier(webhookNotifier)

// 检查并发送通知
manager.CheckAndNotify()
```

## 配置说明

配置文件 `configs/config.toml` 示例：

```toml
[server]
port = 8080
host = "localhost"

[collector]
interval = "5s"
enabled = true

[storage]
retention = "24h"
cleanup_interval = "1m"

[alert]
evaluation_interval = "10s"
max_history = 1000

[notifier]
log_enabled = true
webhook_enabled = false
webhook_url = "http://localhost:8080/webhook"
```

## 学习路径

1. **第一阶段：理解指标**
   - 学习不同指标类型的含义
   - 理解标签的作用
   - 掌握指标的创建和更新

2. **第二阶段：时序存储**
   - 理解时序数据的特点
   - 学习数据压缩和索引
   - 掌握查询和聚合操作

3. **第三阶段：告警规则**
   - 学习规则表达式语法
   - 理解条件评估逻辑
   - 掌握告警状态管理

4. **第四阶段：通知机制**
   - 学习不同通知方式的实现
   - 理解通知节流策略
   - 掌握多通道通知的协调

5. **第五阶段：系统集成**
   - 将各模块整合成完整系统
   - 学习并发和错误处理
   - 优化性能和可靠性

## 参考资源

- [Prometheus 文档](https://prometheus.io/docs/)
- [时序数据库设计](https://www.timescale.com/blog/time-series-data-why-and-how-to-use-a-relational-database-instead-of-nosql-d0cd69fa0e59/)
- [告警最佳实践](https://prometheus.io/docs/practices/alerting/)
- [Go 时序数据库实现](https://github.com/prometheus/prometheus)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
