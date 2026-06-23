# 设备管理 - 开发指南

## 1. 开发环境搭建

### 1.1 环境要求

- Go 1.21+
- Git
- IDE（推荐 VS Code + Go 扩展）

### 1.2 快速开始

```bash
# 克隆项目
git clone <repository-url>
cd projects/device-management

# 安装依赖
go mod tidy

# 运行测试
go test ./...

# 启动服务
go run cmd/server/main.go
```

## 2. 项目结构说明

```
device-management/
├── cmd/
│   └── server/
│       └── main.go           # 服务入口
├── docs/                      # 文档目录
│   ├── 01-RESEARCH.md        # 研究文档
│   ├── 02-ARCHITECTURE.md    # 架构设计
│   ├── 03-IMPLEMENTATION.md  # 实现细节
│   ├── 04-TESTING.md         # 测试文档
│   └── 05-DEVELOPMENT.md     # 开发指南
├── internal/
│   ├── device/
│   │   └── device.go          # 设备核心逻辑
│   ├── group/
│   │   └── group.go           # 设备分组
│   └── handler/
│       └── handler.go         # 请求处理
├── test/                      # 测试
│   ├── device_test.go        # 设备测试
│   ├── group_test.go         # 分组测试
│   └── api_test.go           # API测试
├── go.mod                     # Go模块文件
└── README.md                  # 项目说明
```

## 3. 核心模块开发

### 3.1 设备管理器

**文件位置：** `internal/device/device.go`

**核心功能：**
- 设备注册
- 设备查询
- 状态更新
- 设备删除
- 事件通知

**开发要点：**

1. **并发安全**
```go
type DeviceManager struct {
    mu      sync.RWMutex
    devices map[string]*Device
    eventChan chan *DeviceEvent
}
```

2. **读写锁使用**
```go
// 读操作
func (dm *DeviceManager) GetDevice(id string) (*Device, error) {
    dm.mu.RLock()
    defer dm.mu.RUnlock()
    // ...
}

// 写操作
func (dm *DeviceManager) RegisterDevice(...) (*Device, error) {
    dm.mu.Lock()
    defer dm.mu.Unlock()
    // ...
}
```

3. **事件通道**
```go
// 创建带缓冲的通道
eventChan: make(chan *DeviceEvent, 100)

// 非阻塞发送
select {
case dm.eventChan <- event:
default:
    log.Printf("事件通道已满")
}
```

### 3.2 分组管理器

**文件位置：** `internal/group/group.go`

**核心功能：**
- 创建分组
- 添加设备到分组
- 从分组移除设备
- 获取分组设备

**开发要点：**

1. **依赖注入**
```go
type GroupManager struct {
    mu     sync.RWMutex
    groups map[string]*Group
    dm     *device.DeviceManager
}
```

2. **数据验证**
```go
func (gm *GroupManager) AddDeviceToGroup(groupID, deviceID string) error {
    // 检查分组是否存在
    group, exists := gm.groups[groupID]
    if !exists {
        return fmt.Errorf("分组不存在: %s", groupID)
    }

    // 检查设备是否存在
    _, err := gm.dm.GetDevice(deviceID)
    if err != nil {
        return fmt.Errorf("设备不存在: %s", deviceID)
    }

    // 检查设备是否已在分组中
    for _, id := range group.DeviceIDs {
        if id == deviceID {
            return fmt.Errorf("设备已在分组中: %s", deviceID)
        }
    }
    // ...
}
```

### 3.3 请求处理器

**文件位置：** `internal/handler/handler.go`

**核心功能：**
- HTTP请求处理
- 参数验证
- 错误处理
- 响应格式化

**开发要点：**

1. **HTTP方法检查**
```go
func (h *Handler) RegisterDevice(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
        return
    }
    // ...
}
```

2. **参数验证**
```go
var req RegisterRequest
if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
    h.writeError(w, http.StatusBadRequest, "Invalid request body")
    return
}

if req.Name == "" || req.Type == "" {
    h.writeError(w, http.StatusBadRequest, "Name and type are required")
    return
}
```

3. **统一响应格式**
```go
type Response struct {
    Code    int         `json:"code"`
    Message string      `json:"message"`
    Data    interface{} `json:"data,omitempty"`
}

func (h *Handler) writeSuccess(w http.ResponseWriter, message string, data interface{}) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(Response{
        Code:    0,
        Message: message,
        Data:    data,
    })
}
```

## 4. API开发

### 4.1 设备管理API

#### 注册设备

```
POST /api/device/register

请求体：
{
    "name": "温度传感器",
    "type": "sensor",
    "metadata": {
        "location": "office"
    }
}

响应：
{
    "code": 0,
    "message": "设备注册成功",
    "data": {
        "id": "DEV-1234567890",
        "name": "温度传感器",
        "type": "sensor",
        "status": "online",
        "battery": 100,
        "signal": 100,
        "created_at": "2024-01-01T00:00:00Z"
    }
}
```

