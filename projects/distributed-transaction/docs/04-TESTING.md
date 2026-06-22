# 测试文档

## 1. 测试策略

### 1.1 测试金字塔

```
           /\
          /  \        E2E测试
         /    \       (少量)
        /------\
       /        \     集成测试
      /          \    (适量)
     /------------\
    /              \  单元测试
   /                \ (大量)
  /------------------\
```

### 1.2 测试类型

| 测试类型 | 目的 | 数量 | 执行速度 |
|---------|------|------|---------|
| 单元测试 | 测试单个函数/方法 | 多 | 快 |
| 集成测试 | 测试组件交互 | 中 | 中 |
| E2E测试 | 测试完整流程 | 少 | 慢 |

## 2. 单元测试

### 2.1 事务测试

```go
// test/transaction_test.go
package test

import (
    "testing"
    "time"
    
    "distributed-transaction/internal/transaction"
)

func TestNewTransaction(t *testing.T) {
    tx := transaction.NewTransaction("tx-1")
    
    if tx.ID != "tx-1" {
        t.Errorf("Expected ID 'tx-1', got '%s'", tx.ID)
    }
    
    if tx.Status != transaction.StatusInit {
        t.Errorf("Expected status INIT, got %s", tx.Status)
    }
    
    if tx.Data == nil {
        t.Error("Data map should not be nil")
    }
}

func TestTransactionSetStatus(t *testing.T) {
    tx := transaction.NewTransaction("tx-1")
    
    tx.SetStatus(transaction.StatusPreparing)
    if tx.GetStatus() != transaction.StatusPreparing {
        t.Errorf("Expected status PREPARING, got %s", tx.GetStatus())
    }
    
    tx.SetStatus(transaction.StatusPrepared)
    if tx.GetStatus() != transaction.StatusPrepared {
        t.Errorf("Expected status PREPARED, got %s", tx.GetStatus())
    }
}

func TestTransactionSetData(t *testing.T) {
    tx := transaction.NewTransaction("tx-1")
    
    tx.SetData("key1", "value1")
    val, ok := tx.GetData("key1")
    
    if !ok {
        t.Error("Expected key1 to exist")
    }
    
    if val != "value1" {
        t.Errorf("Expected 'value1', got '%v'", val)
    }
}

func TestTransactionConcurrentAccess(t *testing.T) {
    tx := transaction.NewTransaction("tx-1")
    
    // 并发写入
    done := make(chan bool, 10)
    for i := 0; i < 10; i++ {
        go func(val int) {
            tx.SetData("key", val)
            done <- true
        }(i)
    }
    
    // 等待所有goroutine完成
    for i := 0; i < 10; i++ {
        <-done
    }
    
    // 验证数据存在
    _, ok := tx.GetData("key")
    if !ok {
        t.Error("Expected key to exist after concurrent writes")
    }
}
```

### 2.2 参与者测试

