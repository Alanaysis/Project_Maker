# 04 - 测试策略

## 1. 测试层次

### 1.1 单元测试

单元测试针对单个函数或方法进行测试，验证其正确性。

```go
func TestMetricCreation(t *testing.T) {
    m := NewMetric("cpu_usage", MetricTypeGauge, "CPU usage")
    assert.NotNil(t, m)
    assert.Equal(t, "cpu_usage", m.Name)
    assert.Equal(t, MetricTypeGauge, m.Type)
}
```

### 1.2 集成测试

集成测试验证多个模块之间的交互。

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

### 1.3 并发测试

并发测试验证代码在并发环境下的安全性。

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

## 2. 测试覆盖

### 2.1 模型测试 (model_test.go)

| 测试函数 | 描述 | 预期结果 |
|----------|------|----------|
| TestMetricCreation | 测试指标创建 | 创建成功 |
| TestMetricTypeString | 测试指标类型字符串 | 返回正确类型 |
| TestMetricSetValue | 测试设置指标值 | 值正确设置 |
| TestMetricSetLabels | 测试设置标签 | 标签正确设置 |
| TestMetricString | 测试指标字符串表示 | 格式正确 |
| TestTimeSeriesCreation | 测试时序数据创建 | 创建成功 |
| TestTimeSeriesAddPoint | 测试添加数据点 | 数据点正确添加 |
| TestTimeSeriesGetPointsInRange | 测试按范围查询 | 返回正确数据 |
| TestTimeSeriesLatest | 测试获取最新值 | 返回最新数据 |
| TestAlertCreation | 测试告警创建 | 创建成功 |
| TestAlertSeverityString | 测试告警级别字符串 | 返回正确级别 |
| TestAlertStatusTransitions | 测试告警状态转换 | 状态正确转换 |
| TestAlertSetValue | 测试设置告警值 | 值正确设置 |
| TestAlertString | 测试告警字符串表示 | 格式正确 |
| TestAlertRuleCreation | 测试告警规则创建 | 创建成功 |
| TestAlertRuleSetFor | 测试设置持续时间 | 时间正确设置 |
| TestAlertRuleSetEnabled | 测试设置启用状态 | 状态正确设置 |
| TestMetricConcurrency | 测试指标并发访问 | 无竞态条件 |
| TestTimeSeriesConcurrency | 测试时序数据并发访问 | 无竞态条件 |

### 2.2 采集器测试 (collector_test.go)

| 测试函数 | 描述 | 预期结果 |
|----------|------|----------|
| TestSystemCollectorCreation | 测试系统采集器创建 | 创建成功 |
| TestSystemCollectorCollect | 测试系统采集器采集 | 返回正确指标 |
| TestSystemCollectorStartStop | 测试系统采集器启停 | 启停正常 |
| TestCustomCollector | 测试自定义采集器 | 采集正常 |
| TestCustomCollectorStartStop | 测试自定义采集器启停 | 启停正常 |
| TestCollectorManager | 测试采集器管理器 | 管理正常 |
| TestCollectorManagerStartStop | 测试采集器管理器启停 | 启停正常 |
| TestCollectorManagerCollectAll | 测试采集所有指标 | 采集正常 |
| TestCollectorManagerUnregister | 测试注销采集器 | 注销成功 |

### 2.3 存储测试 (storage_test.go)

