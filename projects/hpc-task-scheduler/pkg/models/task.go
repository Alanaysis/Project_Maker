package models

import (
	"time"
)

// TaskState 任务状态
type TaskState string

const (
	TaskStatePending   TaskState = "pending"
	TaskStateQueued    TaskState = "queued"
	TaskStateRunning   TaskState = "running"
	TaskStateCompleted TaskState = "completed"
	TaskStateFailed    TaskState = "failed"
	TaskStateCancelled TaskState = "cancelled"
	TaskStateRetrying  TaskState = "retrying"
)

// TaskPriority 任务优先级
type TaskPriority int

const (
	PriorityLow    TaskPriority = 1
	PriorityNormal TaskPriority = 5
	PriorityHigh   TaskPriority = 10
)

// ResourceRequest 资源请求
type ResourceRequest struct {
	CPU    int `json:"cpu"`    // CPU 核数
	MemoryMB int `json:"memory_mb"` // 内存(MB)
}

// Task 任务定义
type Task struct {
	ID          string          `json:"id"`
	Name        string          `json:"name"`
	State       TaskState       `json:"state"`
	Priority    TaskPriority    `json:"priority"`
	Resources   ResourceRequest `json:"resources"`
	Command     string          `json:"command"`
	Args        []string        `json:"args"`
	Env         map[string]string `json:"env"`
	Owner       string          `json:"owner"`
	MaxRetries  int             `json:"max_retries"`
	RetryCount  int             `json:"retry_count"`
	ExitCode    *int            `json:"exit_code,omitempty"`
	ErrorMsg    string          `json:"error_msg,omitempty"`
	CreatedAt   time.Time       `json:"created_at"`
	StartedAt   *time.Time      `json:"started_at,omitempty"`
	CompletedAt *time.Time      `json:"completed_at,omitempty"`
	Timeout     int             `json:"timeout"` // 超时(秒)
}

// Node 节点定义
type Node struct {
	ID             string          `json:"id"`
	Hostname       string          `json:"hostname"`
	TotalResources ResourceRequest `json:"total_resources"`
	UsedResources  ResourceRequest `json:"used_resources"`
	State          NodeState       `json:"state"`
	Tasks          []string        `json:"tasks"`
}

// NodeState 节点状态
type NodeState string

const (
	NodeStateIdle     NodeState = "idle"
	NodeStateBusy     NodeState = "busy"
	NodeStateDown     NodeState = "down"
	NodeStateDraining NodeState = "draining"
)

// ClusterInfo 集群信息
type ClusterInfo struct {
	TotalNodes     int             `json:"total_nodes"`
	TotalResources ResourceRequest `json:"total_resources"`
	UsedResources  ResourceRequest `json:"used_resources"`
	PendingTasks   int             `json:"pending_tasks"`
	RunningTasks   int             `json:"running_tasks"`
}

// SubmitTaskRequest 提交任务请求
type SubmitTaskRequest struct {
	Name       string            `json:"name"`
	Priority   TaskPriority      `json:"priority"`
	Resources  ResourceRequest   `json:"resources"`
	Command    string            `json:"command"`
	Args       []string          `json:"args"`
	Env        map[string]string `json:"env"`
	Owner      string            `json:"owner"`
	MaxRetries int               `json:"max_retries"`
	Timeout    int               `json:"timeout"`
}

// TaskResponse 任务响应
type TaskResponse struct {
	Task    *Task   `json:"task"`
	Message string  `json:"message,omitempty"`
}

// TaskListResponse 任务列表响应
type TaskListResponse struct {
	Tasks []*Task `json:"tasks"`
	Total int     `json:"total"`
}
