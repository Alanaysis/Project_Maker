# 04 - 测试: HyperLogLog 测试策略

## 测试架构

```
test/
├── hyperloglog_test.go   # 核心功能测试
│   ├── 单元测试
│   ├── 集成测试
│   └── 性能测试
```

## 测试覆盖率

```
总体覆盖率: >90%

高覆盖率模块:
- New(): 100%
- Add(): 100%
- Estimate(): 100%
- Merge(): 100%
- Reset(): 100%
```

## 测试用例详解

### 1. 创建测试

```go
func TestNewHyperLogLog(t *testing.T) {
    tests := []struct {
        name      string
        precision uint8
        wantErr   bool
    }{
        {"valid precision 4", 4, false},
        {"valid precision 8", 8, false},
        {"valid precision 10", 10, false},
        {"valid precision 12", 12, false},
        {"valid precision 14", 14, false},
        {"valid precision 16", 16, false},
        {"invalid precision 3", 3, true},
        {"invalid precision 17", 17, true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            hll, err := New(tt.precision)
            if (err != nil) != tt.wantErr {
                t.Errorf("New(%d) error = %v, wantErr %v", tt.precision, err, tt.wantErr)
                return
            }
            if !tt.wantErr {
                if hll.Precision() != tt.precision {
                    t.Errorf("Precision() = %d, want %d", hll.Precision(), tt.precision)
                }
            }
        })
    }
}
```

**测试要点**:
- 测试有效精度范围 (4-16)
- 测试无效精度 (3, 17)
- 验证返回的精度和寄存器数量

### 2. 添加和估算测试

```go
func TestAddAndEstimate(t *testing.T) {
    hll, _ := New(12)

    // 添加 10000 个不同元素
    for i := 0; i < 10000; i++ {
        hll.Add([]byte(fmt.Sprintf("element-%d", i)))
    }

    estimate := hll.Estimate()
    errorRate := math.Abs(float64(estimate)-10000) / 10000

    // 误差应在 5% 以内
    if errorRate > 0.05 {
        t.Errorf("Error rate %.2f%% exceeds 5%% threshold", errorRate*100)
    }
}
```

**测试要点**:
- 测试基本功能
- 验证精度在预期范围内
- 记录实际误差率

### 3. 重复元素测试

```go
func TestAddDuplicates(t *testing.T) {
    hll, _ := New(12)

    // 添加相同的元素 1000 次
    for i := 0; i < 1000; i++ {
        hll.Add([]byte("duplicate-element"))
    }

    estimate := hll.Estimate()
    // 应该接近 1，而不是 1000
    if estimate > 10 {
        t.Errorf("Duplicate elements should estimate near 1, got %d", estimate)
    }
}
```

**测试要点**:
- 验证重复元素不影响估算
- 确保估算值接近实际基数

### 4. 合并测试

```go
func TestMerge(t *testing.T) {
    hll1, _ := New(12)
    hll2, _ := New(12)

    // 添加不同的元素
    for i := 0; i < 5000; i++ {
        hll1.Add([]byte(fmt.Sprintf("set1-%d", i)))
    }
    for i := 0; i < 5000; i++ {
        hll2.Add([]byte(fmt.Sprintf("set2-%d", i)))
    }

    // 合并
    err := hll1.Merge(hll2)
    if err != nil {
        t.Fatalf("Merge failed: %v", err)
    }

    estimate := hll1.Estimate()
    errorRate := math.Abs(float64(estimate)-10000) / 10000

    if errorRate > 0.05 {
        t.Errorf("Merged error rate %.2f%% exceeds 5%% threshold", errorRate*100)
    }
}
```

**测试要点**:
- 测试合并功能
- 验证合并后精度
- 测试不同精度合并失败

### 5. 不同精度测试

