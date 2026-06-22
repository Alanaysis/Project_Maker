# 04 - 测试文档

## 测试概述

本项目包含单元测试和集成测试，确保 Chord DHT 实现的正确性。

## 测试结构

```
test/
└── chord_test.go      # 所有测试用例
```

## 测试用例

### 1. 哈希函数测试

#### TestDefaultHash
- 验证相同输入产生相同输出
- 验证不同输入产生不同输出
- 验证哈希值在正确范围内

#### TestBetween
- 测试正常区间判断
- 测试环绕情况 (start > end)
- 测试边界条件

#### TestBetweenRightInclusive
- 测试右包含情况
- 验证边界处理

### 2. 节点测试

#### TestNewNode
- 验证节点初始化
- 验证 finger table 大小
- 验证初始状态

#### TestNodeStoreGet
- 测试键值存储
- 测试键值读取
- 测试不存在的键

#### TestNodeDelete
- 测试删除操作
- 测试删除不存在的键

### 3. Ring 测试

#### TestNewRing
- 验证环初始化
- 验证空环状态

#### TestRingAddNode
- 测试添加单个节点
- 测试添加多个节点
- 测试重复添加

#### TestRingRemoveNode
- 测试移除节点
- 测试键转移
- 测试移除不存在的节点

#### TestRingPutGet
- 测试基本存储和读取
- 测试多节点存储
- 测试键分布

#### TestRingDelete
- 测试删除操作
- 测试删除后读取

### 4. 路由测试

#### TestRouting
- 测试单跳路由
- 测试多跳路由
- 测试环形路由

### 5. 集成测试

#### TestChordIntegration
- 完整的节点生命周期
- 多节点协作
- 键值操作序列

## 运行测试

### 运行所有测试

```bash
cd projects/dht
go test ./test/ -v
```

### 运行特定测试

```bash
go test ./test/ -v -run TestBetween
```

### 查看测试覆盖率

```bash
go test ./test/ -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## 测试数据

### 测试键值对

```go
testData := map[string]string{
    "key1": "value1",
    "key2": "value2",
    "key3": "value3",
    "name": "chord",
    "lang": "go",
}
```

### 测试节点地址

```go
testNodes := []string{
    "node1:8000",
    "node2:8001",
    "node3:8002",
    "node4:8003",
    "node5:8004",
}
```

## 测试结果

### 预期结果

1. 所有哈希函数测试通过
2. 环运算测试覆盖各种边界情况
3. 节点存储操作正确
4. 多节点场景下键值分布正确
5. 路由算法找到正确节点

### 性能基准

```bash
go test ./test/ -bench=.
```

## 持续集成

建议在 CI/CD 流程中:
1. 运行所有测试
2. 检查测试覆盖率 (>80%)
3. 运行基准测试
4. 检查竞态条件 (`go test -race`)

## 测试最佳实践

1. **独立性**: 每个测试独立运行
2. **可重复**: 测试结果一致
3. **清晰性**: 测试意图明确
4. **全面性**: 覆盖正常和异常情况
