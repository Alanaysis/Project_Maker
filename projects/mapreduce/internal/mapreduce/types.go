// Package mapreduce 定义了 MapReduce 框架的核心类型和接口。
package mapreduce

import "hash/fnv"

// KeyValue 是 MapReduce 的基本数据单元。
// Map 函数输出键值对列表，Reduce 函数处理相同 key 的所有 value。
type KeyValue struct {
	Key   string
	Value string
}

// MapFunc 是用户定义的 Map 函数类型。
// 输入: 文件名和文件内容
// 输出: 中间键值对列表
type MapFunc func(filename string, contents string) []KeyValue

// ReduceFunc 是用户定义的 Reduce 函数类型。
// 输入: key 和该 key 对应的所有 value
// 输出: 聚合后的结果
type ReduceFunc func(key string, values []string) string

// CombinerFunc 是可选的 Combiner 函数类型。
// 在 Map 端进行本地聚合，减少 Shuffle 数据量。
type CombinerFunc func(key string, values []string) string

// PartitionFunc 是分区函数类型。
// 决定 key 应该发送到哪个 Reduce 任务。
type PartitionFunc func(key string, nReduce int) int

// IHash 使用 FNV 哈希算法计算 key 的哈希值。
// 用于将 key 映射到对应的 Reduce 任务。
func IHash(key string) int {
	h := fnv.New32a()
	h.Write([]byte(key))
	return int(h.Sum32() & 0x7fffffff)
}

// DefaultPartition 使用默认的哈希分区策略。
func DefaultPartition(key string, nReduce int) int {
	return IHash(key) % nReduce
}

// Phase 表示 MapReduce 的执行阶段
type Phase int

const (
	MapPhase    Phase = iota // Map 阶段
	ReducePhase              // Reduce 阶段
	AllDone                  // 全部完成
)

// String 返回阶段的字符串表示
func (p Phase) String() string {
	switch p {
	case MapPhase:
		return "MapPhase"
	case ReducePhase:
		return "ReducePhase"
	case AllDone:
		return "AllDone"
	default:
		return "Unknown"
	}
}

// TaskStatus 表示任务状态
type TaskStatus int

const (
	TaskIdle       TaskStatus = iota // 空闲
	TaskInProgress                   // 执行中
	TaskCompleted                    // 已完成
	TaskFailed                       // 失败
)

// String 返回任务状态的字符串表示
func (s TaskStatus) String() string {
	switch s {
	case TaskIdle:
		return "Idle"
	case TaskInProgress:
		return "InProgress"
	case TaskCompleted:
		return "Completed"
	case TaskFailed:
		return "Failed"
	default:
		return "Unknown"
	}
}

// TaskInfo 存储任务的元信息
type TaskInfo struct {
	ID         int          // 任务 ID
	Status     TaskStatus   // 任务状态
	WorkerID   string       // 执行该任务的 Worker ID
	StartTime  int64        // 开始执行时间 (Unix timestamp)
	RetryCount int          // 重试次数
	Filename   string       // 输入文件名 (Map 任务)
	OutputFile string       // 输出文件名
}

// WorkerInfo 存储 Worker 的信息
type WorkerInfo struct {
	ID           string    // Worker 唯一标识
	Address      string    // Worker 地址
	LastHeartbeat int64    // 最后心跳时间 (Unix timestamp)
	ActiveTasks  int       // 当前活跃任务数
	TotalTasks   int       // 总完成任务数
	IsAlive      bool      // 是否存活
}
