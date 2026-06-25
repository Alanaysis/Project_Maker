// Package coordinator 实现了 MapReduce 的 Coordinator。
// Coordinator 负责任务分配、状态管理和故障检测。
package coordinator

import (
	"fmt"
	"log"
	"net"
	"net/rpc"
	"os"
	"sync"
	"time"

	"mapreduce/internal/mapreduce"
	mrrpc "mapreduce/internal/rpc"
)

const (
	HeartbeatTimeout = 10 * time.Second // 心跳超时时间
	TaskTimeout      = 60 * time.Second // 任务超时时间
	MaxRetries       = 3                // 最大重试次数
)

// Coordinator 管理 MapReduce 任务的生命周期。
// 它负责:
// 1. 接收输入文件列表并创建 Map 任务
// 2. 响应 Worker 的任务请求
// 3. 跟踪任务状态
// 4. 检测 Worker 故障和任务超时
type Coordinator struct {
	mu          sync.Mutex                // 互斥锁，保护共享状态
	files       []string                  // 输入文件列表
	nReduce     int                       // Reduce 任务数
	nMap        int                       // Map 任务数
	phase       mapreduce.Phase           // 当前执行阶段
	tasks       map[int]*mapreduce.TaskInfo // 任务信息表
	workers     map[string]*mapreduce.WorkerInfo // Worker 信息表
	taskQueue   chan int                   // 空闲任务队列
	done        chan struct{}              // 完成信号
	startTime   time.Time                 // 启动时间
	verbose     bool                      // 是否输出详细日志
}

// New 创建新的 Coordinator 实例。
// 参数:
//   - files: 输入文件列表
//   - nReduce: Reduce 任务数量
//   - verbose: 是否输出详细日志
//
// 返回:
//   - *Coordinator: Coordinator 实例
func New(files []string, nReduce int, verbose bool) *Coordinator {
	c := &Coordinator{
		files:     files,
		nReduce:   nReduce,
		nMap:      len(files),
		phase:     mapreduce.MapPhase,
		tasks:     make(map[int]*mapreduce.TaskInfo),
		workers:   make(map[string]*mapreduce.WorkerInfo),
		taskQueue: make(chan int, len(files)),
		done:      make(chan struct{}),
		startTime: time.Now(),
		verbose:   verbose,
	}

	// 初始化 Map 任务
	for i, file := range files {
		c.tasks[i] = &mapreduce.TaskInfo{
			ID:       i,
			Status:   mapreduce.TaskIdle,
			Filename: file,
		}
		c.taskQueue <- i
	}

	// 启动超时检测协程
	go c.timeoutChecker()

	if verbose {
		log.Printf("[Coordinator] Initialized with %d files, %d reduce tasks", len(files), nReduce)
	}

	return c
}

// Start 启动 Coordinator 的 RPC 服务。
// 参数:
//   - port: 监听端口
func (c *Coordinator) Start(port int) error {
	// 注册 RPC 服务
	if err := rpc.Register(c); err != nil {
		return fmt.Errorf("register rpc: %w", err)
	}

	// 监听端口
	addr := fmt.Sprintf(":%d", port)
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		return fmt.Errorf("listen %s: %w", addr, err)
	}

	log.Printf("[Coordinator] Listening on %s", addr)

	// 接受连接
	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				select {
				case <-c.done:
					return
				default:
					log.Printf("[Coordinator] Accept error: %v", err)
					continue
				}
			}
			go rpc.ServeConn(conn)
		}
	}()

	return nil
}

// RequestTask 处理 Worker 的任务请求。
// 根据当前执行阶段返回 Map 或 Reduce 任务。
// RPC 方法: Coordinator.RequestTask
func (c *Coordinator) RequestTask(args *mrrpc.RequestTaskArgs, reply *mrrpc.RequestTaskReply) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	// 更新 Worker 信息
	c.updateWorker(args.WorkerID)

	switch c.phase {
	case mapreduce.MapPhase:
		return c.assignMapTask(args, reply)
	case mapreduce.ReducePhase:
		return c.assignReduceTask(args, reply)
	case mapreduce.AllDone:
		reply.TaskType = mrrpc.ExitTask
		return nil
	}

	return nil
}

