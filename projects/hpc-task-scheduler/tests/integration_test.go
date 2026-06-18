package tests

import (
	"testing"
	"time"

	"github.com/hpc-scheduler/internal/config"
	"github.com/hpc-scheduler/internal/resource"
	"github.com/hpc-scheduler/internal/scheduler"
	"github.com/hpc-scheduler/internal/task"
	"github.com/hpc-scheduler/pkg/models"
)

func TestIntegrationTaskLifecycle(t *testing.T) {
	// 初始化组件
	cfg := &config.Config{
		Scheduler: config.SchedulerConfig{
			Algorithm:   "fifo",
			IntervalMs:  100,
			MaxRetries:  3,
			TaskTimeout: 60,
		},
		Resources: config.ResourceConfig{
			TotalCPU:      8,
			TotalMemoryMB: 16384,
		},
	}

	rm := resource.NewResourceManager(cfg.Resources)
	tm := task.NewTaskManager()
	sched := scheduler.NewScheduler(cfg.Scheduler, rm, tm)

	// 启动调度器
	sched.Start()
	defer sched.Stop()

	// 创建并提交任务
	req := &models.SubmitTaskRequest{
		Name:    "integration-test-task",
		Command: "echo",
		Args:    []string{"hello"},
		Resources: models.ResourceRequest{
			CPU:      2,
			MemoryMB: 1024,
		},
		Priority:   models.PriorityNormal,
		MaxRetries: 3,
		Timeout:    60,
		Owner:      "test-user",
	}

	task, err := tm.CreateTask(req)
	if err != nil {
		t.Fatalf("Failed to create task: %v", err)
	}

	// 提交到调度器
	sched.SubmitTask(task)

	// 等待任务完成
	time.Sleep(5 * time.Second)

	// 检查任务状态
	task, err = tm.GetTask(task.ID)
	if err != nil {
		t.Fatalf("Failed to get task: %v", err)
	}

	// 任务应该已经完成或正在运行
	if task.State != models.TaskStateCompleted && task.State != models.TaskStateRunning {
		t.Errorf("Expected task to be completed or running, got %s", task.State)
	}

	// 检查资源状态
	if task.State == models.TaskStateCompleted {
		used := rm.GetUsed()
		if used.CPU != 0 || used.MemoryMB != 0 {
			t.Errorf("Expected resources to be released, got CPU=%d, Memory=%dMB",
				used.CPU, used.MemoryMB)
		}
	}
}

func TestIntegrationMultipleTasks(t *testing.T) {
	cfg := &config.Config{
		Scheduler: config.SchedulerConfig{
			Algorithm:   "priority",
			IntervalMs:  100,
			MaxRetries:  3,
			TaskTimeout: 60,
		},
		Resources: config.ResourceConfig{
			TotalCPU:      4,
			TotalMemoryMB: 8192,
		},
	}

	rm := resource.NewResourceManager(cfg.Resources)
	tm := task.NewTaskManager()
	sched := scheduler.NewScheduler(cfg.Scheduler, rm, tm)

	sched.Start()
	defer sched.Stop()

	// 提交多个任务
	tasks := []struct {
		name     string
		priority models.TaskPriority
		cpu      int
		memory   int
	}{
		{"low-priority", models.PriorityLow, 1, 512},
		{"high-priority", models.PriorityHigh, 2, 1024},
		{"normal-priority", models.PriorityNormal, 1, 256},
	}

	var taskIDs []string
	for _, tt := range tasks {
		req := &models.SubmitTaskRequest{
			Name:    tt.name,
			Command: "sleep",
			Args:    []string{"5"},
			Resources: models.ResourceRequest{
				CPU:      tt.cpu,
				MemoryMB: tt.memory,
			},
			Priority:   tt.priority,
			MaxRetries: 1,
			Timeout:    30,
			Owner:      "test-user",
		}

		task, err := tm.CreateTask(req)
		if err != nil {
			t.Fatalf("Failed to create task %s: %v", tt.name, err)
		}

		sched.SubmitTask(task)
		taskIDs = append(taskIDs, task.ID)
	}

	// 等待调度
	time.Sleep(2 * time.Second)

	// 检查队列状态
	queueLength := sched.GetQueueLength()
	if queueLength < 0 {
		t.Errorf("Invalid queue length: %d", queueLength)
	}

	// 检查资源分配
	totalCPU := cfg.Resources.TotalCPU
	totalMemory := cfg.Resources.TotalMemoryMB
	used := rm.GetUsed()

	if used.CPU > totalCPU {
		t.Errorf("Used CPU (%d) exceeds total (%d)", used.CPU, totalCPU)
	}
	if used.MemoryMB > totalMemory {
		t.Errorf("Used Memory (%dMB) exceeds total (%dMB)", used.MemoryMB, totalMemory)
	}
}

