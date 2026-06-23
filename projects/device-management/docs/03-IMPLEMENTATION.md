# 设备管理 - 实现细节

## 1. 项目结构

```
device-management/
├── cmd/
│   └── server/
│       └── main.go           # 服务入口
├── docs/                      # 文档目录
├── internal/
│   ├── device/
│   │   └── device.go          # 设备核心逻辑
│   ├── group/
│   │   └── group.go           # 设备分组
│   └── handler/
│       └── handler.go         # 请求处理
├── test/                      # 测试
└── README.md
```

## 2. 核心模块实现

### 2.1 设备管理器 (DeviceManager)

```go
// internal/device/device.go

type DeviceManager struct {
    mu      sync.RWMutex
    devices map[string]*Device
    eventChan chan *DeviceEvent
}

func NewDeviceManager() *DeviceManager {
    return &DeviceManager{
        devices:   make(map[string]*Device),
        eventChan: make(chan *DeviceEvent, 100),
    }
}
```

**关键实现细节：**

1. **并发安全**
   - 使用 `sync.RWMutex` 保护共享资源
   - 读操作使用 `RLock()`，写操作使用 `Lock()`
   - 通过 `defer` 确保锁的释放

2. **设备ID生成**
   - 使用时间戳生成唯一ID
   - 格式：`DEV-{timestamp}`

3. **事件通知**
   - 使用带缓冲的channel（100）
   - 非阻塞发送，避免影响主流程

### 2.2 设备注册实现

```go
func (dm *DeviceManager) RegisterDevice(name, deviceType string, metadata map[string]string) (*Device, error) {
    dm.mu.Lock()
    defer dm.mu.Unlock()

    deviceID := generateDeviceID()

    // 检查设备ID是否已存在
    if _, exists := dm.devices[deviceID]; exists {
        return nil, fmt.Errorf("设备ID已存在: %s", deviceID)
    }

    now := time.Now()
    device := &Device{
        ID:        deviceID,
        Name:      name,
        Type:      deviceType,
        Status:    StatusOnline,
        LastSeen:  now,
        CreatedAt: now,
        Metadata:  metadata,
        Battery:   100,
        Signal:    100,
    }

    dm.devices[deviceID] = device

    // 发送注册事件
    dm.eventChan <- &DeviceEvent{
        Type:      "device_registered",
        DeviceID:  deviceID,
        Timestamp: now,
        Data:      device,
    }

    return device, nil
}
```

**实现要点：**

1. **原子性操作**
   - 在锁保护下完成设备创建和存储
   - 确保设备ID的唯一性检查

2. **默认值设置**
   - 新设备默认状态为 `online`
   - 默认电量和信号为100

3. **事件触发**
   - 注册成功后发送事件通知
   - 事件包含完整的设备信息

### 2.3 状态上报实现

```go
func (dm *DeviceManager) UpdateDeviceStatus(deviceID string, battery, signal int, firmware, ipAddress string) error {
    dm.mu.Lock()
    defer dm.mu.Unlock()

    device, exists := dm.devices[deviceID]
    if !exists {
        return fmt.Errorf("设备不存在: %s", deviceID)
    }

    device.Battery = battery
    device.Signal = signal
    device.Firmware = firmware
    device.IPAddress = ipAddress
    device.LastSeen = time.Now()

    // 发送状态更新事件
    dm.eventChan <- &DeviceEvent{
        Type:      "status_updated",
        DeviceID:  deviceID,
        Timestamp: time.Now(),
        Data: map[string]interface{}{
            "battery":  battery,
            "signal":   signal,
            "firmware": firmware,
        },
    }

    return nil
}
```

**实现要点：**

1. **状态更新**
   - 更新设备电量、信号、固件版本等信息
   - 更新最后在线时间

2. **事件通知**
   - 状态变化时发送事件
   - 事件包含变化的状态数据

### 2.4 设备分组实现

```go
// internal/group/group.go

type GroupManager struct {
    mu     sync.RWMutex
    groups map[string]*Group
    dm     *device.DeviceManager
}

func (gm *GroupManager) AddDeviceToGroup(groupID, deviceID string) error {
    gm.mu.Lock()
    defer gm.mu.Unlock()

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

    group.DeviceIDs = append(group.DeviceIDs, deviceID)
    group.UpdatedAt = time.Now()

    return nil
}
```

**实现要点：**

1. **依赖注入**
   - GroupManager 持有 DeviceManager 引用
   - 用于验证设备是否存在

2. **唯一性检查**
   - 添加设备前检查是否已在分组中
   - 避免重复添加

3. **时间戳更新**
   - 分组变更时更新 `UpdatedAt`

### 2.5 请求处理器实现

```go
// internal/handler/handler.go

type Handler struct {
    dm *device.DeviceManager
    gm *group.GroupManager
}

func (h *Handler) RegisterDevice(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
        return
    }

    var req RegisterRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        h.writeError(w, http.StatusBadRequest, "Invalid request body")
        return
    }

    if req.Name == "" || req.Type == "" {
        h.writeError(w, http.StatusBadRequest, "Name and type are required")
        return
    }

    device, err := h.dm.RegisterDevice(req.Name, req.Type, req.Metadata)
    if err != nil {
        h.writeError(w, http.StatusInternalServerError, err.Error())
        return
    }

    h.writeSuccess(w, "设备注册成功", device)
}
```

