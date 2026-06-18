package scheduler

import (
	"context"
	"log"
	"sort"
	"sync"
	"time"

	"github.com/hpc-scheduler/internal/config"
	"github.com/hpc-scheduler/internal/resource"
	"github.com/hpc-scheduler/internal/task"
	"github.com/hpc-scheduler/pkg/models"
)

// Scheduler 调度器
// ⭐ 重点：调度器是整个系统的大脑
// 负责决定任务执行顺序和资源分配策略
type Scheduler struct {
	mu sync.RWMutex

	cfg config.SchedulerConfig
	rm  *resource.ResourceManager
	tm  *task.TaskManager

	// 调度队列
	queue []*models.Task

	// 调度算法
	algorithm ScheduleAlgorithm

	// 上下文控制
	ctx    context.Context
	cancel context.CancelFunc

	// 统计信息
	stats SchedulerStats
}

// SchedulerStats 调度器统计
type SchedulerStats struct {
	TotalScheduled   int
	TotalCompleted   int
	TotalFailed      int
	TotalRetried     int
	AvgWaitTimeMs    int64
	AvgRunTimeMs     int64
}

// ScheduleAlgorithm 调度算法接口
// 💡 思考：为什么需要抽象调度算法？
// 答：方便扩展不同的调度策略，如 FIFO、优先级、公平调度等
type ScheduleAlgorithm interface {
	// Sort 对任务队列进行排序
	Sort(tasks []*models.Task)
	// Name 返回算法名称
	Name() string
}

// NewScheduler 创建调度器
func NewScheduler(cfg config.SchedulerConfig, rm *resource.ResourceManager, tm *task.TaskManager) *Scheduler {
	ctx, cancel := context.WithCancel(context.Background())

	s := &Scheduler{
		cfg:    cfg,
		rm:     rm,
		tm:     tm,
		queue:  make([]*models.Task, 0),
		ctx:    ctx,
		cancel: cancel,
	}

	// 根据配置选择调度算法
	switch cfg.Algorithm {
	case "priority":
		s.algorithm = &PriorityAlgorithm{}
	case "fair":
		s.algorithm = &FairAlgorithm{}
	default:
		s.algorithm = &FIFOAlgorithm{}
	}

	return s
}

// Start 启动调度器
func (s *Scheduler) Start() {
	go s.scheduleLoop()
	go s.monitorLoop()
}

// Stop 停止调度器
func (s *Scheduler) Stop() {
	s.cancel()
}

// SubmitTask 提交任务到调度队列
func (s *Scheduler) SubmitTask(task *models.Task) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.queue = append(s.queue, task)
	s.tm.UpdateTaskState(task.ID, models.TaskStateQueued)

	log.Printf("Task %s added to queue (algorithm: %s)", task.ID, s.algorithm.Name())
}

// GetStats 获取调度器统计
func (s *Scheduler) GetStats() SchedulerStats {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.stats
}

// GetAlgorithmName 获取当前调度算法名称
func (s *Scheduler) GetAlgorithmName() string {
	return s.algorithm.Name()
}

// GetQueueLength 获取队列长度
func (s *Scheduler) GetQueueLength() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.queue)
}

// scheduleLoop 调度循环
// ⭐ 重点：这是调度器的核心循环
func (s *Scheduler) scheduleLoop() {
	interval := time.Duration(s.cfg.IntervalMs) * time.Millisecond
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-s.ctx.Done():
			return
		case <-ticker.C:
			s.schedule()
		}
	}
}

// schedule 执行一次调度
func (s *Scheduler) schedule() {
	s.mu.Lock()

	// 没有任务需要调度
	if len(s.queue) == 0 {
		s.mu.Unlock()
		return
	}

	// 对队列排序
	s.algorithm.Sort(s.queue)

	// 尝试调度任务
	var scheduled []*models.Task
	var remaining []*models.Task

	for _, task := range s.queue {
		// 检查资源是否足够
		if s.rm.CheckAvailable(task.Resources) {
			scheduled = append(scheduled, task)
		} else {
			remaining = append(remaining, task)
		}
	}

	s.queue = remaining
	s.mu.Unlock()

	// 执行调度的任务
	for _, task := range scheduled {
		s.executeTask(task)
	}
}

// executeTask 执行任务
func (s *Scheduler) executeTask(task *models.Task) {
	// 分配资源
	err := s.rm.Allocate(task.ID, task.Resources)
	if err != nil {
		log.Printf("Failed to allocate resources for task %s: %v", task.ID, err)
		s.handleTaskFailure(task, err.Error())
		return
	}

	// 更新任务状态
	err = s.tm.MarkTaskRunning(task.ID)
	if err != nil {
		log.Printf("Failed to mark task %s as running: %v", task.ID, err)
		s.rm.Release(task.ID)
		return
	}

	log.Printf("Task %s started (CPU: %d, Memory: %dMB)",
		task.ID, task.Resources.CPU, task.Resources.MemoryMB)

	// 异步执行任务
	go s.runTask(task)
}

