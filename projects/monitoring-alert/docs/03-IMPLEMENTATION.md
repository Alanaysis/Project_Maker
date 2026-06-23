# 03 - 实现细节

## 1. 项目结构

```
monitoring-alert/
├── cmd/
│   └── server/
│       └── main.go                    # 服务器入口
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
└── test/
    ├── model_test.go                  # 模型测试
    ├── collector_test.go              # 采集器测试
    ├── storage_test.go                # 存储测试
    ├── alert_test.go                  # 告警引擎测试
    └── notifier_test.go              # 通知器测试
```

## 2. 核心组件实现

### 2.1 指标模型 (model/metric.go)

#### Metric 结构体

```go
type Metric struct {
    mu        sync.RWMutex
    Name      string            `json:"name"`
    Type      MetricType        `json:"type"`
    Labels    map[string]string `json:"labels"`
    Value     float64           `json:"value"`
    Timestamp time.Time         `json:"timestamp"`
    Help      string            `json:"help"`
    Unit      string            `json:"unit"`
}
```

关键实现：
- 使用 `sync.RWMutex` 保证并发安全
- 使用 getter/setter 方法控制数据访问
- 支持链式调用设置标签和值

#### TimeSeries 结构体

```go
type TimeSeries struct {
    mu      sync.RWMutex
    Metric  string                `json:"metric"`
    Labels  map[string]string     `json:"labels"`
    Points  []TimeSeriesPoint     `json:"points"`
}
```

关键实现：
- 使用 slice 存储数据点
- 支持按时间范围查询
- 提供 Latest() 方法获取最新值

### 2.2 告警模型 (model/alert.go)

#### AlertRule 结构体

```go
type AlertRule struct {
    mu          sync.RWMutex
    ID          string            `json:"id"`
    Name        string            `json:"name"`
    Expr        string            `json:"expr"`
    Severity    AlertSeverity     `json:"severity"`
    Labels      map[string]string `json:"labels"`
    Annotations map[string]string `json:"annotations"`
    For         time.Duration     `json:"for"`
    Enabled     bool              `json:"enabled"`
}
```

#### Alert 结构体

```go
type Alert struct {
    mu        sync.RWMutex
    ID        string            `json:"id"`
    RuleID    string            `json:"rule_id"`
    RuleName  string            `json:"rule_name"`
    Labels    map[string]string `json:"labels"`
    Value     float64           `json:"value"`
    Threshold float64           `json:"threshold"`
    Severity  AlertSeverity     `json:"severity"`
    Status    AlertStatus       `json:"status"`
    StartsAt  time.Time         `json:"starts_at"`
    EndsAt    *time.Time        `json:"ends_at,omitempty"`
    UpdatedAt time.Time         `json:"updated_at"`
}
```

关键实现：
- 状态机管理：Pending -> Firing -> Resolved
- 使用 `sync.RWMutex` 保证并发安全
- 自动设置时间戳

### 2.3 指标采集器 (collector/collector.go)

#### Collector 接口

```go
type Collector interface {
    Name() string
    Start(ctx context.Context) error
    Stop() error
    Collect() ([]*Metric, error)
}
```

#### SystemCollector 实现

```go
type SystemCollector struct {
    mu       sync.RWMutex
    name     string
    interval time.Duration
    metrics  map[string]*Metric
    stopCh   chan struct{}
    running  bool
}
```

关键实现：
- 使用 ticker 实现定时采集
- 使用 channel 实现优雅停止
- 使用 map 缓存最新指标

#### CollectorManager 实现

```go
type CollectorManager struct {
    mu         sync.RWMutex
    collectors map[string]Collector
    running    bool
    ctx        context.Context
    cancel     context.CancelFunc
}
```

关键实现：
- 支持注册/注销采集器
- 支持启动/停止所有采集器
- 使用 context 控制生命周期

### 2.4 时序数据库 (storage/tsdb.go)

