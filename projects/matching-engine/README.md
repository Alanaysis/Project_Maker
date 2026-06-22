# 高频交易引擎 (High-Frequency Trading Matching Engine)

## 学习目标

通过这个项目，你将掌握：
- [ ] 理解订单簿（Order Book）的核心结构和工作原理
- [ ] 掌握价格优先、时间优先的撮合算法
- [ ] 学会低延迟系统设计的基本优化技巧
- [ ] 理解限价单和市价单的处理逻辑
- [ ] 掌握 C++ 中高性能数据结构的选择和使用

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| C++17 | 主语言 | ⭐⭐⭐ |
| STL containers | 数据结构 | ⭐⭐ |
| CMake | 构建系统 | ⭐⭐ |
| Google Test | 单元测试 | ⭐⭐ |

## 重点难点

### 重点1：订单簿数据结构设计
**为什么重要**：订单簿是交易引擎的核心，决定了撮合效率
**关键代码**：`include/order_book.h`
**理解要点**：
- 使用 `std::map` 维护价格层级的有序性
- 每个价格层级使用 `std::list` 维护订单队列（FIFO）
- 买单按价格降序排列，卖单按价格升序排列

### 重点2：撮合算法实现
**为什么重要**：撮合是交易引擎的核心业务逻辑
**关键代码**：`src/matching_engine.cpp`
**理解要点**：
- 价格优先原则：更优价格的订单优先成交
- 时间优先原则：同一价格的订单按提交时间排序
- 市价单直接与最优对手价匹配

### 重点3：低延迟优化策略
**为什么重要**：高频交易对延迟极其敏感
**关键代码**：`include/types.h`
**理解要点**：
- 使用定点数（Fixed-Point）代替浮点数避免精度问题
- 使用纳秒级时间戳记录订单时间
- 避免不必要的内存分配和拷贝

## 值得思考

### 1. 为什么用 std::map 而不是 unordered_map？
**背景**：订单簿需要按价格有序遍历
**权衡**：map 提供 O(log n) 的有序访问，unordered_map 提供 O(1) 的随机访问
**结论**：撮合需要频繁访问最优价格，有序性比随机访问更重要

### 2. 为什么用定点数而不是浮点数？
**背景**：金融计算对精度要求极高
**权衡**：浮点数有精度误差，定点数需要手动管理小数位
**结论**：在高频交易中，精度是第一位的，定点数是更好的选择

### 3. 如何处理并发订单？
**背景**：实际交易系统需要处理大量并发请求
**权衡**：锁会增加延迟，无锁设计复杂度高
**结论**：本项目采用单线程设计，专注于核心算法学习

## 快速开始

### 环境要求
- C++17 兼容的编译器（GCC 7+, Clang 5+）
- CMake 3.14+
- Google Test（可选，用于运行测试）

### 编译

```bash
cd projects/matching-engine
mkdir build && cd build
cmake ..
make
```

### 运行示例

```bash
# 运行基础示例
./examples/basic_example

# 运行高级示例
./examples/advanced_example
```

### 运行测试

```bash
# 编译并运行测试
cd build
cmake -DBUILD_TESTS=ON ..
make
./tests/matching_engine_tests
```

## 项目结构

```
matching-engine/
├── CMakeLists.txt           # 构建配置
├── README.md                # 本文件
├── include/                 # 头文件
│   ├── types.h              # 基础类型定义
│   ├── order_book.h         # 订单簿
│   ├── matching_engine.h    # 撮合引擎
│   └── order_manager.h      # 订单管理器
├── src/                     # 源代码
│   ├── order_book.cpp       # 订单簿实现
│   ├── matching_engine.cpp  # 撮合引擎实现
│   └── order_manager.cpp    # 订单管理器实现
├── tests/                   # 测试
│   ├── test_order_book.cpp  # 订单簿测试
│   ├── test_matching_engine.cpp # 撮合引擎测试
│   └── test_main.cpp        # 测试入口
├── examples/                # 示例
│   ├── basic.cpp            # 基础示例
│   └── advanced.cpp         # 高级示例
├── docs/                    # 文档
│   ├── 01-RESEARCH.md       # 市场调研
│   ├── 02-REQUIREMENTS.md   # 需求分析
│   ├── 03-DESIGN.md         # 技术设计
│   ├── 04-PRODUCT.md        # 产品思维
│   └── 05-DEVELOPMENT.md    # 开发手册
└── LEARNING_NOTES.md        # 学习笔记
```

## 核心循环

```
订单提交 → 订单簿更新 → 撮合匹配 → 成交回报
```

## 学习路径

1. 阅读 [01-RESEARCH.md](docs/01-RESEARCH.md) 了解市场背景
2. 阅读 [02-REQUIREMENTS.md](docs/02-REQUIREMENTS.md) 理解需求
3. 阅读 [03-DESIGN.md](docs/03-DESIGN.md) 学习设计
4. 阅读 [04-PRODUCT.md](docs/04-PRODUCT.md) 理解产品思维
5. 阅读 [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) 开始开发
6. 运行 [examples/](examples/) 中的示例
7. 阅读源代码，重点关注 ⭐ 标记的部分
8. 完成 [LEARNING_NOTES.md](LEARNING_NOTES.md) 中的练习

## 相关资源

- [Investopedia - Order Book](https://www.investopedia.com/terms/o/order-book.asp)
- [Investopedia - Matching Engine](https://www.investopedia.com/terms/m/matching-engine.asp)
- [CppCon - Low Latency C++](https://www.youtube.com/results?search_query=cppcon+low+latency)

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)
