// Package rpc 定义了 MapReduce 系统的 RPC 消息类型。
// Coordinator 和 Worker 之间通过这些消息进行通信。
package rpc

import "time"

// TaskType 表示任务类型
type TaskType int

const (
	MapTask    TaskType = iota // Map 任务
	ReduceTask                 // Reduce 任务
	WaitTask                   // 等待任务 (没有空闲任务)
	ExitTask                   // 退出信号
)

// String 返回任务类型的字符串表示
func (t TaskType) String() string {
	switch t {
	case MapTask:
		return "Map"
	case ReduceTask:
		return "Reduce"
	case WaitTask:
		return "Wait"
	case ExitTask:
		return "Exit"
	default:
		return "Unknown"
	}
}

// RequestTaskArgs 是 Worker 请求任务的参数
type RequestTaskArgs struct {
	WorkerID string // Worker 唯一标识
}

// RequestTaskReply 是 Coordinator 返回的任务信息
type RequestTaskReply struct {
	TaskType   TaskType // 任务类型
	TaskID     int      // 任务 ID
	Filename   string   // 输入文件名 (Map 任务)
	NReduce    int      // Reduce 任务数
	NMap       int      // Map 任务数 (Reduce 任务使用)
	AllMapDone bool     // 所有 Map 任务是否完成
}

// ReportTaskArgs 是 Worker 报告任务完成的参数
type ReportTaskArgs struct {
	WorkerID string   // Worker 唯一标识
	TaskID   int      // 任务 ID
	TaskType TaskType // 任务类型
	Success  bool     // 是否成功
	Duration time.Duration // 执行耗时
}

// ReportTaskReply 是 Coordinator 的确认回复
type ReportTaskReply struct {
	OK bool
}

// HeartbeatArgs 是 Worker 心跳请求的参数
type HeartbeatArgs struct {
	WorkerID string
	Status   WorkerStatus
}

// HeartbeatReply 是 Coordinator 的心跳回复
type HeartbeatReply struct {
	OK     bool
	Leader string // Coordinator 地址
}

// WorkerStatus 表示 Worker 状态
type WorkerStatus struct {
	ActiveTasks int       // 当前活跃任务数
	TotalTasks  int       // 总完成任务数
	Uptime      time.Duration // 运行时间
	MemoryUsage int64     // 内存使用量 (bytes)
}