| 测试函数 | 描述 | 预期结果 |
|----------|------|----------|
| TestMemoryTSDBCreation | 测试时序数据库创建 | 创建成功 |
| TestMemoryTSDBWrite | 测试写入数据 | 写入成功 |
| TestMemoryTSDBWriteMultiple | 测试多次写入 | 写入成功 |
| TestMemoryTSDBWriteDifferentMetrics | 测试写入不同指标 | 写入成功 |
| TestMemoryTSDBWriteDifferentLabels | 测试写入不同标签 | 写入成功 |
| TestMemoryTSDBRead | 测试读取数据 | 读取成功 |
| TestMemoryTSDBReadNotFound | 测试读取不存在的数据 | 返回错误 |
| TestMemoryTSDBGetLatest | 测试获取最新值 | 返回正确值 |
| TestMemoryTSDBGetLatestNotFound | 测试获取不存在的最新值 | 返回 false |
| TestMemoryTSDBDelete | 测试删除数据 | 删除成功 |
| TestMemoryTSDBDeleteNotFound | 测试删除不存在的数据 | 返回错误 |
| TestMemoryTSDBList | 测试列出所有指标 | 列表正确 |
| TestMemoryTSDBQuery | 测试查询指标 | 查询成功 |
| TestMemoryTSDBQueryAll | 测试查询所有指标 | 查询成功 |
| TestQueryEngineSimpleQuery | 测试简单查询 | 查询成功 |
| TestQueryEngineAggregateQuery | 测试聚合查询 | 聚合正确 |
| TestQueryEngineAggregateQueryUnknownAggregation | 测试未知聚合 | 返回错误 |
| TestMemoryTSDBConcurrency | 测试并发访问 | 无竞态条件 |

### 2.4 告警引擎测试 (alert_test.go)

| 测试函数 | 描述 | 预期结果 |
|----------|------|----------|
| TestConditionEvaluate | 测试条件评估 | 评估正确 |
| TestParseCondition | 测试条件解析 | 解析成功 |
| TestParseConditionInvalid | 测试无效条件解析 | 返回错误 |
| TestRuleEvaluatorCreation | 测试规则评估器创建 | 创建成功 |
| TestRuleEvaluatorAddRule | 测试添加规则 | 添加成功 |
| TestRuleEvaluatorAddRuleInvalidExpr | 测试添加无效规则 | 返回错误 |
| TestRuleEvaluatorRemoveRule | 测试移除规则 | 移除成功 |
| TestRuleEvaluatorGetRule | 测试获取规则 | 获取成功 |
| TestRuleEvaluatorEvaluate | 测试评估规则 | 触发告警 |
| TestRuleEvaluatorEvaluateNoTrigger | 测试不触发告警 | 无告警 |
| TestRuleEvaluatorEvaluateDisabledRule | 测试禁用规则 | 无告警 |
| TestRuleEvaluatorGetActiveAlerts | 测试获取活跃告警 | 返回正确告警 |
| TestRuleEvaluatorResolveAlert | 测试解决告警 | 解决成功 |
| TestRuleEvaluatorResolveAlertNotFound | 测试解决不存在的告警 | 返回错误 |
| TestRuleEvaluatorCleanupResolvedAlerts | 测试清理已解决告警 | 清理成功 |
| TestAlertManagerCreation | 测试告警管理器创建 | 创建成功 |
| TestAlertManagerCheckAndNotify | 测试检查并通知 | 通知成功 |

### 2.5 通知器测试 (notifier_test.go)

| 测试函数 | 描述 | 预期结果 |
|----------|------|----------|
| TestLogNotifierCreation | 测试日志通知器创建 | 创建成功 |
| TestLogNotifierNotify | 测试日志通知 | 通知成功 |
| TestLogNotifierMaxSize | 测试日志通知器大小限制 | 限制生效 |
| TestWebhookNotifierCreation | 测试 Webhook 通知器创建 | 创建成功 |
| TestWebhookNotifierNotify | 测试 Webhook 通知 | 通知成功 |
| TestEmailNotifierCreation | 测试邮件通知器创建 | 创建成功 |
| TestEmailNotifierNotify | 测试邮件通知 | 通知成功 |
| TestSlackNotifierCreation | 测试 Slack 通知器创建 | 创建成功 |
| TestSlackNotifierNotify | 测试 Slack 通知 | 通知成功 |
| TestMultiNotifierCreation | 测试多通道通知器创建 | 创建成功 |
| TestMultiNotifierNotify | 测试多通道通知 | 通知成功 |
| TestThrottledNotifierCreation | 测试节流通知器创建 | 创建成功 |
| TestThrottledNotifierNotify | 测试节流通知 | 节流生效 |

## 3. 测试工具

### 3.1 Go testing 包

```bash
# 运行所有测试
go test ./test/...

# 运行特定测试
go test ./test/... -run TestMetricCreation

# 运行测试并显示覆盖率
go test ./test/... -cover

# 运行竞态检测
go test ./test/... -race

# 运行详细测试
go test ./test/... -v
```