func TestIntegrationResourceExhaustion(t *testing.T) {
	cfg := &config.Config{
		Scheduler: config.SchedulerConfig{
			Algorithm:   "fifo",
			IntervalMs:  100,
			MaxRetries:  1,
			TaskTimeout: 30,
		},
		Resources: config.ResourceConfig{
			TotalCPU:      2,
			TotalMemoryMB: 2048,
		},
	}

	rm := resource.NewResourceManager(cfg.Resources)
	tm := task.NewTaskManager()
	sched := scheduler.NewScheduler(cfg.Scheduler, rm, tm)

	sched.Start()
	defer sched.Stop()

	// 提交一个占用大量资源的任务
	req1 := &models.SubmitTaskRequest{
		Name:    "resource-hungry",
		Command: "sleep",
		Args:    []string{"10"},
		Resources: models.ResourceRequest{
			CPU:      2,
			MemoryMB: 2048,
		},
		Priority:   models.PriorityNormal,
		MaxRetries: 1,
		Timeout:    30,
		Owner:      "test-user",
	}

	task1, _ := tm.CreateTask(req1)
	sched.SubmitTask(task1)

	// 等待任务开始执行
	time.Sleep(2 * time.Second)

	// 尝试提交另一个任务，应该因为资源不足而等待
	req2 := &models.SubmitTaskRequest{
		Name:    "waiting-task",
		Command: "echo",
		Args:    []string{"hello"},
		Resources: models.ResourceRequest{
			CPU:      1,
			MemoryMB: 512,
		},
		Priority:   models.PriorityNormal,
		MaxRetries: 1,
		Timeout:    30,
		Owner:      "test-user",
	}

	task2, _ := tm.CreateTask(req2)
	sched.SubmitTask(task2)

	// 检查第二个任务是否在队列中等待
	time.Sleep(1 * time.Second)

	task2, _ = tm.GetTask(task2.ID)
	if task2.State == models.TaskStateRunning {
		t.Error("Second task should not be running due to resource exhaustion")
	}
}

func TestIntegrationSchedulerStats(t *testing.T) {
	cfg := &config.Config{
		Scheduler: config.SchedulerConfig{
			Algorithm:   "fifo",
			IntervalMs:  100,
			MaxRetries:  3,
			TaskTimeout: 60,
		},
		Resources: config.ResourceConfig{
			TotalCPU:      8,
			TotalMemoryMB: 16384,
		},
	}

	rm := resource.NewResourceManager(cfg.Resources)
	tm := task.NewTaskManager()
	sched := scheduler.NewScheduler(cfg.Scheduler, rm, tm)

	sched.Start()
	defer sched.Stop()

	// 提交一些任务
	for i := 0; i < 5; i++ {
		req := &models.SubmitTaskRequest{
			Name:    "stats-test",
			Command: "echo",
			Args:    []string{"hello"},
			Resources: models.ResourceRequest{
				CPU:      1,
				MemoryMB: 256,
			},
			Priority:   models.PriorityNormal,
			MaxRetries: 1,
			Timeout:    30,
			Owner:      "test-user",
		}

		task, _ := tm.CreateTask(req)
		sched.SubmitTask(task)
	}

	// 等待任务完成
	time.Sleep(10 * time.Second)

	// 检查统计信息
	stats := sched.GetStats()
	if stats.TotalScheduled < 0 {
		t.Error("TotalScheduled should be non-negative")
	}

	taskStats := tm.GetStats()
	if taskStats["total"] != 5 {
		t.Errorf("Expected 5 total tasks, got %d", taskStats["total"])
	}
}
