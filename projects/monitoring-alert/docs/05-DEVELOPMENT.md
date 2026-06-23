# 05 - 开发日志

## 开发阶段

### 阶段一：项目初始化

**目标**：搭建项目基础结构

**完成工作**：
1. 创建项目目录结构
2. 初始化 Go 模块
3. 创建基础文档

**关键决策**：
- 使用标准 Go 项目布局 (`cmd/` + `internal/`)
- 使用 testify 作为测试框架
- 使用内存存储简化实现

**遇到的问题**：
- 问题：如何设计清晰的模块边界
- 解决：使用接口定义模块契约，实现松耦合

### 阶段二：模型设计

**目标**：设计核心数据模型

**完成工作**：
1. 设计 Metric 模型
2. 设计 TimeSeries 模型
3. 设计 Alert 和 AlertRule 模型
4. 实现并发安全的访问方法

**关键实现**：

```go
type Metric struct {
    mu        sync.RWMutex
    Name      string
    Type      MetricType
    Labels    map[string]string
    Value     float64
    Timestamp time.Time
}

func (m *Metric) SetValue(value float64) {
    m.mu.Lock()
    defer m.mu.Unlock()
    m.Value = value
    m.Timestamp = time.Now()
}
```

**遇到的问题**：
- 问题：如何保证并发安全
- 解决：使用 sync.RWMutex 保护共享数据

### 阶段三：采集器实现

**目标**：实现指标采集功能

**完成工作**：
1. 定义 Collector 接口
2. 实现 SystemCollector
3. 实现 CustomCollector
4. 实现 CollectorManager

**关键实现**：

```go
type Collector interface {
    Name() string
    Start(ctx context.Context) error
    Stop() error
    Collect() ([]*Metric, error)
}

type SystemCollector struct {
    mu       sync.RWMutex
    name     string
    interval time.Duration
    stopCh   chan struct{}
    running  bool
}
```

**遇到的问题**：
- 问题：如何优雅地停止采集器
- 解决：使用 channel 和 context 控制生命周期

### 阶段四：存储实现

**目标**：实现时序数据存储

**完成工作**：
1. 定义 TimeSeriesDB 接口
2. 实现 MemoryTSDB
3. 实现数据键生成算法
4. 实现数据清理机制
5. 实现 QueryEngine

**关键实现**：

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

**遇到的问题**：
- 问题：如何高效地生成数据键
- 解决：对标签按字母顺序排序，保证相同标签生成相同键

### 阶段五：告警引擎实现

**目标**：实现告警规则引擎

**完成工作**：
1. 实现条件解析器
2. 实现 RuleEvaluator
3. 实现 AlertManager
4. 实现告警状态管理

**关键实现**：

```go
func ParseCondition(expr string) (*Condition, error) {
    parts := strings.Fields(expr)
    if len(parts) < 3 {
        return nil, fmt.Errorf("invalid expression: %s", expr)
    }
    
    cond := &Condition{
        Metric: parts[0],
    }
    
    switch parts[1] {
    case ">":
        cond.Operator = OpGreaterThan
    case ">=":
        cond.Operator = OpGreaterThanOrEqual
    // ... 其他操作符
    }
    
    var threshold float64
    if _, err := fmt.Sscanf(parts[2], "%f", &threshold); err != nil {
        return nil, fmt.Errorf("invalid threshold: %s", parts[2])
    }
    cond.Threshold = threshold
    
    return cond, nil
}
```

**遇到的问题**：
- 问题：如何解析告警规则表达式
- 解决：使用字符串分割和类型转换实现简单解析器

### 阶段六：通知器实现

**目标**：实现多通道通知

**完成工作**：
1. 定义 Notifier 接口
2. 实现 LogNotifier
3. 实现 WebhookNotifier
4. 实现 EmailNotifier
5. 实现 SlackNotifier
6. 实现 MultiNotifier
7. 实现 ThrottledNotifier

**关键实现**：

