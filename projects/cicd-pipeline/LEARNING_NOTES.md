# 学习笔记: CI/CD 流水线

## 学习目标回顾

本项目的学习目标：
1. 理解 CI/CD 的核心概念
2. 掌握流水线编排技术
3. 学会构建和部署自动化
4. 掌握环境管理和部署策略

## 核心收获

### 1. CI/CD 的本质

CI/CD 不仅仅是工具，而是一种**开发文化**和**工程实践**：

- **CI (持续集成)**: 频繁集成 + 自动验证 = 尽早发现问题
- **CD (持续交付/部署)**: 自动化部署 = 快速、可靠的发布

关键理解：CI/CD 的价值不在于工具本身，而在于它带来的**反馈循环加速**。

### 2. 流水线编排模式

通过实现 DAG 依赖模型，理解了三种编排模式：

```
串行: A → B → C        (简单，但慢)
并行: A → [B, C] → D   (快，但需处理依赖)
DAG:  复杂依赖关系      (最灵活)
```

**关键洞察**:
- 识别哪些阶段可以并行是性能优化的关键
- 依赖关系决定了执行顺序，必须正确建模
- 拓扑排序是检测循环依赖的经典算法

### 3. Go 并发模型的应用

Go 的 goroutine + channel 天然适合流水线并行执行：

```go
// 同组阶段并行执行
for _, stage := range group {
    wg.Add(1)
    go func(s Stage) {
        defer wg.Done()
        executeStage(s)
    }(stage)
}
wg.Wait()
```

**学到了**:
- WaitGroup 用于等待一组 goroutine 完成
- Mutex 保护共享状态（结果收集）
- Context 实现超时和取消传播

### 4. 接口设计的力量

Executor 接口的设计体现了**依赖倒置原则**：

```go
type Executor interface {
    Execute(ctx context.Context, command string, env map[string]string) (string, int, error)
}
```

- 引擎只依赖接口，不依赖具体实现
- 可以轻松添加新的执行后端（Docker, K8s, SSH 等）
- 测试时可以用 mock 替换

### 5. 配置即代码

使用 YAML 定义流水线的好处：
- **版本控制**: 配置与代码一起存储
- **可审计**: 变更历史清晰
- **可复现**: 相同配置产生相同行为
- **可审查**: PR 中可以审查流水线变更

### 6. 错误处理策略

实现了多层错误处理：
1. **任务级**: 重试机制
2. **阶段级**: 失败终止，不执行后续任务
3. **流水线级**: 依赖失败自动跳过下游
4. **系统级**: 超时和取消支持

### 7. 触发机制设计

实现了三种触发方式：

**Git Push 触发**:
- 监听代码推送事件
- 支持分支过滤（精确匹配 + 通配符）
- 支持路径过滤（只在特定文件变更时触发）

**定时触发**:
- 使用 Cron 表达式定义调度计划
- 适合夜间构建、定期回归测试

**手动触发**:
- 支持通过 CLI 或 API 手动启动
- 适合热修复部署、临时任务

**关键设计**:
```go
type TriggerConfig struct {
    Push     *PushTrigger // Git Push 触发
    Schedule string       // Cron 表达式
    Manual   bool         // 手动触发
}
```

### 8. 部署策略

理解了三种主流部署策略：

**滚动部署 (Rolling)**:
```
逐步替换旧版本实例
[v1] [v1] [v1] [v1]
  ↓
[v2] [v1] [v1] [v1]
[v2] [v2] [v1] [v1]
[v2] [v2] [v2] [v1]
[v2] [v2] [v2] [v2]
优点: 零停机，风险低
缺点: 部署慢，新旧版本共存
```

**蓝绿部署 (Blue-Green)**:
```
维护两套完整环境
蓝环境: [v1] ← 当前流量
绿环境: [v2] ← 部署新版本
切换: 流量从蓝切到绿
优点: 快速切换，快速回滚
缺点: 资源占用翻倍
```

**金丝雀部署 (Canary)**:
```
逐步扩大新版本流量比例
10% → [v2]  90% → [v1]
50% → [v2]  50% → [v1]
100% → [v2]
优点: 风险可控，可观察
缺点: 实现复杂
```

