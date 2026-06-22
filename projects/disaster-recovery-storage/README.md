# 容灾数据存储系统 (Disaster Recovery Storage System)

## 项目概述

这是一个用于学习分布式存储系统核心原理的教学项目。通过从零实现一个具备容灾能力的存储系统，深入理解数据冗余、纠删码、跨数据中心复制和故障检测等关键技术。

## ⭐ 学习目标

### 核心知识点
1. **数据冗余原理** - 理解为什么需要冗余以及不同冗余策略的权衡
2. **纠删码(Erasure Coding)** - 掌握Reed-Solomon编码的数学原理和实现
3. **跨数据中心复制** - 学习数据在多个地理位置之间的一致性同步
4. **故障检测与恢复** - 理解心跳检测、故障转移和数据重建机制

### 技术栈学习难度
| 技术 | 难度 | 说明 |
|------|------|------|
| C++ | ⭐⭐⭐ | 需要掌握现代C++特性 |
| 纠删码算法 | ⭐⭐⭐⭐ | 涉及有限域数学 |
| 分布式协议 | ⭐⭐⭐⭐ | 一致性、容错性 |
| 网络编程 | ⭐⭐⭐ | TCP/UDP通信 |

## 技术栈

- **主语言**: C++17
- **构建系统**: CMake
- **测试框架**: Google Test
- **网络库**: 自实现（学习目的）
- **数学库**: 自实现有限域运算

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Client API                             │
├─────────────────────────────────────────────────────────────┤
│                    Storage Manager                          │
├──────────────┬──────────────┬───────────────────────────────┤
│  Data Shard  │  EC Encoder  │    Replication Manager        │
├──────────────┴──────────────┴───────────────────────────────┤
│                    Network Layer                            │
├──────────────┬──────────────┬───────────────────────────────┤
│   Node 1     │   Node 2     │   Node 3 ... N               │
└──────────────┴──────────────┴───────────────────────────────┘
```

## 核心流程

```
写入请求 → 数据分片 → 纠删码编码 → 多副本写入 → 确认返回
    │                                          │
    └────────────── 读取请求 ←─────────────────┘
                       ↓
              数据重组 → 解码 → 返回
```

## ⭐ 重点难点

### 1. 纠删码(Reed-Solomon)
**难点**: 需要理解有限域(Galois Field)的数学运算
**解决方案**: 从GF(2^8)开始，逐步理解编码矩阵和解码过程

### 2. 一致性保证
**难点**: 分布式环境下的数据一致性
**解决方案**: 实现简化的Quorum机制(NWR模型)

### 3. 故障检测
**难点**: 如何准确判断节点故障（避免误判）
**解决方案**: 使用心跳+Phi Accrual Failure Detector

### 4. 数据重建
**难点**: 部分数据丢失后的自动恢复
**解决方案**: 基于纠删码的增量修复

## 💡 值得思考的地方

1. **纠删码 vs 多副本**: 何时选择哪种策略？存储效率和性能如何权衡？
2. **CAP定理**: 在一致性、可用性和分区容错性之间如何选择？
3. **数据分片策略**: 如何设计才能最大化并行度？
4. **故障域隔离**: 如何确保同一故障不会同时影响多个副本？

## 项目结构

```
disaster-recovery-storage/
├── CMakeLists.txt
├── README.md
├── include/                  # 头文件
│   ├── storage/             # 存储核心
│   ├── ec/                  # 纠删码模块
│   ├── network/             # 网络层
│   └── utils/               # 工具类
├── src/                     # 源代码
│   ├── core/                # 核心实现
│   ├── ec/                  # 纠删码实现
│   ├── network/             # 网络实现
│   └── node/                # 存储节点
├── tests/                   # 单元测试
├── examples/                # 使用示例
└── docs/                    # 文档
```

## 快速开始

### 环境要求
- C++17 编译器 (GCC 7+ / Clang 6+)
- CMake 3.14+
- Google Test (自动下载)

### 编译运行
```bash
mkdir build && cd build
cmake ..
make -j$(nproc)
./tests/unit_tests
```

### 运行示例
```bash
./examples/basic_usage
```

## 参考资源

### 开源项目
- [Ceph](https://github.com/ceph/ceph) - 分布式存储系统
- [MinIO](https://github.com/minio/minio) - 对象存储
- [GlusterFS](https://github.com/gluster/glusterfs) - 分布式文件系统
- [TiKV](https://github.com/tikv/tikv) - 分布式KV存储(Rust)

### 学习资料
- [Erasure Coding Theory](https://www.cs.cmu.edu/~guyb/realworld/reedsolomon/reed_solomon_codes.html)
- [Reed-Solomon Interactive Demo](https://research.swtch.com/field)
- [Distributed Systems](https://www.distributed-systems.net/)

## 许可证

MIT License - 仅供学习使用
