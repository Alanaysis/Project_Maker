# CI/CD 流水线

实现一个完整的 CI/CD 流水线系统，支持流水线定义、阶段编排、任务执行、状态报告、环境管理、滚动部署和回滚。

## 学习目标

- 理解 CI/CD 的核心概念和工作流程
- 掌握流水线编排技术（DAG 依赖模型）
- 学会构建、测试和部署自动化
- 掌握环境管理和部署策略

## 技术栈

- **主语言**: Go 1.21+
- **配置**: YAML
- **容器**: Docker (可选)

## 核心循环

```
代码提交 → 代码检出 → 依赖安装 → 代码编译 → 单元测试 → 集成测试 → 代码覆盖率 → 部署
```

## 项目结构

```
cicd-pipeline/
├── cmd/cicd/main.go                  # CLI 入口
├── internal/
│   ├── pipeline/                      # 流水线核心
│   │   ├── config.go                 # 配置解析（触发、变量、阶段）
│   │   ├── engine.go                 # 执行引擎
│   │   └── status.go                 # 状态定义
│   ├── executor/                      # 命令执行器
│   │   └── executor.go               # 本地/Docker 执行
│   ├── deploy/                        # 部署管理
│   │   ├── deployer.go               # 部署器（滚动/蓝绿/金丝雀）
│   │   └── rollback.go               # 回滚管理
│   ├── trigger/                       # 触发管理
│   │   └── trigger.go                # Git Push/定时/手动触发
│   └── reporter/                      # 报告输出
│       └── reporter.go               # 控制台报告
├── examples/
│   ├── simple.yaml                   # 简单流水线
│   ├── pipeline.yaml                 # 示例流水线
│   └── full-pipeline.yaml            # 完整 CI/CD 流水线
├── Dockerfile                        # Docker 构建
└── docs/                             # 文档
```

## 快速开始

### 编译

```bash
go build -o cicd ./cmd/cicd
```

### 运行示例

```bash
# 执行简单流水线
./cicd run -f examples/simple.yaml

# 执行完整流水线
./cicd run -f examples/full-pipeline.yaml

# 详细模式
./cicd run -f examples/full-pipeline.yaml -v

# 校验配置
./cicd validate -f examples/full-pipeline.yaml

# 查看执行计划
./cicd plan -f examples/full-pipeline.yaml
```

### Docker 运行

```bash
docker build -t cicd-pipeline .
docker run --rm -v $(pwd)/examples:/app/examples cicd-pipeline run -f /app/examples/full-pipeline.yaml
```

## 核心功能

### 1. 流水线定义

YAML 配置文件定义完整的 CI/CD 流水线：

```yaml
name: "我的 CI/CD 流水线"

# 触发配置
trigger:
  push:
    branches: [main, develop]
    paths: ["src/**", "tests/**"]
  schedule: "0 2 * * *"
  manual: true

# 全局变量
variables:
  APP_NAME: "myapp"
  REGISTRY: "registry.example.com"

stages:
  - name: build
    tasks:
      - name: compile
        command: go build ./...
        timeout: 120
```

### 2. 构建阶段

- **代码检出**: 从 Git 仓库检出代码
- **依赖安装**: 下载和验证依赖
- **代码编译**: 编译应用和工具
- **制品打包**: 生成可部署的制品

```yaml
- name: build
  tasks:
    - name: "代码检出"
      command: git clone https://github.com/user/repo.git

    - name: "依赖安装"
      command: go mod download
      timeout: 180

    - name: "代码编译"
      command: go build -o app ./cmd/app
      timeout: 300
```

### 3. 测试阶段

- **单元测试**: 测试单个函数/模块
- **集成测试**: 测试模块间交互
- **代码覆盖率**: 生成覆盖率报告

```yaml
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
```

### 4. 部署阶段

支持多种部署策略：

#### 滚动部署
逐步更新服务实例，零停机时间。

```yaml
- name: deploy
  deploy:
    strategy: rolling
    targets:
      - name: production
        url: "https://www.example.com"
    tasks:
      - name: "滚动更新"
        command: ./deploy.sh rolling
```

#### 蓝绿部署
维护两套完整环境，快速切换。

```yaml
- name: deploy
  deploy:
    strategy: blue-green
    targets:
      - name: blue
        url: "https://blue.example.com"
      - name: green
        url: "https://green.example.com"
```

#### 金丝雀部署
逐步扩大新版本流量比例。

```yaml
- name: deploy
  deploy:
    strategy: canary
    targets:
      - name: canary
        url: "https://canary.example.com"
        weight: 10
      - name: production
        url: "https://www.example.com"
        weight: 100
```