#### 获取设备

```
GET /api/device/get?id=DEV-1234567890

响应：
{
    "code": 0,
    "message": "Success",
    "data": {
        "id": "DEV-1234567890",
        "name": "温度传感器",
        "type": "sensor",
        "status": "online",
        "battery": 85,
        "signal": 92,
        "firmware": "v1.0.0",
        "ip_address": "192.168.1.100"
    }
}
```

#### 列出设备

```
GET /api/device/list

响应：
{
    "code": 0,
    "message": "Success",
    "data": [
        {
            "id": "DEV-1234567890",
            "name": "温度传感器",
            "type": "sensor",
            "status": "online"
        },
        {
            "id": "DEV-1234567891",
            "name": "湿度传感器",
            "type": "sensor",
            "status": "offline"
        }
    ]
}
```

#### 更新状态

```
POST /api/device/status?id=DEV-1234567890

请求体：
{
    "battery": 85,
    "signal": 92,
    "firmware": "v1.0.0",
    "ip_address": "192.168.1.100"
}

响应：
{
    "code": 0,
    "message": "状态更新成功",
    "data": null
}
```

#### 发送命令

```
POST /api/device/command

请求体：
{
    "device_id": "DEV-1234567890",
    "command": "turn_on",
    "params": {
        "brightness": "100"
    }
}

响应：
{
    "code": 0,
    "message": "命令发送成功",
    "data": {
        "device_id": "DEV-1234567890",
        "command": "turn_on",
        "params": {
            "brightness": "100"
        },
        "status": "executed",
        "time": "2024-01-01T00:00:00Z"
    }
}
```

#### 删除设备

```
DELETE /api/device/delete?id=DEV-1234567890

响应：
{
    "code": 0,
    "message": "设备删除成功",
    "data": null
}
```

### 4.2 分组管理API

#### 创建分组

```
POST /api/group/create

请求体：
{
    "name": "办公室传感器",
    "description": "办公室内的所有传感器设备"
}

响应：
{
    "code": 0,
    "message": "分组创建成功",
    "data": {
        "id": "GRP-1234567890",
        "name": "办公室传感器",
        "description": "办公室内的所有传感器设备",
        "device_ids": [],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}
```

#### 列出分组

```
GET /api/group/list

响应：
{
    "code": 0,
    "message": "Success",
    "data": [
        {
            "id": "GRP-1234567890",
            "name": "办公室传感器",
            "description": "办公室内的所有传感器设备",
            "device_ids": ["DEV-1234567890"]
        }
    ]
}
```

#### 添加设备到分组

```
POST /api/group/add-device?group_id=GRP-1234567890

请求体：
{
    "device_id": "DEV-1234567890"
}

响应：
{
    "code": 0,
    "message": "设备添加到分组成功",
    "data": null
}
```

#### 从分组移除设备

```
DELETE /api/group/remove-device?group_id=GRP-1234567890&device_id=DEV-1234567890

响应：
{
    "code": 0,
    "message": "设备从分组移除成功",
    "data": null
}
```

#### 获取分组设备

```
GET /api/group/devices?group_id=GRP-1234567890

响应：
{
    "code": 0,
    "message": "Success",
    "data": [
        {
            "id": "DEV-1234567890",
            "name": "温度传感器",
            "type": "sensor",
            "status": "online"
        }
    ]
}
```

## 5. 错误处理

### 5.1 错误码定义

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 405 | 请求方法不允许 |
| 500 | 服务器内部错误 |

### 5.2 错误响应格式

```json
{
    "code": -1,
    "message": "设备不存在: DEV-1234567890",
    "data": null
}
```

### 5.3 错误处理示例

```go
// 设备不存在
if _, exists := dm.devices[deviceID]; !exists {
    return nil, fmt.Errorf("设备不存在: %s", deviceID)
}

// 分组不存在
if _, exists := gm.groups[groupID]; !exists {
    return nil, fmt.Errorf("分组不存在: %s", groupID)
}

// 设备已存在
if _, exists := dm.devices[deviceID]; exists {
    return nil, fmt.Errorf("设备ID已存在: %s", deviceID)
}
```

## 6. 并发处理

### 6.1 读写锁

```go
// 读操作使用读锁
func (dm *DeviceManager) GetDevice(id string) (*Device, error) {
    dm.mu.RLock()
    defer dm.mu.RUnlock()
    // ...
}

// 写操作使用写锁
func (dm *DeviceManager) RegisterDevice(...) (*Device, error) {
    dm.mu.Lock()
    defer dm.mu.Unlock()
    // ...
}
```

### 6.2 事件通道

```go
// 创建带缓冲的通道
eventChan: make(chan *DeviceEvent, 100)

// 非阻塞发送
select {
case dm.eventChan <- event:
    // 发送成功
default:
    // 通道满，记录日志
    log.Printf("事件通道已满")
}
```

