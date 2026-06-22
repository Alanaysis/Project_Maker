# 技术设计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层 (Application)                    │
├─────────────────────────────────────────────────────────────┤
│                    输入事件系统 (Input Event)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 事件队列    │  │ 事件分发    │  │ 事件处理器  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    核心驱动层 (Core Driver)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 矩阵扫描    │  │ 中断处理    │  │ 去抖处理    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    硬件抽象层 (HAL)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ GPIO控制    │  │ 中断控制    │  │ 定时器      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    硬件层 (Hardware)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 矩阵键盘    │  │ 中断控制器  │  │ 微控制器    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
keyboard-driver/
├── 核心模块
│   ├── keyboard_driver.c    # 主驱动逻辑
│   ├── matrix_scanner.c     # 矩阵扫描
│   ├── interrupt_handler.c  # 中断处理
│   ├── debounce.c           # 去抖算法
│   └── input_event.c        # 输入事件
├── 头文件
│   └── keyboard.h           # 公共接口
├── 测试
│   └── test_keyboard.c      # 单元测试
└── 示例
    └── example.c            # 使用示例
```

## 2. 数据结构设计

### 2.1 核心数据结构

#### 按键事件 (key_event_t)
```c
typedef struct {
    uint8_t row;            // 行号
    uint8_t col;            // 列号
    uint8_t keycode;        // 键值
    uint8_t state;          // 状态 (PRESS/RELEASE)
    uint32_t timestamp;     // 时间戳 (ms)
} key_event_t;
```

**设计考虑**:
- 使用8位整数节省空间
- 包含时间戳用于去抖和排序
- 状态字段支持多种按键状态

#### 键盘矩阵 (matrix_t)
```c
typedef struct {
    uint8_t state[MATRIX_ROWS][MATRIX_COLS];      // 当前状态
    uint8_t prev_state[MATRIX_ROWS][MATRIX_COLS]; // 上一次状态
    uint32_t debounce_time[MATRIX_ROWS][MATRIX_COLS]; // 去抖时间
} matrix_t;
```

**设计考虑**:
- 保存上一次状态用于变化检测
- 每个按键独立的去抖时间
- 使用二维数组对应物理矩阵

#### 键盘设备 (keyboard_dev_t)
```c
typedef struct {
    matrix_t matrix;                // 键盘矩阵
    key_event_t event_queue[64];    // 事件队列
    int queue_head;                 // 队列头
    int queue_tail;                 // 队列尾
    bool initialized;               // 初始化标志
} keyboard_dev_t;
```

**设计考虑**:
- 包含完整的设备状态
- 使用循环队列管理事件
- 初始化标志防止误用

### 2.2 状态机设计

#### 按键状态机
```
        ┌──────────────────────────────────────┐
        │                                      │
        ▼                                      │
   ┌─────────┐    按下    ┌─────────────┐      │
   │  IDLE   │───────────►│ DEBOUNCING  │      │
   └─────────┘            └─────────────┘      │
        ▲                        │              │
        │                        │ 超时且按下   │
        │ 释放                   ▼              │
        │                 ┌─────────────┐      │
        │                 │  PRESSED    │      │
        │                 └─────────────┘      │
        │                        │              │
        │                        │ 释放         │
        │                        ▼              │
        │                 ┌─────────────┐      │
        └─────────────────│  RELEASED   │      │
           超时且释放      └─────────────┘      │
                                      │         │
                                      └─────────┘
```

**状态说明**:
- `IDLE`: 空闲状态，无按键
- `DEBOUNCING`: 去抖状态，等待稳定
- `PRESSED`: 按下状态，按键已确认
- `RELEASED`: 释放状态，等待确认释放

### 2.3 队列设计

#### 循环队列
```
     head
       │
       ▼
   ┌───┬───┬───┬───┬───┬───┬───┬───┐
   │   │ E1│ E2│ E3│ E4│   │   │   │
   └───┴───┴───┴───┴───┴───┴───┴───┘
       ▲
       │
     tail
```

**队列操作**:
- 入队: `tail = (tail + 1) % SIZE`
- 出队: `head = (head + 1) % SIZE`
- 判空: `head == tail`
- 判满: `(tail + 1) % SIZE == head`

## 3. 接口设计

### 3.1 初始化接口

```c
// 初始化键盘设备
int keyboard_init(keyboard_dev_t *dev);