```go
// test/cohort_test.go
package test

import (
    "testing"
    
    "distributed-transaction/internal/cohort"
    "distributed-transaction/internal/transaction"
)

func TestNewCohort(t *testing.T) {
    ch := cohort.NewCohort("cohort-1")
    
    if ch.ID() != "cohort-1" {
        t.Errorf("Expected ID 'cohort-1', got '%s'", ch.ID())
    }
    
    if ch.Status() != cohort.StatusReady {
        t.Errorf("Expected status READY, got %d", ch.Status())
    }
}

func TestCohortPrepare(t *testing.T) {
    ch := cohort.NewCohort("cohort-1")
    tx := transaction.NewTransaction("tx-1")
    
    err := ch.Prepare(tx)
    if err != nil {
        t.Errorf("Prepare failed: %v", err)
    }
    
    if ch.Status() != cohort.StatusPrepared {
        t.Errorf("Expected status PREPARED, got %d", ch.Status())
    }
}

func TestCohortCommit(t *testing.T) {
    ch := cohort.NewCohort("cohort-1")
    tx := transaction.NewTransaction("tx-1")
    
    // 先准备
    if err := ch.Prepare(tx); err != nil {
        t.Fatalf("Prepare failed: %v", err)
    }
    
    // 再提交
    err := ch.Commit(tx)
    if err != nil {
        t.Errorf("Commit failed: %v", err)
    }
    
    if ch.Status() != cohort.StatusCommitted {
        t.Errorf("Expected status COMMITTED, got %d", ch.Status())
    }
}

func TestCohortAbort(t *testing.T) {
    ch := cohort.NewCohort("cohort-1")
    tx := transaction.NewTransaction("tx-1")
    
    // 先准备
    if err := ch.Prepare(tx); err != nil {
        t.Fatalf("Prepare failed: %v", err)
    }
    
    // 再回滚
    err := ch.Abort(tx)
    if err != nil {
        t.Errorf("Abort failed: %v", err)
    }
    
    if ch.Status() != cohort.StatusAborted {
        t.Errorf("Expected status ABORTED, got %d", ch.Status())
    }
}

func TestCohortPrepareError(t *testing.T) {
    ch := cohort.NewCohort("cohort-1")
    ch.SetSimulateError(true)
    
    tx := transaction.NewTransaction("tx-1")
    
    err := ch.Prepare(tx)
    if err == nil {
        t.Error("Expected error, got nil")
    }
    
    if ch.Status() != cohort.StatusFailed {
        t.Errorf("Expected status FAILED, got %d", ch.Status())
    }
}

func TestCohortCommitWithoutPrepare(t *testing.T) {
    ch := cohort.NewCohort("cohort-1")
    tx := transaction.NewTransaction("tx-1")
    
    // 直接提交，应该失败
    err := ch.Commit(tx)
    if err == nil {
        t.Error("Expected error for commit without prepare, got nil")
    }
}
```

### 2.3 协调者测试

