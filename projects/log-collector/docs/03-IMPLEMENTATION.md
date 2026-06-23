# 03 - 实现：日志收集系统

## 实现概述

本项目使用 Go 语言实现，采用模块化设计，每个模块有清晰的职责边界。

## 实现顺序

1. **Parser 模块**：核心解析逻辑，无外部依赖
2. **Storage 模块**：存储和索引，依赖 Parser 的数据结构
3. **Collector 模块**：日志采集，依赖 Parser
4. **Query Engine**：查询接口，依赖 Storage
5. **CLI**：命令行界面，集成所有模块

## 关键实现细节

### 1. Parser 实现

#### JSON 解析

```go
func (p *Parser) parseJSON(line string) (*Entry, error) {
    var raw map[string]interface{}
    if err := json.Unmarshal([]byte(line), &raw); err != nil {
        return nil, fmt.Errorf("not valid JSON: %w", err)
    }
    // 提取已知字段，其余放入 Fields
}
```

关键点：
- 使用 `map[string]interface{}` 接受任意 JSON 结构
- 已知字段（level, msg, time）提取到 Entry 的对应字段
- 其余字段保留在 Fields map 中

#### Logfmt 解析

```go
func tokenizeLogfmt(line string) map[string]string {
    // 处理带引号的值
    // level=info msg="hello world" -> {level: info, msg: hello world}
}
```

关键点：
- 自定义 tokenizer 处理带引号的值
- 支持 `key=value` 和 `key="value with spaces"` 两种形式

#### 自动检测

```go
func (p *Parser) parseAuto(line string) (*Entry, error) {
    // 1. 尝试 JSON
    // 2. 尝试 Logfmt
    // 3. 尝试 Common
    // 4. 兜底：整行作为消息
}
```

### 2. Storage 实现

#### 索引设计

```go
type Storage struct {
    entries  []Entry           // 所有条目
    timeIdx  []int             // 时间索引（按插入顺序）
    levelIdx map[Level][]int   // 级别索引
    srcIdx   map[string][]int  // 来源索引
}
```

#### 查询优化

```go
func (s *Storage) Query(q Query) []Entry {
    // 1. 选择最选择性的索引
    if q.Level != nil {
        indices = s.levelIdx[*q.Level]
    } else if len(q.Levels) > 0 {
        // 合并多个级别的索引
    } else {
        // 使用所有条目
    }

    // 2. 应用过滤条件
    // 3. 应用排序、偏移、限制
}
```

### 3. Collector 实现

#### 并发采集

```go
func (c *Collector) Start() error {
    for _, src := range c.sources {
        c.wg.Add(1)
        go c.collectSource(src)
    }
    return nil
}
```

#### 安全关闭

```go
func (c *Collector) Stop() {
    c.stopOnce.Do(func() {
        close(c.done)
    })
    c.wg.Wait()
}
```

使用 `sync.Once` 防止重复关闭 channel。

### 4. Query Engine 实现

#### 高级查询解析

```go
func (e *Engine) AdvancedQuery(queryStr string) ([]Entry, error) {
    // 解析 "level:error source:app.log after:2024-01-01"
    // 1. 按空格分割（尊重引号）
    // 2. 识别 key:value 对
    // 3. 自由文本作为消息搜索
}
```

## 测试策略

### 单元测试

每个模块都有独立的测试：
- `parser_test.go`：测试各种格式的解析
- `storage_test.go`：测试存储和查询
- `collector_test.go`：测试采集逻辑
- `query_test.go`：测试查询引擎

### 测试覆盖

- 正常路径：各种格式的正确解析
- 边界情况：空行、无效格式、缺失字段
- 并发安全：多 goroutine 读写

## 已知限制

1. **单机存储**：仅支持内存存储，重启后数据丢失
2. **无网络**：仅支持文件和 stdin，不支持网络接收
3. **简单查询**：查询语言功能有限
4. **无持久化**：需要手动导出数据
