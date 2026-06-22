# 技术设计文档：容灾数据存储系统

## 1. 架构概述

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          应用层 (Application Layer)                  │
│                     StorageClient / REST API                        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        存储管理层 (Storage Manager)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ DataSharder  │  │ ECManager    │  │ ReplicaManager│              │
│  │  (数据分片)    │  │ (纠删码管理)  │  │  (副本管理)    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         网络层 (Network Layer)                       │
│                 NodeManager / RPC / Heartbeat                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       存储节点层 (Storage Nodes)                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │ Node 1  │  │ Node 2  │  │ Node 3  │  │ Node N  │              │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 分层设计

| 层次 | 职责 | 主要组件 |
|------|------|----------|
| 应用层 | 对外接口 | StorageClient, REST API |
| 存储管理层 | 核心逻辑 | 分片、编码、副本管理 |
| 网络层 | 节点通信 | RPC、心跳、故障检测 |
| 存储节点层 | 数据持久化 | 本地存储引擎 |

## 2. 核心模块设计

### 2.1 纠删码模块 (EC Module)

#### 2.1.1 设计目标
- 实现Reed-Solomon编码
- 支持可配置的k(数据块)和m(校验块)
- 高性能的编解码

#### 2.1.2 有限域设计

**GF(2^8) 有限域**:
- 使用不可约多项式: x^8 + x^4 + x^3 + x^2 + 1 (0x11d)
- 预计算对数表和反对数表加速运算

```
┌────────────────────────────────────────┐
│         GF(2^8) 运算实现              │
├────────────────────────────────────────┤
│  加法: XOR                            │
│  乘法: 对数表查表                      │
│  除法: 对数表查表                      │
│  求逆: 对数表查表                      │
└────────────────────────────────────────┘
```

#### 2.1.3 编码矩阵

**生成矩阵 G**:
```
G = [I_k | P]

其中:
- I_k: k×k 单位矩阵
- P: k×m 校验矩阵
```

**范德蒙德矩阵**:
```
V(i,j) = α^(i*j)

其中 α 是GF(2^8)的本原元
```

#### 2.1.4 编码流程

```
输入数据 (D bytes)
       │
       ▼
┌──────────────────┐
│  数据分片         │
│  D → [d0,d1,...,dk-1] │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  矩阵乘法        │
│  [d0,...,dk-1] × G │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  输出分片         │
│  [s0,s1,...,sk+mk-1] │
└──────────────────┘
```

#### 2.1.5 解码流程

```
输入: k个可用分片 (任意组合)
       │
       ▼
┌──────────────────┐
│  构造解码矩阵     │
│  从G中选择对应行   │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  高斯消元求逆     │
│  D = S × G^(-1)  │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  重组原始数据     │
└──────────────────┘
```

### 2.2 数据分片模块 (Sharding Module)

#### 2.2.1 分片策略

```
┌─────────────────────────────────────────┐
│           分片流程                       │
├─────────────────────────────────────────┤
│ 1. 计算分片数量:                         │
│    num_shards = ceil(data_size / shard_size) │
│                                         │
│ 2. 分割数据:                            │
│    for i in range(num_shards):          │
│        shard[i] = data[i*ss : (i+1)*ss] │
│                                         │
│ 3. 处理最后一片:                         │
│    if len(last_shard) < shard_size:     │
│        pad with zeros                   │
└─────────────────────────────────────────┘
```

#### 2.2.2 分片元数据

```cpp
struct ShardInfo {
    std::string object_id;      // 所属对象ID
    uint32_t shard_index;       // 分片序号
    uint32_t total_shards;      // 总分片数
    uint64_t shard_size;        // 分片大小
    uint64_t original_size;     // 原始数据大小
    std::string checksum;       // 分片校验和
};
```

### 2.3 副本管理模块 (Replication Module)

#### 2.3.1 副本放置策略

**策略1: 随机放置**
```
优点: 简单，负载均衡
缺点: 可能不满足故障域隔离
```

**策略2: 故障域感知放置**
```
┌─────────────────────────────────────────┐
│         故障域层次结构                   │
├─────────────────────────────────────────┤
│ 机架 (Rack)                             │
│   └── 机箱 (Chassis)                    │
│        └── 节点 (Node)                   │
│             └── 磁盘 (Disk)              │
└─────────────────────────────────────────┘

放置原则:
- 副本分布在不同机架
- 尽量分散在不同故障域
```

#### 2.3.2 Quorum机制

**NWR模型**:
- N: 副本总数
- W: 写入确认数
- R: 读取确认数

**一致性保证**: W + R > N

