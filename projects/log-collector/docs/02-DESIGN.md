# 02 - 设计：日志收集系统

## 系统设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Log Collector System                            │
│                                                                      │
│  ┌──────────────┐                                                    │
│  │   Sources    │  Files, Stdin, TCP, UDP, File Watcher              │
│  └──────┬───────┘                                                    │
│         │                                                            │
│         ▼                                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐    ┌───────┐  │
│  │  Collector   │───▶│    Parser    │───▶│  Filter  │───▶│Storage│  │
│  │              │    │              │    │          │    │       │  │
│  │ - Read lines │    │ - JSON       │    │ - Level  │    │ - Mem │  │
│  │ - Multi-src  │    │ - Logfmt     │    │ - Keyword│    │ - Idx │  │
│  │ - Tail       │    │ - Common     │    │ - Regex  │    │ - R/W │  │
│  │ - TCP/UDP    │    │ - Regex      │    │ - Chain  │    │       │  │
│  └──────────────┘    └──────────────┘    └──────────┘    └───┬───┘  │
│                                                              │       │
│  ┌──────────────┐                                    ┌───────┴─────┐ │
│  │   Output     │◀───────────────────────────────────│   Query     │ │
│  │              │                                    │   Engine    │ │
│  │ - Stdout     │                                    │             │ │
│  │ - File       │                                    │ - Search    │ │
│  │ - Rotation   │                                    │ - Filter    │ │
│  └──────────────┘                                    │ - Format    │ │
│                                                      └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 数据流

```
Source (File/Stdin/TCP/UDP) → Collector → Parser → Filter → Storage → Query Engine → Output
```

## 模块设计

### 1. Collector 模块

**职责**：从配置的源读取原始日志行

**接口**：
```go
type Collector struct {
    sources []Source
    output  chan RawLog
}

type Tailer struct {
    path     string
    output   chan RawLog
    interval time.Duration
}

type MultiTailer struct {
    tailers []*Tailer
    output  chan RawLog
}

type RawLog struct {
    Line    string
    Source  string
    LineNum int
}
```

**设计决策**：
- 每个源在独立 goroutine 中读取
- 使用 channel 传递原始日志行
- 支持文件、stdin、文件监控三种源
- Tailer 使用轮询方式监控文件变化

### 2. Parser 模块

**职责**：将原始日志行解析为结构化条目

**接口**：
```go
type Parser struct {
    format      Format
    regexParser *RegexParser
}

type RegexParser struct {
    pattern    *regexp.Regexp
    groupNames []string
}

type Entry struct {
    Timestamp time.Time
    Level     Level
    Message   string
    Fields    map[string]string
}
```

**支持的格式**：
- FormatJSON：JSON 格式
- FormatLogfmt：key=value 格式
- FormatCommon：`YYYY-MM-DD HH:MM:SS [LEVEL] message`
- FormatRegex：自定义正则表达式
- FormatAuto：自动检测

**设计决策**：
- 自动检测格式，按 JSON → Logfmt → Common 顺序尝试
- 正则解析器使用命名捕获组映射到字段
- 解析失败时降级为 UNKNOWN 级别
- 保留原始行用于调试

### 3. Filter 模块

**职责**：根据条件筛选日志条目

**接口**：
```go
type Filter interface {
    Match(entry Entry) bool
}

type LevelFilter struct {
    MinLevel Level
}

type KeywordFilter struct {
    Keyword       string
    CaseSensitive bool
    Exclude       bool
}

type RegexFilter struct {
    Pattern *regexp.Regexp
    Exclude bool
}

type Chain struct {
    Filters []Filter
}

type MatchAny struct {
    Filters []Filter
}
```

**设计决策**：
- 使用接口模式，支持自定义过滤器
- Chain 实现 AND 逻辑，MatchAny 实现 OR 逻辑
- 每个过滤器支持 Include/Exclude 两种模式
- 正则过滤器预编译正则表达式

### 4. Transport 模块

**职责**：网络日志接收和文件输出

**接口**：
```go
type TCPReceiver struct {
    addr   string
    output chan RawLog
}

type UDPReceiver struct {
    addr   string
    output chan RawLog
}

type FileWriter struct {
    path    string
    maxSize int64
}
```

**设计决策**：
- TCP 支持多客户端并发连接
- UDP 每个数据包视为一行日志
- FileWriter 支持大小轮转
- 所有组件通过 channel 解耦

### 5. Storage 模块

**职责**：存储和索引日志条目

**接口**：
```go
type Storage struct {
    entries  []Entry
    timeIdx  []int
    levelIdx map[Level][]int
    srcIdx   map[string][]int
}

type Query struct {
    StartTime *time.Time
    EndTime   *time.Time
    Level     *Level
    Levels    []Level
    Source    string
    Message   string
    Fields    map[string]string
    Limit     int
    Offset    int
    Reverse   bool
}
```

**索引设计**：
- 时间索引：条目按插入顺序存储（天然有序）
- 级别索引：每个级别维护一个条目 ID 列表
- 来源索引：每个来源维护一个条目 ID 列表

**设计决策**：
- 使用 `sync.RWMutex` 保护并发访问
- 查询时选择最选择性的索引
- 支持组合过滤条件

### 6. Query Engine 模块

**职责**：提供高级查询接口

**接口**：
```go
type Engine struct {
    store *storage.Storage
}

func (e *Engine) Search(text string, limit int) []Entry
func (e *Engine) ByLevel(level Level, limit int) []Entry
func (e *Engine) ByTimeRange(start, end time.Time, limit int) []Entry
func (e *Engine) AdvancedQuery(queryStr string) ([]Entry, error)
```

**查询语法**：
```
level:error source:app.log after:2024-01-01 before:2024-12-31 limit:50
```

## 并发模型

```
Collector Goroutine ──┐
                      │
Collector Goroutine ──┼──▶ Channel ──▶ Parser ──▶ Filter ──▶ Storage
                      │
TCP/UDP Goroutine ────┘
```

- Collector、Tailer、TCP/UDP 在独立 goroutine 中运行
- 通过 channel 解耦各组件
- Storage 使用读写锁保护并发访问
- Query Engine 是无状态的，可以并发调用

## 错误处理策略

1. **文件打开失败**：记录错误，继续处理其他源
2. **解析失败**：降级为 UNKNOWN 级别，保留原始行
3. **空行**：自动跳过
4. **超长行**：增加 scanner 缓冲区到 1MB
5. **网络断开**：记录错误，继续接受其他连接
6. **过滤器错误**：跳过无效过滤器，记录警告

## 扩展性考虑

- **持久化**：可以添加文件或数据库后端
- **分布式**：可以添加多节点聚合
- **告警**：可以添加基于规则的告警
- **Kafka**：可以添加 Kafka 生产者/消费者
- **更多格式**：可以添加 CSV、XML 等格式解析
