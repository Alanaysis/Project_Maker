# 设备管理 - 测试文档

## 1. 测试策略

### 1.1 测试层次

```
┌─────────────────────────────────────────┐
│           端到端测试 (E2E)               │
├─────────────────────────────────────────┤
│           集成测试 (Integration)          │
├─────────────────────────────────────────┤
│           单元测试 (Unit)                 │
└─────────────────────────────────────────┘
```

### 1.2 测试覆盖目标

- 单元测试覆盖率：> 80%
- 集成测试覆盖所有API端点
- 关键路径100%覆盖

## 2. 单元测试

### 2.1 设备管理器测试

#### 测试用例：设备注册

```go
func TestRegisterDevice(t *testing.T) {
    dm := device.NewDeviceManager()

    metadata := map[string]string{"location": "office"}
    dev, err := dm.RegisterDevice("温度传感器", "sensor", metadata)
    if err != nil {
        t.Fatalf("注册设备失败: %v", err)
    }

    // 验证设备属性
    if dev.Name != "温度传感器" {
        t.Errorf("设备名称错误: got %s, want %s", dev.Name, "温度传感器")
    }

    if dev.Type != "sensor" {
        t.Errorf("设备类型错误: got %s, want %s", dev.Type, "sensor")
    }

    if dev.Status != device.StatusOnline {
        t.Errorf("设备状态错误: got %s, want %s", dev.Status, device.StatusOnline)
    }
}
```

**验证点：**
- 设备注册成功
- 设备属性正确设置
- 设备状态为在线
- 生成唯一设备ID

#### 测试用例：获取设备

```go
func TestGetDevice(t *testing.T) {
    dm := device.NewDeviceManager()

    // 先注册设备
    dev, _ := dm.RegisterDevice("湿度传感器", "sensor", nil)

    // 获取设备
    got, err := dm.GetDevice(dev.ID)
    if err != nil {
        t.Fatalf("获取设备失败: %v", err)
    }

    if got.ID != dev.ID {
        t.Errorf("设备ID不匹配: got %s, want %s", got.ID, dev.ID)
    }

    // 测试不存在的设备
    _, err = dm.GetDevice("non-existent-id")
    if err == nil {
        t.Error("应该返回错误")
    }
}
```

**验证点：**
- 正确获取已注册设备
- 返回错误当设备不存在

#### 测试用例：列出设备

```go
func TestListDevices(t *testing.T) {
    dm := device.NewDeviceManager()

    // 注册多个设备
    dm.RegisterDevice("设备1", "sensor", nil)
    dm.RegisterDevice("设备2", "actuator", nil)
    dm.RegisterDevice("设备3", "gateway", nil)

    // 列出设备
    devices := dm.ListDevices()
    if len(devices) != 3 {
        t.Errorf("设备数量错误: got %d, want %d", len(devices), 3)
    }
}
```

**验证点：**
- 返回所有已注册设备
- 设备数量正确

#### 测试用例：更新设备状态

```go
func TestUpdateDeviceStatus(t *testing.T) {
    dm := device.NewDeviceManager()

    dev, _ := dm.RegisterDevice("传感器", "sensor", nil)

    // 更新状态
    err := dm.UpdateDeviceStatus(dev.ID, 80, 90, "v1.0", "192.168.1.100")
    if err != nil {
        t.Fatalf("更新设备状态失败: %v", err)
    }

    // 验证更新
    updated, _ := dm.GetDevice(dev.ID)
    if updated.Battery != 80 {
        t.Errorf("电量错误: got %d, want %d", updated.Battery, 80)
    }

    if updated.Signal != 90 {
        t.Errorf("信号强度错误: got %d, want %d", updated.Signal, 90)
    }

    if updated.Firmware != "v1.0" {
        t.Errorf("固件版本错误: got %s, want %s", updated.Firmware, "v1.0")
    }
}
```

**验证点：**
- 状态更新成功
- 电量、信号、固件版本正确更新
- 最后在线时间更新

#### 测试用例：设备上线/离线