```
示例: N=3, W=2, R=2
- 写入: 至少2个节点确认
- 读取: 至少2个节点响应
- 保证: 总能读到最新数据
```

### 2.4 故障检测模块 (Failure Detection)

#### 2.4.1 心跳机制

```
┌─────────────────────────────────────────┐
│           心跳检测流程                   │
├─────────────────────────────────────────┤
│ 协调器 (Coordinator)                    │
│   │                                     │
│   │  heartbeat_request                  │
│   ├──────────────────────────────────►  │
│   │                                     │ 节点
│   │  heartbeat_response                 │
│   ◄────────────────────────────────────┤
│   │                                     │
│   │  记录响应时间                        │
│   │  更新节点状态                        │
└─────────────────────────────────────────┘
```

#### 2.4.2 Phi Accrual Failure Detector

**算法原理**:
1. 统计心跳间隔的分布
2. 计算当前间隔的Phi值
3. Phi超过阈值则判定故障

```cpp
// Phi值计算
phi = -log10(1 - CDF(current_interval))

// CDF使用正态分布或指数分布
```

#### 2.4.3 节点状态机

```
┌─────────┐    heartbeat_ok    ┌─────────┐
│  ONLINE │◄──────────────────│ RECOVER │
└─────────┘                   └─────────┘
     │                             ▲
     │ timeout                     │
     ▼                             │
┌─────────┐    recovery_ok    ┌─────────┐
│SUSPECTED│──────────────────►│OFFLINE  │
└─────────┘                   └─────────┘
```

### 2.5 数据恢复模块 (Recovery Module)

#### 2.5.1 检测到数据丢失

```
┌─────────────────────────────────────────┐
│           数据丢失检测                   │
├─────────────────────────────────────────┤
│ 1. 节点故障检测                         │
│ 2. 查询该节点存储的分片列表              │
│ 3. 检查每个分片的副本数                  │
│ 4. 如果副本数 < 阈值，触发恢复          │
└─────────────────────────────────────────┘
```

#### 2.5.2 数据重建流程

```
┌─────────────────────────────────────────┐
│           数据重建流程                   │
├─────────────────────────────────────────┤
│ 1. 确定需要重建的分片                    │
│ 2. 从其他副本读取k个分片                │
│ 3. 使用纠删码解码                       │
│ 4. 重新编码生成缺失分片                 │
│ 5. 将分片写入新节点                     │
│ 6. 更新元数据                          │
└─────────────────────────────────────────┘
```

## 3. 数据结构设计

### 3.1 核心数据结构

```cpp
// 数据对象
struct Object {
    std::string id;                 // 对象ID
    uint64_t size;                  // 数据大小
    uint32_t version;               // 版本号
    std::string checksum;           // 整体校验和
    std::vector<ShardInfo> shards;  // 分片信息
    Timestamp create_time;          // 创建时间
    Timestamp update_time;          // 更新时间
};

// 分片信息
struct Shard {
    std::string id;                 // 分片ID
    std::string object_id;          // 所属对象
    uint32_t index;                 // 分片序号
    bool is_parity;                 // 是否校验块
    std::vector<uint8_t> data;      // 分片数据
    std::string checksum;           // 分片校验和
};

// 存储节点
struct StorageNode {
    std::string id;                 // 节点ID
    std::string address;            // 网络地址
    uint16_t port;                  // 端口
    NodeStatus status;              // 节点状态
    uint64_t capacity;              // 总容量
    uint64_t used;                  // 已用容量
    Timestamp last_heartbeat;       // 最后心跳时间
    std::vector<std::string> shards;// 存储的分片列表
};

// 副本信息
struct Replica {
    std::string shard_id;           // 分片ID
    std::string node_id;            // 节点ID
    ReplicaStatus status;           // 副本状态
    Timestamp last_verify;          // 最后验证时间
};
```

### 3.2 元数据存储

```cpp
// 元数据管理器
class MetadataManager {
    // 对象索引: object_id -> Object
    std::unordered_map<std::string, Object> objects_;

    // 分片索引: shard_id -> Shard
    std::unordered_map<std::string, Shard> shards_;

    // 节点索引: node_id -> StorageNode
    std::unordered_map<std::string, StorageNode> nodes_;

    // 副本索引: shard_id -> [Replica]
    std::unordered_map<std::string, std::vector<Replica>> replicas_;
};
```

## 4. 接口设计

### 4.1 客户端API

```cpp
class StorageClient {
public:
    // 初始化客户端
    Status init(const ClientConfig& config);

    // 写入数据
    Status put(const std::string& key,
               const void* data,
               size_t size);

    // 读取数据
    Status get(const std::string& key,
               std::vector<uint8_t>& data);

    // 删除数据
    Status remove(const std::string& key);

    // 查询数据信息
    Status stat(const std::string& key,
                ObjectInfo& info);

    // 列出所有对象
    Status list(std::vector<std::string>& keys);
};
```

