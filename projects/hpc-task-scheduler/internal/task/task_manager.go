package task

import (
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/hpc-scheduler/pkg/models"
)

// TaskManager 任务管理器
type TaskManager struct {
	mu    sync.RWMutex
	tasks map[string]*models.Task
	// 按状态索引
	byState map[models.TaskState]map[string]bool
}

// NewTaskManager 创建任务管理器
func NewTaskManager() *TaskManager {
	tm := &TaskManager{
		tasks:   make(map[string]*models.Task),
		byState: make(map[models.TaskState]map[string]bool),
	}
	// 初始化状态索引
	for _, state := range []models.TaskState{
		models.TaskStatePending,
		models.TaskStateQueued,
		models.TaskStateRunning,
		models.TaskStateCompleted,
		models.TaskStateFailed,
		models.TaskStateCancelled,
		models.TaskStateRetrying,
	} {
		tm.byState[state] = make(map[string]bool)
	}
	return tm
}

// CreateTask 创建新任务
func (tm *TaskManager) CreateTask(req *models.SubmitTaskRequest) (*models.Task, error) {
	if req.Command == "" {
		return nil, fmt.Errorf("command is required")
	}
	if req.Resources.CPU <= 0 {
		req.Resources.CPU = 1
	}
	if req.Resources.MemoryMB <= 0 {
		req.Resources.MemoryMB = 256
	}

	task := &models.Task{
		ID:         uuid.New().String(),
		Name:       req.Name,
		State:      models.TaskStatePending,
		Priority:   req.Priority,
		Resources:  req.Resources,
		Command:    req.Command,
		Args:       req.Args,
		Env:        req.Env,
		Owner:      req.Owner,
		MaxRetries: req.MaxRetries,
		Timeout:    req.Timeout,
		CreatedAt:  time.Now(),
	}

	if task.Priority == 0 {
		task.Priority = models.PriorityNormal
	}
	if task.MaxRetries == 0 {
		task.MaxRetries = 3
	}

	tm.mu.Lock()
	defer tm.mu.Unlock()

	tm.tasks[task.ID] = task
	tm.byState[models.TaskStatePending][task.ID] = true

	return task, nil
}

// GetTask 获取任务
func (tm *TaskManager) GetTask(id string) (*models.Task, error) {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	task, ok := tm.tasks[id]
	if !ok {
		return nil, fmt.Errorf("task not found: %s", id)
	}
	return task, nil
}

// GetTasksByState 按状态获取任务
func (tm *TaskManager) GetTasksByState(state models.TaskState) []*models.Task {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	var tasks []*models.Task
	for id := range tm.byState[state] {
		if task, ok := tm.tasks[id]; ok {
			tasks = append(tasks, task)
		}
	}
	return tasks
}

// GetAllTasks 获取所有任务
func (tm *TaskManager) GetAllTasks() []*models.Task {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	tasks := make([]*models.Task, 0, len(tm.tasks))
	for _, task := range tm.tasks {
		tasks = append(tasks, task)
	}
	return tasks
}

// UpdateTaskState 更新任务状态
func (tm *TaskManager) UpdateTaskState(id string, newState models.TaskState) error {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	task, ok := tm.tasks[id]
	if !ok {
		return fmt.Errorf("task not found: %s", id)
	}

	oldState := task.State
	// 从旧状态索引中删除
	delete(tm.byState[oldState], id)

	// 更新状态
	task.State = newState

	// 添加到新状态索引
	tm.byState[newState][id] = true

	return nil
}

// CancelTask 取消任务
func (tm *TaskManager) CancelTask(id string) error {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	task, ok := tm.tasks[id]
	if !ok {
		return fmt.Errorf("task not found: %s", id)
	}

	if task.State == models.TaskStateCompleted || task.State == models.TaskStateFailed {
		return fmt.Errorf("cannot cancel task in state: %s", task.State)
	}

	oldState := task.State
	delete(tm.byState[oldState], id)

	task.State = models.TaskStateCancelled
	tm.byState[models.TaskStateCancelled][id] = true

	return nil
}

// MarkTaskRunning 标记任务为运行中
func (tm *TaskManager) MarkTaskRunning(id string) error {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	task, ok := tm.tasks[id]
	if !ok {
		return fmt.Errorf("task not found: %s", id)
	}

	if task.State != models.TaskStatePending && task.State != models.TaskStateQueued {
		return fmt.Errorf("task cannot transition from %s to running", task.State)
	}

	oldState := task.State
	delete(tm.byState[oldState], id)

	task.State = models.TaskStateRunning
	now := time.Now()
	task.StartedAt = &now
	tm.byState[models.TaskStateRunning][id] = true

	return nil
}

// MarkTaskCompleted 标记任务完成
func (tm *TaskManager) MarkTaskCompleted(id string, exitCode int) error {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	task, ok := tm.tasks[id]
	if !ok {
		return fmt.Errorf("task not found: %s", id)
	}

	oldState := task.State
	delete(tm.byState[oldState], id)

	task.State = models.TaskStateCompleted
	task.ExitCode = &exitCode
	now := time.Now()
	task.CompletedAt = &now
	tm.byState[models.TaskStateCompleted][id] = true

	return nil
}

// MarkTaskFailed 标记任务失败
func (tm *TaskManager) MarkTaskFailed(id string, errMsg string) error {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	task, ok := tm.tasks[id]
	if !ok {
		return fmt.Errorf("task not found: %s", id)
	}

	oldState := task.State
	delete(tm.byState[oldState], id)

	task.State = models.TaskStateFailed
	task.ErrorMsg = errMsg
	now := time.Now()
	task.CompletedAt = &now
	tm.byState[models.TaskStateFailed][id] = true

	return nil
}

// IncrementRetry 增加重试次数
func (tm *TaskManager) IncrementRetry(id string) (bool, error) {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	task, ok := tm.tasks[id]
	if !ok {
		return false, fmt.Errorf("task not found: %s", id)
	}

	task.RetryCount++
	if task.RetryCount > task.MaxRetries {
		return false, nil // 不能再重试
	}

	oldState := task.State
	delete(tm.byState[oldState], id)

	task.State = models.TaskStateRetrying
	tm.byState[models.TaskStateRetrying][id] = true

	return true, nil
}

// GetStats 获取任务统计
func (tm *TaskManager) GetStats() map[string]int {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	stats := make(map[string]int)
	for state, ids := range tm.byState {
		stats[string(state)] = len(ids)
	}
	stats["total"] = len(tm.tasks)
	return stats
}