```go
// test/coordinator_test.go
package test

import (
    "testing"
    
    "distributed-transaction/internal/cohort"
    "distributed-transaction/internal/coordinator"
    "distributed-transaction/internal/transaction"
)

func TestNewCoordinator(t *testing.T) {
    coord := coordinator.NewCoordinator("coordinator-1")
    
    if coord == nil {
        t.Error("Expected coordinator, got nil")
    }
}

func TestRegisterCohort(t *testing.T) {
    coord := coordinator.NewCoordinator("coordinator-1")
    ch := cohort.NewCohort("cohort-1")
    
    err := coord.RegisterCohort(ch)
    if err != nil {
        t.Errorf("RegisterCohort failed: %v", err)
    }
}

func TestRegisterDuplicateCohort(t *testing.T) {
    coord := coordinator.NewCoordinator("coordinator-1")
    ch := cohort.NewCohort("cohort-1")
    
    // 第一次注册
    if err := coord.RegisterCohort(ch); err != nil {
        t.Fatalf("First RegisterCohort failed: %v", err)
    }
    
    // 第二次注册，应该失败
    err := coord.RegisterCohort(ch)
    if err == nil {
        t.Error("Expected error for duplicate registration, got nil")
    }
}

func TestExecuteTransactionSuccess(t *testing.T) {
    coord := coordinator.NewCoordinator("coordinator-1")
    
    // 创建并注册参与者
    ch1 := cohort.NewCohort("cohort-1")
    ch2 := cohort.NewCohort("cohort-2")
    
    if err := coord.RegisterCohort(ch1); err != nil {
        t.Fatal(err)
    }
    if err := coord.RegisterCohort(ch2); err != nil {
        t.Fatal(err)
    }
    
    // 执行事务
    tx := transaction.NewTransaction("tx-1")
    result, err := coord.ExecuteTransaction(tx)
    
    if err != nil {
        t.Errorf("ExecuteTransaction failed: %v", err)
    }
    
    if result.Status != "COMMITTED" {
        t.Errorf("Expected status COMMITTED, got %s", result.Status)
    }
}

func TestExecuteTransactionFailure(t *testing.T) {
    coord := coordinator.NewCoordinator("coordinator-1")
    
    // 创建会失败的参与者
    ch := cohort.NewCohort("cohort-1")
    ch.SetSimulateError(true)
    
    if err := coord.RegisterCohort(ch); err != nil {
        t.Fatal(err)
    }
    
    // 执行事务
    tx := transaction.NewTransaction("tx-1")
    result, err := coord.ExecuteTransaction(tx)
    
    if err == nil {
        t.Error("Expected error, got nil")
    }
    
    if result.Status != "ABORTED" {
        t.Errorf("Expected status ABORTED, got %s", result.Status)
    }
}

func TestExecuteTransactionNoCohorts(t *testing.T) {
    coord := coordinator.NewCoordinator("coordinator-1")
    
    // 不注册参与者
    tx := transaction.NewTransaction("tx-1")
    _, err := coord.ExecuteTransaction(tx)
    
    if err == nil {
        t.Error("Expected error for no cohorts, got nil")
    }
}

func TestExecuteTransactionPartialFailure(t *testing.T) {
    coord := coordinator.NewCoordinator("coordinator-1")
    
    // 创建一个成功和一个失败的参与者
    ch1 := cohort.NewCohort("cohort-1")
    ch2 := cohort.NewCohort("cohort-2")
    ch2.SetSimulateError(true)
    
    if err := coord.RegisterCohort(ch1); err != nil {
        t.Fatal(err)
    }
    if err := coord.RegisterCohort(ch2); err != nil {
        t.Fatal(err)
    }
    
    // 执行事务
    tx := transaction.NewTransaction("tx-1")
    result, err := coord.ExecuteTransaction(tx)
    
    if err == nil {
        t.Error("Expected error for partial failure, got nil")
    }
    
    if result.Status != "ABORTED" {
        t.Errorf("Expected status ABORTED, got %s", result.Status)
    }
    
    // 验证成功的参与者被回滚
    if ch1.Status() != cohort.StatusAborted {
        t.Errorf("Expected cohort-1 to be ABORTED, got %d", ch1.Status())
    }
}
```

## 3. 集成测试

```go
// test/integration_test.go
package test

import (
    "testing"
    
    "distributed-transaction/internal/cohort"
    "distributed-transaction/internal/coordinator"
    "distributed-transaction/internal/transaction"
)

func TestFull2PCFlow(t *testing.T) {
    // 创建协调者
    coord := coordinator.NewCoordinator("coordinator-1")
    
    // 创建多个参与者
    cohorts := make([]*cohort.Cohort, 5)
    for i := 0; i < 5; i++ {
        cohorts[i] = cohort.NewCohort("cohort-" + string(rune('1'+i)))
        if err := coord.RegisterCohort(cohorts[i]); err != nil {
            t.Fatal(err)
        }
    }
    
    // 执行多个事务
    for i := 0; i < 10; i++ {
        tx := transaction.NewTransaction("tx-" + string(rune('1'+i)))
        result, err := coord.ExecuteTransaction(tx)
        
        if err != nil {
            t.Errorf("Transaction %s failed: %v", tx.ID, err)
            continue
        }
        
        if result.Status != "COMMITTED" {
            t.Errorf("Transaction %s: expected COMMITTED, got %s", tx.ID, result.Status)
        }
    }
    
    // 验证所有参与者状态
    for _, ch := range cohorts {
        if ch.Status() != cohort.StatusReady {
            t.Errorf("Cohort %s: expected READY, got %d", ch.ID(), ch.Status())
        }
    }
}

func TestFull3PCFlow(t *testing.T) {
    // 创建3PC协调者
    coord := coordinator.NewThreePhaseCoordinator("coordinator-1")
    
    // 创建参与者
    ch1 := cohort.NewCohort("cohort-1")
    ch2 := cohort.NewCohort("cohort-2")
    
    if err := coord.RegisterCohort(ch1); err != nil {
        t.Fatal(err)
    }
    if err := coord.RegisterCohort(ch2); err != nil {
        t.Fatal(err)
    }
    
    // 执行事务
    tx := transaction.NewTransaction("tx-1")
    result, err := coord.ExecuteTransaction(tx)
    
    if err != nil {
        t.Errorf("3PC transaction failed: %v", err)
    }
    
    if result.Status != "COMMITTED" {
        t.Errorf("Expected COMMITTED, got %s", result.Status)
    }
}

func TestConcurrentTransactions(t *testing.T) {
    coord := coordinator.NewCoordinator("coordinator-1")
    
    ch := cohort.NewCohort("cohort-1")
    if err := coord.RegisterCohort(ch); err != nil {
        t.Fatal(err)
    }
    
    // 并发执行事务
    done := make(chan bool, 100)
    for i := 0; i < 100; i++ {
        go func(id int) {
            tx := transaction.NewTransaction("tx-" + string(rune('A'+id%26)))
            _, err := coord.ExecuteTransaction(tx)
            if err != nil {
                t.Errorf("Transaction %s failed: %v", tx.ID, err)
            }
            done <- true
        }(i)
    }
    
    // 等待所有事务完成
    for i := 0; i < 100; i++ {
        <-done
    }
}
```

