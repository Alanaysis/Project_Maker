# 市场调研

## 1. 开源键盘固件项目

### 1.1 QMK Firmware

**项目地址**: https://github.com/qmk/qmk_firmware

**特点**:
- 最广泛使用的开源键盘固件
- 支持500+种键盘
- 使用C语言编写
- 功能丰富：宏、层、RGB控制、Tap Dance、Combo等
- 社区活跃，文档完善

**技术栈**:
- AVR微控制器（ATmega32U4等）
- ARM微控制器（STM32等）
- LUFA/ChibiOS USB栈

**学习价值**:
- 矩阵扫描实现
- USB HID协议
- 按键映射和层管理
- 低延迟优化

### 1.2 ZMK Firmware

**项目地址**: https://github.com/zmkfirmware/zmk

**特点**:
- 基于Zephyr RTOS的现代固件
- 专为无线键盘设计
- 支持蓝牙连接
- 使用设备树配置
- 正在快速发展

**技术栈**:
- Zephyr RTOS
- nRF Connect SDK
- 设备树（Devicetree）

**学习价值**:
- 实时操作系统应用
- 无线通信协议
- 电源管理
- 现代固件架构

### 1.3 Kaleidoscope

**项目地址**: https://github.com/keyboardio/Kaleidoscope

**特点**:
- Arduino-based固件
- 模块化插件系统
- 支持Keyboardio键盘
- 易于扩展

**学习价值**:
- 插件架构设计
- Arduino生态
- 模块化编程

### 1.4 KMK Firmware

**项目地址**: https://github.com/KMKfw/kmk_firmware

**特点**:
- CircuitPython实现
- 易于学习和修改
- 支持多种开发板
- 快速原型开发

**学习价值**:
- Python在嵌入式的应用
- 快速原型开发
- 脚本化配置

## 2. Linux内核键盘驱动

### 2.1 输入子系统架构

**核心组件**:
- `drivers/input/input.c` - 输入核心
- `drivers/input/evdev.c` - 事件设备
- `drivers/input/keyboard/atkbd.c` - AT键盘驱动
- `drivers/input/keyboard/usbkbd.c` - USB键盘驱动

**关键数据结构**:
```c
struct input_dev {
    const char *name;
    unsigned long evbit[BITS_TO_LONGS(EV_CNT)];
    unsigned long keybit[BITS_TO_LONGS(KEY_CNT)];
    // ...
};

struct input_event {
    struct timeval time;
    __u16 type;
    __u16 code;
    __s32 value;
};
```

### 2.2 中断处理机制

**中断处理流程**:
1. 硬件触发中断
2. 中断控制器路由到CPU
3. CPU执行中断处理程序
4. 驱动读取硬件状态
5. 生成输入事件
6. 通过输入子系统分发

**中断类型**:
- 硬中断（Hard IRQ）
- 软中断（Soft IRQ）
- 任务队列（Tasklet）
- 工作队列（Work Queue）

## 3. 技术变体和演进路径

### 3.1 扫描方式

**轮询扫描**:
- 定时扫描矩阵
- 实现简单
- 响应延迟较高
- CPU占用高

**中断扫描**:
- 按键触发中断
- 响应快速
- CPU占用低
- 实现复杂

**DMA扫描**:
- DMA传输矩阵数据
- 零CPU占用
- 适合高速扫描
- 硬件要求高

### 3.2 去抖算法

**硬件去抖**:
- RC电路滤波
- 施密特触发器
- 增加成本和复杂度

**软件去抖**:
- 定时器去抖
- 计数器去抖
- 状态机去抖
- 灵活可调

### 3.3 通信协议

**PS/2**:
- 传统协议
- 中断驱动
- 速度较慢

**USB HID**:
- 现代标准
- 即插即用
- 支持多种设备

**蓝牙 HID**:
- 无线连接
- 低功耗设计
- 延迟较高

## 4. 技术趋势

### 4.1 低延迟优化

- 扫描频率提升（1000Hz+）
- 中断处理优化
- USB轮询率提升
- 固件级优化

### 4.2 无线技术

- 蓝牙5.0+
- 2.4GHz专有协议
- 低功耗设计
- 多设备切换

### 4.3 可编程性

- 在线配置
- 宏录制
- 层管理
- RGB控制

## 5. 学习路径建议

### 初级阶段
1. 理解矩阵键盘原理
2. 学习GPIO编程
3. 实现基本扫描
4. 简单去抖处理

### 中级阶段
1. 中断处理机制
2. 输入子系统
3. USB HID协议
4. 高级去抖算法

### 高级阶段
1. 实时操作系统
2. 无线通信
3. 电源管理
4. 性能优化

## 6. 参考资源

- [Linux Input Subsystem Documentation](https://www.kernel.org/doc/html/latest/driver-api/input.html)
- [QMK Firmware Documentation](https://docs.qmk.fm/)
- [ZMK Documentation](https://zmk.dev/)
- [USB HID Specification](https://usb.org/document-library/device-class-definition-hid-111)
