# Stream Processing Framework / 流式计算框架

> 一个用于学习流式计算概念的教育性 Go 框架

---

## English

### Overview

A lightweight stream processing framework implementing core concepts from
distributed stream processing systems (Apache Flink, Apache Kafka Streams,
Spark Streaming). This project is designed for learning and education,
not production use.

### Learning Objectives

- **Stream Processing Model**: Understand how data flows through a stream
  processing pipeline (source → processing → sink).
- **Window Aggregation**: Master tumbling, sliding, and session windows.
- **State Management**: Learn per-window and global state for continuous processing.
- **Watermarking**: Handle out-of-order events and late data gracefully.
- **Event-Time Processing**: Process data based on when events occurred,
  not when they were observed.
- **Trigger Mechanism**: Control when window results are emitted.

### Architecture

```
┌──────────┐    ┌──────────────┐    ┌───────────┐    ┌────────┐
│  Source   │───▶│ WindowAssign │───▶│ Aggregator│───▶│  Sink  │
│ (Input)   │    │ (Tumbling/   │    │ (Sum/Count│    │(Output) │
│           │    │  Sliding/     │    │ /Avg/etc) │    │        │
│           │    │  Session)     │    │           │    │        │
└──────────┘    └──────────────┘    └───────────┘    └────────┘
                      │                    │
                      ▼                    ▼
               ┌──────────────┐    ┌───────────┐
               │ Watermark    │    │  Trigger  │
               │ (Late data   │    │ (When to  │
               │  detection)  │    │  emit?)   │
               └──────────────┘    └───────────┘
```

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Event** | A data point with an event-time timestamp |
| **Window** | A time-bounded bucket for grouping events |
| **Watermark** | A progress guarantee: "no events before time T will arrive" |
| **Trigger** | Determines when window results are emitted |
| **State** | Per-window accumulators for continuous aggregation |
| **Source** | Interface for reading input events |
| **Sink** | Interface for writing output results |

### Window Types

| Window Type | Description | Use Case |
|-------------|-------------|----------|
| **Tumbling** | Non-overlapping, fixed-size windows | Hourly totals, daily reports |
| **Sliding** | Overlapping, fixed-size windows with slide interval | Rolling averages, moving totals |
| **Session** | Gap-based windows that grow with activity | User session analysis, click streams |

### Project Structure

```
stream-processing/
├── src/
│   ├── stream.go            # Core types: Event, Window, WindowAssigner, Aggregator, Watermark, StateManager, Trigger, Source/Sink interfaces
│   ├── windowed_stream.go   # WindowedStream: higher-level API with windowing support
│   └── session_window.go    # SessionWindow & SessionManager: dynamic session window management
├── examples/
│   ├── word_count.go        # Classic word count on streaming text
│   ├── sliding_window.go    # Sliding window temperature aggregation
│   ├── session_window.go    # Session window user behavior analysis
│   └── late_event_handling.go # Watermark progression and late event policies
├── tests/
│   └── stream_test.go       # Unit tests for all core components
├── go.mod
└── README.md
```

### How to Run Examples

```bash
cd projects/stream-processing

# Word count example
go run examples/word_count.go

# Sliding window example
go run examples/sliding_window.go

# Session window example
go run examples/session_window.go

# Late event handling example
go run examples/late_event_handling.go

# Run all tests
go test ./tests/
```

### Key Implementation Details

1. **Event-Time Assignment**: Each event carries both event-time (when it happened)
   and processing-time (when it was observed). Windows are assigned based on event-time.

2. **Watermark Progression**: Watermarks advance monotonically. The watermark is set
   to `max(event_time_seen - maxOutOfOrderness)`, allowing for out-of-order events.

3. **Late Event Handling**: Events that arrive after the watermark has passed their
   window are considered late. Four policies are supported:
   - `LateDiscard`: Drop the event
   - `LateOutput`: Send to a separate late sink
   - `LateSideOutput`: Send to a side output stream
   - `LateUpdate`: Re-open windows and re-aggregate (may produce duplicates)

4. **State Management**: Per-window state is stored in a `StateManager` keyed by
   `(window_start, window_end, window_type, partition)`. State persists across events
   within the same window.

5. **Trigger Mechanism**: Triggers determine when window results are computed and
   emitted. Two trigger types are implemented:
   - `CountTrigger`: Fires after N events in a window
   - `WatermarkTrigger`: Fires when watermark passes window end

---

## 中文

### 概述

