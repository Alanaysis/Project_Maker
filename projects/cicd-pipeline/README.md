# CI/CD 流水线

实现一个简易的 CI/CD 流水线，支持流水线定义、阶段编排、任务执行和状态报告。

## 学习目标

- 理解 CI/CD 的核心概念
- 掌握流水线编排技术（DAG 依赖模型）
- 学会构建和部署自动化

## 技术栈

- **主语言**: Go
- **配置**: YAML
- **容器**: Docker (可选)

## 核心循环

```
代码提交 → 构建 → 测试 → 部署
```

## 项目结构

```
cicd-pipeline/
├── cmd/cicd/main.go              # CLI 入口
├── internal/
│   ├── pipeline/                  # 流水线核心
│   │   ├── config.go             # 配置解析
│   │   ├── engine.go             # 执行引擎
│   │   └── status.go             # 状态定义
│   ├── executor/                  # 命令执行器
│   │   └── executor.go           # 本地/Docker 执行
│   └── reporter/                  # 报告输出
│       └── reporter.go           # 控制台报告
├── examples/
│   └── pipeline.yaml             # 示例配置
├── Dockerfile                    # Docker 构建
└── docs/                         # 文档
```

## 快速开始

### 编译

```bash
go build -o cicd ./cmd/cicd
```

### 运行示例

```bash
# 执行流水线
./cicd run -f examples/pipeline.yaml

# 详细模式
./cicd run -f examples/pipeline.yaml -v

# 校验配置
./cicd validate -f examples/pipeline.yaml

# 查看执行计划
./cicd plan -f examples/pipeline.yaml
```

### Docker 运行

```bash
docker build -t cicd-pipeline .
docker run --rm -v $(pwd)/examples:/app/examples cicd-pipeline run -f /app/examples/pipeline.yaml
```

## 配置格式

```yaml
name: "我的流水线"
stages:
  - name: build
    tasks:
      - name: compile
        command: go build ./...
        timeout: 120

  - name: test
    depends_on:
      - build
    tasks:
      - name: unit-test
        command: go test ./...
        retries: 2

  - name: deploy
    depends_on:
      - test
    tasks:
      - name: deploy-task
        command: ./deploy.sh
        env:
          ENV: production
```

## 核心功能

### 流水线定义
- YAML 配置文件
- 支持多阶段、多任务
- 环境变量配置

### 阶段编排
- DAG 依赖模型
- 自动拓扑排序
- 循环依赖检测
- 并行阶段执行

### 任务执行
- 本地 Shell 执行
- Docker 容器执行
- 超时控制
- 失败重试

### 状态报告
- 实时进度显示
- 阶段/任务状态
- 执行时间统计
- 错误信息展示

## 测试

```bash
# 运行所有测试
go test ./...

# 运行测试并显示覆盖率
go test ./... -cover

# 详细测试输出
go test ./... -v
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
