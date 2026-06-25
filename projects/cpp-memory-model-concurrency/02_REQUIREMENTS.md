# 需求分析：C++ 内存模型和并发

## 功能需求

### 1. 内存模型基础模块
- 展示内存位置的概念和对齐要求
- 演示对象模型和对象表示
- 解释值类别（左值、右值、将亡值）
- 演示对象生命周期管理

### 2. 内存序模块
- 对比五种内存序的行为差异
- 演示内存屏障的使用
- 展示不同内存序的性能差异
- 提供内存序选择指南

### 3. 原子操作模块
- std::atomic 基本用法
- atomic_flag 实现自旋锁
- C++20 原子智能指针
- C++20 原子浮点操作
- CAS 操作和 ABA 问题
- 原子操作性能基准测试

### 4. 并发数据结构模块
- 无锁栈（Treiber Stack）
- 无锁队列（Michael-Scott Queue）
- 无锁链表（Harris Linked List）
- 并发哈希表（分段锁）
- 读写锁实现

### 5. 线程同步模块
- mutex 类型对比
- 条件变量使用模式
- C++20 latch 使用场景
- C++20 barrier 使用场景
- C++20 counting_semaphore
- C++20 stop_token 协作取消

### 6. 并发模式模块
- 固定大小线程池
- 生产者-消费者队列
- 优先级任务调度器
- std::async 和 std::future
- 协程并发基础

### 7. 性能和调试模块
- 伪共享演示和解决方案
- 缓存行对齐技术
- 线程亲和性设置
- 并发调试技巧

## 知识点清单

### 内存模型
- [ ] 内存位置定义
- [ ] 对象存储和对齐
- [ ] 值类别（lvalue, rvalue, xvalue）
- [ ] 对象生命周期
- [ ] 存储期（自动、静态、线程、动态）

### 内存序
- [ ] memory_order_relaxed
- [ ] memory_order_acquire
- [ ] memory_order_release
- [ ] memory_order_acq_rel
- [ ] memory_order_seq_cst
- [ ] std::atomic_thread_fence
- [ ] std::atomic_signal_fence

### 原子操作
- [ ] std::atomic<T>
- [ ] load/store/exchange
- [ ] compare_exchange_weak/strong
- [ ] fetch_add/fetch_sub
- [ ] atomic_flag
- [ ] atomic_shared_ptr (C++20)
- [ ] atomic_ref (C++20)

### 并发数据结构
- [ ] Treiber Stack
- [ ] Michael-Scott Queue
- [ ] Harris Linked List
- [ ] 分段锁哈希表
- [ ] 读写锁

### 线程同步
- [ ] std::mutex
- [ ] std::recursive_mutex
- [ ] std::shared_mutex
- [ ] std::condition_variable
- [ ] std::latch
- [ ] std::barrier
- [ ] std::counting_semaphore
- [ ] std::stop_token

### 并发模式
- [ ] 线程池
- [ ] 生产者-消费者
- [ ] 任务调度器
- [ ] std::async/future
- [ ] 协程

### 性能优化
- [ ] 伪共享
- [ ] 缓存行对齐
- [ ] 线程亲和性
- [ ] 性能分析工具