**实现要点：**

1. **HTTP方法检查**
   - 严格限制请求方法
   - 返回405 Method Not Allowed

2. **参数验证**
   - 验证必填字段
   - 返回400 Bad Request

3. **错误处理**
   - 捕获业务层错误
   - 返回合适的HTTP状态码

4. **响应格式**
   - 统一的成功/失败响应格式
   - JSON格式返回

### 2.6 路由配置

```go
func (h *Handler) SetupRoutes() *http.ServeMux {
    mux := http.NewServeMux()

    // 设备管理接口
    mux.HandleFunc("/api/device/register", h.RegisterDevice)
    mux.HandleFunc("/api/device/get", h.GetDevice)
    mux.HandleFunc("/api/device/list", h.ListDevices)
    mux.HandleFunc("/api/device/status", h.UpdateStatus)
    mux.HandleFunc("/api/device/command", h.SendCommand)
    mux.HandleFunc("/api/device/delete", h.DeleteDevice)

    // 分组管理接口
    mux.HandleFunc("/api/group/create", h.CreateGroup)
    mux.HandleFunc("/api/group/list", h.ListGroups)
    mux.HandleFunc("/api/group/add-device", h.AddDeviceToGroup)
    mux.HandleFunc("/api/group/remove-device", h.RemoveDeviceFromGroup)
    mux.HandleFunc("/api/group/devices", h.GetGroupDevices)

    return mux
}
```

## 3. 数据结构设计

### 3.1 设备状态枚举

```go
type DeviceStatus string

const (
    StatusOnline    DeviceStatus = "online"
    StatusOffline   DeviceStatus = "offline"
    StatusUpgrading DeviceStatus = "upgrading"
)
```

### 3.2 请求/响应结构

```go
// 设备注册请求
type RegisterRequest struct {
    Name     string            `json:"name"`
    Type     string            `json:"type"`
    Metadata map[string]string `json:"metadata,omitempty"`
}

// 状态更新请求
type StatusUpdateRequest struct {
    Battery  int    `json:"battery"`
    Signal   int    `json:"signal"`
    Firmware string `json:"firmware"`
    IP       string `json:"ip_address"`
}

// 控制命令请求
type CommandRequest struct {
    DeviceID string            `json:"device_id"`
    Command  string            `json:"command"`
    Params   map[string]string `json:"params,omitempty"`
}

// 通用响应
type Response struct {
    Code    int         `json:"code"`
    Message string      `json:"message"`
    Data    interface{} `json:"data,omitempty"`
}
```

## 4. 并发处理

### 4.1 读写锁使用

```go
// 读操作 - 使用读锁
func (dm *DeviceManager) GetDevice(deviceID string) (*Device, error) {
    dm.mu.RLock()
    defer dm.mu.RUnlock()
    
    device, exists := dm.devices[deviceID]
    if !exists {
        return nil, fmt.Errorf("设备不存在: %s", deviceID)
    }
    return device, nil
}

// 写操作 - 使用写锁
func (dm *DeviceManager) RegisterDevice(...) (*Device, error) {
    dm.mu.Lock()
    defer dm.mu.Unlock()
    // ...
}
```

### 4.2 事件通道

```go
// 创建带缓冲的通道
eventChan: make(chan *DeviceEvent, 100)

// 非阻塞发送
select {
case dm.eventChan <- event:
    // 发送成功
default:
    // 通道满，记录日志
    log.Printf("事件通道已满，丢弃事件: %s", event.Type)
}
```

## 5. 错误处理策略

### 5.1 错误类型定义

```go
var (
    ErrDeviceNotFound = errors.New("设备不存在")
    ErrGroupNotFound  = errors.New("分组不存在")
    ErrDeviceExists   = errors.New("设备已存在")
    ErrDeviceInGroup  = errors.New("设备已在分组中")
    ErrDeviceOffline  = errors.New("设备离线")
)
```

### 5.2 HTTP错误响应

```go
func (h *Handler) writeError(w http.ResponseWriter, statusCode int, message string) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(statusCode)
    json.NewEncoder(w).Encode(Response{
        Code:    -1,
        Message: message,
    })
}
```

## 6. 测试策略

### 6.1 单元测试

- 测试每个方法的正常流程
- 测试边界条件
- 测试错误处理

### 6.2 集成测试

- 测试API端点
- 测试模块间交互
- 测试并发场景

## 7. 性能优化

### 7.1 内存优化

- 使用map存储，O(1)查询
- 限制事件通道缓冲大小
- 及时清理过期数据

### 7.2 并发优化

- 读写锁分离
- 异步事件处理
- 限制并发数

## 8. 部署配置

### 8.1 服务启动

```go
func main() {
    dm := device.NewDeviceManager()
    gm := group.NewGroupManager(dm)
    h := handler.NewHandler(dm, gm)
    mux := h.SetupRoutes()

    // 启动事件监听
    go func() {
        for event := range dm.GetEventChannel() {
            log.Printf("设备事件: %s", event.Type)
        }
    }()

    http.ListenAndServe(":8080", mux)
}
```

### 8.2 配置项

- 服务端口：默认8080
- 事件缓冲大小：默认100
- 日志级别：默认INFO
