# 03 - 实现文档: 分布式哈希表 DHT

## 实现概述

本文档详细描述 DHT 项目的核心实现细节。

## 1. 哈希函数实现

### SHA-1 哈希

```go
func DefaultHash(key string) *big.Int {
    hash := sha1.New()
    hash.Write([]byte(key))
    hashBytes := hash.Sum(nil)
    return new(big.Int).SetBytes(hashBytes)
}
```

**特点**:
- 输出 160 位哈希值
- 使用 `math/big.Int` 处理大数
- 确定性输出

### XOR 距离计算

```go
func XOR(a, b *big.Int) *big.Int {
    return new(big.Int).Xor(a, b)
}
```

**特点**:
- 对称性: XOR(a,b) = XOR(b,a)
- 自反性: XOR(a,a) = 0
- 高效位运算

## 2. Chord 协议实现

### Finger Table 实现

```go
type FingerEntry struct {
    Start *big.Int
    Node  *NodeID
}

// 初始化 Finger Table
for i := 0; i < M; i++ {
    start := new(big.Int).Add(node.ID, PowerOfTwo(i))
    start.Mod(start, PowerOfTwo(M))
    node.FingerTable[i] = FingerEntry{
        Start: start,
        Node:  nil,
    }
}
```

### FindSuccessor 算法

```go
func (n *Node) FindSuccessor(id *big.Int) *NodeID {
    // 如果 successor 为空，返回自身
    if n.Successor == nil {
        return &NodeID{ID: n.ID, Addr: n.Addr}
    }

    // 检查 id 是否在 (n, successor] 之间
    if BetweenRightInclusive(id, n.ID, n.Successor.ID) {
        return n.Successor
    }

    // 找到最近的前驱节点
    closest := n.closestPrecedingFinger(id)
    if closest == nil {
        return n.Successor
    }

    return closest
}
```

### 节点加入实现

```go
func (n *Node) Join(existing *NodeID) error {
    if existing == nil {
        // 第一个节点
        n.Successor = &NodeID{ID: n.ID, Addr: n.Addr}
        n.Predecessor = &NodeID{ID: n.ID, Addr: n.Addr}
        return nil
    }

    // 通过现有节点查找后继
    // 实际实现中需要网络调用
    return nil
}
```

## 3. Kademlia 协议实现

### K-桶实现

```go
type KBucket struct {
    contacts []*Contact
}

func (kb *KBucket) AddContact(contact *Contact) bool {
    // 检查是否已存在
    for i, c := range kb.contacts {
        if c.ID.Cmp(contact.ID) == 0 {
            // 移到末尾（最近使用）
            kb.contacts = append(kb.contacts[:i], kb.contacts[i+1:]...)
            kb.contacts = append(kb.contacts, contact)
            return true
        }
    }

    // 如果桶满，移除最旧的
    if len(kb.contacts) >= K {
        kb.contacts = kb.contacts[1:]
    }

    kb.contacts = append(kb.contacts, contact)
    return true
}
```

### 路由表实现

```go
type RoutingTable struct {
    localID   *big.Int
    buckets   [160]*KBucket
}

func (rt *RoutingTable) FindClosestContacts(target *big.Int, count int) []*Contact {
    // 收集所有联系人
    var allContacts []*Contact
    for _, bucket := range rt.buckets {
        allContacts = append(allContacts, bucket.GetContacts()...)
    }

    // 按 XOR 距离排序
    sort.Slice(allContacts, func(i, j int) bool {
        distI := XOR(allContacts[i].ID, target)
        distJ := XOR(allContacts[j].ID, target)
        return distI.Cmp(distJ) < 0
    })

    // 返回前 count 个
    if count > len(allContacts) {
        count = len(allContacts)
    }
    return allContacts[:count]
}
```

### FIND_NODE 实现

```go
func (kn *KademliaNode) FindNode(target *big.Int) []*Contact {
    return kn.RT.FindClosestContacts(target, K)
}
```

### FIND_VALUE 实现

```go
func (kn *KademliaNode) FindValue(key string) (string, []*Contact, bool) {
    // 本地查找
    if val, ok := kn.storage[key]; ok {
        return val, nil, true
    }

    // 返回最近节点
    keyID := kn.hashFunc(key)
    contacts := kn.RT.FindClosestContacts(keyID, K)
    return "", contacts, false
}
```

## 4. 网络层实现

### HTTP 服务器

```go
func (nn *NetworkNode) Start() error {
    mux := http.NewServeMux()
    mux.HandleFunc("/ping", nn.handlePing)
    mux.HandleFunc("/store", nn.handleStore)
    mux.HandleFunc("/find_node", nn.handleFindNode)
    mux.HandleFunc("/find_value", nn.handleFindValue)

    nn.httpServer = &http.Server{
        Addr:    nn.node.Addr,
        Handler: mux,
    }

    go nn.httpServer.ListenAndServe()
    return nil
}
```

### 消息处理

```go
func (nn *NetworkNode) handleFindNode(w http.ResponseWriter, r *http.Request) {
    var msg Message
    json.NewDecoder(r.Body).Decode(&msg)

    // 解析目标 ID
    targetID, _ := new(big.Int).SetString(msg.TargetID, 16)

    // 查找最近节点
    contacts := nn.node.FindNode(targetID)

    // 返回结果
    resp := Message{
        Type:     MsgFindNodeResp,
        Contacts: contactsToInfo(contacts),
    }
    json.NewEncoder(w).Encode(resp)
}
```

