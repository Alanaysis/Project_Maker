# 学习笔记

## 项目信息

- **项目名称**: HPC Task Scheduler
- **学习周期**: ____年__月__日 至 ____年__月__日
- **学习目标**: 理解任务调度算法、资源管理、容错机制

## 1. 学习目标检查清单

### 1.1 调度算法
- [ ] 理解 FIFO 调度算法的原理和实现
- [ ] 理解优先级调度算法的原理和实现
- [ ] 理解公平调度算法的原理和实现
- [ ] 能够对比不同算法的优缺点
- [ ] 能够根据场景选择合适的算法

### 1.2 资源管理
- [ ] 理解资源分配的基本原理
- [ ] 掌握原子性分配的实现方法
- [ ] 理解资源碎片问题
- [ ] 了解 cgroups 资源隔离技术
- [ ] 能够实现基本的资源管理器

### 1.3 并发控制
- [ ] 理解 Go 的并发模型（goroutine、channel）
- [ ] 掌握 sync.Mutex 和 sync.RWMutex 的使用
- [ ] 理解竞态条件和 race detector
- [ ] 能够编写并发安全的代码
- [ ] 理解 context 包的使用

### 1.4 容错机制
- [ ] 理解任务重试的原理和实现
- [ ] 掌握超时控制的实现方法
- [ ] 了解故障检测和恢复机制
- [ ] 能够实现基本的容错逻辑

### 1.5 系统设计
- [ ] 理解模块化设计的原则
- [ ] 掌握接口抽象的方法
- [ ] 理解 RESTful API 设计
- [ ] 能够设计清晰的系统架构

## 2. 重点难点记录

### 2.1 ⭐ 资源管理的原子性

**问题描述**:
如何确保资源分配的原子性？要么全部分配成功，要么全部失败。

**解决方案**:
```go
func (rm *ResourceManager) Allocate(taskID string, req ResourceRequest) error {
    rm.mu.Lock()
    defer rm.mu.Unlock()

    // 先检查是否有足够资源
    if rm.usedCPU+req.CPU > rm.totalCPU {
        return fmt.Errorf("insufficient CPU")
    }
    if rm.usedMemoryMB+req.MemoryMB > rm.totalMemoryMB {
        return fmt.Errorf("insufficient memory")
    }

    // 再分配资源
    rm.usedCPU += req.CPU
    rm.usedMemoryMB += req.MemoryMB
    rm.allocations[taskID] = req

    return nil
}
```

**关键点**:
1. 使用互斥锁保护整个分配过程
2. 先检查再分配，保证原子性
3. 错误时返回，不修改任何状态

### 2.2 ⭐ 调度算法的可扩展性

**问题描述**:
如何设计调度算法，使其易于扩展？

**解决方案**:
使用接口抽象调度算法：
```go
type ScheduleAlgorithm interface {
    Sort(tasks []*models.Task)
    Name() string
}
```

**关键点**:
1. 定义清晰的接口
2. 每个算法独立实现
3. 在配置中选择算法
4. 易于添加新算法

### 2.3 ⭐ 并发安全的任务状态管理

**问题描述**:
多个 goroutine 可能同时修改任务状态，如何保证线程安全？

**解决方案**:
```go
type TaskManager struct {
    mu      sync.RWMutex
    tasks   map[string]*models.Task
    byState map[models.TaskState]map[string]bool
}

func (tm *TaskManager) UpdateTaskState(id string, newState TaskState) error {
    tm.mu.Lock()
    defer tm.mu.Unlock()

    task, ok := tm.tasks[id]
    if !ok {
        return fmt.Errorf("task not found")
    }

    oldState := task.State
    delete(tm.byState[oldState], id)
    task.State = newState
    tm.byState[newState][id] = true

    return nil
}
```

**关键点**:
1. 使用 sync.RWMutex 保护共享资源
2. 读操作使用 RLock()
3. 写操作使用 Lock()
4. 状态变更时同时更新索引

