package task

import (
	"testing"

	"github.com/hpc-scheduler/pkg/models"
)

func TestCreateTask(t *testing.T) {
	tm := NewTaskManager()

	req := &models.SubmitTaskRequest{
		Name:    "test-task",
		Command: "echo hello",
		Resources: models.ResourceRequest{
			CPU:      2,
			MemoryMB: 512,
		},
	}

	task, err := tm.CreateTask(req)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if task.ID == "" {
		t.Error("expected task ID to be set")
	}
	if task.State != models.TaskStatePending {
		t.Errorf("expected state pending, got %s", task.State)
	}
	if task.Name != "test-task" {
		t.Errorf("expected name test-task, got %s", task.Name)
	}
}

func TestCreateTaskValidation(t *testing.T) {
	tm := NewTaskManager()

	// 空命令应该失败
	req := &models.SubmitTaskRequest{
		Command: "",
	}
	_, err := tm.CreateTask(req)
	if err == nil {
		t.Error("expected error for empty command")
	}
}

func TestGetTask(t *testing.T) {
	tm := NewTaskManager()

	req := &models.SubmitTaskRequest{
		Name:    "test-task",
		Command: "echo hello",
	}

	task, _ := tm.CreateTask(req)

	// 获取存在的任务
	got, err := tm.GetTask(task.ID)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got.ID != task.ID {
		t.Errorf("expected ID %s, got %s", task.ID, got.ID)
	}

	// 获取不存在的任务
	_, err = tm.GetTask("nonexistent")
	if err == nil {
		t.Error("expected error for nonexistent task")
	}
}

func TestUpdateTaskState(t *testing.T) {
	tm := NewTaskManager()

	req := &models.SubmitTaskRequest{
		Name:    "test-task",
		Command: "echo hello",
	}

	task, _ := tm.CreateTask(req)

	// 更新状态
	err := tm.UpdateTaskState(task.ID, models.TaskStateRunning)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	got, _ := tm.GetTask(task.ID)
	if got.State != models.TaskStateRunning {
		t.Errorf("expected state running, got %s", got.State)
	}

	// 验证状态索引
	pendingTasks := tm.GetTasksByState(models.TaskStatePending)
	if len(pendingTasks) != 0 {
		t.Errorf("expected 0 pending tasks, got %d", len(pendingTasks))
	}

	runningTasks := tm.GetTasksByState(models.TaskStateRunning)
	if len(runningTasks) != 1 {
		t.Errorf("expected 1 running task, got %d", len(runningTasks))
	}
}

func TestCancelTask(t *testing.T) {
	tm := NewTaskManager()

	req := &models.SubmitTaskRequest{
		Name:    "test-task",
		Command: "echo hello",
	}

	task, _ := tm.CreateTask(req)

	// 取消任务
	err := tm.CancelTask(task.ID)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	got, _ := tm.GetTask(task.ID)
	if got.State != models.TaskStateCancelled {
		t.Errorf("expected state cancelled, got %s", got.State)
	}
}

func TestCancelCompletedTask(t *testing.T) {
	tm := NewTaskManager()

	req := &models.SubmitTaskRequest{
		Name:    "test-task",
		Command: "echo hello",
	}

	task, _ := tm.CreateTask(req)
	tm.MarkTaskRunning(task.ID)
	tm.MarkTaskCompleted(task.ID, 0)

	// 不能取消已完成的任务
	err := tm.CancelTask(task.ID)
	if err == nil {
		t.Error("expected error when cancelling completed task")
	}
}

func TestMarkTaskRunning(t *testing.T) {
	tm := NewTaskManager()

	req := &models.SubmitTaskRequest{
		Name:    "test-task",
		Command: "echo hello",
	}

	task, _ := tm.CreateTask(req)

	err := tm.MarkTaskRunning(task.ID)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	got, _ := tm.GetTask(task.ID)
	if got.State != models.TaskStateRunning {
		t.Errorf("expected state running, got %s", got.State)
	}
	if got.StartedAt == nil {
		t.Error("expected StartedAt to be set")
	}
}

func TestMarkTaskCompleted(t *testing.T) {
	tm := NewTaskManager()

	req := &models.SubmitTaskRequest{
		Name:    "test-task",
		Command: "echo hello",
	}

	task, _ := tm.CreateTask(req)
	tm.MarkTaskRunning(task.ID)

	err := tm.MarkTaskCompleted(task.ID, 0)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	got, _ := tm.GetTask(task.ID)
	if got.State != models.TaskStateCompleted {
		t.Errorf("expected state completed, got %s", got.State)
	}
	if got.ExitCode == nil || *got.ExitCode != 0 {
		t.Errorf("expected exit code 0, got %v", got.ExitCode)
	}
	if got.CompletedAt == nil {
		t.Error("expected CompletedAt to be set")
	}
}

func TestIncrementRetry(t *testing.T) {
	tm := NewTaskManager()

	req := &models.SubmitTaskRequest{
		Name:       "test-task",
		Command:    "echo hello",
		MaxRetries: 2,
	}

	task, _ := tm.CreateTask(req)

	// 第一次重试
	canRetry, err := tm.IncrementRetry(task.ID)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !canRetry {
		t.Error("expected to be able to retry")
	}

	// 第二次重试
	canRetry, _ = tm.IncrementRetry(task.ID)
	if !canRetry {
		t.Error("expected to be able to retry")
	}

	// 第三次重试应该失败
	canRetry, _ = tm.IncrementRetry(task.ID)
	if canRetry {
		t.Error("should not be able to retry after max retries")
	}
}

func TestGetStats(t *testing.T) {
	tm := NewTaskManager()

	// 创建几个任务
	for i := 0; i < 5; i++ {
		tm.CreateTask(&models.SubmitTaskRequest{
			Name:    "test-task",
			Command: "echo hello",
		})
	}

	stats := tm.GetStats()
	if stats["total"] != 5 {
		t.Errorf("expected total 5, got %d", stats["total"])
	}
	if stats["pending"] != 5 {
		t.Errorf("expected pending 5, got %d", stats["pending"])
	}
}