### 4.2 存储节点接口

```cpp
class StorageNodeService {
public:
    // 存储分片
    virtual Status storeShard(const Shard& shard) = 0;

    // 读取分片
    virtual Status readShard(const std::string& shard_id,
                             Shard& shard) = 0;

    // 删除分片
    virtual Status deleteShard(const std::string& shard_id) = 0;

    // 心跳响应
    virtual Status heartbeat(NodeStatus& status) = 0;

    // 获取节点信息
    virtual Status getNodeInfo(NodeInfo& info) = 0;
};
```

### 4.3 纠删码接口

```cpp
class ErasureCodec {
public:
    // 初始化编解码器
    Status init(int data_shards, int parity_shards);

    // 编码数据
    Status encode(const uint8_t* data,
                  size_t size,
                  std::vector<std::vector<uint8_t>>& shards);

    // 解码数据
    Status decode(const std::vector<std::vector<uint8_t>>& shards,
                  const std::vector<bool>& shard_available,
                  std::vector<uint8_t>& data);

    // 获取分片大小
    size_t getShardSize(size_t data_size) const;
};
```

## 5. 核心流程设计

### 5.1 写入流程

```
Client                StorageManager          Node1    Node2    Node3
   │                        │                   │        │        │
   │    put(key, data)      │                   │        │        │
   ├───────────────────────►│                   │        │        │
   │                        │                   │        │        │
   │                        │  1. 分片数据       │        │        │
   │                        │───────────┐       │        │        │
   │                        │◄──────────┘       │        │        │
   │                        │                   │        │        │
   │                        │  2. 纠删码编码     │        │        │
   │                        │───────────┐       │        │        │
   │                        │◄──────────┘       │        │        │
   │                        │                   │        │        │
   │                        │  3. 选择节点       │        │        │
   │                        │───────────┐       │        │        │
   │                        │◄──────────┘       │        │        │
   │                        │                   │        │        │
   │                        │  4. 并行写入       │        │        │
   │                        ├──────────────────►│        │        │
   │                        ├──────────────────────────►│        │
   │                        ├────────────────────────────────►│
   │                        │                   │        │        │
   │                        │  5. 等待确认       │        │        │
   │                        │◄──────────────────┤        │        │
   │                        │◄───────────────────────────┤        │
   │                        │◄────────────────────────────────┤
   │                        │                   │        │        │
   │     write_ok           │                   │        │        │
   │◄───────────────────────┤                   │        │        │
```

### 5.2 读取流程

```
Client                StorageManager          Node1    Node2    Node3
   │                        │                   │        │        │
   │      get(key)          │                   │        │        │
   ├───────────────────────►│                   │        │        │
   │                        │                   │        │        │
   │                        │  1. 查询元数据     │        │        │
   │                        │───────────┐       │        │        │
   │                        │◄──────────┘       │        │        │
   │                        │                   │        │        │
   │                        │  2. 并行读取       │        │        │
   │                        ├──────────────────►│        │        │
   │                        ├──────────────────────────►│        │
   │                        ├────────────────────────────────►│
   │                        │                   │        │        │
   │                        │  3. 收集响应       │        │        │
   │                        │◄──────────────────┤        │        │
   │                        │◄───────────────────────────┤        │
   │                        │◄────────────────────────────────┤
   │                        │                   │        │        │
   │                        │  4. 纠删码解码     │        │        │
   │                        │───────────┐       │        │        │
   │                        │◄──────────┘       │        │        │
   │                        │                   │        │        │
   │       data             │                   │        │        │
   │◄───────────────────────┤                   │        │        │
```

### 5.3 故障检测流程

```
Coordinator              Node1           Node2           Node3
    │                      │               │               │
    │  heartbeat_request   │               │               │
    ├─────────────────────►│               │               │
    │                      │               │               │
    │  heartbeat_response  │               │               │
    │◄─────────────────────┤               │               │
    │                      │               │               │
    │  heartbeat_request   │               │               │
    ├──────────────────────────────────────►               │
    │                      │               │               │
    │  heartbeat_response  │               │               │
    │◄──────────────────────────────────────┤               │
    │                      │               │               │
    │  heartbeat_request   │               │               │
    ├───────────────────────────────────────────────────────►
    │                      │               │               │
    │        timeout       │               │               │
    │                      │               │               │
    │  mark Node3 as SUSPECTED             │               │
    │                      │               │               │
    │  retry heartbeat     │               │               │
    ├───────────────────────────────────────────────────────►
    │                      │               │               │
    │        timeout       │               │               │
    │                      │               │               │
    │  mark Node3 as OFFLINE               │               │
    │                      │               │               │
    │  trigger recovery    │               │               │
```

