# 04 - 测试：日志收集系统

## 测试策略

### 测试层次

1. **单元测试**：测试单个函数和方法
2. **集成测试**：测试模块间的交互
3. **端到端测试**：测试完整的日志处理流程

### 测试覆盖目标

- 核心解析逻辑：100% 覆盖
- 存储和查询：90%+ 覆盖
- 采集器：80%+ 覆盖

## 测试用例

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
    // ...
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