// 初始化输入事件系统
int input_event_init(void);

// 初始化去抖器
int debounce_init(debounce_type_t type, uint32_t debounce_time);
```

**设计原则**:
- 返回错误码，便于错误处理
- 参数简单，易于使用
- 幂等性，可重复调用

### 3.2 扫描接口

```c
// 扫描键盘矩阵
int keyboard_scan(keyboard_dev_t *dev);

// 完整矩阵扫描
int matrix_scan_full(matrix_t *matrix);

// 检测按键变化
int matrix_detect_changes(const matrix_t *matrix, key_event_t *events, int max_events);
```

**设计原则**:
- 分离扫描和变化检测
- 支持批量处理
- 限制事件数量防止溢出

### 3.3 中断接口

```c
// 中断处理函数
int keyboard_interrupt_handler(keyboard_dev_t *dev);

// 中断服务程序
int interrupt_service_routine(keyboard_dev_t *dev);

// 模拟中断触发
int interrupt_simulate_trigger(keyboard_dev_t *dev);
```

**设计原则**:
- 快速响应
- 最小化处理时间
- 支持模拟测试

### 3.4 去抖接口

```c
// 去抖处理
bool keyboard_debounce(keyboard_dev_t *dev, uint8_t row, uint8_t col);

// 通用去抖处理
bool debounce_process(uint8_t row, uint8_t col, bool pressed, uint32_t current_time);

// 获取按键状态
key_state_t debounce_get_state(uint8_t row, uint8_t col);
```

**设计原则**:
- 支持多种算法
- 可配置参数
- 状态可查询

### 3.5 事件接口

```c
// 报告按键事件
int keyboard_report_event(keyboard_dev_t *dev, key_event_t *event);

// 获取按键事件
int keyboard_get_event(keyboard_dev_t *dev, key_event_t *event);

// 提交输入事件
int input_event_report(const key_event_t *event);

// 获取输入事件
int input_event_get(key_event_t *event);
```

**设计原则**:
- 非阻塞操作
- 支持事件队列
- 支持事件回调

## 4. 算法设计

### 4.1 矩阵扫描算法

**算法流程**:
```
for each row in rows:
    set row pin LOW
    delay(10us)  // 等待电平稳定
    for each col in cols:
        read col pin
        if col == LOW:
            key pressed at (row, col)
    set row pin HIGH
```

**优化考虑**:
- 扫描延迟可配置
- 支持快速扫描模式
- 批量读取列状态

### 4.2 去抖算法

#### 定时器去抖
```
if (current_time - last_time >= debounce_time):
    if (state changed):
        update state
        return true
return false
```

#### 计数器去抖
```
if (pressed):
    counter++
    if (counter >= threshold):
        state = PRESSED
        return true
else:
    counter--
    if (counter <= -threshold):
        state = RELEASED
        return true
return false
```

#### 状态机去抖
```
switch (state):
    case IDLE:
        if (pressed):
            state = DEBOUNCING
            start_timer()
    case DEBOUNCING:
        if (timer expired):
            if (pressed):
                state = PRESSED
                return true
            else:
                state = IDLE
    case PRESSED:
        if (!pressed):
            state = RELEASED
            start_timer()
    case RELEASED:
        if (timer expired):
            if (!pressed):
                state = IDLE
                return true
            else:
                state = PRESSED