## 6. 关键算法设计

### 6.1 GF(2^8) 乘法算法

```cpp
// 使用对数表加速
uint8_t gf_multiply(uint8_t a, uint8_t b) {
    if (a == 0 || b == 0) return 0;
    int log_sum = gf_log[a] + gf_log[b];
    if (log_sum >= 255) log_sum -= 255;
    return gf_exp[log_sum];
}
```

### 6.2 高斯消元求逆矩阵

```cpp
// 求解 Ax = b
std::vector<uint8_t> gaussian_elimination(
    Matrix A, std::vector<uint8_t> b) {
    int n = A.rows();

    // 前向消元
    for (int i = 0; i < n; i++) {
        // 选主元
        int pivot = i;
        for (int j = i + 1; j < n; j++) {
            if (A[j][i] != 0) {
                pivot = j;
                break;
            }
        }
        std::swap(A[i], A[pivot]);
        std::swap(b[i], b[pivot]);

        // 消元
        for (int j = i + 1; j < n; j++) {
            uint8_t factor = gf_divide(A[j][i], A[i][i]);
            for (int k = i; k < n; k++) {
                A[j][k] ^= gf_multiply(factor, A[i][k]);
            }
            b[j] ^= gf_multiply(factor, b[i]);
        }
    }

    // 回代
    std::vector<uint8_t> x(n);
    for (int i = n - 1; i >= 0; i--) {
        uint8_t sum = b[i];
        for (int j = i + 1; j < n; j++) {
            sum ^= gf_multiply(A[i][j], x[j]);
        }
        x[i] = gf_divide(sum, A[i][i]);
    }
    return x;
}
```

### 6.3 节点选择算法

```cpp
// 考虑故障域的节点选择
std::vector<NodeId> select_nodes(
    const std::vector<Node>& available_nodes,
    int replica_count,
    const FaultDomainMap& fault_domains) {

    std::vector<NodeId> selected;
    std::set<FaultDomain> used_domains;

    // 按容量排序
    auto sorted = sort_by_capacity(available_nodes);

    for (const auto& node : sorted) {
        if (selected.size() >= replica_count) break;

        // 检查故障域是否已使用
        auto domain = fault_domains.get_domain(node.id);
        if (used_domains.find(domain) == used_domains.end()) {
            selected.push_back(node.id);
            used_domains.insert(domain);
        }
    }

    // 如果故障域不够，放宽约束
    if (selected.size() < replica_count) {
        for (const auto& node : sorted) {
            if (selected.size() >= replica_count) break;
            if (std::find(selected.begin(), selected.end(), node.id)
                == selected.end()) {
                selected.push_back(node.id);
            }
        }
    }

    return selected;
}
```

## 7. 配置设计

### 7.1 系统配置

```yaml
# 存储系统配置
storage:
  # 纠删码配置
  erasure_coding:
    data_shards: 4          # 数据分片数
    parity_shards: 2        # 校验分片数
    shard_size: 65536       # 分片大小 (64KB)

  # 副本配置
  replication:
    factor: 3               # 副本因子
    write_quorum: 2         # 写入Quorum
    read_quorum: 2          # 读取Quorum

  # 故障检测配置
  failure_detection:
    heartbeat_interval: 5000    # 心跳间隔 (ms)
    heartbeat_timeout: 15000    # 心跳超时 (ms)
    suspect_timeout: 30000      # 怀疑超时 (ms)

  # 恢复配置
  recovery:
    auto_recovery: true         # 自动恢复
    recovery_parallelism: 3     # 恢复并行度
```

## 8. 性能优化设计

### 8.1 编码优化
- 使用查表法替代实时计算
- SIMD指令加速矩阵运算
- 并行编码多个分片

### 8.2 网络优化
- 批量传输减少RTT
- 数据压缩
- 连接池复用

### 8.3 存储优化
- 顺序写入
- 内存映射文件
- 异步IO

## 9. 扩展性设计

### 9.1 插件化架构
```
┌─────────────────────────────────────┐
│           Plugin Manager            │
├─────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐         │
│  │ EC      │  │ Storage │         │
│  │ Plugin  │  │ Plugin  │         │
│  └─────────┘  └─────────┘         │
└─────────────────────────────────────┘
```

### 9.2 动态配置
- 运行时修改配置
- 热更新纠删码参数
- 动态调整副本数

---

*本设计文档将随着开发进展持续更新*
