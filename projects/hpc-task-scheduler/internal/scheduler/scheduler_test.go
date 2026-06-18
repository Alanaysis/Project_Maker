package scheduler

import (
	"testing"
	"time"

	"github.com/hpc-scheduler/internal/config"
	"github.com/hpc-scheduler/internal/resource"
	"github.com/hpc-scheduler/internal/task"
	"github.com/hpc-scheduler/pkg/models"
)

func TestFIFOAlgorithm(t *testing.T) {
	algo := &FIFOAlgorithm{}

	tasks := []*models.Task{
		{ID: "1", CreatedAt: time.Now().Add(-3 * time.Hour)},
		{ID: "2", CreatedAt: time.Now().Add(-1 * time.Hour)},
		{ID: "3", CreatedAt: time.Now().Add(-2 * time.Hour)},
	}

	algo.Sort(tasks)

	if tasks[0].ID != "1" {
		t.Errorf("expected first task to be 1, got %s", tasks[0].ID)
	}
	if tasks[1].ID != "3" {
		t.Errorf("expected second task to be 3, got %s", tasks[1].ID)
	}
	if tasks[2].ID != "2" {
		t.Errorf("expected third task to be 2, got %s", tasks[2].ID)
	}
}

func TestPriorityAlgorithm(t *testing.T) {
	algo := &PriorityAlgorithm{}

	tasks := []*models.Task{
		{ID: "1", Priority: models.PriorityLow, CreatedAt: time.Now()},
		{ID: "2", Priority: models.PriorityHigh, CreatedAt: time.Now()},
		{ID: "3", Priority: models.PriorityNormal, CreatedAt: time.Now()},
	}

	algo.Sort(tasks)

	if tasks[0].ID != "2" {
		t.Errorf("expected first task to be 2 (high priority), got %s", tasks[0].ID)
	}
	if tasks[1].ID != "3" {
		t.Errorf("expected second task to be 3 (normal priority), got %s", tasks[1].ID)
	}
	if tasks[2].ID != "1" {
		t.Errorf("expected third task to be 1 (low priority), got %s", tasks[2].ID)
	}
}

func TestFairAlgorithm(t *testing.T) {
	algo := &FairAlgorithm{}

	tasks := []*models.Task{
		{ID: "1", Priority: models.PriorityHigh, CreatedAt: time.Now()},
		{ID: "2", Priority: models.PriorityLow, CreatedAt: time.Now()},
		{ID: "3", Priority: models.PriorityNormal, CreatedAt: time.Now()},
	}

	algo.Sort(tasks)

	// 公平调度：低优先级优先
	if tasks[0].ID != "2" {
		t.Errorf("expected first task to be 2 (low priority), got %s", tasks[0].ID)
	}
}

func TestSchedulerSubmitTask(t *testing.T) {
	cfg := config.SchedulerConfig{
		Algorithm:   "fifo",
		IntervalMs:  100,
		MaxRetries:  3,
		TaskTimeout: 60,
	}
	rmCfg := config.ResourceConfig{
		TotalCPU:      8,
		TotalMemoryMB: 16384,
	}

	rm := resource.NewResourceManager(rmCfg)
	tm := task.NewTaskManager()
	sched := NewScheduler(cfg, rm, tm)

	task := &models.Task{
		ID:       "test-task-1",
		Name:     "Test Task",
		State:    models.TaskStatePending,
		Priority: models.PriorityNormal,
		Resources: models.ResourceRequest{
			CPU:      2,
			MemoryMB: 1024,
		},
		Command:   "echo hello",
		Timeout:   60,
		CreatedAt: time.Now(),
	}

	sched.SubmitTask(task)

	// 验证任务已加入队列
	if sched.GetQueueLength() != 1 {
		t.Errorf("expected queue length 1, got %d", sched.GetQueueLength())
	}
}

func TestSchedulerAlgorithmSelection(t *testing.T) {
	tests := []struct {
		algorithm string
		expected  string
	}{
		{"fifo", "fifo"},
		{"priority", "priority"},
		{"fair", "fair"},
		{"unknown", "fifo"}, // 默认是 FIFO
	}

	for _, tt := range tests {
		cfg := config.SchedulerConfig{
			Algorithm: tt.algorithm,
		}
		rmCfg := config.ResourceConfig{
			TotalCPU:      8,
			TotalMemoryMB: 16384,
		}

		rm := resource.NewResourceManager(rmCfg)
		tm := task.NewTaskManager()
		sched := NewScheduler(cfg, rm, tm)

		if sched.GetAlgorithmName() != tt.expected {
			t.Errorf("algorithm %s: expected %s, got %s",
				tt.algorithm, tt.expected, sched.GetAlgorithmName())
		}
	}
}