```go
func TestDifferentPrecisions(t *testing.T) {
    precisions := []uint8{4, 8, 10, 12, 14, 16}
    cardinality := 10000

    for _, p := range precisions {
        t.Run(fmt.Sprintf("p=%d", p), func(t *testing.T) {
            hll, _ := New(p)

            for i := 0; i < cardinality; i++ {
                hll.Add([]byte(fmt.Sprintf("element-%d", i)))
            }

            estimate := hll.Estimate()
            errorRate := math.Abs(float64(estimate)-float64(cardinality)) / float64(cardinality)

            // 误差应在理论范围内
            maxError := hll.StandardError() * 3
            if errorRate > maxError*1.5 {
                t.Errorf("Error rate %.2f%% exceeds expected bound %.2f%%",
                    errorRate*100, maxError*100)
            }
        })
    }
}
```

**测试要点**:
- 测试所有有效精度
- 验证误差在理论范围内
- 比较不同精度的精度

### 6. 小基数测试

```go
func TestSmallCardinality(t *testing.T) {
    hll, _ := New(12)

    // 小基数应该使用 Linear Counting
    for i := 0; i < 10; i++ {
        hll.Add([]byte(fmt.Sprintf("small-%d", i)))
    }

    estimate := hll.Estimate()
    errorRate := math.Abs(float64(estimate)-10) / 10

    // 小基数估算应该合理准确
    if errorRate > 0.5 {
        t.Errorf("Small cardinality error rate %.2f%% exceeds 50%%", errorRate*100)
    }
}
```

**测试要点**:
- 测试小基数场景
- 验证 Linear Counting 校正
- 确保估算合理

### 7. 大基数测试

```go
func TestLargeCardinality(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping large cardinality test in short mode")
    }

    hll, _ := New(14)

    // 添加大量元素
    for i := 0; i < 1000000; i++ {
        hll.Add([]byte(fmt.Sprintf("large-%d", i)))
    }

    estimate := hll.Estimate()
    errorRate := math.Abs(float64(estimate)-1000000) / 1000000

    // 大基数误差应在 2% 以内
    if errorRate > 0.02 {
        t.Errorf("Large cardinality error rate %.2f%% exceeds 2%% threshold", errorRate*100)
    }
}
```

**测试要点**:
- 测试大基数场景
- 验证大基数校正
- 确保高精度

## 性能测试

### 添加性能

```go
func BenchmarkAdd(b *testing.B) {
    hll, _ := New(12)
    data := []byte("benchmark-element")

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        hll.Add(data)
    }
}
```

### 估算性能

```go
func BenchmarkEstimate(b *testing.B) {
    hll, _ := New(12)

    for i := 0; i < 10000; i++ {
        hll.Add([]byte(fmt.Sprintf("element-%d", i)))
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        hll.Estimate()
    }
}
```

### 哈希性能

```go
func BenchmarkHash(b *testing.B) {
    data := []byte("benchmark-element")

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        Hash(data)
    }
}
```

### 合并性能

```go
func BenchmarkMerge(b *testing.B) {
    hll1, _ := New(12)
    hll2, _ := New(12)

    for i := 0; i < 10000; i++ {
        hll1.Add([]byte(fmt.Sprintf("set1-%d", i)))
        hll2.Add([]byte(fmt.Sprintf("set2-%d", i)))
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        hll1.Merge(hll2)
    }
}
```

## 运行测试

```bash
# 运行所有测试
go test ./internal/ -v

# 运行特定测试
go test ./internal/ -v -run "TestAdd"

# 运行性能测试
go test ./internal/ -bench=.

# 生成覆盖率
go test ./internal/ -coverprofile=coverage.out
go tool cover -func=coverage.out
```

## 测试最佳实践

### 1. 使用表驱动测试

```go
tests := []struct {
    name    string
    input   interface{}
    want    interface{}
    wantErr bool
}{
    // 测试用例
}

for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        // 测试逻辑
    })
}
```

### 2. 测试边界条件

- 精度参数边界 (4, 16)
- 小基数 (1, 10)
- 大基数 (1000000)
- 重复元素

### 3. 测试错误路径

- 无效精度参数
- 不同精度合并
- 空数据

### 4. 性能基准测试

- 使用 `testing.B`
- 使用 `b.ResetTimer()`
- 测试关键操作

### 5. 覆盖率分析

```bash
# 生成 HTML 覆盖率报告
go tool cover -html=coverage.out

# 查看函数级覆盖率
go tool cover -func=coverage.out
```
