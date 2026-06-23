# 设备管理 - 架构设计

## 1. 系统架构概览

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │ Web控制台 │ │ 移动APP   │ │ 设备端    │ │ API客户端 │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              │
┌─────────────────────────────────────────────────────────────┐
│                      API网关层                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  路由 │ 认证 │ 限流 │ 日志 │ 监控                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      业务服务层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ 设备服务    │ │ 分组服务    │ │ 命令服务    │          │
│  │ (Device)    │ │ (Group)     │ │ (Command)   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ 状态服务    │ │ 注册服务    │ │ 事件服务    │          │
│  │ (Status)    │ │ (Register)  │ │ (Event)     │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ 设备存储    │ │ 状态存储    │ │ 事件存储    │          │
│  │ (Memory)    │ │ (TimeSeries)│ │ (Log)       │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心模块

| 模块 | 职责 | 主要功能 |
|------|------|----------|
| DeviceManager | 设备管理 | 注册、查询、更新、删除 |
| GroupManager | 分组管理 | 创建、删除、成员管理 |
| StatusManager | 状态管理 | 状态上报、状态查询 |
| CommandManager | 命令管理 | 命令下发、执行跟踪 |
| EventManager | 事件管理 | 事件生成、事件分发 |

## 2. 详细架构设计

### 2.1 设备管理模块

```go
// DeviceManager 设备管理器
type DeviceManager struct {
    devices   map[string]*Device    // 设备存储
    mu        sync.RWMutex          // 并发控制
    eventChan chan *DeviceEvent      // 事件通道
}

// 核心方法
- RegisterDevice()    // 注册设备
- GetDevice()        // 获取设备
- ListDevices()      // 列出设备
- UpdateDeviceStatus() // 更新状态
- DeleteDevice()     // 删除设备
```

### 2.2 分组管理模块

```go
// GroupManager 分组管理器
type GroupManager struct {
    groups map[string]*Group    // 分组存储
    dm     *DeviceManager       // 设备管理器引用
    mu     sync.RWMutex         // 并发控制
}

// 核心方法
- CreateGroup()           // 创建分组
- GetGroup()              // 获取分组
- ListGroups()            // 列出分组
- AddDeviceToGroup()      // 添加设备
- RemoveDeviceFromGroup() // 移除设备
- GetGroupDevices()       // 获取分组设备
- DeleteGroup()           // 删除分组
```

### 2.3 请求处理模块

```go
// Handler 请求处理器
type Handler struct {
    dm *DeviceManager    // 设备管理器
    gm *GroupManager     // 分组管理器
}

// API端点
- /api/device/register   // 设备注册
- /api/device/get        // 获取设备
- /api/device/list       // 列出设备
- /api/device/status     // 更新状态
- /api/device/command    // 发送命令
- /api/device/delete     // 删除设备
- /api/group/create      // 创建分组
- /api/group/list        // 列出分组
- /api/group/add-device  // 添加设备到分组
- /api/group/remove-device // 从分组移除设备
- /api/group/devices     // 获取分组设备
```

## 3. 数据模型

### 3.1 设备模型

```go
type Device struct {
    ID        string            `json:"id"`         // 设备唯一标识
    Name      string            `json:"name"`       // 设备名称
    Type      string            `json:"type"`       // 设备类型
    Status    DeviceStatus      `json:"status"`     // 设备状态
    GroupID   string            `json:"group_id"`   // 所属分组
    LastSeen  time.Time         `json:"last_seen"`  // 最后在线时间
    CreatedAt time.Time         `json:"created_at"` // 创建时间
    Metadata  map[string]string `json:"metadata"`   // 元数据
    Battery   int               `json:"battery"`    // 电量
    Signal    int               `json:"signal"`     // 信号强度
    Firmware  string            `json:"firmware"`   // 固件版本
    IPAddress string            `json:"ip_address"` // IP地址
}
```

### 3.2 分组模型

```go
type Group struct {
    ID          string    `json:"id"`          // 分组唯一标识
    Name        string    `json:"name"`        // 分组名称
    Description string    `json:"description"` // 分组描述
    DeviceIDs   []string  `json:"device_ids"`  // 设备ID列表
    CreatedAt   time.Time `json:"created_at"`  // 创建时间
    UpdatedAt   time.Time `json:"updated_at"`  // 更新时间
}
```

### 3.3 事件模型

```go
type DeviceEvent struct {
    Type      string      `json:"type"`      // 事件类型
    DeviceID  string      `json:"device_id"` // 设备ID
    Timestamp time.Time   `json:"timestamp"` // 时间戳
    Data      interface{} `json:"data"`      // 事件数据
}
```

## 4. 并发设计

### 4.1 读写锁策略

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

### 4.2 事件通道设计

```go
// 事件通道缓冲大小
const eventBufferSize = 100

// 非阻塞事件发送
select {
case dm.eventChan <- event:
    // 发送成功
default:
    // 通道满，丢弃事件或记录日志
}
```

## 5. 错误处理

### 5.1 错误类型

```go
var (
    ErrDeviceNotFound = fmt.Errorf("设备不存在")
    ErrGroupNotFound  = fmt.Errorf("分组不存在")
    ErrDeviceExists   = fmt.Errorf("设备已存在")
    ErrDeviceInGroup  = fmt.Errorf("设备已在分组中")
    ErrDeviceOffline  = fmt.Errorf("设备离线")
)
```

### 5.2 错误响应格式

```json
{
    "code": -1,
    "message": "设备不存在: DEV-001",
    "data": null
}
```

## 6. 性能考虑

### 6.1 内存管理

- 使用map存储设备和分组，O(1)查询
- 定期清理离线设备数据
- 限制事件通道缓冲大小

### 6.2 并发处理

- 使用读写锁分离读写操作
- 异步事件处理
- 限制并发请求数

### 6.3 扩展性

- 支持水平扩展
- 支持数据持久化
- 支持分布式部署

## 7. 安全设计

### 7.1 认证机制

- 设备注册时验证身份
- API访问使用Token认证
- 敏感操作需要额外验证

### 7.2 数据安全

- 敏感数据加密存储
- 传输过程使用HTTPS
- 定期备份数据

## 8. 监控与告警

### 8.1 监控指标

- 设备在线率
- 状态上报成功率
- 命令执行成功率
- API响应时间

### 8.2 告警规则

- 设备离线告警
- 电量低告警
- 信号弱告警
- 固件版本过旧告警