// assignMapTask 分配 Map 任务。
// 从空闲任务队列中获取任务并分配给 Worker。
func (c *Coordinator) assignMapTask(args *mrrpc.RequestTaskArgs, reply *mrrpc.RequestTaskReply) error {
	// 检查队列是否有任务
	select {
	case taskID := <-c.taskQueue:
		task := c.tasks[taskID]
		if task.Status != mapreduce.TaskIdle {
			// 任务已被分配，跳过
			reply.TaskType = mrrpc.WaitTask
			return nil
		}

		// 分配任务
		task.Status = mapreduce.TaskInProgress
		task.WorkerID = args.WorkerID
		task.StartTime = time.Now().Unix()
		task.RetryCount++

		reply.TaskType = mrrpc.MapTask
		reply.TaskID = taskID
		reply.Filename = task.Filename
		reply.NReduce = c.nReduce

		if c.verbose {
			log.Printf("[Coordinator] Assigned Map task %d to Worker %s", taskID, args.WorkerID)
		}
		return nil
	default:
		// 没有空闲任务
		// 检查是否所有 Map 任务都已完成
		if c.allTasksCompleted(mapreduce.MapPhase) {
			// 切换到 Reduce 阶段
			c.transitionToReducePhase()
			reply.TaskType = mrrpc.WaitTask
			return nil
		}
		reply.TaskType = mrrpc.WaitTask
		return nil
	}
}

// assignReduceTask 分配 Reduce 任务。
// 从空闲 Reduce 任务队列中获取任务并分配给 Worker。
func (c *Coordinator) assignReduceTask(args *mrrpc.RequestTaskArgs, reply *mrrpc.RequestTaskReply) error {
	// 检查队列是否有任务
	select {
	case taskID := <-c.taskQueue:
		task := c.tasks[c.nMap+taskID]
		if task.Status != mapreduce.TaskIdle {
			reply.TaskType = mrrpc.WaitTask
			return nil
		}

		// 分配任务
		task.Status = mapreduce.TaskInProgress
		task.WorkerID = args.WorkerID
		task.StartTime = time.Now().Unix()
		task.RetryCount++

		reply.TaskType = mrrpc.ReduceTask
		reply.TaskID = taskID
		reply.NMap = c.nMap
		reply.NReduce = c.nReduce
		reply.AllMapDone = true

		if c.verbose {
			log.Printf("[Coordinator] Assigned Reduce task %d to Worker %s", taskID, args.WorkerID)
		}
		return nil
	default:
		// 检查是否所有 Reduce 任务都已完成
		if c.allTasksCompleted(mapreduce.ReducePhase) {
			// 切换到 AllDone 阶段
			c.phase = mapreduce.AllDone
			close(c.done)
			reply.TaskType = mrrpc.ExitTask
			log.Printf("[Coordinator] All tasks completed in %v", time.Since(c.startTime))
			return nil
		}
		reply.TaskType = mrrpc.WaitTask
		return nil
	}
}

// ReportTask 处理 Worker 的任务完成报告。
// 更新任务状态，如果失败则重新调度。
// RPC 方法: Coordinator.ReportTask
func (c *Coordinator) ReportTask(args *mrrpc.ReportTaskArgs, reply *mrrpc.ReportTaskReply) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	var taskID int
	if args.TaskType == mrrpc.MapTask {
		taskID = args.TaskID
	} else {
		taskID = c.nMap + args.TaskID
	}

	task, exists := c.tasks[taskID]
	if !exists {
		reply.OK = false
		return fmt.Errorf("task %d not found", taskID)
	}

	if args.Success {
		// 任务成功完成
		task.Status = mapreduce.TaskCompleted
		reply.OK = true

		if c.verbose {
			log.Printf("[Coordinator] %s task %d completed by Worker %s (took %v)",
				args.TaskType, args.TaskID, args.WorkerID, args.Duration)
		}
	} else {
		// 任务失败
		if task.RetryCount >= MaxRetries {
			// 超过最大重试次数
			task.Status = mapreduce.TaskFailed
			log.Printf("[Coordinator] %s task %d failed after %d retries",
				args.TaskType, args.TaskID, MaxRetries)
		} else {
			// 重新调度
			task.Status = mapreduce.TaskIdle
			task.WorkerID = ""
			c.taskQueue <- taskID - c.nMap*(int(args.TaskType))

			log.Printf("[Coordinator] %s task %d failed, rescheduling (retry %d/%d)",
				args.TaskType, args.TaskID, task.RetryCount, MaxRetries)
		}
		reply.OK = true
	}

	// 更新 Worker 信息
	if worker, exists := c.workers[args.WorkerID]; exists {
		worker.TotalTasks++
		worker.ActiveTasks--
	}

	return nil
}

