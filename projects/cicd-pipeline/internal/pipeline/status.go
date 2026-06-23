package pipeline

import (
	"fmt"
	"time"
)

// Status 表示流水线/阶段/任务的执行状态
type Status int

const (
	StatusPending  Status = iota // 等待执行
	StatusRunning                // 执行中
	StatusSuccess                // 成功
	StatusFailed                 // 失败
	StatusSkipped                // 已跳过（前置依赖失败）
	StatusTimeout                // 超时
)

// String 返回状态的可读字符串
func (s Status) String() string {
	switch s {
	case StatusPending:
		return "pending"
	case StatusRunning:
		return "running"
	case StatusSuccess:
		return "success"
	case StatusFailed:
		return "failed"
	case StatusSkipped:
		return "skipped"
	case StatusTimeout:
		return "timeout"
	default:
		return "unknown"
	}
}

// Emoji 返回状态对应的 emoji 标记
func (s Status) Emoji() string {
	switch s {
	case StatusPending:
		return "⏳"
	case StatusRunning:
		return "🔄"
	case StatusSuccess:
		return "✅"
	case StatusFailed:
		return "❌"
	case StatusSkipped:
		return "⏭️"
	case StatusTimeout:
		return "⏰"
	default:
		return "❓"
	}
}

// ExecutionResult 单个任务的执行结果
type ExecutionResult struct {
	TaskName  string        // 任务名称
	Status    Status        // 执行状态
	Output    string        // 命令输出
	Error     string        // 错误信息
	StartTime time.Time     // 开始时间
	EndTime   time.Time     // 结束时间
	Duration  time.Duration // 执行耗时
	Retries   int           // 实际重试次数
}

// StageResult 阶段执行结果
type StageResult struct {
	StageName string            // 阶段名称
	Status    Status            // 执行状态
	Results   []ExecutionResult // 任务执行结果列表
	StartTime time.Time         // 开始时间
	EndTime   time.Time         // 结束时间
	Duration  time.Duration     // 执行耗时
}

// PipelineResult 流水线执行结果
type PipelineResult struct {
	PipelineName string        // 流水线名称
	Status       Status        // 执行状态
	StageResults []StageResult // 阶段执行结果列表
	StartTime    time.Time     // 开始时间
	EndTime      time.Time     // 结束时间
	Duration     time.Duration // 总执行耗时
}

// Summary 返回一行摘要
func (pr *PipelineResult) Summary() string {
	return fmt.Sprintf("[%s] %s - 耗时 %s",
		pr.Status.Emoji(), pr.PipelineName, pr.Duration.Round(time.Millisecond))
}

// StageSummary 返回阶段摘要
func (sr *StageResult) Summary() string {
	return fmt.Sprintf("[%s] %s - 耗时 %s (%d 个任务)",
		sr.Status.Emoji(), sr.StageName, sr.Duration.Round(time.Millisecond), len(sr.Results))
}
