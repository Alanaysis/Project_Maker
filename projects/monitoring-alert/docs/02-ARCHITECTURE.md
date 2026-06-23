# 02 - 项目架构设计

## 1. 系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      Monitoring Alert System                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Collector   │  │   Storage    │  │    Alert     │         │
│  │   Manager     │  │    Layer     │  │    Engine    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                   │
│         v                 v                 v                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  System      │  │  Memory     │  │  Rule        │         │
│  │  Collector   │  │  TSDB       │  │  Evaluator   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Alert Manager                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│  │
│  │  │   Log    │  │ Webhook  │  │  Email   │  │  Slack   ││  │
│  │  │ Notifier │  │ Notifier │  │ Notifier │  │ Notifier ││  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Metric    │ -> │  Collector  │ -> │   Storage   │ -> │    Alert    │
│   Source    │    │   Manager   │    │     DB      │    │   Engine    │
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                │
                                                                v
                                                         ┌─────────────┐
                                                         │  Notifier   │
                                                         └─────────────┘
```

## 2. 核心组件设计

### 2.1 指标模型 (Metric)

```go
type Metric struct {
    Name      string            // 指标名称
    Type      MetricType        // 指标类型 (Counter/Gauge/Histogram)
    Labels    map[string]string // 标签
    Value     float64           // 当前值
    Timestamp time.Time         // 时间戳
    Help      string            // 帮助说明
    Unit      string            // 单位
}
```

### 2.2 时序数据模型 (TimeSeries)

```go
type TimeSeries struct {
    Metric  string                // 指标名称
    Labels  map[string]string     // 标签
    Points  []TimeSeriesPoint     // 数据点序列
}