## 4. 故障注入测试

```go
// test/failure_test.go
package test

import (
    "testing"
    
    "distributed-transaction/internal/cohort"
    "distributed-transaction/internal/coordinator"
    "distributed-transaction/internal/transaction"
)

func TestCoordinatorFailure(t *testing.T) {
    // 模拟协调者故障
    coord := coordinator.NewCoordinator("coordinator-1")
    
    ch := cohort.NewCohort("cohort-1")
    if err := coord.RegisterCohort(ch); err != nil {
        t.Fatal(err)
    }
    
    // 执行事务
    tx := transaction.NewTransaction("tx-1")
    _, err := coord.ExecuteTransaction(tx)
    
    // 这个测试主要验证没有panic
    if err != nil {
        t.Logf("Transaction failed (expected in some cases): %v", err)
    }
}

func TestParticipantFailureDuringPrepare(t *testing.T) {
    coord := coordinator.NewCoordinator("coordinator-1")
    
    // 创建在准备阶段失败的参与者
    ch := cohort.NewCohort("cohort-1")
    ch.SetSimulateError(true)
    
    if err := coord.RegisterCohort(ch); err != nil {
        t.Fatal(err)
    }
    
    tx := transaction.NewTransaction("tx-1")
    result, err := coord.ExecuteTransaction(tx)
    
    if err == nil {
        t.Error("Expected error, got nil")
    }
    
    if result.Status != "ABORTED" {
        t.Errorf("Expected ABORTED, got %s", result.Status)
    }
}

func TestParticipantFailureDuringCommit(t *testing.T) {
    // 这个测试更复杂，需要在Prepare成功后模拟Commit失败
    // 可以通过更复杂的mock实现
    t.Skip("需要更复杂的mock实现")
}

func TestNetworkPartition(t *testing.T) {
    // 模拟网络分区
    // 可以通过超时来模拟
    t.Skip("需要网络模拟工具")
}
```

## 5. 性能测试

