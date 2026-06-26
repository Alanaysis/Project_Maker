# 🔌 嵌入式系统模块

> 11 个项目 | 涵盖 RTOS、设备驱动、通信协议、传感器融合、嵌入式 GUI、OTA、低功耗、文件系统、网络栈、安全、边缘推理

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [rtos-kernel](rtos-kernel/) | RTOS 内核 | C | ⭐⭐⭐⭐⭐ | ✅ |
| [device-driver](device-driver/) | 设备驱动框架 | C, Linux kernel | ⭐⭐⭐⭐⭐ | ✅ |
| [comm-protocol](comm-protocol/) | 通信协议栈 (UART/SPI/I2C) | C | ⭐⭐⭐⭐ | ✅ |
| [sensor-fusion](sensor-fusion/) | 传感器融合 | C/Python, numpy | ⭐⭐⭐⭐⭐ | ✅ |
| [embedded-gui](embedded-gui/) | 嵌入式 GUI 框架 | C | ⭐⭐⭐⭐⭐ | ✅ |
| [ota-upgrade](ota-upgrade/) | OTA 升级系统 | C/Go | ⭐⭐⭐⭐ | ✅ |
| [low-power](low-power/) | 低功耗设计 | C | ⭐⭐⭐⭐ | ✅ |
| [embedded-fs](embedded-fs/) | 嵌入式文件系统 | C | ⭐⭐⭐⭐⭐ | ✅ |
| [embedded-network](embedded-network/) | 嵌入式网络栈 | C | ⭐⭐⭐⭐⭐ | ✅ |
| [embedded-security](embedded-security/) | 嵌入式安全 | C | ⭐⭐⭐⭐⭐ | ✅ |
| [edge-inference](edge-inference/) | 边缘推理引擎 | C/C++ | ⭐⭐⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
RTOS 内核 → 设备驱动 → 通信协议 → 传感器融合 → 嵌入式 GUI → OTA → 低功耗
     ↓          ↓          ↓           ↓           ↓         ↓      ↓
  任务调度   字符设备    UART/SPI    卡尔曼滤波  渲染引擎  固件验证  睡眠模式
  同步原语   中断处理    I2C         姿态估计    事件处理  差分升级  DVFS
  上下文切换  MMIO       协议栈      互补滤波    字体渲染  双Bank   电源管理
```

### 推荐学习顺序

1. **rtos-kernel** (RTOS 内核)
   - 学习任务调度和上下文切换
   - 理解同步原语（信号量、互斥锁）
   - 掌握消息队列

2. **device-driver** (设备驱动框架)
   - 学习字符设备驱动
   - 理解中断处理
   - 掌握平台驱动模型

3. **comm-protocol** (通信协议栈)
   - 学习 UART/SPI/I2C 协议
   - 理解 DMA 传输
   - 掌握错误处理

4. **sensor-fusion** (传感器融合)
   - 学习 IMU 数据处理
   - 理解卡尔曼滤波
   - 掌握姿态估计

5. **embedded-gui** (嵌入式 GUI)
   - 学习渲染引擎
   - 理解 Widget 系统
   - 掌握事件处理

6. **ota-upgrade** (OTA 升级系统)
   - 学习固件验证
   - 理解双 Bank 机制
   - 掌握差分升级

7. **low-power** (低功耗设计)
   - 学习睡眠模式
   - 理解 DVFS
   - 掌握唤醒处理

8. **embedded-fs** (嵌入式文件系统)
   - 学习闪存管理
   - 理解磨损均衡
   - 掌握日志结构

9. **embedded-network** (嵌入式网络栈)
   - 学习 TCP/IP 协议
   - 理解 Socket API
   - 掌握 DHCP

10. **embedded-security** (嵌入式安全)
    - 学习安全启动
    - 理解加密通信
    - 掌握密钥存储

11. **edge-inference** (边缘推理引擎)
    - 学习模型量化
    - 理解推理优化
    - 掌握 INT8 推理

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **C** | 核心实现 | [C 官方文档](https://en.cppreference.com/w/c) |
| **Linux kernel** | 驱动开发 | [Linux 内核文档](https://www.kernel.org/doc/) |
| **Python** | 传感器融合 | [Python 官方文档](https://docs.python.org/3/) |
| **numpy** | 数值计算 | [NumPy 文档](https://numpy.org/) |

---

## 📚 学习资源

### 书籍
- 《实时操作系统》- Sanjoy Moham
- 《Linux 设备驱动》- Jonathan Corbet
- 《嵌入式系统设计与实践》- Wayne Wolf

### 开源项目
- [FreeRTOS](https://github.com/FreeRTOS/FreeRTOS)
- [Zephyr](https://github.com/zephyrproject-rtos/zephyr)
- [LVGL](https://github.com/lvgl/lvgl)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)
