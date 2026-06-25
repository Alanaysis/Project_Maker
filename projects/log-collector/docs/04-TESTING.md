# 04 - 测试：日志收集系统

## 测试策略

### 测试层次

1. **单元测试**：测试单个函数和方法
2. **集成测试**：测试模块间的交互
3. **端到端测试**：测试完整的日志处理流程

### 测试覆盖目标

- 核心过滤逻辑：100% 覆盖
- 核心解析逻辑：100% 覆盖
- 存储和查询：90%+ 覆盖
- 采集器：80%+ 覆盖
- 网络传输：80%+ 覆盖

## 测试用例

### Filter 测试

#### 级别过滤测试

```go
func TestLevelFilter(t *testing.T) {
    // 测试各级别的过滤
    // DEBUG < INFO < WARN < ERROR < FATAL
    f := &LevelFilter{MinLevel: LevelError}
    // ERROR 和 FATAL 应该通过
    // DEBUG、INFO、WARN 应该被过滤
}
```

#### 关键词过滤测试

```go
func TestKeywordFilter(t *testing.T) {
    // 测试基本关键词匹配
    // 测试大小写敏感/不敏感
    // 测试排除模式
}
```

#### 正则过滤测试

```go
func TestRegexFilter(t *testing.T) {
    // 测试正则匹配
    // 测试排除模式
    // 测试无效正则
}
```

#### 组合过滤测试

```go
func TestChain(t *testing.T) {
    // 测试 AND 逻辑
    // 所有过滤器都匹配才通过
}

func TestMatchAny(t *testing.T) {
    // 测试 OR 逻辑
    // 任一过滤器匹配就通过
}
```

### Parser 测试

#### JSON 解析测试

```go
func TestParseJSON(t *testing.T) {
    tests := []struct {
        name    string
        line    string
        level   Level
        message string
    }{
        {"basic JSON", `{"level":"info","msg":"hello"}`, LevelInfo, "hello"},
        {"with timestamp", `{"level":"error","message":"fail","ts":"2024-01-01T00:00:00Z"}`, LevelError, "fail"},
        {"unknown level", `{"msg":"test"}`, LevelUnknown, "test"},
    }
}
```

#### Logfmt 解析测试

```go
func TestParseLogfmt(t *testing.T) {
    // 测试基本 key=value
    // 测试带引号的值
    // 测试多个字段
}
```

#### Regex 解析测试

```go
func TestRegexParserBasic(t *testing.T) {
    // 测试基本正则解析
    // 测试命名捕获组映射
    // 测试不匹配的行
}

func TestRegexParserCustomFields(t *testing.T) {
    // 测试自定义字段提取
}

func TestRegexParserApachePattern(t *testing.T) {
    // 测试内置 Apache 日志模式
}

func TestRegexParserSyslogPattern(t *testing.T) {
    // 测试内置 Syslog 模式
}
```

#### 自动检测测试

```go
func TestParseAuto(t *testing.T) {
    // 测试 JSON 自动检测
    // 测试 Logfmt 自动检测
    // 测试 Common 自动检测
    // 测试纯文本兜底
}
```

### Storage 测试

#### 存储测试

```go
func TestStoreAndCount(t *testing.T) {
    // 测试存储单条日志
    // 测试计数
}

func TestStoreMultiple(t *testing.T) {
    // 测试批量存储
}
```

#### 查询测试

```go
func TestQueryByLevel(t *testing.T) {
    // 测试按级别查询
}

func TestQueryByTimeRange(t *testing.T) {
    // 测试按时间范围查询
}

func TestQueryByMessage(t *testing.T) {
    // 测试按消息内容查询
}

func TestQueryBySource(t *testing.T) {
    // 测试按来源查询
}

func TestQueryByFields(t *testing.T) {
    // 测试按字段查询
}
```

#### 边界测试

```go
func TestQueryLimit(t *testing.T) {
    // 测试限制返回数量
}

func TestQueryOffset(t *testing.T) {
    // 测试偏移量
}

func TestQueryReverse(t *testing.T) {
    // 测试反向排序
}
```

### Collector 测试

```go
func TestCollectFromReader(t *testing.T) {
    // 测试从 Reader 读取日志
}

func TestCollectFromReaderSkipsEmptyLines(t *testing.T) {
    // 测试跳过空行
}

func TestCollectorStartStop(t *testing.T) {
    // 测试启动和停止
}
```

### Tailer 测试

```go
func TestTailerReadsNewContent(t *testing.T) {
    // 测试读取新增内容
}

func TestTailerSkipsEmptyLines(t *testing.T) {
    // 测试跳过空行
}

func TestTailerNonExistentFile(t *testing.T) {
    // 测试不存在的文件
}

func TestMultiTailer(t *testing.T) {
    // 测试多文件监控
}
```

### Transport 测试

```go
func TestTCPReceiver(t *testing.T) {
    // 测试 TCP 接收
}

func TestTCPReceiverMultipleClients(t *testing.T) {
    // 测试多客户端
}

func TestUDPReceiver(t *testing.T) {
    // 测试 UDP 接收
}

func TestFileWriter(t *testing.T) {
    // 测试文件写入
}

func TestFileWriterRotation(t *testing.T) {
    // 测试文件轮转
}
```

### Query Engine 测试

```go
func TestSearch(t *testing.T) {
    // 测试文本搜索
}

func TestAdvancedQueryLevel(t *testing.T) {
    // 测试高级查询：按级别
}

func TestAdvancedQueryDateRange(t *testing.T) {
    // 测试高级查询：按日期范围
}

func TestAdvancedQueryCombined(t *testing.T) {
    // 测试高级查询：组合条件
}
```

## 运行测试

```bash
# 运行所有测试
go test ./...

# 运行测试并显示详细输出
go test ./... -v

# 运行特定包的测试
go test ./internal/parser -v
go test ./internal/filter -v
go test ./internal/transport -v

# 运行特定测试
go test ./internal/parser -run TestParseJSON

# 显示测试覆盖率
go test ./... -cover

# 生成覆盖率报告
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## 测试数据

### 示例日志行

**JSON 格式**：
```json
{"level":"info","msg":"server started","port":8080,"ts":"2024-01-01T12:00:00Z"}
{"level":"error","message":"connection timeout","host":"db.example.com"}
```

**Logfmt 格式**：
```
level=info msg=server_started port=8080
level=error msg="connection timeout" host=db.example.com
```

**Common 格式**：
```
2024-01-15 10:30:00 [INFO] Application started successfully
2024-01-15 10:30:01 [ERROR] Database connection timeout
```

**Regex 格式**：
```
192.168.1.1 - - [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.0" 200 2326
Jan 15 10:30:00 myhost sshd[1234]: Accepted publickey for user
```