// Heartbeat 处理 Worker 的心跳请求。
// RPC 方法: Coordinator.Heartbeat
func (c *Coordinator) Heartbeat(args *mrrpc.HeartbeatArgs, reply *mrrpc.HeartbeatReply) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.updateWorker(args.WorkerID)
	reply.OK = true
	return nil
}

// updateWorker 更新 Worker 信息。
// 如果 Worker 不存在则创建新记录。
func (c *Coordinator) updateWorker(workerID string) {
	if worker, exists := c.workers[workerID]; exists {
		worker.LastHeartbeat = time.Now().Unix()
		worker.IsAlive = true
	} else {
		c.workers[workerID] = &mapreduce.WorkerInfo{
			ID:            workerID,
			LastHeartbeat: time.Now().Unix(),
			IsAlive:       true,
		}
	}
}

// allTasksCompleted 检查指定阶段的所有任务是否完成。
func (c *Coordinator) allTasksCompleted(phase mapreduce.Phase) bool {
	var start, end int
	if phase == mapreduce.MapPhase {
		start, end = 0, c.nMap
	} else {
		start, end = c.nMap, c.nMap+c.nReduce
	}

	for i := start; i < end; i++ {
		if c.tasks[i].Status != mapreduce.TaskCompleted {
			return false
		}
	}
	return true
}

// transitionToReducePhase 从 Map 阶段切换到 Reduce 阶段。
func (c *Coordinator) transitionToReducePhase() {
	c.phase = mapreduce.ReducePhase

	// 初始化 Reduce 任务
	for i := 0; i < c.nReduce; i++ {
		c.tasks[c.nMap+i] = &mapreduce.TaskInfo{
			ID:     i,
			Status: mapreduce.TaskIdle,
		}
		c.taskQueue <- i
	}

	log.Printf("[Coordinator] Transitioning to Reduce phase (%d tasks)", c.nReduce)
}

// timeoutChecker 定期检查任务超时和 Worker 心跳超时。
func (c *Coordinator) timeoutChecker() {
	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-c.done:
			return
		case <-ticker.C:
			c.checkTimeouts()
		}
	}
}

// checkTimeouts 检查任务和 Worker 超时。
func (c *Coordinator) checkTimeouts() {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now().Unix()

	// 检查任务超时
	for _, task := range c.tasks {
		if task.Status == mapreduce.TaskInProgress {
			if now-task.StartTime > int64(TaskTimeout.Seconds()) {
				// 任务超时，重新调度
				log.Printf("[Coordinator] Task %d timeout, rescheduling", task.ID)
				task.Status = mapreduce.TaskIdle
				task.WorkerID = ""

				if task.ID < c.nMap {
					c.taskQueue <- task.ID
				} else {
					c.taskQueue <- task.ID - c.nMap
				}
			}
		}
	}

	// 检查 Worker 心跳超时
	for _, worker := range c.workers {
		if worker.IsAlive && now-worker.LastHeartbeat > int64(HeartbeatTimeout.Seconds()) {
			worker.IsAlive = false
			log.Printf("[Coordinator] Worker %s heartbeat timeout", worker.ID)
		}
	}
}

// Done 返回 Coordinator 是否完成的信号 channel。
func (c *Coordinator) Done() <-chan struct{} {
	return c.done
}

// IsDone 检查 Coordinator 是否已完成所有任务。
func (c *Coordinator) IsDone() bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.phase == mapreduce.AllDone
}

// GetStats 获取 Coordinator 的统计信息。
func (c *Coordinator) GetStats() map[string]interface{} {
	c.mu.Lock()
	defer c.mu.Unlock()

	mapCompleted := 0
	reduceCompleted := 0
	for _, task := range c.tasks {
		if task.Status == mapreduce.TaskCompleted {
			if task.ID < c.nMap {
				mapCompleted++
			} else {
				reduceCompleted++
			}
		}
	}

	return map[string]interface{}{
		"phase":           c.phase.String(),
		"map_total":       c.nMap,
		"map_completed":   mapCompleted,
		"reduce_total":    c.nReduce,
		"reduce_completed": reduceCompleted,
		"workers":         len(c.workers),
		"uptime":          time.Since(c.startTime).String(),
	}
}

// Cleanup 清理临时文件。
func (c *Coordinator) Cleanup() {
	// 清理临时目录
	os.RemoveAll("tmp")
	if c.verbose {
		log.Println("[Coordinator] Cleaned up temporary files")
	}
}