```go
// test/benchmark_test.go
package test

import (
    "testing"
    
    "distributed-transaction/internal/cohort"
    "distributed-transaction/internal/coordinator"
    "distributed-transaction/internal/transaction"
)

func Benchmark2PCTransaction(b *testing.B) {
    coord := coordinator.NewCoordinator("coordinator-1")
    
    ch := cohort.NewCohort("cohort-1")
    if err := coord.RegisterCohort(ch); err != nil {
        b.Fatal(err)
    }
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        tx := transaction.NewTransaction("tx-1")
        _, _ = coord.ExecuteTransaction(tx)
    }
}

func Benchmark3PCTransaction(b *testing.B) {
    coord := coordinator.NewThreePhaseCoordinator("coordinator-1")
    
    ch := cohort.NewCohort("cohort-1")
    if err := coord.RegisterCohort(ch); err != nil {
        b.Fatal(err)
    }
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        tx := transaction.NewTransaction("tx-1")
        _, _ = coord.ExecuteTransaction(tx)
    }
}

func BenchmarkMultipleCohorts(b *testing.B) {
    coord := coordinator.NewCoordinator("coordinator-1")
    
    for i := 0; i < 10; i++ {
        ch := cohort.NewCohort("cohort-" + string(rune('1'+i)))
        if err := coord.RegisterCohort(ch); err != nil {
            b.Fatal(err)
        }
    }
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        tx := transaction.NewTransaction("tx-1")
        _, _ = coord.ExecuteTransaction(tx)
    }
}
```

## 6. 测试覆盖率

### 6.1 运行测试

```bash
# 运行所有测试
go test ./...

# 运行特定包的测试
go test ./test/...

# 运行带详细输出的测试
go test -v ./...

# 运行带覆盖率的测试
go test -cover ./...

# 生成覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### 6.2 覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| transaction | 90%+ |
| cohort | 85%+ |
| coordinator | 80%+ |
| utils | 90%+ |

## 7. 测试最佳实践

### 7.1 测试命名

- 使用`Test`前缀
- 描述被测试的功能
- 包含预期行为

```go
// 好的命名
func TestTransactionSetStatus(t *testing.T) { ... }
func TestCohortPrepareWithInvalidInput(t *testing.T) { ... }

// 不好的命名
func Test1(t *testing.T) { ... }
func TestStuff(t *testing.T) { ... }
```

### 7.2 测试结构

使用Arrange-Act-Assert模式：

```go
func TestSomething(t *testing.T) {
    // Arrange - 准备测试数据
    tx := transaction.NewTransaction("tx-1")
    
    // Act - 执行被测试的操作
    tx.SetStatus(transaction.StatusPreparing)
    
    // Assert - 验证结果
    if tx.GetStatus() != transaction.StatusPreparing {
        t.Errorf("Expected PREPARING, got %s", tx.GetStatus())
    }
}
```

### 7.3 错误处理

```go
func TestSomething(t *testing.T) {
    result, err := doSomething()
    
    // 检查错误
    if err != nil {
        t.Fatalf("Unexpected error: %v", err)
    }
    
    // 检查结果
    if result == nil {
        t.Fatal("Expected result, got nil")
    }
}
```

## 8. 持续集成

### 8.1 GitHub Actions配置

```yaml
name: Go Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Go
      uses: actions/setup-go@v2
      with:
        go-version: 1.21
    
    - name: Run tests
      run: go test -v -cover ./...
    
    - name: Run benchmarks
      run: go test -bench=. ./...
```

## 9. 测试工具

### 9.1 常用测试库

- **testing**: Go标准库
- **testify**: 断言和mock
- **gomock**: Mock框架
- **go-cmp**: 比较工具

### 9.2 测试辅助函数

```go
// test/helpers_test.go
package test

import "testing"

func assertEqual(t *testing.T, expected, actual interface{}) {
    t.Helper()
    if expected != actual {
        t.Errorf("Expected %v, got %v", expected, actual)
    }
}

func assertNoError(t *testing.T, err error) {
    t.Helper()
    if err != nil {
        t.Fatalf("Expected no error, got %v", err)
    }
}

func assertError(t *testing.T, err error) {
    t.Helper()
    if err == nil {
        t.Fatal("Expected error, got nil")
    }
}
```
