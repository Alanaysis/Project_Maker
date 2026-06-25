# 04 - 测试文档: 分布式哈希表 DHT

## 测试策略

### 测试层次

1. **单元测试**: 测试单个函数和方法
2. **集成测试**: 测试模块间交互
3. **网络测试**: 测试网络通信
4. **端到端测试**: 测试完整流程

### 测试覆盖

- 核心功能测试覆盖率 > 80%
- 边界条件测试充分
- 并发安全测试
- 错误处理测试

## 测试结构

```
test/
├── chord_test.go       # Chord 协议测试
├── kademlia_test.go    # Kademlia 协议测试
├── network_test.go     # 网络层测试
└── storage_test.go     # 存储层测试
```

## 单元测试

### 1. 哈希函数测试

```go
func TestDefaultHash(t *testing.T) {
    // 测试确定性
    hash1 := internal.DefaultHash("test")
    hash2 := internal.DefaultHash("test")
    if hash1.Cmp(hash2) != 0 {
        t.Errorf("Same input should produce same hash")
    }

    // 测试不同输入产生不同输出
    hash3 := internal.DefaultHash("test2")
    if hash1.Cmp(hash3) == 0 {
        t.Errorf("Different inputs should produce different hashes")
    }
}
```

### 2. XOR 距离测试

```go
func TestXOR(t *testing.T) {
    tests := []struct {
        name     string
        a        int64
        b        int64
        expected int64
    }{
        {"same value", 5, 5, 0},
        {"different values", 5, 3, 6},
        {"zero and value", 0, 7, 7},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            a := big.NewInt(tt.a)
            b := big.NewInt(tt.b)
            result := internal.XOR(a, b)
            expected := big.NewInt(tt.expected)
            if result.Cmp(expected) != 0 {
                t.Errorf("XOR(%d, %d) = %s, want %s", tt.a, tt.b, result.String(), expected.String())
            }
        })
    }
}
```

### 3. K-桶测试

```go
func TestKBucketAddContact(t *testing.T) {
    bucket := internal.NewKBucket()

    // 添加 K 个联系人
    for i := 0; i < internal.K; i++ {
        id := big.NewInt(int64(i))
        contact := internal.NewContact(id, "addr")
        added := bucket.AddContact(contact)
        if !added {
            t.Errorf("Contact %d should be added", i)
        }
    }

    if bucket.Size() != internal.K {
        t.Errorf("Bucket size = %d, want %d", bucket.Size(), internal.K)
    }
}
```

### 4. 路由表测试

```go
func TestRoutingTableFindClosest(t *testing.T) {
    localID := big.NewInt(100)
    rt := internal.NewRoutingTable(localID, "local:8000")

    // 添加联系人
    for i := 0; i < 10; i++ {
        id := big.NewInt(int64(i * 10))
        contact := internal.NewContact(id, "addr")
        rt.AddContact(contact)
    }

    // 查找最近的 5 个
    target := big.NewInt(55)
    closest := rt.FindClosestContacts(target, 5)

    if len(closest) != 5 {
        t.Errorf("FindClosestContacts returned %d contacts, want 5", len(closest))
    }
}
```

### 5. Chord 节点测试

```go
func TestNodeStoreGet(t *testing.T) {
    node := internal.NewNode("test:8000", nil)

    node.Store("key1", "value1")

    value, ok := node.Get("key1")
    if !ok {
        t.Error("Should find key1")
    }
    if value != "value1" {
        t.Errorf("Got %s, want value1", value)
    }
}
```

### 6. Kademlia 节点测试

```go
func TestKademliaNodeFindValue(t *testing.T) {
    node := internal.NewKademliaNode("test:8000", nil)

    node.Store("testkey", "testvalue")

    value, contacts, found := node.FindValue("testkey")
    if !found {
        t.Error("FindValue should find stored value")
    }
    if value != "testvalue" {
        t.Errorf("FindValue returned %s, want testvalue", value)
    }
}
```

## 集成测试

### 1. Chord 环集成测试

```go
func TestChordIntegration(t *testing.T) {
    ring := internal.NewRing(nil)

    // 添加节点
    nodeAddrs := []string{
        "node1:8000",
        "node2:8001",
        "node3:8002",
    }

    for _, addr := range nodeAddrs {
        ring.AddNode(addr)
    }

    // 存储数据
    testData := map[string]string{
        "key1": "value1",
        "key2": "value2",
    }

    for key, value := range testData {
        ring.Put(key, value)
    }

    // 验证数据
    for key, expected := range testData {
        actual, err := ring.Get(key)
        if err != nil {
            t.Fatalf("Failed to get key %s: %v", key, err)
        }
        if actual != expected {
            t.Errorf("Key %s: got %s, want %s", key, actual, expected)
        }
    }
}
```

### 2. Kademlia 集成测试

```go
func TestKademliaIntegration(t *testing.T) {
    nodes := make([]*internal.KademliaNode, 5)
    for i := 0; i < 5; i++ {
        addr := "node" + string(rune('0'+i)) + ":800" + string(rune('0'+i))
        nodes[i] = internal.NewKademliaNode(addr, nil)
    }

    // 连接节点
    for i := 1; i < len(nodes); i++ {
        for j := 0; j < i; j++ {
            contact := internal.NewContact(nodes[j].ID, nodes[j].Addr)
            nodes[i].RT.AddContact(contact)
        }
    }

    // 存储数据
    nodes[0].Store("key1", "value1")

    // 验证
    value, ok := nodes[0].Get("key1")
    if !ok || value != "value1" {
        t.Error("Failed to get stored value")
    }
}
```