一个轻量级的流式计算框架，实现了分布式流处理系统的核心概念（Apache Flink、
Apache Kafka Streams、Spark Streaming）。本项目用于学习和教育目的，不用于生产。

### 学习目标

- **流处理模型**：理解数据如何在流处理管道中流动（source → processing → sink）
- **窗口聚合**：掌握翻滚窗口、滑动窗口和会话窗口
- **状态管理**：学习用于连续处理的分窗口和全局状态
- **水位线机制**：优雅处理乱序事件和迟到数据
- **事件时间处理**：基于事件发生时间而非观测时间处理数据
- **触发机制**：控制窗口结果的输出时机

### 架构图

```
┌──────────┐    ┌──────────────┐    ┌───────────┐    ┌────────┐
│  数据源   │───▶│  窗口分配器   │───▶│  聚合器   │───▶│  输出  │
│ (Source)  │    │ (翻滚/滑动/  │    │ (求和/计数│    │ (Sink) │
│           │    │  会话窗口)    │    │ /平均等)  │    │        │
└──────────┘    └──────────────┘    └───────────┘    └────────┘
                      │                    │
                      ▼                    ▼
               ┌──────────────┐    ┌───────────┐
               │ 水位线        │    │  触发器   │
               │ (迟到数据检测)│    │ (何时输出)│
               └──────────────┘    └───────────┘
```

### 核心概念

| 概念 | 描述 |
|------|------|
| **事件 (Event)** | 带有事件时间戳的数据点 |
| **窗口 (Window)** | 用于分组事件的时间边界桶 |
| **水位线 (Watermark)** | 进度保证："不会在时间 T 之前收到事件" |
| **触发器 (Trigger)** | 决定何时输出窗口结果 |
| **状态 (State)** | 用于连续聚合的分窗口累加器 |
| **数据源 (Source)** | 读取输入事件的接口 |
| **输出 (Sink)** | 写入输出结果的接口 |

### 窗口类型

| 窗口类型 | 描述 | 使用场景 |
|----------|------|----------|
| **翻滚窗口** | 非重叠的固定大小窗口 | 每小时统计、每日报告 |
| **滑动窗口** | 重叠的固定大小窗口，带有滑动间隔 | 移动平均、滚动总计 |
| **会话窗口** | 基于空闲间隔的窗口，随活动增长 | 用户会话分析、点击流 |

### 项目结构

```
stream-processing/
├── src/
│   ├── stream.go            # 核心类型：Event, Window, WindowAssigner, Aggregator, Watermark, StateManager, Trigger, Source/Sink 接口
│   ├── windowed_stream.go   # WindowedStream：带窗口支持的高级 API
│   └── session_window.go    # SessionWindow 和 SessionManager：动态会话窗口管理
├── examples/
│   ├── word_count.go        # 经典流式文本词频统计
│   ├── sliding_window.go    # 滑动窗口温度聚合
│   ├── session_window.go    # 会话窗口用户行为分析
│   └── late_event_handling.go # 水位线演进和迟到事件策略
├── tests/
│   └── stream_test.go       # 所有核心组件的单元测试
├── go.mod
└── README.md
```

### 运行示例

```bash
cd projects/stream-processing

# 词频统计示例
go run examples/word_count.go

# 滑动窗口示例
go run examples/sliding_window.go

# 会话窗口示例
go run examples/session_window.go

# 迟到事件处理示例
go run examples/late_event_handling.go

# 运行所有测试
go test ./tests/
```

### 关键实现细节

1. **事件时间分配**：每个事件携带事件时间（何时发生）和处理时间（何时被观测到）。
   窗口基于事件时间分配。

2. **水位线演进**：水位线单调递增。水位线设置为 `max(观测到的事件时间 - 最大乱序容忍度)`，
   允许乱序事件。

3. **迟到事件处理**：在水位线经过其窗口后到达的事件被认为是迟到的。支持四种策略：
   - `LateDiscard`：丢弃事件
   - `LateOutput`：发送到单独的迟到输出
   - `LateSideOutput`：发送到侧输出流
   - `LateUpdate`：重新打开窗口并重新聚合（可能产生重复结果）

4. **状态管理**：分窗口状态存储在 `StateManager` 中，键为 `(window_start, window_end, window_type, partition)`。
   状态在同一个窗口的事件之间持久化。

5. **触发机制**：触发器决定何时计算和输出窗口结果。实现了两种触发器：
   - `CountTrigger`：窗口中 N 个事件后触发
   - `WatermarkTrigger`：水位线经过窗口结束时触发

---

## License

MIT