```go
func TestSetDeviceOnlineOffline(t *testing.T) {
    dm := device.NewDeviceManager()

    dev, _ := dm.RegisterDevice("设备", "sensor", nil)

    // 设置离线
    err := dm.SetDeviceOffline(dev.ID)
    if err != nil {
        t.Fatalf("设置设备离线失败: %v", err)
    }

    offline, _ := dm.GetDevice(dev.ID)
    if offline.Status != device.StatusOffline {
        t.Errorf("设备状态错误: got %s, want %s", offline.Status, device.StatusOffline)
    }

    // 设置在线
    err = dm.SetDeviceOnline(dev.ID)
    if err != nil {
        t.Fatalf("设置设备在线失败: %v", err)
    }

    online, _ := dm.GetDevice(dev.ID)
    if online.Status != device.StatusOnline {
        t.Errorf("设备状态错误: got %s, want %s", online.Status, device.StatusOnline)
    }
}
```

**验证点：**
- 设备状态切换正确
- 离线状态设置成功
- 在线状态设置成功

#### 测试用例：删除设备

```go
func TestDeleteDevice(t *testing.T) {
    dm := device.NewDeviceManager()

    dev, _ := dm.RegisterDevice("临时设备", "sensor", nil)

    // 删除设备
    err := dm.DeleteDevice(dev.ID)
    if err != nil {
        t.Fatalf("删除设备失败: %v", err)
    }

    // 验证删除
    _, err = dm.GetDevice(dev.ID)
    if err == nil {
        t.Error("设备应该已被删除")
    }

    // 测试删除不存在的设备
    err = dm.DeleteDevice("non-existent-id")
    if err == nil {
        t.Error("应该返回错误")
    }
}
```

**验证点：**
- 设备删除成功
- 删除后无法获取设备
- 删除不存在的设备返回错误

#### 测试用例：设备事件

```go
func TestDeviceEvents(t *testing.T) {
    dm := device.NewDeviceManager()

    dev, _ := dm.RegisterDevice("事件测试设备", "sensor", nil)

    eventChan := dm.GetEventChannel()

    // 应该有注册事件
    event := <-eventChan
    if event.Type != "device_registered" {
        t.Errorf("事件类型错误: got %s, want %s", event.Type, "device_registered")
    }

    if event.DeviceID != dev.ID {
        t.Errorf("事件设备ID错误: got %s, want %s", event.DeviceID, dev.ID)
    }
}
```

**验证点：**
- 设备注册触发事件
- 事件类型正确
- 事件包含正确的设备ID

### 2.2 分组管理器测试

#### 测试用例：创建分组

```go
func TestCreateGroup(t *testing.T) {
    dm := device.NewDeviceManager()
    gm := group.NewGroupManager(dm)

    grp, err := gm.CreateGroup("办公室传感器", "办公室内的所有传感器设备")
    if err != nil {
        t.Fatalf("创建分组失败: %v", err)
    }

    if grp.Name != "办公室传感器" {
        t.Errorf("分组名称错误: got %s, want %s", grp.Name, "办公室传感器")
    }

    if len(grp.DeviceIDs) != 0 {
        t.Errorf("初始设备数量应该为0: got %d", len(grp.DeviceIDs))
    }
}
```

**验证点：**
- 分组创建成功
- 分组属性正确
- 初始设备列表为空

#### 测试用例：添加设备到分组

```go
func TestAddDeviceToGroup(t *testing.T) {
    dm := device.NewDeviceManager()
    gm := group.NewGroupManager(dm)

    dev, _ := dm.RegisterDevice("温度传感器", "sensor", nil)
    grp, _ := gm.CreateGroup("传感器组", "所有传感器")

    // 添加设备到分组
    err := gm.AddDeviceToGroup(grp.ID, dev.ID)
    if err != nil {
        t.Fatalf("添加设备到分组失败: %v", err)
    }

    // 验证设备已添加
    group, _ := gm.GetGroup(grp.ID)
    if len(group.DeviceIDs) != 1 {
        t.Errorf("分组设备数量错误: got %d, want %d", len(group.DeviceIDs), 1)
    }

    // 测试重复添加
    err = gm.AddDeviceToGroup(grp.ID, dev.ID)
    if err == nil {
        t.Error("应该返回错误")
    }
}
```

**验证点：**
- 设备添加成功
- 分组设备数量正确
- 重复添加返回错误

#### 测试用例：从分组移除设备