#### TimeSeriesDB 接口

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
    mu        sync.RWMutex
    series    map[string]*TimeSeries
    index     map[string][]string
    retention time.Duration
}
```

关键实现：
- 使用 map 存储时序数据
- 使用索引加速查询
- 支持数据保留策略
- 自动清理过期数据

#### 数据键生成

```go
func generateKey(metric string, labels map[string]string) string {
    key := metric
    if len(labels) > 0 {
        keys := make([]string, 0, len(labels))
        for k := range labels {
            keys = append(keys, k)
        }
        sort.Strings(keys)
        for _, k := range keys {
            key += fmt.Sprintf(";%s=%s", k, labels[k])
        }
    }
    return key
}
```

关键实现：
- 标签按字母顺序排序
- 使用分号分隔标签
- 保证相同标签生成相同键

#### QueryEngine 实现

```go
type QueryEngine struct {
    db TimeSeriesDB
}
```

功能：
- SimpleQuery：简单时间范围查询
- AggregateQuery：聚合查询（avg, sum, min, max, count）

### 2.5 告警规则引擎 (alert/engine.go)

#### Condition 解析

```go
func ParseCondition(expr string) (*Condition, error) {
    // 格式: metric_name operator threshold [for duration]
    parts := strings.Fields(expr)
    // ... 解析逻辑
}
```

关键实现：
- 支持多种操作符：>, >=, <, <=, ==, !=
- 支持可选的持续时间
- 详细的错误信息

#### RuleEvaluator 实现

```go
type RuleEvaluator struct {
    mu       sync.RWMutex
    rules    map[string]*AlertRule
    condMap  map[string]*Condition
    db       TimeSeriesDB
    alerts   map[string]*Alert
}
```

关键实现：
- 使用 map 存储规则和条件
- 支持启用/禁用规则
- 支持告警状态管理

#### 规则评估

```go
func (e *RuleEvaluator) evaluateRule(rule *AlertRule, cond *Condition) (*Alert, error) {
    // 获取指标的最新值
    value, ok := e.db.GetLatest(cond.Metric, cond.Labels)
    
    // 评估条件
    if !cond.Evaluate(value) {
        return nil, nil
    }
    
    // 创建新告警
    alert := NewAlert(rule.ID, rule.Name, rule.Severity, rule.Labels)
    alert.SetValue(value, cond.Threshold)
    alert.SetStatus(AlertStatusFiring)
    return alert, nil
}
```

#### AlertManager 实现

```go
type AlertManager struct {
    mu         sync.RWMutex
    evaluator  *RuleEvaluator
    notifiers  []Notifier
    history    []*Alert
    maxHistory int
}
```

关键实现：
- 支持多通知器
- 支持告警历史管理
- 支持历史大小限制

### 2.6 通知器 (notifier/notifier.go)

#### Notifier 接口

```go
type Notifier interface {
    Name() string
    Notify(alert *Alert) error
}
```

#### LogNotifier 实现

```go
type LogNotifier struct {
    mu      sync.RWMutex
    name    string
    alerts  []*Alert
    maxSize int
}
```

关键实现：
- 输出到控制台
- 支持历史记录
- 支持大小限制

#### WebhookNotifier 实现

```go
type WebhookNotifier struct {
    mu       sync.RWMutex
    name     string
    url      string
    alerts   []*Alert
    maxSize  int
}
```

关键实现：
- 发送 HTTP 请求
- 支持自定义 URL
- 支持历史记录

#### MultiNotifier 实现

```go
type MultiNotifier struct {
    mu        sync.RWMutex
    name      string
    notifiers []Notifier
}
```

关键实现：
- 同时发送到多个渠道
- 支持错误聚合

#### ThrottledNotifier 实现

```go
type ThrottledNotifier struct {
    mu           sync.RWMutex
    name         string
    notifier     Notifier
    interval     time.Duration
    lastNotify   map[string]time.Time
}
```

关键实现：
- 限制通知频率
- 基于规则和严重程度的节流
- 使用 map 记录上次通知时间

## 3. 并发模型

### 3.1 同步机制

所有共享数据结构都使用 `sync.RWMutex` 保护：

```go
type Metric struct {
    mu sync.RWMutex
    // ... 其他字段
}

func (m *Metric) GetValue() float64 {
    m.mu.RLock()
    defer m.mu.RUnlock()
    return m.Value
}

func (m *Metric) SetValue(value float64) {
    m.mu.Lock()
    defer m.mu.Unlock()
    m.Value = value
}
```

### 3.2 Goroutine 设计

- 采集器 goroutine：定时采集指标
- 告警检查 goroutine：定时评估规则
- 数据清理 goroutine：定时清理过期数据

### 3.3 Channel 通信

```go
type SystemCollector struct {
    stopCh chan struct{}
}

func (c *SystemCollector) Stop() error {
    close(c.stopCh)
    return nil
}
```

## 4. 错误处理

### 4.1 错误类型

- 采集器启动失败
- 规则表达式解析错误
- 指标未找到
- 通知发送失败

### 4.2 错误处理策略

```go
// 采集器错误处理
metrics, err := c.Collect()
if err != nil {
    // 记录错误，继续运行
    fmt.Printf("Failed to collect metrics: %v\n", err)
    continue
}

// 规则解析错误处理
cond, err := ParseCondition(expr)
if err != nil {
    return fmt.Errorf("failed to parse rule expression: %w", err)
}

// 通知错误处理
for _, n := range notifiers {
    if err := n.Notify(alert); err != nil {
        // 记录错误，继续发送其他通知
        fmt.Printf("Failed to notify via %s: %v\n", n.Name(), err)
    }
}
```

## 5. 性能优化

### 5.1 数据结构优化

- 使用 map 实现 O(1) 查找
- 使用 slice 实现高效遍历
- 使用指针减少拷贝

### 5.2 内存优化

- 定期清理过期数据
- 限制历史数据大小
- 使用数据压缩

### 5.3 并发优化

- 使用 RWMutex 实现读写分离
- 使用 goroutine 并行处理
- 使用 channel 减少锁竞争

## 6. 测试策略

### 6.1 单元测试

```go
func TestMetricCreation(t *testing.T) {
    m := NewMetric("cpu_usage", MetricTypeGauge, "CPU usage")
    assert.NotNil(t, m)
    assert.Equal(t, "cpu_usage", m.Name)
}
```

### 6.2 并发测试

```go
func TestMetricConcurrency(t *testing.T) {
    m := NewMetric("test", MetricTypeGauge, "test")
    
    done := make(chan bool)
    for i := 0; i < 100; i++ {
        go func(val float64) {
            m.SetValue(val)
            m.GetValue()
            done <- true
        }(float64(i))
    }
    
    for i := 0; i < 100; i++ {
        <-done
    }
}
```

### 6.3 集成测试

```go
func TestRuleEvaluatorEvaluate(t *testing.T) {
    db := NewMemoryTSDB(24 * time.Hour)
    evaluator := NewRuleEvaluator(db)
    
    // 添加规则
    rule := NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", SeverityWarning)
    evaluator.AddRule(rule)
    
    // 写入触发告警的数据
    m := NewMetric("cpu_usage", MetricTypeGauge, "CPU usage")
    m.SetValue(85.0)
    db.Write(m)
    
    // 评估规则
    alerts, err := evaluator.Evaluate()
    assert.NoError(t, err)
    assert.Equal(t, 1, len(alerts))
}
```
