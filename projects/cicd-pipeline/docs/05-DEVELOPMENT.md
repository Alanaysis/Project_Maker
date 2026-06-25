# 05 - 开发: CI/CD 流水线

## 开发环境

### 前置条件
- Go 1.21+
- Docker (可选，用于 Docker 执行器)
- Make (可选)

### 本地开发

```bash
# 克隆项目
cd projects/cicd-pipeline

# 安装依赖
go mod download

# 运行测试
go test ./...

# 编译
go build -o cicd ./cmd/cicd

# 运行示例
./cicd run -f examples/simple.yaml -v
./cicd run -f examples/full-pipeline.yaml -v
```

## 编译构建

### 本地编译
```bash
go build -o cicd ./cmd/cicd
```

### 交叉编译
```bash
# Linux
GOOS=linux GOARCH=amd64 go build -o cicd-linux ./cmd/cicd

# macOS
GOOS=darwin GOARCH=arm64 go build -o cicd-macos ./cmd/cicd

# Windows
GOOS=windows GOARCH=amd64 go build -o cicd.exe ./cmd/cicd
```

### Docker 构建
```bash
# 构建镜像
docker build -t cicd-pipeline .

# 运行
docker run --rm -v $(pwd)/examples:/app/examples cicd-pipeline run -f /app/examples/full-pipeline.yaml -v
```

## 使用方法

### CLI 命令

```bash
# 执行流水线
cicd run -f pipeline.yaml
cicd run -f pipeline.yaml -v      # 详细模式

# 校验配置
cicd validate -f pipeline.yaml

# 查看执行计划
cicd plan -f pipeline.yaml

# 显示帮助
cicd help
```

### 配置文件格式

#### 完整配置示例

```yaml
name: "生产级 CI/CD 流水线"

# 触发配置
trigger:
  push:
    branches: [main, develop, "release/*"]
    paths: ["src/**", "tests/**"]
  schedule: "0 2 * * *"
  manual: true

# 全局变量
variables:
  APP_NAME: "myapp"
  REGISTRY: "registry.example.com"
  GO_VERSION: "1.21"

stages:
  # 构建阶段
  - name: build
    tasks:
      - name: "代码检出"
        command: git clone https://github.com/user/repo.git
        timeout: 60

      - name: "依赖安装"
        command: go mod download
        timeout: 180

      - name: "代码编译"
        command: go build -o app ./cmd/app
        timeout: 300

  # 测试阶段
  - name: test
    depends_on: [build]
    tasks:
      - name: "单元测试"
        command: go test ./... -v
        timeout: 300

      - name: "集成测试"
        command: go test ./tests/integration/ -v
        timeout: 600

      - name: "代码覆盖率"
        command: go test ./... -coverprofile=coverage.out

  # 部署阶段
  - name: deploy
    depends_on: [test]
    deploy:
      strategy: rolling
      targets:
        - name: production
          url: "https://www.example.com"
          region: "us-east-1"
      rollback:
        enabled: true
        max_versions: 5
        health_check: 60
    tasks:
      - name: "部署到生产"
        command: ./deploy.sh
        env:
          ENV: production
```

### 任务配置选项

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | 是 | 任务名称 |
| command | string | 是 | 要执行的命令 |
| image | string | 否 | Docker 镜像（不填则本地执行）|
| env | map | 否 | 环境变量 |
| timeout | int | 否 | 超时秒数（0=不限）|
| retries | int | 否 | 失败重试次数 |

### 触发配置选项

| 字段 | 类型 | 说明 |
|------|------|------|
| push.branches | []string | 触发的分支列表 |
| push.paths | []string | 文件路径过滤 |
| schedule | string | Cron 表达式 |
| manual | bool | 是否允许手动触发 |

### 部署配置选项

| 字段 | 类型 | 说明 |
|------|------|------|
| strategy | string | 部署策略: rolling, blue-green, canary |
| targets.name | string | 目标名称 |
| targets.url | string | 目标 URL |
| targets.region | string | 区域 |
| targets.weight | int | 流量权重（金丝雀部署）|
| rollback.enabled | bool | 是否启用自动回滚 |
| rollback.max_versions | int | 保留的历史版本数 |
| rollback.health_check | int | 健康检查超时(秒) |

