# 05 - 开发：日志收集系统

## 开发环境

### 依赖

- Go 1.21 或更高版本
- 无第三方依赖（仅使用标准库）

### 项目结构

```
log-collector/
├── cmd/collector/main.go      # CLI 入口
├── internal/
│   ├── collector/             # 日志采集
│   ├── parser/                # 日志解析
│   ├── storage/               # 日志存储
│   └── query/                 # 查询引擎
├── docs/                      # 文档
├── go.mod                     # Go 模块文件
├── README.md                  # 项目说明
└── LEARNING_NOTES.md          # 学习笔记
```

## 构建

```bash
# 构建可执行文件
go build -o collector ./cmd/collector

# 交叉编译
GOOS=linux GOARCH=amd64 go build -o collector-linux ./cmd/collector
GOOS=darwin GOARCH=arm64 go build -o collector-mac ./cmd/collector
```

## 运行

### 基本用法

```bash
# 从 stdin 读取日志
echo '{"level":"info","msg":"hello"}' | ./collector

# 从文件读取日志
./collector app.log error.log

# 指定格式
./collector -format json app.log
```

### 查询模式

```bash
# 交互式查询
./collector
log> level:error
log> recent 20
log> search "timeout"
log> stats
log> quit

# 命令行查询
./collector -query "level:error source:app.log"
./collector -recent 50
./collector -errors 10
./collector -search "connection"
./collector -stats
```

## 测试

```bash
# 运行所有测试
go test ./...

# 运行测试并显示详细输出
go test ./... -v

# 运行特定包的测试
go test ./internal/parser -v
go test ./internal/storage -v
go test ./internal/collector -v
go test ./internal/query -v

# 显示测试覆盖率
go test ./... -cover
```

## 调试

### 启用详细日志

目前没有内置的调试日志。可以通过以下方式调试：

1. 使用 `-format` 参数确保正确解析
2. 检查 `stats` 输出确认数据已存储
3. 使用 `recent` 查看最近的日志条目

### 常见问题

**Q: 日志没有被解析？**
A: 检查日志格式是否正确。使用 `-format` 参数指定格式，或检查自动检测是否正确。

**Q: 查询没有结果？**
A: 先运行 `stats` 确认有数据存储。检查查询语法是否正确。

**Q: 内存占用过高？**
A: 当前使用内存存储，大量日志会占用较多内存。未来可以添加持久化支持。

## 扩展开发

### 添加新的日志格式

1. 在 `parser.go` 中添加新的 Format 常量
2. 实现 `parseXxx` 方法
3. 在 `parseAuto` 中添加检测逻辑
4. 添加相应的测试

### 添加持久化

1. 在 `storage.go` 中添加 `Save` 和 `Load` 方法
2. 实现文件或数据库后端
3. 在 `main.go` 中添加 `-db` 参数支持

### 添加网络接收

1. 创建新的 `receiver` 包
2. 实现 TCP/UDP 服务器
3. 将接收到的日志发送到 Collector 的 channel

## 代码规范

- 使用 `gofmt` 格式化代码
- 使用 `go vet` 检查代码
- 每个导出的函数和类型都要有注释
- 测试文件与源文件放在同一个包中
