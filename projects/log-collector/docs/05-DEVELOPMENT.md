# 05 - 开发：日志收集系统

## 开发环境

### 依赖

- Go 1.21 或更高版本
- 无第三方依赖（仅使用标准库）

### 项目结构

```
log-collector/
├── cmd/collector/main.go          # CLI 入口
├── internal/
│   ├── collector/                 # 日志采集
│   │   ├── collector.go           # 文件/stdin 采集
│   │   └── tailer.go              # 文件监控
│   ├── parser/                    # 日志解析
│   │   ├── parser.go              # 多格式解析
│   │   └── regex_parser.go        # 正则解析
│   ├── filter/                    # 日志过滤
│   │   └── filter.go              # 级别/关键词/正则过滤
│   ├── storage/                   # 日志存储
│   │   └── storage.go             # 内存存储+索引
│   ├── transport/                 # 网络传输
│   │   ├── tcp.go                 # TCP 接收
│   │   ├── udp.go                 # UDP 接收
│   │   └── filewriter.go          # 文件输出
│   └── query/                     # 查询引擎
│       └── query.go               # 查询和格式化
├── tests/                         # 集成测试
│   └── integration_test.go
├── docs/                          # 文档
├── go.mod
├── README.md
└── LEARNING_NOTES.md
```

## 构建

```bash
# 构建可执行文件
go build -o collector ./cmd/collector

# 交叉编译
GOOS=linux GOARCH=amd64 go build -o collector-linux ./cmd/collector
GOOS=darwin GOARCH=arm64 go build -o collector-mac ./cmd/collector
GOOS=windows GOARCH=amd64 go build -o collector.exe ./cmd/collector
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

# 使用正则解析
./collector -format regex \
  -regex '^\d{4}-\d{2}-\d{2} \[(?P<level>\w+)\] (?P<msg>.+)$' \
  app.log
```

### 文件监控模式

```bash
# 监控单个文件
./collector -watch app.log

# 监控多个文件
./collector -watch app.log error.log

# 监控并过滤
./collector -watch -level error app.log
```

### 网络接收模式

```bash
# TCP 接收
./collector -tcp :5514

# UDP 接收
./collector -udp :5515

# TCP + UDP 同时接收
./collector -tcp :5514 -udp :5515

# 接收并输出到文件
./collector -tcp :5514 -output server.log
```

### 过滤模式

```bash
# 按级别过滤
./collector -level error app.log

# 按关键词过滤
./collector -keyword timeout app.log

# 排除关键词
./collector -keyword debug -keyword-exclude app.log

# 按正则过滤
./collector -regex-filter "connection.*timeout" app.log

# 组合过滤
./collector -level error -keyword timeout app.log
```

### 输出模式

```bash
# 输出到文件
./collector -output logs.out app.log

# 输出到文件，带轮转
./collector -output logs.out -output-max-size 10485760 app.log
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
go test ./internal/filter -v
go test ./internal/transport -v
go test ./internal/query -v

# 运行特定测试
go test ./internal/parser -run TestParseJSON
go test ./internal/filter -run TestRegexFilter

# 显示测试覆盖率
go test ./... -cover

# 生成覆盖率报告
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## 调试

### 启用详细日志

目前没有内置的调试日志。可以通过以下方式调试：

1. 使用 `-format` 参数确保正确解析
2. 检查 `stats` 输出确认数据已存储
3. 使用 `recent` 查看最近的日志条目
4. 使用 `-output` 将日志写入文件检查

### 常见问题

**Q: 日志没有被解析？**
A: 检查日志格式是否正确。使用 `-format` 参数指定格式，或检查自动检测是否正确。

**Q: 查询没有结果？**
A: 先运行 `stats` 确认有数据存储。检查查询语法是否正确。

**Q: 内存占用过高？**
A: 当前使用内存存储，大量日志会占用较多内存。使用过滤减少存储量。

**Q: 文件监控没有检测到新内容？**
A: 确保文件是被追加写入的，而不是被替换。检查轮询间隔是否合适。

**Q: TCP/UDP 连接失败？**
A: 检查端口是否被占用。确认防火墙设置允许相应端口。

## 扩展开发

### 添加新的日志格式

1. 在 `parser.go` 中添加新的 Format 常量
2. 实现 `parseXxx` 方法
3. 在 `parseAuto` 中添加检测逻辑
4. 添加相应的测试

### 添加新的过滤器

1. 在 `filter.go` 中实现 `Filter` 接口
2. 在 `main.go` 中添加命令行参数
3. 添加相应的测试

### 添加持久化

1. 在 `storage.go` 中添加 `Save` 和 `Load` 方法
2. 实现文件或数据库后端
3. 在 `main.go` 中添加 `-db` 参数支持

### 添加 Kafka 支持

1. 创建新的 `kafka` 包
2. 实现 Kafka 生产者和消费者
3. 将接收到的日志发送到 Collector 的 channel

## 代码规范

- 使用 `gofmt` 格式化代码
- 使用 `go vet` 检查代码
- 每个导出的函数和类型都要有注释
- 测试文件与源文件放在同一个包中
- 使用标准库，避免第三方依赖