#### 环境管理

```yaml
- name: deploy-staging
  deploy:
    strategy: rolling
    targets:
      - name: staging
        url: "https://staging.example.com"
        region: "us-east-1"
    rollback:
      enabled: true
      max_versions: 3
      health_check: 30
```

### 5. 触发方式

#### Git Push 触发
代码推送到指定分支时自动触发。

```yaml
trigger:
  push:
    branches: [main, develop, "release/*"]
    paths: ["src/**", "tests/**"]
```

#### 定时触发
使用 Cron 表达式定时触发。

```yaml
trigger:
  schedule: "0 2 * * *"  # 每天凌晨 2 点
```

#### 手动触发
支持手动触发执行。

```yaml
trigger:
  manual: true
```

### 6. 实际应用

#### 自动构建
```bash
# Git Push 自动触发
git push origin main
# → 自动检出代码
# → 自动安装依赖
# → 自动编译代码
```

#### 自动测试
```bash
# 构建完成后自动测试
# → 运行单元测试
# → 运行集成测试
# → 生成覆盖率报告
```

#### 自动部署
```bash
# 测试通过后自动部署
# → 部署到预发布环境
# → 运行冒烟测试
# → 部署到生产环境
# → 发送通知
```

## 阶段编排

### DAG 依赖模型

使用有向无环图 (DAG) 定义阶段依赖关系：

```
checkout → dependencies → build
                           ↓
                    ┌──────┼──────┐
                    ↓      ↓      ↓
              unit-test  quality  integration-test
                    ↓      ↓      ↓
                    └──────┼──────┘
                           ↓
                    docker-build → deploy-staging → deploy-production
```

### 并行执行

无依赖的阶段自动并行执行：

```yaml
stages:
  - name: unit-test
    depends_on: [build]

  - name: integration-test
    depends_on: [build]

  - name: quality
    depends_on: [build]
# unit-test、integration-test、quality 会并行执行
```

### 循环依赖检测

自动检测并拒绝循环依赖配置。

## 配置格式

### 完整配置示例

```yaml
name: "生产级 CI/CD 流水线"

trigger:
  push:
    branches: [main]
  schedule: "0 2 * * *"
  manual: true

variables:
  APP_NAME: "myapp"
  VERSION: "v1.0.0"

stages:
  - name: build
    tasks:
      - name: compile
        command: go build ./...
        timeout: 120
        env:
          CGO_ENABLED: "0"

  - name: test
    depends_on: [build]
    tasks:
      - name: unit-test
        command: go test ./...
        retries: 2

  - name: deploy
    depends_on: [test]
    deploy:
      strategy: rolling
      targets:
        - name: production
          url: "https://www.example.com"
      rollback:
        enabled: true
        max_versions: 5
    tasks:
      - name: deploy-task
        command: ./deploy.sh
        env:
          ENV: production
```

### 任务配置选项

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | 是 | 任务名称 |
| command | string | 是 | 要执行的命令 |
| image | string | 否 | Docker 镜像 |
| env | map | 否 | 环境变量 |
| timeout | int | 否 | 超时秒数（0=不限）|
| retries | int | 否 | 失败重试次数 |

## 测试

```bash
# 运行所有测试
go test ./...

# 运行测试并显示覆盖率
go test ./... -cover

# 详细测试输出
go test ./... -v

# 运行特定包的测试
go test ./internal/pipeline/...
go test ./internal/deploy/...
go test ./internal/trigger/...
```

## 文档

- [研究文档](docs/01-RESEARCH.md) - CI/CD 概念研究
- [设计文档](docs/02-DESIGN.md) - 架构设计
- [实现文档](docs/03-IMPLEMENTATION.md) - 实现细节
- [测试文档](docs/04-TESTING.md) - 测试策略
- [开发文档](docs/05-DEVELOPMENT.md) - 开发指南
- [学习笔记](LEARNING_NOTES.md) - 学习总结

## 依赖

- `gopkg.in/yaml.v3` - YAML 解析

## 扩展功能

### 添加新的执行器

```go
type K8sExecutor struct{}

func (e *K8sExecutor) Execute(ctx context.Context, command string, env map[string]string) (string, int, error) {
    // 在 Kubernetes Pod 中执行命令
    return output, exitCode, nil
}
```

### 添加新的部署策略

```go
func (d *Deployer) customDeploy(ctx context.Context, env *Environment, deployment *Deployment) error {
    // 实现自定义部署策略
    return nil
}
```

### 添加通知集成

```go
type SlackNotifier struct {
    WebhookURL string
}

func (n *SlackNotifier) Notify(message string) error {
    // 发送 Slack 通知
    return nil
}
```