### 2.4 ⭐ 调度循环的实现

**问题描述**:
如何实现定时调度循环？

**解决方案**:
```go
func (s *Scheduler) scheduleLoop() {
    interval := time.Duration(s.cfg.IntervalMs) * time.Millisecond
    ticker := time.NewTicker(interval)
    defer ticker.Stop()

    for {
        select {
        case <-s.ctx.Done():
            return
        case <-ticker.C:
            s.schedule()
        }
    }
}
```

**关键点**:
1. 使用 time.Ticker 实现定时触发
2. 使用 context.Context 控制生命周期
3. select 监听多个 channel
4. 优雅退出机制

## 3. 值得思考的地方

### 3.1 💡 为什么需要状态索引？

**思考**:
任务管理器中使用了 `byState` 索引，按状态索引任务。为什么需要这个索引？

**答案**:
1. 快速按状态查询任务，避免遍历所有任务
2. 调度器需要快速获取待调度的任务
3. 监控系统需要统计各状态的任务数量
4. 提高查询效率，减少锁的持有时间

### 3.2 💡 如何处理资源碎片？

**思考**:
资源分配和释放后，可能会产生资源碎片。如何处理？

**答案**:
1. **当前方案**: 简单的分配和释放，不处理碎片
2. **改进方案**: 实现资源整理（defragmentation）
3. **高级方案**: 使用内存池或 slab 分配器
4. **权衡**: 简单方案适合学习，生产环境需要更复杂的策略

### 3.3 💡 调度算法如何影响系统性能？

**思考**:
不同的调度算法对系统性能有什么影响？

**答案**:
1. **FIFO**: 简单公平，但可能导致长任务阻塞短任务
2. **优先级**: 重要任务优先，但可能导致低优先级任务饥饿
3. **公平调度**: 保证公平性，但可能降低整体效率
4. **回填调度**: 提高利用率，但实现复杂

**权衡**: 需要根据具体场景选择合适的算法。

### 3.4 💡 如何扩展到分布式系统？

**思考**:
当前是单机版本，如何扩展到分布式系统？

**答案**:
1. **任务分发**: 将任务分发到多个 worker 节点
2. **资源同步**: 同步各节点的资源信息
3. **故障检测**: 检测节点故障并重新调度
4. **状态一致性**: 保证任务状态的一致性

**挑战**: 分布式系统的一致性、分区容错、可用性权衡（CAP 定理）

### 3.5 💡 为什么选择 Go 语言？

**思考**:
为什么选择 Go 语言实现 HPC 调度系统？

**答案**:
1. **并发模型**: goroutine + channel，适合并发编程
2. **性能**: 编译型语言，性能优秀
3. **标准库**: 丰富的标准库，减少依赖
4. **部署**: 单二进制文件，易于部署
5. **学习曲线**: 语法简单，易于学习

**对比**:
- C/C++: 性能更好，但开发效率低
- Python: 开发效率高，但性能差
- Java: 生态丰富，但部署复杂

## 4. 遇到的问题和解决方案

### 4.1 问题 1: 任务状态转换错误

**问题描述**:
任务从 completed 状态转换到 running 状态，应该报错但没有。

**原因分析**:
状态转换逻辑没有检查合法的状态转换。

**解决方案**:
```go
func (tm *TaskManager) MarkTaskRunning(id string) error {
    // ...
    if task.State != models.TaskStatePending && task.State != models.TaskStateQueued {
        return fmt.Errorf("task cannot transition from %s to running", task.State)
    }
    // ...
}
```

**经验教训**: 状态机需要严格的状态转换规则。

### 4.2 问题 2: 资源泄漏

**问题描述**:
任务失败后，占用的资源没有释放。

**原因分析**:
任务失败时没有调用资源释放逻辑。