## 5. 迭代查找实现

### Kademlia 迭代查找

```go
func (nn *NetworkNode) KademliaIterativeFindNode(targetID *big.Int) []*Contact {
    closest := nn.node.FindNode(targetID)
    queried := make(map[string]bool)

    for i := 0; i < Alpha; i++ {
        var newClosest []*Contact
        for _, c := range closest {
            if queried[c.Addr] {
                continue
            }
            queried[c.Addr] = true

            contacts, err := nn.RemoteFindNode(c.Addr, targetID)
            if err != nil {
                continue
            }

            newClosest = append(newClosest, contacts...)
        }

        // 合并并排序
        closest = append(closest, newClosest...)
        sort.Slice(closest, func(i, j int) bool {
            distI := XOR(closest[i].ID, targetID)
            distJ := XOR(closest[j].ID, targetID)
            return distI.Cmp(distJ) < 0
        })

        if len(closest) > K {
            closest = closest[:K]
        }
    }

    return closest
}
```

## 6. 节点发现实现

### Bootstrap 实现

```go
func (d *Discovery) Bootstrap() error {
    for _, addr := range d.config.BootstrapAddrs {
        // Ping 引导节点
        if err := d.node.Ping(addr); err != nil {
            continue
        }

        // 查找接近自己的节点
        contacts, err := d.node.RemoteFindNode(addr, d.node.GetID())
        if err != nil {
            continue
        }

        // 添加到路由表
        for _, c := range contacts {
            d.node.node.RT.AddContact(c)
        }
    }
    return nil
}
```

### 定期刷新

```go
func (d *Discovery) refreshLoop() {
    ticker := time.NewTicker(d.config.RefreshInterval)
    for {
        select {
        case <-d.stopCh:
            return
        case <-ticker.C:
            d.refreshBuckets()
        }
    }
}
```

## 7. P2P 文件共享实现

### 文件共享

```go
func (p2p *P2PNetwork) ShareFile(filePath string) (*FileInfo, error) {
    // 计算文件哈希
    hash := sha1.New()
    io.Copy(hash, file)
    hashStr := fmt.Sprintf("%x", hash.Sum(nil))

    // 复制文件到共享目录
    copyFile(filePath, destPath)

    // 存储元数据到 DHT
    metadata := fmt.Sprintf("%s|%s|%d|%s", hash, name, size, uploader)
    p2p.node.KademliaStore("file:"+hashStr, metadata)

    return info, nil
}
```

## 8. 分布式存储实现

### 带 TTL 的存储

```go
func (ds *DistributedStorage) Put(key, value string, ttl int64) error {
    item := &StorageItem{
        Key:       key,
        Value:     value,
        CreatedAt: time.Now(),
        TTL:       ttl,
    }
    ds.items[key] = item

    // 存储到 DHT
    return ds.node.KademliaStore(key, value)
}
```

### 过期清理

```go
func (ds *DistributedStorage) Cleanup() int {
    removed := 0
    for key, item := range ds.items {
        if item.TTL > 0 && time.Since(item.CreatedAt).Seconds() > float64(item.TTL) {
            delete(ds.items, key)
            removed++
        }
    }
    return removed
}
```

## 并发控制

### 读写锁使用

```go
type Node struct {
    mu sync.RWMutex
    // ...
}

func (n *Node) Get(key string) (string, bool) {
    n.mu.RLock()
    defer n.mu.RUnlock()
    return n.storage[key]
}

func (n *Node) Store(key, value string) {
    n.mu.Lock()
    defer n.mu.Unlock()
    n.storage[key] = value
}
```

## 错误处理

### 网络错误处理

```go
func (nn *NetworkNode) sendMessage(addr string, msg Message) (*Message, error) {
    client := &http.Client{Timeout: 5 * time.Second}
    resp, err := client.Post(url, "application/json", body)
    if err != nil {
        return nil, fmt.Errorf("failed to send message: %v", err)
    }
    defer resp.Body.Close()

    // 处理响应
    var response Message
    json.NewDecoder(resp.Body).Decode(&response)
    return &response, nil
}
```

## 性能优化

### 并发存储

```go
func (nn *NetworkNode) KademliaStore(key, value string) error {
    closest := nn.node.FindNode(keyID)

    var wg sync.WaitGroup
    for _, c := range closest {
        wg.Add(1)
        go func(addr string) {
            defer wg.Done()
            nn.RemoteStore(addr, key, value)
        }(c.Addr)
    }
    wg.Wait()

    return nil
}
```

## 已知限制

1. **单进程模拟**: 所有节点在同一进程，未实现真正的分布式部署
2. **简化网络**: 使用 HTTP 而非更高效的协议如 gRPC
3. **无持久化**: 数据存储在内存中，重启后丢失
4. **简化文件传输**: P2P 文件共享未实现真正的文件传输

## 未来改进

1. 实现真正的分布式部署
2. 添加数据持久化
3. 实现文件分片传输
4. 添加加密和认证机制
