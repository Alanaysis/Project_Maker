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
./cicd run -f examples/pipeline.yaml -v
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
docker run --rm -v $(pwd)/examples:/app/examples cicd-pipeline run -f /app/examples/pipeline.yaml -v
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
      - name: deploy-prod
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

## 功能特性

### 1. 依赖编排
- 支持阶段间依赖定义
- 自动拓扑排序
- 循环依赖检测
- 依赖失败自动跳过

### 2. 并行执行
- 无依赖的阶段自动并行
- 基于 goroutine 的并发
- 互斥锁保护共享状态

### 3. Docker 支持
- 任务可指定 Docker 镜像
- 自动在容器中执行命令
- 环境变量透传

### 4. 错误处理
- 任务失败终止阶段
- 支持超时控制
- 支持失败重试
- Ctrl+C 优雅取消

### 5. 状态报告
- 实时执行进度
- 阶段和任务状态
- 执行时间统计
- 彩色 emoji 状态标记

## 扩展开发

### 添加新的执行器

```go
type MyExecutor struct{}

func (e *MyExecutor) Execute(ctx context.Context, command string, env map[string]string) (string, int, error) {
    // 实现执行逻辑
    return output, exitCode, nil
}

func (e *MyExecutor) Type() string {
    return "my-executor"
}
```

### 添加新的报告格式

```go
type JSONReporter struct {
    output io.Writer
}

func (r *JSONReporter) OnPipelineStart(name string) {
    // JSON 格式输出
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

### 未来计划
- [ ] Web UI 界面
- [ ] Webhook 通知
- [ ] 制品管理
- [ ] 日志持久化
- [ ] 多环境部署