### 6.3 并发测试

```go
func TestConcurrentAccess(t *testing.T) {
    dm := device.NewDeviceManager()

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            dm.RegisterDevice("设备", "sensor", nil)
        }()
    }

    wg.Wait()

    devices := dm.ListDevices()
    if len(devices) != 100 {
        t.Errorf("设备数量错误: got %d, want %d", len(devices), 100)
    }
}
```

## 7. 测试开发

### 7.1 单元测试

```go
func TestRegisterDevice(t *testing.T) {
    dm := device.NewDeviceManager()

    metadata := map[string]string{"location": "office"}
    dev, err := dm.RegisterDevice("温度传感器", "sensor", metadata)
    if err != nil {
        t.Fatalf("注册设备失败: %v", err)
    }

    if dev.Name != "温度传感器" {
        t.Errorf("设备名称错误: got %s, want %s", dev.Name, "温度传感器")
    }
}
```

### 7.2 集成测试

```go
func TestAPIRegisterDevice(t *testing.T) {
    server, _ := setupTestServer()
    defer server.Close()

    reqBody := handler.RegisterRequest{
        Name: "测试传感器",
        Type: "sensor",
    }

    body, _ := json.Marshal(reqBody)
    resp, err := http.Post(server.URL+"/api/device/register", "application/json", bytes.NewBuffer(body))
    if err != nil {
        t.Fatalf("请求失败: %v", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        t.Errorf("状态码错误: got %d, want %d", resp.StatusCode, http.StatusOK)
    }
}
```

### 7.3 基准测试

```go
func BenchmarkRegisterDevice(b *testing.B) {
    dm := device.NewDeviceManager()

    for i := 0; i < b.N; i++ {
        dm.RegisterDevice("设备", "sensor", nil)
    }
}
```

## 8. 代码规范

### 8.1 命名规范

- 包名：小写单词，如 `device`、`group`
- 结构体：大驼峰，如 `DeviceManager`、`GroupManager`
- 方法：大驼峰，如 `RegisterDevice`、`GetDevice`
- 变量：小驼峰，如 `deviceID`、`groupName`
- 常量：全大写，如 `StatusOnline`、`StatusOffline`

### 8.2 注释规范

```go
// RegisterDevice 注册设备
// 参数：
//   - name: 设备名称
//   - deviceType: 设备类型
//   - metadata: 设备元数据
// 返回：
//   - *Device: 设备信息
//   - error: 错误信息
func (dm *DeviceManager) RegisterDevice(name, deviceType string, metadata map[string]string) (*Device, error) {
    // ...
}
```

### 8.3 错误处理

```go
// 返回错误，不忽略
if err != nil {
    return nil, err
}

// 包装错误，提供上下文
if _, exists := dm.devices[deviceID]; !exists {
    return nil, fmt.Errorf("设备不存在: %s", deviceID)
}
```

## 9. 部署指南

### 9.1 编译

```bash
# 编译可执行文件
go build -o device-management cmd/server/main.go

# 交叉编译
GOOS=linux GOARCH=amd64 go build -o device-management-linux cmd/server/main.go
```

### 9.2 运行

```bash
# 直接运行
go run cmd/server/main.go

# 运行编译后的文件
./device-management
```

### 9.3 配置

```bash
# 环境变量配置
export PORT=8080
export LOG_LEVEL=info

# 命令行参数
./device-management --port=8080 --log-level=info
```

## 10. 调试技巧

### 10.1 日志输出

```go
import "log"

// 基本日志
log.Printf("设备注册: %s", deviceID)

// 错误日志
log.Printf("错误: %v", err)

// 调试日志
log.Printf("[DEBUG] 设备状态: %+v", device)
```

### 10.2 性能分析

```go
import "runtime/pprof"

// CPU分析
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()

// 内存分析
pprof.WriteHeapProfile(f)
```

### 10.3 调试工具

```bash
# Delve调试器
dlv debug cmd/server/main.go

# pprof
go tool pprof http://localhost:8080/debug/pprof/profile
```

## 11. 常见问题

### 11.1 编译错误

**问题：** `cannot find module`
**解决：** 运行 `go mod tidy`

### 11.2 并发问题

**问题：** 数据竞争
**解决：** 使用读写锁保护共享资源

### 11.3 内存泄漏

**问题：** 事件通道阻塞
**解决：** 使用带缓冲的通道，及时消费事件

## 12. 最佳实践

### 12.1 代码组织

- 按功能模块划分包
- 使用internal包限制访问
- 保持包的职责单一

### 12.2 错误处理

- 不忽略错误
- 提供有意义的错误信息
- 使用错误包装

### 12.3 测试

- 编写单元测试
- 测试正常和异常流程
- 使用表驱动测试

### 12.4 性能

- 使用读写锁
- 避免锁竞争
- 使用缓冲通道