type TimeSeriesPoint struct {
    Timestamp time.Time // 时间戳
    Value     float64   // 值
}
```

### 2.3 告警规则模型 (AlertRule)

```go
type AlertRule struct {
    ID          string            // 规则 ID
    Name        string            // 规则名称
    Expr        string            // 表达式
    Severity    AlertSeverity     // 严重程度
    Labels      map[string]string // 标签
    Annotations map[string]string // 注解
    For         time.Duration     // 持续时间
    Enabled     bool              // 是否启用
}
```

### 2.4 告警模型 (Alert)

```go
type Alert struct {
    ID        string            // 告警 ID
    RuleID    string            // 规则 ID
    RuleName  string            // 规则名称
    Labels    map[string]string // 标签
    Value     float64           // 触发值
    Threshold float64           // 阈值
    Severity  AlertSeverity     // 严重程度
    Status    AlertStatus       // 告警状态
    StartsAt  time.Time         // 开始时间
    EndsAt    *time.Time        // 结束时间
}
```

## 3. 模块设计

### 3.1 Collector 模块

#### 接口定义

```go
type Collector interface {
    Name() string
    Start(ctx context.Context) error
    Stop() error
    Collect() ([]*Metric, error)
}
```

#### 实现类

- **SystemCollector**：系统指标采集器
  - CPU 使用率
  - 内存使用率
  - 磁盘使用率
  - 网络流量

- **CustomCollector**：自定义采集器
  - 用户自定义采集函数
  - 灵活的扩展机制

#### CollectorManager

```go
type CollectorManager struct {
    collectors map[string]Collector
    running    bool
    ctx        context.Context
    cancel     context.CancelFunc
}
```

功能：
- 注册/注销采集器
- 启动/停止所有采集器
- 统一采集所有指标

### 3.2 Storage 模块

#### 接口定义

```go
type TimeSeriesDB interface {
    Write(metric *Metric) error
    Read(metric string, labels map[string]string, start, end time.Time) (*TimeSeries, error)
    Query(query string) ([]*TimeSeries, error)
    Delete(metric string, labels map[string]string) error
    List() []string
}
```

#### MemoryTSDB 实现

```go
type MemoryTSDB struct {
    series    map[string]*TimeSeries
    index     map[string][]string
    retention time.Duration
}
```

特性：
- 基于内存的存储
- 支持标签索引
- 自动数据清理
- 线程安全

#### QueryEngine

```go
type QueryEngine struct {
    db TimeSeriesDB
}
```

功能：
- 简单查询
- 聚合查询 (avg, sum, min, max, count)

### 3.3 Alert 模块

#### Condition 解析

```go
type Condition struct {
    Metric    string
    Operator  Operator
    Threshold float64
    Duration  time.Duration
}
```

支持的操作符：
- `>` 大于
- `>=` 大于等于
- `<` 小于
- `<=` 小于等于
- `==` 等于
- `!=` 不等于

#### RuleEvaluator

```go
type RuleEvaluator struct {
    rules   map[string]*AlertRule
    condMap map[string]*Condition
    db      TimeSeriesDB
    alerts  map[string]*Alert
}
```

功能：
- 添加/移除规则
- 评估所有规则
- 管理告警状态

#### AlertManager

```go
type AlertManager struct {
    evaluator  *RuleEvaluator
    notifiers  []Notifier
    history    []*Alert
    maxHistory int
}
```

功能：
- 检查并发送通知
- 管理告警历史
- 支持多通知器

### 3.4 Notifier 模块

#### 接口定义

```go
type Notifier interface {
    Name() string
    Notify(alert *Alert) error
}
```

#### 实现类

- **LogNotifier**：日志通知器
- **WebhookNotifier**：Webhook 通知器
- **EmailNotifier**：邮件通知器
- **SlackNotifier**：Slack 通知器
- **MultiNotifier**：多通道通知器
- **ThrottledNotifier**：节流通知器

## 4. 并发模型

### 4.1 Goroutine 设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Goroutine                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Collector Manager                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │  System     │  │  Custom     │  │  ...        │ │   │
│  │  │  Collector  │  │  Collector  │  │             │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Alert Check Loop                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │  Evaluate   │  │  Notify     │  │  Cleanup    │ │   │
│  │  │  Rules      │  │  Alerts     │  │  History    │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 同步机制

- **sync.RWMutex**：保护共享数据结构
- **context.Context**：控制 goroutine 生命周期
- **channel**：goroutine 间通信

## 5. 错误处理

### 5.1 错误类型

- **采集错误**：采集器启动失败、采集超时
- **存储错误**：写入失败、查询失败
- **规则错误**：表达式解析错误、评估错误
- **通知错误**：发送失败、超时

### 5.2 错误处理策略

- **重试机制**：对可恢复的错误进行重试
- **降级处理**：在部分组件失败时继续运行
- **错误日志**：记录所有错误用于排查
- **告警通知**：对关键错误发送告警

## 6. 性能优化

### 6.1 数据结构优化

- 使用 map 实现 O(1) 查找
- 使用 slice 实现高效遍历
- 使用 sync.RWMutex 实现读写分离

### 6.2 内存优化

- 定期清理过期数据
- 限制历史数据大小
- 使用指针减少拷贝

### 6.3 并发优化

- 使用 goroutine 并行处理
- 使用 channel 减少锁竞争
- 使用 context 控制超时

## 7. 测试策略

### 7.1 测试层次

- **单元测试**：测试单个函数和方法
- **集成测试**：测试模块间交互
- **端到端测试**：测试完整流程

### 7.2 测试覆盖

- 指标模型测试
- 采集器测试
- 存储测试
- 告警引擎测试
- 通知器测试

### 7.3 测试工具

- Go testing 包
- testify 断言库
- 竞态检测 (-race)

## 8. 扩展性设计

### 8.1 采集器扩展

实现 Collector 接口即可添加新的采集器：

```go
type CustomCollector struct {
    // 自定义字段
}

func (c *CustomCollector) Collect() ([]*Metric, error) {
    // 自定义采集逻辑
}
```

### 8.2 通知器扩展

实现 Notifier 接口即可添加新的通知器：

```go
type CustomNotifier struct {
    // 自定义字段
}

func (n *CustomNotifier) Notify(alert *Alert) error {
    // 自定义通知逻辑
}
```

### 8.3 存储扩展

实现 TimeSeriesDB 接口即可添加新的存储后端：

```go
type CustomTSDB struct {
    // 自定义字段
}

func (db *CustomTSDB) Write(metric *Metric) error {
    // 自定义写入逻辑
}
```