// runTask 运行任务
// 💡 思考：实际系统中，任务执行应该在哪里？
// 答：应该在独立的 worker 节点上执行，这里简化为本地执行
func (s *Scheduler) runTask(task *models.Task) {
	// 模拟任务执行
	// 实际系统中，这里会调用命令执行器或发送到 worker 节点
	timeout := time.Duration(task.Timeout) * time.Second
	if timeout == 0 {
		timeout = time.Duration(s.cfg.TaskTimeout) * time.Second
	}

	// 创建带超时的上下文
	ctx, cancel := context.WithTimeout(s.ctx, timeout)
	defer cancel()

	// 模拟执行（实际系统中这里会执行真实命令）
	done := make(chan error, 1)
	go func() {
		// 模拟任务执行时间
		time.Sleep(2 * time.Second)
		done <- nil
	}()

	select {
	case err := <-done:
		if err != nil {
			s.handleTaskFailure(task, err.Error())
		} else {
			s.handleTaskSuccess(task)
		}
	case <-ctx.Done():
		s.handleTaskFailure(task, "task timeout")
	}
}

// handleTaskSuccess 处理任务成功
func (s *Scheduler) handleTaskSuccess(task *models.Task) {
	// 释放资源
	s.rm.Release(task.ID)

	// 更新任务状态
	s.tm.MarkTaskCompleted(task.ID, 0)

	s.mu.Lock()
	s.stats.TotalCompleted++
	s.mu.Unlock()

	log.Printf("Task %s completed successfully", task.ID)
}

// handleTaskFailure 处理任务失败
func (s *Scheduler) handleTaskFailure(task *models.Task, errMsg string) {
	// 释放资源
	s.rm.Release(task.ID)

	// 尝试重试
	canRetry, _ := s.tm.IncrementRetry(task.ID)
	if canRetry {
		s.mu.Lock()
		s.stats.TotalRetried++
		s.queue = append(s.queue, task)
		s.mu.Unlock()

		log.Printf("Task %s failed, retrying (attempt %d/%d)",
			task.ID, task.RetryCount, task.MaxRetries)
	} else {
		s.tm.MarkTaskFailed(task.ID, errMsg)

		s.mu.Lock()
		s.stats.TotalFailed++
		s.mu.Unlock()

		log.Printf("Task %s failed permanently: %s", task.ID, errMsg)
	}
}

// monitorLoop 监控循环
// 💡 思考：监控循环的作用是什么？
// 答：定期检查任务状态，处理超时、僵尸任务等
func (s *Scheduler) monitorLoop() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-s.ctx.Done():
			return
		case <-ticker.C:
			s.monitor()
		}
	}
}

// monitor 执行监控检查
func (s *Scheduler) monitor() {
	// 检查运行中的任务
	runningTasks := s.tm.GetTasksByState(models.TaskStateRunning)
	for _, task := range runningTasks {
		if task.StartedAt != nil {
			elapsed := time.Since(*task.StartedAt)
			timeout := time.Duration(task.Timeout) * time.Second
			if timeout == 0 {
				timeout = time.Duration(s.cfg.TaskTimeout) * time.Second
			}

			if elapsed > timeout {
				log.Printf("Task %s exceeded timeout, marking as failed", task.ID)
				s.handleTaskFailure(task, "task timeout exceeded")
			}
		}
	}
}

// FIFOAlgorithm 先进先出调度算法
// ⭐ 重点：最简单的调度算法，按提交时间排序
type FIFOAlgorithm struct{}

func (a *FIFOAlgorithm) Sort(tasks []*models.Task) {
	// 按创建时间排序（先进先出）
	sort.Slice(tasks, func(i, j int) bool {
		return tasks[i].CreatedAt.Before(tasks[j].CreatedAt)
	})
}

func (a *FIFOAlgorithm) Name() string {
	return "fifo"
}

// PriorityAlgorithm 优先级调度算法
// ⭐ 重点：高优先级任务优先执行
type PriorityAlgorithm struct{}

func (a *PriorityAlgorithm) Sort(tasks []*models.Task) {
	sort.Slice(tasks, func(i, j int) bool {
		// 先按优先级降序，再按创建时间升序
		if tasks[i].Priority != tasks[j].Priority {
			return tasks[i].Priority > tasks[j].Priority
		}
		return tasks[i].CreatedAt.Before(tasks[j].CreatedAt)
	})
}

func (a *PriorityAlgorithm) Name() string {
	return "priority"
}

// FairAlgorithm 公平调度算法
// ⭐ 重点：保证每个用户获得公平的资源份额
type FairAlgorithm struct{}

func (a *FairAlgorithm) Sort(tasks []*models.Task) {
	// 按用户分组，然后轮询调度
	// 这里简化为按优先级和创建时间排序
	sort.Slice(tasks, func(i, j int) bool {
		// 同优先级下，按创建时间排序
		if tasks[i].Priority == tasks[j].Priority {
			return tasks[i].CreatedAt.Before(tasks[j].CreatedAt)
		}
		// 不同优先级，低优先级优先（公平性）
		return tasks[i].Priority < tasks[j].Priority
	})
}

func (a *FairAlgorithm) Name() string {
	return "fair"
}
