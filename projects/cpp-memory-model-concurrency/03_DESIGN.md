# 技术设计：C++ 内存模型和并发

## 文件组织

```
cpp-memory-model-concurrency/
├── CMakeLists.txt              # 构建配置
├── README.md                   # 项目文档
├── 01_RESEARCH.md              # 市场调研
├── 02_REQUIREMENTS.md          # 需求分析
├── 03_DESIGN.md                # 技术设计
├── 04_PRODUCT.md               # 产品思考
├── 05_DEVELOPMENT.md           # 开发手册
├── include/
│   └── utils/
│       ├── timer.hpp           # 计时工具
│       └── thread_safe_cout.hpp # 线程安全输出
└── src/
    ├── 01_memory_model/        # 内存模型基础
    ├── 02_memory_order/        # 内存序
    ├── 03_atomic/              # 原子操作
    ├── 04_concurrent_data_structures/ # 并发数据结构
    ├── 05_thread_synchronization/     # 线程同步
    ├── 06_concurrent_patterns/        # 并发模式
    └── 07_performance/                # 性能和调试
```

## 示例设计原则

### 1. 独立性
每个 .cpp 文件都是独立的可执行程序，可以单独编译运行。

### 2. 渐进性
示例从简单到复杂，逐步引入新概念。

### 3. 实用性
每个示例解决一个实际问题，而非抽象演示。

### 4. 可验证性
包含输出验证和断言检查，确保正确性。

## 核心数据结构设计

### 无锁栈 (Treiber Stack)
```cpp
template<typename T>
class LockFreeStack {
    struct Node {
        T data;
        Node* next;
    };
    std::atomic<Node*> head_{nullptr};
public:
    void push(const T& data);
    std::optional<T> pop();
};
```

### 无锁队列 (Michael-Scott Queue)
```cpp
template<typename T>
class LockFreeQueue {
    struct Node {
        std::shared_ptr<T> data;
        std::atomic<Node*> next;
    };
    std::atomic<Node*> head_;
    std::atomic<Node*> tail_;
public:
    void enqueue(T data);
    std::shared_ptr<T> dequeue();
};
```

### 并发哈希表
```cpp
template<typename K, typename V>
class ConcurrentHashMap {
    struct Bucket {
        std::shared_mutex mutex;
        std::list<std::pair<K, V>> entries;
    };
    std::vector<Bucket> buckets_;
    size_t bucket_count_;
public:
    void insert(const K& key, const V& value);
    std::optional<V> find(const K& key);
    bool erase(const K& key);
};
```

### 线程池
```cpp
class ThreadPool {
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex mutex_;
    std::condition_variable cv_;
    std::atomic<bool> stop_{false};
public:
    explicit ThreadPool(size_t threads);
    ~ThreadPool();
    template<typename F>
    auto submit(F&& f) -> std::future<decltype(f())>;
};
```

## 内存序选择指南

| 场景 | 推荐内存序 | 原因 |
|------|-----------|------|
| 计数器 | relaxed | 只需原子性，不需顺序 |
| 标志位 | release/acquire | 需要同步数据 |
| 锁实现 | acq_rel | 既获取又释放 |
| 全局顺序 | seq_cst | 需要全局一致顺序 |
| 单向屏障 | release 或 acquire | 只需单向同步 |

## 线程安全保证

### 基本保证
- 所有原子操作本身是线程安全的
- 标准库容器不是线程安全的

### 强保证
- 无锁数据结构提供无锁保证
- 互斥量提供互斥访问保证

### 无等待保证
- 无等待数据结构保证有限步骤完成
- 本项目中的无锁结构不保证无等待
