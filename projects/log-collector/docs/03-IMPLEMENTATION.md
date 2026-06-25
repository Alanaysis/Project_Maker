# 03 - 实现：日志收集系统

## 实现概述

本项目使用 Go 语言实现，采用模块化设计，每个模块有清晰的职责边界。

## 实现顺序

1. **Filter 模块**：日志过滤逻辑，无外部依赖
2. **Parser 模块**：核心解析逻辑，含正则解析器
3. **Storage 模块**：存储和索引，依赖 Parser 的数据结构
4. **Transport 模块**：网络接收和文件输出
5. **Collector 模块**：日志采集，含文件监控
6. **Query Engine**：查询接口，依赖 Storage
7. **CLI**：命令行界面，集成所有模块

## 关键实现细节

### 1. Filter 实现

#### 接口设计

```go
type Filter interface {
    Match(entry Entry) bool
}
```

使用接口模式，支持自定义过滤器。

#### 级别过滤

```go
type LevelFilter struct {
    MinLevel Level
}

func (f *LevelFilter) Match(entry Entry) bool {
    return entry.Level >= f.MinLevel
}
```

#### 关键词过滤

```go
type KeywordFilter struct {
    Keyword       string
    CaseSensitive bool
    Exclude       bool
}
```

#### 正则过滤

```go
type RegexFilter struct {
    Pattern *regexp.Regexp
    Exclude bool
}
```

#### 组合过滤

```go
// AND 逻辑
type Chain struct {
    Filters []Filter
}

// OR 逻辑
type MatchAny struct {
    Filters []Filter
}
```

### 2. Regex Parser 实现

#### 命名捕获组映射

```go
type RegexParser struct {
    pattern    *regexp.Regexp
    groupNames []string
}

func (rp *RegexParser) Parse(rawLine string, source string, lineNum int) (*Entry, error) {
    matches := rp.pattern.FindStringSubmatch(rawLine)
    // 映射命名组到 Entry 字段
    for i, name := range rp.groupNames {
        switch name {
        case "time", "ts", "timestamp":
            entry.Timestamp = rp.parseTime(matches[i])
        case "level", "severity", "lvl":
            entry.Level = ParseLevel(matches[i])
        case "msg", "message":
            entry.Message = matches[i]
        default:
            entry.Fields[name] = matches[i]
        }
    }
}
```

#### 内置模式

```go
var CommonPatterns = map[string]string{
    "apache":  `^(?P<remote>\S+) ...`,
    "syslog":  `^(?P<time>\w{3} \d{1,2} ...)`,
    "generic": `^(?P<time>\d{4}-\d{2}-\d{2} ...)`,
    "access":  `^(?P<ip>\d{1,3}\.\d{1,3}...)`,
}
```

### 3. Transport 实现

#### TCP Receiver

```go
type TCPReceiver struct {
    addr     string
    output   chan RawLog
    listener net.Listener
}

func (r *TCPReceiver) accept() {
    for {
        conn, err := r.listener.Accept()
        go r.handleConn(conn)
    }
}

func (r *TCPReceiver) handleConn(conn net.Conn) {
    scanner := bufio.NewScanner(conn)
    for scanner.Scan() {
        r.output <- RawLog{Line: scanner.Text(), Source: "tcp:" + addr}
    }
}
```

#### UDP Receiver

```go
type UDPReceiver struct {
    addr   string
    output chan RawLog
    conn   *net.UDPConn
}

func (r *UDPReceiver) receive() {
    buf := make([]byte, 65535)
    for {
        n, addr, _ := r.conn.ReadFromUDP(buf)
        r.output <- RawLog{Line: string(buf[:n]), Source: "udp:" + addr}
    }
}
```

#### File Writer

```go
type FileWriter struct {
    path    string
    maxSize int64
    curSize int64
}

func (w *FileWriter) Write(line string) error {
    if w.needsRotation() {
        w.rotate()
    }
    n, _ := fmt.Fprintln(w.file, line)
    w.curSize += int64(n)
}
```

### 4. Tailer 实现

#### 轮询式文件监控

```go
type Tailer struct {
    path     string
    output   chan RawLog
    interval time.Duration
}

func (t *Tailer) watch(file *os.File) {
    // Seek to end，只获取新内容
    file.Seek(0, io.SeekEnd)
    scanner := bufio.NewScanner(file)

    ticker := time.NewTicker(t.interval)
    for {
        select {
        case <-t.done:
            return
        case <-ticker.C:
            // 读取所有可用行
            for scanner.Scan() {
                t.output <- RawLog{Line: scanner.Text()}
            }
        }
    }
}
```

### 5. Parser 实现

#### JSON 解析

```go
func (p *Parser) parseJSON(line string) (*Entry, error) {
    var raw map[string]interface{}
    json.Unmarshal([]byte(line), &raw)
    // 提取已知字段，其余放入 Fields
}
```

#### Logfmt 解析

```go
func tokenizeLogfmt(line string) map[string]string {
    // 处理带引号的值
    // level=info msg="hello world" -> {level: info, msg: hello world}
}
```

#### 自动检测

```go
func (p *Parser) parseAuto(line string) (*Entry, error) {
    // 1. 尝试 JSON
    // 2. 尝试 Logfmt
    // 3. 尝试 Common
    // 4. 兜底：整行作为消息
}
```

### 6. Storage 实现

#### 索引设计

```go
type Storage struct {
    entries  []Entry
    timeIdx  []int
    levelIdx map[Level][]int
    srcIdx   map[string][]int
}
```

#### 查询优化

```go
func (s *Storage) Query(q Query) []Entry {
    // 1. 选择最选择性的索引
    // 2. 应用过滤条件
    // 3. 应用排序、偏移、限制
}
```

## 测试策略

### 单元测试

每个模块都有独立的测试：
- `filter_test.go`：测试各种过滤器
- `parser_test.go`：测试各种格式的解析
- `regex_parser_test.go`：测试正则解析器
- `storage_test.go`：测试存储和查询
- `collector_test.go`：测试采集逻辑
- `tailer_test.go`：测试文件监控
- `transport_test.go`：测试网络传输和文件输出
- `query_test.go`：测试查询引擎

### 集成测试

`integration_test.go` 测试完整流程：
- JSON/Logfmt/Common/Auto 格式的端到端测试
- 多数据源测试
- 大数据量测试
- 并发安全测试
- 时间范围查询测试

## 已知限制

1. **单机存储**：仅支持内存存储，重启后数据丢失
2. **简单查询**：查询语言功能有限
3. **无持久化**：需要手动导出数据
4. **无 Kafka**：未实现 Kafka 生产者/消费者
