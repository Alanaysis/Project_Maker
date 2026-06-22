# 04-TESTING.md - 测试策略

## 1. 测试类型

### 1.1 单元测试
- 测试各个模块的核心功能
- 测试边界条件和错误处理
- 测试并发安全性

### 1.2 集成测试
- 测试模块间交互
- 测试完整业务流程
- 测试网络通信

### 1.3 性能测试
- 测试挖矿性能
- 测试交易吞吐量
- 测试网络延迟

## 2. 测试用例

### 2.1 区块测试
```go
func TestBlockCreation(t *testing.T) {
    // 测试创建区块
    // 测试区块哈希计算
    // 测试区块序列化/反序列化
}

func TestBlockValidation(t *testing.T) {
    // 测试区块验证
    // 测试无效区块检测
}
```

### 2.2 区块链测试
```go
func TestBlockchainCreation(t *testing.T) {
    // 测试创建区块链
    // 测试添加区块
    // 测试区块链验证
}

func TestBlockchainPersistence(t *testing.T) {
    // 测试保存区块链
    // 测试加载区块链
}
```

### 2.3 交易测试
```go
func TestTransactionCreation(t *testing.T) {
    // 测试创建交易
    // 测试交易签名
    // 测试交易验证
}

func TestCoinbaseTransaction(t *testing.T) {
    // 测试创币交易
}
```

### 2.4 工作量证明测试
```go
func TestProofOfWork(t *testing.T) {
    // 测试挖矿算法
    // 测试难度调整
    // 测试验证证明
}
```

### 2.5 钱包测试
```go
func TestWalletCreation(t *testing.T) {
    // 测试创建钱包
    // 测试地址生成
    // 测试密钥对生成
}
```

## 3. 测试数据

### 3.1 测试配置
```go
const (
    testDifficulty = 2
    testBlockTime  = 10 * time.Second
    testMaxNonce   = 1000000
)
```

### 3.2 测试工具
```go
func createTestBlockchain() *Blockchain {
    // 创建测试区块链
}

func createTestTransaction() *Transaction {
    // 创建测试交易
}

func createTestBlock() *Block {
    // 创建测试区块
}
```

## 4. 测试覆盖率

### 4.1 覆盖率目标
- 区块模块：>90%
- 区块链模块：>90%
- 交易模块：>85%
- 钱包模块：>80%
- 网络模块：>70%

### 4.2 覆盖率检查
```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## 5. 测试运行

### 5.1 运行所有测试
```bash
go test ./...
```

### 5.2 运行特定测试
```bash
go test -run TestBlockCreation ./...
```

### 5.3 运行性能测试
```bash
go test -bench=. ./...
```

## 6. 测试最佳实践

### 6.1 测试命名
- 使用描述性名称
- 包含被测功能
- 包含预期行为

### 6.2 测试结构
- Arrange：准备测试数据
- Act：执行被测功能
- Assert：验证结果

### 6.3 测试隔离
- 每个测试独立运行
- 避免测试间依赖
- 清理测试数据

## 7. 持续集成

### 7.1 CI 流程
1. 代码提交
2. 运行单元测试
3. 运行集成测试
4. 检查测试覆盖率
5. 性能测试
6. 代码审查

### 7.2 CI 工具
- GitHub Actions
- GitLab CI
- Jenkins
