# 05 - 开发日志

## 开发历程

### 阶段 1: 项目初始化

**目标**: 搭建项目基础结构

**完成工作**:
- 创建项目目录结构
- 初始化 Go 模块
- 编写 README 文档

### 阶段 2: 核心哈希实现

**目标**: 实现一致性哈希基础

**完成工作**:
- 实现 SHA-1 哈希函数
- 实现环上数学运算 (Between, PowerOfTwo)
- 编写哈希函数测试

**关键代码**:
```go
func DefaultHash(key string) *big.Int {
    hash := sha1.New()
    hash.Write([]byte(key))
    return new(big.Int).SetBytes(hash.Sum(nil))
}
```

### 阶段 3: Chord 协议实现

**目标**: 实现 Chord 节点核心功能

**完成工作**:
- 实现 Node 数据结构
- 实现 Finger Table
- 实现键值存储
- 实现 FindSuccessor 算法

**关键代码**:
```go
type Node struct {
    ID          *big.Int
    FingerTable []FingerEntry
    Predecessor *NodeID
    Successor   *NodeID
    storage     map[string]string
}
```

### 阶段 4: Chord 环管理

**目标**: 实现 Chord 环管理

**完成工作**:
- 实现 Ring 数据结构
- 实现节点添加/移除
- 实现键值路由
- 实现 finger table 更新

**关键代码**:
```go
type Ring struct {
    nodes     map[string]*Node
    sortedIDs []*big.Int
}
```

### 阶段 5: Kademlia 协议实现

**目标**: 实现 Kademlia 协议

**完成工作**:
- 实现 XOR 距离计算
- 实现 K-桶数据结构
- 实现路由表管理
- 实现 FIND_NODE 和 FIND_VALUE

**关键代码**:
```go
func XOR(a, b *big.Int) *big.Int {
    return new(big.Int).Xor(a, b)
}

type KBucket struct {
    contacts []*Contact
}

type RoutingTable struct {
    localID   *big.Int
    buckets   [160]*KBucket
}
```

### 阶段 6: 网络层实现

**目标**: 实现 HTTP 网络通信

**完成工作**:
- 实现 HTTP 服务器
- 实现消息协议
- 实现 PING/STORE/FIND_NODE/FIND_VALUE 操作
- 实现迭代查找

**关键代码**:
```go
type NetworkNode struct {
    node       *KademliaNode
    httpServer *http.Server
}

func (nn *NetworkNode) Start() error {
    mux := http.NewServeMux()
    mux.HandleFunc("/ping", nn.handlePing)
    mux.HandleFunc("/store", nn.handleStore)
    mux.HandleFunc("/find_node", nn.handleFindNode)
    mux.HandleFunc("/find_value", nn.handleFindValue)
    // ...
}
```

### 阶段 7: 节点发现实现

**目标**: 实现节点发现和引导

**完成工作**:
- 实现 Bootstrap 机制
- 实现定期刷新
- 实现 Ping 检测
- 实现节点管理器

**关键代码**:
```go
type Discovery struct {
    node   *NetworkNode
    config *DiscoveryConfig
}

func (d *Discovery) Bootstrap() error {
    for _, addr := range d.config.BootstrapAddrs {
        d.node.Ping(addr)
        contacts, _ := d.node.RemoteFindNode(addr, d.node.GetID())
        for _, c := range contacts {
            d.node.node.RT.AddContact(c)
        }
    }
    return nil
}
```

### 阶段 8: 应用层实现

**目标**: 实现 P2P 文件共享和分布式存储

**完成工作**:
- 实现 P2P 文件共享
- 实现分布式键值存储
- 实现 TTL 过期机制
- 实现批量操作

**关键代码**:
```go
type P2PNetwork struct {
    node     *NetworkNode
    filesDir string
    files    map[string]*FileInfo
}

type DistributedStorage struct {
    node     *NetworkNode
    items    map[string]*StorageItem
    replicas int
}
```

### 阶段 9: 测试和文档

**目标**: 确保代码质量和可维护性

**完成工作**:
- 编写全面的单元测试
- 编写集成测试
- 编写网络测试
- 完善文档

## 遇到的问题与解决方案

### 问题 1: 大数运算

**问题**: SHA-1 产生 160 位哈希，超出 Go 基本类型范围

**解决方案**: 使用 `math/big.Int` 进行大数运算

### 问题 2: 环绕处理

**问题**: 环上的区间判断需要处理 start > end 的情况

**解决方案**: 实现专门的 Between 函数处理各种情况

### 问题 3: 并发访问

**问题**: 多个 goroutine 可能同时访问节点数据

**解决方案**: 使用 sync.RWMutex 进行并发控制

### 问题 4: 网络超时

**问题**: HTTP 请求可能超时导致阻塞

**解决方案**: 设置合理的超时时间和重试机制

### 问题 5: 路由表一致性

**问题**: 节点加入/离开时路由表需要更新

**解决方案**: 实现定期刷新和 Bootstrap 机制

## 代码质量

### 代码风格

- 遵循 Go 官方代码规范
- 使用有意义的变量名
- 添加必要的注释
- 保持函数简洁

### 测试覆盖

- 核心功能测试覆盖率 > 80%
- 边界条件测试充分
- 包含性能基准测试
- 并发安全测试

## 性能分析

### 时间复杂度

- 查找操作: O(log N)
- 插入操作: O(log N)
- 删除操作: O(log N)
- XOR 运算: O(1)

### 空间复杂度

- 每个节点: O(M) - Finger Table / K-桶
- 整体: O(N * M) - N 个节点，M 为标识符位数

### 网络开销

- PING: O(1)
- STORE: O(K) - 存储到 K 个节点
- FIND_NODE: O(log N) - 迭代查找
- FIND_VALUE: O(log N) - 迭代查找

## 未来改进

### 短期改进

1. 实现数据复制策略
2. 添加监控指标
3. 优化网络连接池
4. 添加配置文件支持

### 长期改进

1. 支持多种哈希函数
2. 实现负载均衡
3. 添加安全机制 (加密、认证)
4. 支持 NAT 穿透
5. 实现文件分片传输

## 开发工具

### 使用的工具

- **Go**: 主要编程语言
- **Go testing**: 测试框架
- **Go vet**: 代码检查
- **golangci-lint**: 代码质量检查

### 开发环境

- Go 1.22+
- Linux/macOS/Windows
- Git 版本控制

## 总结

本项目成功实现了完整的分布式哈希表系统，包括:

1. **Chord 协议**: 一致性哈希、Finger Table、节点管理
2. **Kademlia 协议**: XOR 距离、K-桶、迭代查找
3. **网络层**: HTTP 服务器、消息协议
4. **节点发现**: Bootstrap、定期刷新
5. **应用层**: P2P 文件共享、分布式存储
6. **测试**: 全面的单元测试和集成测试

通过这个项目，深入理解了分布式哈希表的工作原理和实现细节，掌握了分布式系统设计的核心概念。