### 9. 回滚机制

版本快照 + 历史管理的设计：

```go
type RollbackManager struct {
    maxVersions int
    snapshots   map[string][]*Snapshot
}

// 保存快照
func (rm *RollbackManager) SaveSnapshot(envName, version string)

// 获取上一个版本
func (rm *RollbackManager) GetPreviousVersion(envName string) (string, error)
```

**关键洞察**:
- 每次部署前保存当前版本快照
- 保留 N 个历史版本，自动清理旧版本
- 回滚就是重新部署上一个版本
- 回滚操作也需要健康检查

## 技术细节

### 拓扑排序算法

```go
// BFS 实现拓扑排序
// 1. 计算每个节点的入度
// 2. 将入度为 0 的节点加入队列
// 3. BFS 遍历，减少后继节点入度
// 4. 入度变为 0 时加入队列
// 5. 访问节点数 != 总节点数 → 有环
```

时间复杂度: O(V + E)，其中 V 是节点数，E 是边数。

### Context 的使用

```go
// 创建带超时的上下文
ctx, cancel := context.WithTimeout(parentCtx, 30*time.Second)
defer cancel()

// 在执行器中检查上下文
select {
case <-ctx.Done():
    return "", -1, ctx.Err()
default:
    // 继续执行
}
```

### 并发安全

```go
var mu sync.Mutex

// 在 goroutine 中安全写入结果
mu.Lock()
results = append(results, result)
mu.Unlock()
```

## 实际应用思考

### 如何在真实项目中应用

1. **代码提交触发**: 集成 Git webhook
2. **构建产物管理**: 上传到制品仓库
3. **多环境部署**: dev → staging → production
4. **通知机制**: Slack/邮件/钉钉通知
5. **回滚机制**: 部署失败自动回滚

### 完整 CI/CD 流程

```
代码提交
  ↓
[Git Push 触发]
  ↓
代码检出 → 依赖安装 → 代码编译
  ↓
单元测试 → 集成测试 → 代码覆盖率
  ↓
代码质量检查 → 安全扫描
  ↓
构建 Docker 镜像
  ↓
部署到预发布 → 冒烟测试
  ↓
部署到生产（金丝雀）
  ↓
健康检查 → 通知团队
```

### 与主流工具对比

| 特性 | 本项目 | GitHub Actions | Jenkins |
|------|--------|----------------|---------|
| 配置 | YAML | YAML | Groovy/UI |
| 并行 | 支持 | 支持 | 支持 |
| 容器 | Docker | Docker | Docker/K8s |
| 触发 | Push/定时/手动 | Push/定时/手动 | 多种 |
| 部署 | 滚动/蓝绿/金丝雀 | 需插件 | 需插件 |
| 回滚 | 内置 | 需脚本 | 需插件 |
| 生态 | 学习级 | 完整 | 完整 |
| 复杂度 | 低 | 中 | 高 |

## 进一步学习方向

1. **GitOps**: 声明式基础设施管理
2. **Kubernetes 部署**: 容器编排与部署
3. **监控与可观测性**: Prometheus, Grafana
4. **安全扫描**: SAST, DAST, 依赖漏洞扫描
5. **性能测试**: 负载测试集成到流水线
6. **制品管理**: 制品仓库集成
7. **审批流程**: 人工审批节点

## 项目复盘

### 做得好的地方
- 清晰的模块划分（pipeline, executor, deploy, trigger, reporter）
- 接口设计便于扩展
- 完整的测试覆盖
- 良好的错误处理
- 支持多种部署策略
- 内置回滚机制

### 可以改进的地方
- 添加日志系统
- 实现制品管理
- 添加 Web UI
- 支持更多执行后端（K8s, SSH）
- 添加通知集成（Slack, 钉钉）
- 支持审批流程

## 总结

通过实现这个 CI/CD 流水线项目，深入理解了：
1. CI/CD 的核心原理和价值
2. DAG 依赖图的建模和算法
3. Go 并发编程的实际应用
4. 接口驱动的设计思想
5. 自动化测试的重要性
6. 触发机制的设计
7. 部署策略的选择和实现
8. 回滚机制的重要性

这些知识不仅适用于 CI/CD，也是通用的软件工程技能。
