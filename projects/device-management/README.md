# Device Management (设备管理)

> An IoT Device Management System learning project implementing the core device management lifecycle.

---

## English

A learning project that implements the core components of an IoT device management system. It covers the complete device lifecycle from registration to retirement, including device authentication, status monitoring, remote command execution, firmware update management, device shadowing, and hierarchical device grouping.

### Learning Objectives

- **Understand device management**: Learn the core concepts of managing IoT devices at scale
- **Master device registration**: Implement device identity, authentication, and lifecycle management
- **Learn remote control**: Design and implement remote command execution for IoT devices

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  IoT Device Management System            │
├─────────────┬──────────────┬─────────────┬─────────────┤
│  Registry   │  Status      │  Command    │  Firmware   │
│  & Auth     │  Tracker     │  Executor   │  Manager    │
│             │              │             │             │
│ - Device    │ - Heartbeat  │ - Remote    │ - Update    │
│   register  │   monitoring │   commands  │   creation  │
│ - Auth      │ - Metrics    │ - Batch     │ - Progress  │
│   verify    │   history    │   execution │   tracking  │
│ - Lifecycle │ - Stale      │ - Command   │ - Checksum  │
│   management│   detection  │   history   │   verify    │
├─────────────┴──────────────┴─────────────┴─────────────┤
│                  Device Shadow Manager                   │
│                                                          │
│  desired state ──→ delta ──→ reported state              │
│  (application)          (what needs to change)           │
│                          (device)                        │
├─────────────────────────────────────────────────────────┤
│                  Group Manager                           │
│                                                          │
│  Building A ──→ Floor 1 ──→ Sensors / Actuators        │
│        └──→ Floor 2 ──→ Sensors / Cameras               │
└─────────────────────────────────────────────────────────┘
```

### Core Loop

```
Device Registration → Status Reporting → Remote Control → Firmware Update
```

1. **Device Registration**: Register device identity, generate authentication credentials
2. **Status Reporting**: Heartbeat mechanism for device monitoring and metrics collection
3. **Remote Control**: Send commands to devices, track execution status
4. **Firmware Update**: Manage firmware updates with progress tracking and integrity verification

### Project Structure

```
device-management/
├── go.mod                    # Go module definition
├── README.md                 # This file
├── src/                      # Core implementation
│   ├── types.go              # Core data types (Device, Shadow, etc.)
│   ├── registry.go           # Device registration and authentication
│   ├── status_tracker.go     # Device status and heartbeat tracking
│   ├── group_manager.go      # Device grouping and filtering
│   ├── command_executor.go   # Remote command execution
│   ├── firmware_manager.go   # Firmware update management
│   ├── shadow_manager.go     # Device shadow (digital twin)
│   └── lifecycle.go          # Device lifecycle management
├── examples/                 # Demo programs
│   ├── 01_registration_monitoring.go  # Device registration & monitoring
│   ├── 02_remote_commands.go          # Remote command execution
│   ├── 03_grouping_filtering.go       # Device grouping & filtering
│   └── 04_firmware_update.go          # Firmware update simulation
└── tests/                    # Unit tests
    ├── registry_test.go
    ├── status_tracker_test.go
    ├── group_manager_test.go
    ├── command_executor_test.go
    ├── firmware_manager_test.go
    ├── shadow_manager_test.go
    └── lifecycle_test.go
```

### How to Run Examples

```bash
# Run all examples
cd examples
go run 01_registration_monitoring.go
go run 02_remote_commands.go
go run 03_grouping_filtering.go
go run 04_firmware_update.go

# Run all tests
cd tests
go test -v ./...
```

### IoT Architecture Explanation

#### Device Registry
The registry is the central authority for device identity. Each device has:
- **Unique ID**: Generated at registration time
- **Authentication Secret**: Random token for secure identification
- **Metadata**: Name, type, location, tags for organization

#### Heartbeat Mechanism
Devices periodically send heartbeat messages containing:
- Current metrics (CPU, memory, temperature, battery)
- Timestamp for staleness detection
- Optional custom data

The system uses heartbeats to:
- Determine device online/offline status
- Track device health over time
- Detect and alert on stale devices

#### Device Shadow (Digital Twin)
A device shadow is a JSON document that maintains:
- **Desired state**: What the application wants the device to be
- **Reported state**: What the device actually reports
- **Delta**: The difference between desired and reported (reconciliation)

This enables applications to interact with devices even when offline.

#### Device Grouping
Devices are organized hierarchically:
- **Top-level**: Buildings, sites, or regions
- **Mid-level**: Floors, rooms, or zones
- **Bottom-level**: Individual devices

Tags enable cross-cutting organization (by device type, environment, etc.).

#### Remote Commands
Commands flow through a lifecycle:
1. **Created**: Command with payload is queued
2. **Pending**: Waiting for device to be available
3. **Executed**: Device has processed the command
4. **Failed**: Command could not be completed
5. **Cancelled**: Command was withdrawn before execution

#### Firmware Updates
Firmware update process includes:
1. **Creation**: Define target version, download URL, checksum
2. **Download**: Device downloads firmware, reports progress
3. **Installation**: Device installs firmware, may reboot
4. **Verification**: Checksum verification for integrity
5. **Completion**: Update recorded in device history

---

## 中文

物联网设备管理系统学习项目，实现设备管理的核心组件。涵盖从设备注册到退役的完整生命周期，包括设备认证、状态监控、远程控制、固件更新管理、设备影子和分层设备分组。

### 学习目标

- **理解设备管理**：学习大规模管理 IoT 设备的核心概念
- **掌握设备注册**：实现设备身份、认证和生命周期管理
- **学会远程控制**：设计和实现 IoT 设备的远程控制

### 核心循环

```
设备注册 → 状态上报 → 远程控制 → 固件升级
```

### 运行示例

```bash
# 运行所有示例
cd examples
go run 01_registration_monitoring.go
go run 02_remote_commands.go
go run 03_grouping_filtering.go
go run 04_firmware_update.go

# 运行所有测试
cd tests
go test -v ./...
```

### IoT 架构说明

#### 设备注册中心
注册中心是设备身份的中心权威。每个设备具有：
- **唯一 ID**：注册时生成
- **认证密钥**：用于安全标识的随机令牌
- **元数据**：名称、类型、位置、标签

#### 心跳机制
设备定期发送心跳消息，包含：
- 当前指标（CPU、内存、温度、电池）
- 时间戳用于过期检测
- 可选自定义数据

#### 设备影子（数字孪生）
设备影子是一个 JSON 文档，维护：
- **期望状态**：应用程序希望设备处于的状态
- **上报状态**：设备实际报告的状态
- **差异**：期望与上报之间的差异（状态同步）

#### 设备分组
设备按层次结构组织：
- **顶层**：建筑物、站点或区域
- **中层**：楼层、房间或区域
- **底层**：单个设备

标签支持跨层组织（按设备类型、环境等）。

#### 固件升级
固件更新流程包括：
1. **创建**：定义目标版本、下载 URL、校验和
2. **下载**：设备下载固件，报告进度
3. **安装**：设备安装固件，可能需要重启
4. **验证**：校验和验证确保完整性
5. **完成**：更新记录在设备历史中