```go
func TestRemoveDeviceFromGroup(t *testing.T) {
    dm := device.NewDeviceManager()
    gm := group.NewGroupManager(dm)

    dev, _ := dm.RegisterDevice("传感器", "sensor", nil)
    grp, _ := gm.CreateGroup("测试组", "测试")

    gm.AddDeviceToGroup(grp.ID, dev.ID)

    // 移除设备
    err := gm.RemoveDeviceFromGroup(grp.ID, dev.ID)
    if err != nil {
        t.Fatalf("移除设备失败: %v", err)
    }

    // 验证设备已移除
    group, _ := gm.GetGroup(grp.ID)
    if len(group.DeviceIDs) != 0 {
        t.Errorf("分组设备数量应该为0: got %d", len(group.DeviceIDs))
    }
}
```

**验证点：**
- 设备移除成功
- 分组设备数量正确
- 移除不存在的设备返回错误

#### 测试用例：获取分组设备

```go
func TestGetGroupDevices(t *testing.T) {
    dm := device.NewDeviceManager()
    gm := group.NewGroupManager(dm)

    dev1, _ := dm.RegisterDevice("设备1", "sensor", nil)
    dev2, _ := dm.RegisterDevice("设备2", "sensor", nil)
    dev3, _ := dm.RegisterDevice("设备3", "actuator", nil)

    grp, _ := gm.CreateGroup("混合组", "混合设备")

    gm.AddDeviceToGroup(grp.ID, dev1.ID)
    gm.AddDeviceToGroup(grp.ID, dev2.ID)
    gm.AddDeviceToGroup(grp.ID, dev3.ID)

    // 获取分组设备
    devices, err := gm.GetGroupDevices(grp.ID)
    if err != nil {
        t.Fatalf("获取分组设备失败: %v", err)
    }

    if len(devices) != 3 {
        t.Errorf("设备数量错误: got %d, want %d", len(devices), 3)
    }
}
```

**验证点：**
- 返回分组内所有设备
- 设备数量正确
- 设备信息完整

### 2.3 请求处理器测试

#### 测试用例：注册设备API

```go
func TestAPIRegisterDevice(t *testing.T) {
    server, _ := setupTestServer()
    defer server.Close()

    reqBody := handler.RegisterRequest{
        Name: "测试传感器",
        Type: "sensor",
        Metadata: map[string]string{"location": "office"},
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

    var result handler.Response
    json.NewDecoder(resp.Body).Decode(&result)

    if result.Code != 0 {
        t.Errorf("响应代码错误: got %d, want %d", result.Code, 0)
    }
}
```

**验证点：**
- HTTP状态码200
- 响应代码为0（成功）
- 返回设备信息

#### 测试用例：发送控制命令API

```go
func TestAPISendCommand(t *testing.T) {
    server, _ := setupTestServer()
    defer server.Close()

    // 先注册设备
    reqBody := handler.RegisterRequest{
        Name: "可控设备",
        Type: "actuator",
    }
    body, _ := json.Marshal(reqBody)
    resp, _ := http.Post(server.URL+"/api/device/register", "application/json", bytes.NewBuffer(body))

    var regResult handler.Response
    json.NewDecoder(resp.Body).Decode(&regResult)
    resp.Body.Close()

    data, _ := json.Marshal(regResult.Data)
    var dev device.Device
    json.Unmarshal(data, &dev)

    // 发送命令
    cmdReq := handler.CommandRequest{
        DeviceID: dev.ID,
        Command:  "turn_on",
        Params:   map[string]string{"brightness": "100"},
    }
    cmdBody, _ := json.Marshal(cmdReq)
    resp, err := http.Post(server.URL+"/api/device/command", "application/json", bytes.NewBuffer(cmdBody))
    if err != nil {
        t.Fatalf("请求失败: %v", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        t.Errorf("状态码错误: got %d, want %d", resp.StatusCode, http.StatusOK)
    }
}
```

**验证点：**
- 设备注册成功
- 命令发送成功
- HTTP状态码200

## 3. 集成测试

### 3.1 完整流程测试