## 网络测试

### 1. PING 测试

```go
func TestNetworkNodePing(t *testing.T) {
    server := internal.NewNetworkNode("localhost:19000")
    server.Start()
    defer server.Stop()

    time.Sleep(100 * time.Millisecond)

    client := internal.NewNetworkNode("localhost:19001")
    client.Start()
    defer client.Stop()

    time.Sleep(100 * time.Millisecond)

    if err := client.Ping("localhost:19000"); err != nil {
        t.Fatalf("Failed to ping: %v", err)
    }
}
```

### 2. FIND_NODE 测试

```go
func TestNetworkNodeFindNode(t *testing.T) {
    server := internal.NewNetworkNode("localhost:19002")
    server.Start()
    defer server.Stop()

    time.Sleep(100 * time.Millisecond)

    client := internal.NewNetworkNode("localhost:19003")
    client.Start()
    defer client.Stop()

    time.Sleep(100 * time.Millisecond)

    targetID := internal.KademliaHash("target")
    contacts, err := client.RemoteFindNode("localhost:19002", targetID)
    if err != nil {
        t.Fatalf("Failed to find nodes: %v", err)
    }

    if len(contacts) == 0 {
        t.Error("FindNode should return contacts")
    }
}
```

## 存储测试

### 1. TTL 测试

```go
func TestDistributedStorageTTL(t *testing.T) {
    node := internal.NewNetworkNode("localhost:19020")
    node.Start()
    defer node.Stop()

    storage := internal.NewDistributedStorage(node, 3)

    storage.Put("key1", "value1", 1) // 1秒 TTL

    // 立即获取应该成功
    value, err := storage.Get("key1")
    if err != nil || value != "value1" {
        t.Error("Should get value immediately")
    }

    // 等待过期
    time.Sleep(1100 * time.Millisecond)

    // 应该过期
    _, err = storage.Get("key1")
    if err == nil {
        t.Error("Key should be expired")
    }
}
```

### 2. 批量操作测试

```go
func TestDistributedStorageBatchPut(t *testing.T) {
    node := internal.NewNetworkNode("localhost:19021")
    node.Start()
    defer node.Stop()

    storage := internal.NewDistributedStorage(node, 3)

    items := map[string]string{
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
    }

    if err := storage.BatchPut(items, 0); err != nil {
        t.Fatalf("BatchPut failed: %v", err)
    }

    if storage.Size() != 3 {
        t.Errorf("Size should be 3, got %d", storage.Size())
    }
}
```

## 并发测试

### 1. 并发读写测试

```go
func TestConcurrency(t *testing.T) {
    node := internal.NewKademliaNode("test:8000", nil)

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(idx int) {
            defer wg.Done()
            key := fmt.Sprintf("key%d", idx)
            node.Store(key, "value")
            node.Get(key)
        }(i)
    }
    wg.Wait()
}
```

### 2. 路由表并发测试

```go
func TestRoutingTableConcurrency(t *testing.T) {
    localID := big.NewInt(100)
    rt := internal.NewRoutingTable(localID, "local:8000")

    var wg sync.WaitGroup

    // 并发添加
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(idx int) {
            defer wg.Done()
            id := big.NewInt(int64(idx * 100))
            contact := internal.NewContact(id, "addr")
            rt.AddContact(contact)
        }(i)
    }

    // 并发读取
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            target := big.NewInt(50)
            rt.FindClosestContacts(target, 5)
        }()
    }

    wg.Wait()
}
```

## 边界条件测试

### 1. 空环测试

```go
func TestEmptyRing(t *testing.T) {
    ring := internal.NewRing(nil)

    // 空环应该返回错误
    _, err := ring.Get("key")
    if err == nil {
        t.Error("Getting from empty ring should fail")
    }
}
```

### 2. 单节点测试

```go
func TestSingleNode(t *testing.T) {
    node := internal.NewKademliaNode("test:8000", nil)

    // 单节点应该能找到自己
    contacts := node.FindNode(node.ID)
    if len(contacts) != 0 {
        t.Error("Single node should not find other contacts")
    }
}
```

## 性能测试

### 1. 查找性能测试

```go
func BenchmarkFindNode(b *testing.B) {
    node := internal.NewKademliaNode("test:8000", nil)

    // 添加联系人
    for i := 0; i < 100; i++ {
        id := internal.KademliaHash(fmt.Sprintf("node%d", i))
        contact := internal.NewContact(id, "addr")
        node.RT.AddContact(contact)
    }

    target := internal.KademliaHash("target")

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        node.FindNode(target)
    }
}
```

## 运行测试

### 运行所有测试

```bash
cd projects/dht
go test ./test/ -v
```

### 运行特定测试

```bash
# 运行 Kademlia 测试
go test ./test/ -v -run TestKademlia

# 运行网络测试
go test ./test/ -v -run TestNetwork

# 运行存储测试
go test ./test/ -v -run TestStorage
```

### 运行性能测试

```bash
go test ./test/ -bench=.
```

### 生成覆盖率报告

```bash
go test ./test/ -coverprofile=coverage.out
go tool cover -html=coverage.out
```

### 检查竞态条件

```bash
go test ./test/ -race
```

## 测试最佳实践

1. **独立性**: 每个测试独立运行
2. **可重复**: 测试结果一致
3. **清晰性**: 测试意图明确
4. **全面性**: 覆盖正常和异常情况
5. **并发安全**: 测试并发场景

## 持续集成

建议在 CI/CD 流程中:
1. 运行所有测试
2. 检查测试覆盖率 (>80%)
3. 运行基准测试
4. 检查竞态条件 (`go test -race`)