```go
type ThrottledNotifier struct {
    mu           sync.RWMutex
    notifier     Notifier
    interval     time.Duration
    lastNotify   map[string]time.Time
}

func (n *ThrottledNotifier) Notify(alert *Alert) error {
    n.mu.Lock()
    defer n.mu.Unlock()
    
    key := fmt.Sprintf("%s:%s", alert.RuleID, alert.Severity)
    lastTime, exists := n.lastNotify[key]
    if exists && time.Since(lastTime) < n.interval {
        return nil // 节流
    }
    
    err := n.notifier.Notify(alert)
    if err == nil {
        n.lastNotify[key] = time.Now()
    }
    return err
}
```

**遇到的问题**：
- 问题：如何实现通知节流
- 解决：使用 map 记录上次通知时间，检查时间间隔

### 阶段七：系统集成

**目标**：整合所有模块

**完成工作**：
1. 创建服务器入口
2. 初始化所有组件
3. 实现主循环
4. 实现优雅关闭

**关键实现**：

```go
func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    // 初始化组件
    db := storage.NewMemoryTSDB(24 * time.Hour)
    collectorMgr := collector.NewCollectorManager()
    evaluator := alert.NewRuleEvaluator(db)
    alertMgr := alert.NewAlertManager(evaluator, 1000)
    
    // 启动采集器
    collectorMgr.Start(ctx)
    
    // 主循环
    go func() {
        ticker := time.NewTicker(10 * time.Second)
        defer ticker.Stop()
        
        for {
            select {
            case <-ctx.Done():
                return
            case <-ticker.C:
                metrics, _ := collectorMgr.CollectAll()
                for _, m := range metrics {
                    db.Write(m)
                }
                alertMgr.CheckAndNotify()
            }
        }
    }()
    
    // 等待信号
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
    <-sigCh
    
    cancel()
    collectorMgr.Stop()
}
```

**遇到的问题**：
- 问题：如何实现优雅关闭
- 解决：使用 context 和 signal 实现优雅关闭

## 技术难点

### 1. 并发控制

**问题**：多个 goroutine 同时访问共享数据

**解决**：
- 使用 sync.RWMutex 保护共享数据
- 使用 channel 进行 goroutine 间通信
- 使用 context 控制 goroutine 生命周期

### 2. 数据键生成

**问题**：如何高效地生成唯一的数据键

**解决**：
- 对标签按字母顺序排序
- 使用分号分隔标签
- 保证相同标签生成相同键

### 3. 告警状态管理

**问题**：如何管理告警的生命周期

**解决**：
- 使用状态机管理告警状态
- Pending -> Firing -> Resolved
- 使用 map 存储活跃告警

### 4. 通知节流

**问题**：如何避免告警风暴

**解决**：
- 使用 ThrottledNotifier 限制通知频率
- 基于规则和严重程度的节流
- 使用 map 记录上次通知时间

## 性能优化

### 1. 数据结构优化

- 使用 map 实现 O(1) 查找
- 使用 slice 实现高效遍历
- 使用指针减少拷贝

### 2. 内存优化

- 定期清理过期数据
- 限制历史数据大小
- 使用数据压缩

### 3. 并发优化

- 使用 RWMutex 实现读写分离
- 使用 goroutine 并行处理
- 使用 channel 减少锁竞争

## 未来改进

### 1. 功能扩展

- 支持更多指标类型
- 支持更复杂的查询语言
- 支持更多通知方式
- 支持告警分组和静默

### 2. 性能优化

- 实现数据持久化
- 实现分布式存储
- 实现查询优化
- 实现数据压缩

### 3. 可靠性提升

- 实现错误重试
- 实现降级处理
- 实现健康检查
- 实现监控告警

## 经验总结

### 1. 设计原则

- **接口先行**：先定义接口，再实现具体类
- **单一职责**：每个模块只负责一个功能
- **开闭原则**：对扩展开放，对修改关闭
- **依赖倒置**：依赖接口而不是具体实现

### 2. 开发流程

- **测试驱动**：先写测试，再写实现
- **小步迭代**：每次只实现一个小功能
- **持续重构**：不断优化代码结构
- **代码审查**：定期审查代码质量

### 3. 学习收获

- 理解了监控系统的核心概念
- 掌握了时序数据的存储和查询
- 学会了告警规则的设计和实现
- 了解了通知机制的实现方式