```go
func TestFullWorkflow(t *testing.T) {
    server, _ := setupTestServer()
    defer server.Close()

    // 1. 注册设备
    regReq := handler.RegisterRequest{
        Name: "集成测试设备",
        Type: "sensor",
    }
    body, _ := json.Marshal(regReq)
    resp, _ := http.Post(server.URL+"/api/device/register", "application/json", bytes.NewBuffer(body))
    
    var regResult handler.Response
    json.NewDecoder(resp.Body).Decode(&regResult)
    resp.Body.Close()
    
    data, _ := json.Marshal(regResult.Data)
    var dev device.Device
    json.Unmarshal(data, &dev)

    // 2. 更新状态
    statusReq := handler.StatusUpdateRequest{
        Battery:  75,
        Signal:   85,
        Firmware: "v2.0",
        IP:       "192.168.1.100",
    }
    body, _ = json.Marshal(statusReq)
    http.Post(server.URL+"/api/device/status?id="+dev.ID, "application/json", bytes.NewBuffer(body))

    // 3. 创建分组
    grpReq := handler.GroupRequest{
        Name:        "集成测试组",
        Description: "集成测试分组",
    }
    body, _ = json.Marshal(grpReq)
    resp, _ = http.Post(server.URL+"/api/group/create", "application/json", bytes.NewBuffer(body))
    
    var grpResult handler.Response
    json.NewDecoder(resp.Body).Decode(&grpResult)
    resp.Body.Close()
    
    grpData, _ := json.Marshal(grpResult.Data)
    var grp group.Group
    json.Unmarshal(grpData, &grp)

    // 4. 添加设备到分组
    addReq := handler.GroupDeviceRequest{DeviceID: dev.ID}
    body, _ = json.Marshal(addReq)
    http.Post(server.URL+"/api/group/add-device?group_id="+grp.ID, "application/json", bytes.NewBuffer(body))

    // 5. 获取分组设备
    resp, _ = http.Get(server.URL + "/api/group/devices?group_id=" + grp.ID)
    var devicesResult handler.Response
    json.NewDecoder(resp.Body).Decode(&devicesResult)
    resp.Body.Close()

    if devicesResult.Code != 0 {
        t.Errorf("获取分组设备失败: %s", devicesResult.Message)
    }
}
```

### 3.2 错误处理测试

```go
func TestErrorHandling(t *testing.T) {
    server, _ := setupTestServer()
    defer server.Close()

    // 测试获取不存在的设备
    resp, _ := http.Get(server.URL + "/api/device/get?id=non-existent")
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusNotFound {
        t.Errorf("状态码错误: got %d, want %d", resp.StatusCode, http.StatusNotFound)
    }

    // 测试无效请求体
    resp, _ = http.Post(server.URL+"/api/device/register", "application/json", bytes.NewBuffer([]byte("invalid")))
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusBadRequest {
        t.Errorf("状态码错误: got %d, want %d", resp.StatusCode, http.StatusBadRequest)
    }
}
```

## 4. 性能测试

### 4.1 基准测试

```go
func BenchmarkRegisterDevice(b *testing.B) {
    dm := device.NewDeviceManager()

    for i := 0; i < b.N; i++ {
        dm.RegisterDevice("设备", "sensor", nil)
    }
}

func BenchmarkGetDevice(b *testing.B) {
    dm := device.NewDeviceManager()
    dev, _ := dm.RegisterDevice("设备", "sensor", nil)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        dm.GetDevice(dev.ID)
    }
}

func BenchmarkListDevices(b *testing.B) {
    dm := device.NewDeviceManager()
    for i := 0; i < 1000; i++ {
        dm.RegisterDevice("设备", "sensor", nil)
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        dm.ListDevices()
    }
}
```

### 4.2 并发测试

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

## 5. 测试运行

### 5.1 运行所有测试

```bash
cd projects/device-management
go test ./...
```

### 5.2 运行特定测试

```bash
go test -v -run TestRegisterDevice ./test/
```

### 5.3 运行基准测试

```bash
go test -bench=. ./test/
```

### 5.4 查看测试覆盖率

```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## 6. 测试最佳实践

### 6.1 测试命名规范

- 测试函数以 `Test` 开头
- 使用描述性的测试名称
- 示例：`TestRegisterDevice_Success`

### 6.2 测试数据准备

- 使用辅助函数创建测试数据
- 每个测试独立，不依赖其他测试
- 测试后清理数据

### 6.3 断言使用

- 使用 `t.Errorf` 报告错误但继续执行
- 使用 `t.Fatalf` 报告错误并停止测试
- 提供清晰的错误消息

### 6.4 测试覆盖率

- 关注核心业务逻辑
- 测试正常流程和异常流程
- 测试边界条件

## 7. 持续集成

### 7.1 CI配置

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
        with:
          go-version: '1.21'
      - run: go test ./...
```

### 7.2 代码质量检查

```bash
# 静态分析
go vet ./...

# 代码格式检查
gofmt -l .

# 代码复杂度检查
gocyclo -over 15 .
```