```

### 4.3 按键映射算法

**映射表设计**:
```c
static const uint8_t keymap[ROWS][COLS] = {
    {KEY_ESC, KEY_F1, KEY_F2, ...},
    {KEY_GRAVE, KEY_1, KEY_2, ...},
    ...
};
```

**映射函数**:
```c
uint8_t keyboard_map_key(uint8_t row, uint8_t col) {
    if (row >= ROWS || col >= COLS)
        return KEY_NONE;
    return keymap[row][col];
}
```

**扩展考虑**:
- 支持多层映射
- 支持动态映射
- 支持组合键

## 5. 错误处理设计

### 5.1 错误码定义

```c
#define KB_OK           0       // 成功
#define KB_ERR_INIT     -1      // 初始化错误
#define KB_ERR_SCAN     -2      // 扫描错误
#define KB_ERR_IRQ      -3      // 中断错误
#define KB_ERR_MAP      -4      // 映射错误
```

### 5.2 错误处理策略

**初始化错误**:
- 检查参数有效性
- 重试机制（最多3次）
- 返回错误码

**运行时错误**:
- 记录错误日志
- 继续运行
- 错误统计

**严重错误**:
- 安全停机
- 错误报告
- 恢复机制

### 5.3 防御性编程

**参数检查**:
```c
if (dev == NULL) {
    return KB_ERR_INIT;
}
```

**边界检查**:
```c
if (row >= MATRIX_ROWS || col >= MATRIX_COLS) {
    return KEY_NONE;
}
```

**状态检查**:
```c
if (!dev->initialized) {
    return KB_ERR_INIT;
}
```

## 6. 性能优化设计

### 6.1 扫描优化

**批量扫描**:
- 一次扫描整行
- 减少GPIO操作次数
- 提高扫描效率

**快速扫描**:
- 减少扫描延迟
- 使用DMA传输
- 中断驱动扫描

### 6.2 去抖优化

**自适应去抖**:
- 根据按键特性调整
- 动态调整去抖时间
- 减少不必要的延迟

**选择性去抖**:
- 只对变化的按键去抖
- 减少处理开销
- 提高响应速度

### 6.3 事件处理优化

**批量处理**:
- 一次处理多个事件
- 减少函数调用开销
- 提高吞吐量

**优先级处理**:
- 重要事件优先处理
- 支持事件排序
- 减少延迟

## 7. 可扩展性设计

### 7.1 插件架构

**接口定义**:
```c
typedef struct {
    const char *name;
    int (*init)(void);
    int (*process)(key_event_t *event);
    void (*cleanup)(void);
} keyboard_plugin_t;
```

**插件管理**:
```c
int plugin_register(const keyboard_plugin_t *plugin);
int plugin_unregister(const char *name);
```

### 7.2 配置管理

**配置文件格式**:
```json
{
    "matrix": {
        "rows": 6,
        "cols": 14
    },
    "debounce": {
        "type": "state_machine",
        "time_ms": 5
    }
}
```

**配置加载**:
```c
int config_load(const char *filename);
int config_save(const char *filename);
```

### 7.3 动态映射

**映射表管理**:
```c
int keymap_load(const char *filename);
int keymap_save(const char *filename);
int keymap_set_layer(int layer, uint8_t row, uint8_t col, uint8_t keycode);
```

## 8. 测试设计

### 8.1 单元测试

**测试覆盖**:
- 初始化测试
- 扫描测试
- 中断测试
- 去抖测试
- 映射测试
- 事件测试

**测试方法**:
- Mock硬件接口
- 模拟输入信号
- 验证输出结果

### 8.2 集成测试

**测试场景**:
- 完整工作流程
- 多键同时按下
- 快速连续按键
- 错误恢复

### 8.3 性能测试

**测试指标**:
- 扫描延迟
- 中断响应时间
- 去抖准确性
- 事件处理吞吐量

## 9. 部署设计

### 9.1 编译环境

**工具链**:
- GCC编译器
- Make构建系统
- GDB调试器

**依赖库**:
- 标准C库
- POSIX线程库（可选）

### 9.2 运行环境

**操作系统**:
- Linux（主要）
- macOS（测试）
- Windows（实验性）

**硬件要求**:
- 无特殊要求（模拟运行）
- GPIO支持（实际硬件）

### 9.3 安装部署

**编译安装**:
```bash
make
make install
```

**配置文件**:
- `/etc/keyboard-driver/config.json`
- `~/.keyboard-driver/config.json`

## 10. 监控设计

### 10.1 日志系统

**日志级别**:
- ERROR: 错误信息
- WARN: 警告信息
- INFO: 一般信息
- DEBUG: 调试信息

**日志格式**:
```
[Timestamp] [Level] [Module] Message
```

### 10.2 性能监控

**监控指标**:
- 扫描频率
- 中断次数
- 事件处理延迟
- 错误率

**监控接口**:
```c
void monitor_dump_stats(void);
int monitor_get_metric(const char *name);
```

### 10.3 健康检查

**检查项目**:
- 内存使用
- 队列状态
- 错误统计
- 性能指标

**健康状态**:
- HEALTHY: 正常
- DEGRADED: 降级
- UNHEALTHY: 异常