### 3.2 testify 断言库

```go
import "github.com/stretchr/testify/assert"

// 相等断言
assert.Equal(t, expected, actual)

// 非空断言
assert.NotNil(t, obj)

// 包含断言
assert.Contains(t, str, substr)

// 错误断言
assert.NoError(t, err)
assert.Error(t, err)

// 布尔断言
assert.True(t, value)
assert.False(t, value)

// 大小断言
assert.Greater(t, a, b)
assert.Less(t, a, b)
```

## 4. 测试用例详情

### 4.1 模型测试用例

#### TestMetricCreation
- 输入：指标名称、类型、帮助信息
- 预期：创建成功，字段正确

#### TestMetricSetValue
- 输入：指标值 42.5
- 预期：值正确设置，时间戳更新

#### TestTimeSeriesAddPoint
- 输入：3 个数据点
- 预期：数据点正确添加，顺序正确

#### TestAlertStatusTransitions
- 输入：Pending -> Firing -> Resolved
- 预期：状态正确转换，时间戳更新

### 4.2 采集器测试用例

#### TestSystemCollectorCollect
- 输入：无
- 预期：返回 5 个指标（CPU、内存、磁盘、网络入、网络出）

#### TestCollectorManagerCollectAll
- 输入：注册系统采集器
- 预期：返回所有采集器的指标

### 4.3 存储测试用例

#### TestMemoryTSDBWriteMultiple
- 输入：10 个相同指标的数据点
- 预期：1 个时序，10 个数据点

#### TestQueryEngineAggregateQuery
- 输入：10 个数据点，不同的聚合函数
- 预期：avg=45, sum=450, min=0, max=90, count=10

### 4.4 告警引擎测试用例

#### TestConditionEvaluate
- 输入：13 种不同的条件组合
- 预期：每种组合返回正确的布尔值

#### TestRuleEvaluatorEvaluate
- 输入：规则 cpu_usage > 80，数据 cpu_usage = 85
- 预期：触发告警

#### TestRuleEvaluatorEvaluateNoTrigger
- 输入：规则 cpu_usage > 80，数据 cpu_usage = 70
- 预期：不触发告警

### 4.5 通知器测试用例

#### TestLogNotifierNotify
- 输入：告警对象
- 预期：通知成功，历史记录增加

#### TestThrottledNotifierNotify
- 输入：两次相同告警，间隔小于节流时间
- 预期：只有第一次通知被发送

## 5. 性能测试

### 5.1 基准测试

```go
func BenchmarkMetricSetValue(b *testing.B) {
    m := NewMetric("test", MetricTypeGauge, "test")
    for i := 0; i < b.N; i++ {
        m.SetValue(float64(i))
    }
}

func BenchmarkTimeSeriesAddPoint(b *testing.B) {
    ts := NewTimeSeries("test", nil)
    now := time.Now()
    for i := 0; i < b.N; i++ {
        ts.AddPoint(now, float64(i))
    }
}
```

### 5.2 负载测试

- 测试大量指标写入
- 测试大量并发查询
- 测试大量规则评估

### 5.3 压力测试

- 测试内存使用情况
- 测试 CPU 使用情况
- 测试长时间运行稳定性

## 6. 测试环境

### 6.1 本地测试

```bash
# 运行所有测试
go test ./test/...

# 运行特定包的测试
go test ./test/... -run TestMetric

# 生成测试覆盖率报告
go test ./test/... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

### 6.2 CI/CD 集成

```yaml
# GitHub Actions 示例
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
        with:
          go-version: 1.22
      - run: go test ./test/... -race -cover
```

## 7. 测试最佳实践

### 7.1 命名规范

- 测试函数以 `Test` 开头
- 使用描述性的名称
- 使用 CamelCase 命名

### 7.2 测试隔离

- 每个测试独立运行
- 不依赖外部状态
- 使用 mock 或 stub

### 7.3 断言清晰

- 使用明确的断言
- 提供清晰的错误信息
- 测试边界条件

### 7.4 测试覆盖

- 追求高覆盖率
- 重点关注核心逻辑
- 测试错误路径