**解决方案**:
```go
func (s *Scheduler) handleTaskFailure(task *models.Task, errMsg string) {
    // 释放资源
    s.rm.Release(task.ID)
    // ...
}
```

**经验教训**: 任何路径都需要释放资源。

### 4.3 问题 3: 并发竞态条件

**问题描述**:
多个 goroutine 同时修改任务状态，导致数据不一致。

**原因分析**:
没有使用锁保护共享资源。

**解决方案**:
使用 sync.RWMutex 保护所有共享资源的访问。

**经验教训**: 并发编程需要仔细考虑同步问题。

## 5. 学习资源记录

### 5.1 官方文档
- [ ] Go 官方文档: https://go.dev/doc/
- [ ] Go by Example: https://gobyexample.com/
- [ ] Slurm 文档: https://slurm.schedmd.com/

### 5.2 技术文章
- [ ] Go Concurrency Patterns: https://go.dev/blog/pipelines
- [ ] Kubernetes Scheduling: https://kubernetes.io/docs/concepts/scheduling-eviction/
- [ ] Linux cgroups: https://www.kernel.org/doc/Documentation/cgroup-v1/cgroups.txt

### 5.3 开源项目
- [ ] Slurm: https://github.com/SchedMD/slurm
- [ ] Kubernetes: https://github.com/kubernetes/kubernetes
- [ ] Mesos: https://github.com/apache/mesos

## 6. 后续学习计划

### 6.1 短期计划（1-2 周）
- [ ] 完善单元测试
- [ ] 实现真实的命令执行
- [ ] 添加 cgroups 资源隔离

### 6.2 中期计划（1-2 月）
- [ ] 实现分布式 worker 节点
- [ ] 添加任务依赖支持
- [ ] 实现资源预留机制

### 6.3 长期计划（3-6 月）
- [ ] 实现 Web UI
- [ ] 支持任务队列持久化
- [ ] 性能优化和压力测试

## 7. 学习总结

### 7.1 学到了什么
- ________________________________________________________________________
- ________________________________________________________________________
- ________________________________________________________________________

### 7.2 遇到了什么困难
- ________________________________________________________________________
- ________________________________________________________________________
- ________________________________________________________________________

### 7.3 如何解决的
- ________________________________________________________________________
- ________________________________________________________________________
- ________________________________________________________________________

### 7.4 下一步计划
- ________________________________________________________________________
- ________________________________________________________________________
- ________________________________________________________________________

## 8. 参考资料

### 8.1 书籍
- 《Go 程序设计语言》
- 《分布式系统：概念与设计》
- 《操作系统概念》

### 8.2 在线课程
- [ ] Coursera: Cloud Computing
- [ ] edX: Introduction to Cloud Computing
- [ ] Udacity: High Performance Computing

### 8.3 技术博客
- [ ] Go 官方博客
- [ ] Kubernetes 官方博客
- [ ] Slurm 官方文档

## 9. 代码审查清单

### 9.1 代码风格
- [ ] 命名规范
- [ ] 注释完整
- [ ] 代码格式化
- [ ] 无魔法数字

### 9.2 功能正确性
- [ ] 功能完整
- [ ] 边界条件处理
- [ ] 错误处理
- [ ] 并发安全

### 9.3 性能
- [ ] 无性能瓶颈
- [ ] 内存使用合理
- [ ] 锁的粒度合适
- [ ] 无资源泄漏

### 9.4 可维护性
- [ ] 模块化设计
- [ ] 接口抽象
- [ ] 代码复用
- [ ] 易于扩展

## 10. 版本记录

### v1.0.0 (____年__月__日)
- 初始版本
- 实现基本的任务调度功能
- 支持 FIFO、优先级、公平调度算法
- 实现基本的资源管理

---

**笔记完成日期**: ____年__月__日

**学习时长**: ____ 小时

**学习状态**: ____

**备注**:
________________________________________________________________________
________________________________________________________________________
________________________________________________________________________
