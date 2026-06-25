# 分布式事务 (Distributed Transaction)

分布式事务学习项目，使用 Go 实现了四种主流的分布式事务解决方案：2PC、3PC、Saga、TCC。

## 项目概述

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **2PC** | 两阶段提交 | 强一致性、数据库层面 |
| **3PC** | 三阶段提交 | 减少阻塞、自主恢复 |
| **Saga** | 长事务拆分 | 跨服务业务流程 |
| **TCC** | Try-Confirm-Cancel | 高性能柔性事务 |

## 技术栈

- **语言**: Go 1.21+
- **框架**: 无（纯标准库实现）
- **测试**: Go 标准测试框架

## 项目结构

```
distributed-transaction/
├── cmd/
│   └── main.go                    # 命令行入口
├── coordinator/
│   ├── coordinator.go             # 2PC 协调者
│   └── three_phase.go             # 3PC 协调者
├── participant/
│   └── participant.go             # 参与者（Cohort）
├── saga/
│   ├── saga.go                    # 编排式 Saga
│   └── choreography.go            # 协调式 Saga
├── tcc/
│   └── tcc.go                     # TCC 事务
├── transaction/
│   └── transaction.go             # 事务定义
├── pkg/utils/
│   ├── errors.go                  # 错误类型
│   └── logger.go                  # 日志工具
├── examples/
│   ├── transfer/main.go           # 转账系统示例
│   └── order/main.go              # 订单系统示例
├── tests/                         # 测试文件
│   ├── transaction_test.go
│   ├── participant_test.go
│   ├── coordinator_test.go
│   ├── three_phase_test.go
│   ├── saga_test.go
│   └── tcc_test.go
├── docs/                          # 文档
├── go.mod
└── README.md
```

## 快速开始

### 运行演示

```bash
# 运行所有示例
go run cmd/main.go all

# 单独运行某种模式
go run cmd/main.go 2pc
go run cmd/main.go 3pc
go run cmd/main.go saga
go run cmd/main.go tcc
```

### 运行示例程序

```bash
# 转账系统示例（Saga + TCC）
go run examples/transfer/main.go

# 订单系统示例（2PC + 3PC + Saga + TCC）
go run examples/order/main.go
```

### 运行测试

```bash
go test ./tests/ -v
```

## 四种模式详解

### 1. 两阶段提交 (2PC)

```
协调者                    参与者A    参与者B
  |                         |          |
  |------ Prepare --------->|          |
  |------ Prepare -------------------->|
  |<----- Agree ------------|          |
  |<----- Agree -----------------------|
  |------ Commit ---------->|          |
  |------ Commit ---------------------->|
```

**特点**：强一致性，协调者是单点，存在阻塞问题。

### 2. 三阶段提交 (3PC)

增加 PreCommit 阶段，参与者在协调者崩溃后可超时自主决定提交或回滚。

**三个阶段**：CanCommit -> PreCommit -> DoCommit

### 3. Saga 模式

- **编排式**：中心协调器按顺序执行步骤，失败时逆序补偿
- **协调式**：通过事件总线驱动，无中心协调者

### 4. TCC 模式

- **Try**: 预留资源（冻结金额、预留库存）
- **Confirm**: 确认提交（扣减冻结金额）
- **Cancel**: 取消释放（解冻金额）

## 2PC vs 3PC 对比

| 特性 | 2PC | 3PC |
|------|-----|-----|
| 阶段数 | 2 | 3 |
| 阻塞问题 | 有 | 减少 |
| 协调者故障 | 参与者阻塞 | 可自主决定 |
| 一致性 | 强 | 强 |
| 性能 | 较低 | 稍高 |

## 核心接口

```go
// Cohort 参与者接口
type Cohort interface {
    ID() string
    Prepare(tx *Transaction) error
    Commit(tx *Transaction) error
    Abort(tx *Transaction) error
    Status() Status
}

// TCC 参与者
type TCCParticipant struct {
    Name    string
    Try     TCCFunc
    Confirm TCCFunc
    Cancel  TCCFunc
}

// Saga 步骤
type Step struct {
    Name       string
    Action     StepFunc
    Compensate StepFunc
}
```

## 参考资料

- [Distributed Transaction Processing: XA Specification](https://pubs.opengroup.org/onlinepubs/009680699/toc.pdf)
- [Sagas - Hector Garcia-Molina & Kenneth Salem](https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf)
- [Life beyond Distributed Transactions](https://queue.acm.org/detail.cfm?id=3025012)
- [Designing Data-Intensive Applications](https://www.amazon.com/Designing-Data-Intensive-Applications-Reliable-Maintainable/dp/1449373321)

---

[返回主目录](../../README.md)