## 功能特性

### 1. 流水线定义
- YAML 配置文件
- 支持多阶段、多任务
- 环境变量配置
- 触发配置
- 部署配置

### 2. 阶段编排
- DAG 依赖模型
- 自动拓扑排序
- 循环依赖检测
- 并行阶段执行
- 依赖失败自动跳过

### 3. 任务执行
- 本地 Shell 执行
- Docker 容器执行
- 超时控制
- 失败重试

### 4. 触发机制
- Git Push 触发
- 定时触发（Cron）
- 手动触发
- 分支过滤
- 路径过滤

### 5. 部署管理
- 多环境管理
- 滚动部署
- 蓝绿部署
- 金丝雀部署
- 版本历史管理
- 自动回滚

### 6. 状态报告
- 实时执行进度
- 阶段和任务状态
- 执行时间统计
- 彩色 emoji 状态标记

## 扩展开发

### 添加新的执行器

```go
type K8sExecutor struct {
    KubeConfig string
}

func (e *K8sExecutor) Execute(ctx context.Context, command string, env map[string]string) (string, int, error) {
    // 在 Kubernetes Pod 中执行命令
    return output, exitCode, nil
}

func (e *K8sExecutor) Type() string {
    return "kubernetes"
}
```

### 添加新的部署策略

```go
func (d *Deployer) customDeploy(ctx context.Context, env *Environment, deployment *Deployment) error {
    // 实现自定义部署策略
    // 1. 准备部署环境
    // 2. 上传制品
    // 3. 执行部署
    // 4. 健康检查
    return nil
}
```

### 添加新的报告格式

```go
type JSONReporter struct {
    output io.Writer
}

func (r *JSONReporter) OnPipelineStart(name string) {
    json.NewEncoder(r.output).Encode(map[string]interface{}{
        "event": "pipeline_start",
        "name": name,
        "time": time.Now(),
    })
}
```

### 添加通知集成

```go
type SlackNotifier struct {
    WebhookURL string
}

func (n *SlackNotifier) Notify(message string) error {
    payload := map[string]string{"text": message}
    jsonData, _ := json.Marshal(payload)
    _, err := http.Post(n.WebhookURL, "application/json", bytes.NewBuffer(jsonData))
    return err
}
```

## 常见问题

### Q: 如何添加新的阶段？
在 YAML 配置的 `stages` 列表中添加新的阶段定义，通过 `depends_on` 指定依赖关系。

### Q: 任务失败后如何处理？
默认情况下，任务失败会终止当前阶段，所有依赖该阶段的下游阶段会被跳过。

### Q: 如何实现并行任务？
目前阶段内的任务是串行执行的。如需并行，可以将任务拆分到不同的并行阶段中。

### Q: 如何在 Docker 中执行任务？
在任务配置中指定 `image` 字段，任务会自动在该 Docker 镜像的容器中执行。

### Q: 如何配置触发方式？
在 `trigger` 配置中设置 `push`、`schedule` 或 `manual` 选项。

### Q: 如何配置部署策略？
在部署阶段的 `deploy` 配置中设置 `strategy` 为 `rolling`、`blue-green` 或 `canary`。

### Q: 如何启用自动回滚？
在部署阶段的 `deploy.rollback` 配置中设置 `enabled: true`。

## 开发计划

### 已实现
- [x] YAML 配置解析
- [x] 依赖关系校验（拓扑排序）
- [x] 阶段编排与并行执行
- [x] 本地命令执行
- [x] Docker 执行器
- [x] 超时控制
- [x] 失败重试
- [x] 状态报告
- [x] CLI 工具
- [x] Git Push 触发
- [x] 定时触发
- [x] 手动触发
- [x] 环境管理
- [x] 滚动部署
- [x] 蓝绿部署
- [x] 金丝雀部署
- [x] 版本回滚

### 未来计划
- [ ] Web UI 界面
- [ ] Webhook 通知
- [ ] 制品管理
- [ ] 日志持久化
- [ ] 多环境部署
- [ ] Kubernetes 集成
- [ ] Slack/钉钉通知
- [ ] 部署审批流程
