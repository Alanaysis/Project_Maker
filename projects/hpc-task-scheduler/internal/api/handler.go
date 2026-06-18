package api

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/hpc-scheduler/internal/resource"
	"github.com/hpc-scheduler/internal/scheduler"
	"github.com/hpc-scheduler/internal/task"
	"github.com/hpc-scheduler/pkg/models"
)

// Handler HTTP API 处理器
type Handler struct {
	scheduler *scheduler.Scheduler
	taskMgr   *task.TaskManager
	resMgr    *resource.ResourceManager
}

// NewHandler 创建处理器
func NewHandler(sched *scheduler.Scheduler, tm *task.TaskManager, rm *resource.ResourceManager) *Handler {
	return &Handler{
		scheduler: sched,
		taskMgr:   tm,
		resMgr:    rm,
	}
}

// SetupRoutes 设置路由
func (h *Handler) SetupRoutes() *http.ServeMux {
	mux := http.NewServeMux()

	// 任务相关 API
	mux.HandleFunc("/api/v1/tasks", h.handleTasks)
	mux.HandleFunc("/api/v1/tasks/", h.handleTaskByID)
	mux.HandleFunc("/api/v1/tasks/stats", h.handleTaskStats)

	// 集群相关 API
	mux.HandleFunc("/api/v1/cluster", h.handleCluster)
	mux.HandleFunc("/api/v1/cluster/nodes", h.handleNodes)

	// 调度器相关 API
	mux.HandleFunc("/api/v1/scheduler", h.handleScheduler)

	// 健康检查
	mux.HandleFunc("/health", h.handleHealth)

	return mux
}

// handleTasks 处理任务相关请求
func (h *Handler) handleTasks(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		h.listTasks(w, r)
	case http.MethodPost:
		h.submitTask(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleTaskByID 处理单个任务请求
func (h *Handler) handleTaskByID(w http.ResponseWriter, r *http.Request) {
	// 从路径中提取任务 ID
	// 格式: /api/v1/tasks/{id}
	path := r.URL.Path
	if len(path) < 16 { // "/api/v1/tasks/" = 14 chars
		http.Error(w, "Invalid task ID", http.StatusBadRequest)
		return
	}
	taskID := path[14:] // 提取 "/api/v1/tasks/" 之后的部分

	switch r.Method {
	case http.MethodGet:
		h.getTask(w, taskID)
	case http.MethodDelete:
		h.cancelTask(w, taskID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// submitTask 提交新任务
func (h *Handler) submitTask(w http.ResponseWriter, r *http.Request) {
	var req models.SubmitTaskRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// 设置默认值
	if req.Priority == 0 {
		req.Priority = models.PriorityNormal
	}
	if req.MaxRetries == 0 {
		req.MaxRetries = 3
	}
	if req.Timeout == 0 {
		req.Timeout = 300
	}

	// 创建任务
	task, err := h.taskMgr.CreateTask(&req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// 提交到调度器
	h.scheduler.SubmitTask(task)

	log.Printf("Task submitted: %s (name: %s)", task.ID, task.Name)

	// 返回响应
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(models.TaskResponse{
		Task:    task,
		Message: "Task submitted successfully",
	})
}

// listTasks 获取任务列表
func (h *Handler) listTasks(w http.ResponseWriter, r *http.Request) {
	// 获取查询参数
	state := r.URL.Query().Get("state")

	var tasks []*models.Task
	if state != "" {
		tasks = h.taskMgr.GetTasksByState(models.TaskState(state))
	} else {
		tasks = h.taskMgr.GetAllTasks()
	}

	// 返回响应
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models.TaskListResponse{
		Tasks: tasks,
		Total: len(tasks),
	})
}

// getTask 获取单个任务
func (h *Handler) getTask(w http.ResponseWriter, taskID string) {
	task, err := h.taskMgr.GetTask(taskID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models.TaskResponse{
		Task: task,
	})
}

// cancelTask 取消任务
func (h *Handler) cancelTask(w http.ResponseWriter, taskID string) {
	err := h.taskMgr.CancelTask(taskID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// 释放资源
	h.resMgr.Release(taskID)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"message": "Task cancelled successfully",
	})
}

// handleTaskStats 处理任务统计请求
func (h *Handler) handleTaskStats(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	stats := h.taskMgr.GetStats()
	schedulerStats := h.scheduler.GetStats()

	response := map[string]interface{}{
		"tasks":     stats,
		"scheduler": schedulerStats,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleCluster 处理集群信息请求
func (h *Handler) handleCluster(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	info := h.resMgr.GetClusterInfo()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
}

// handleNodes 处理节点列表请求
func (h *Handler) handleNodes(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	nodes := h.resMgr.GetAllNodes()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(nodes)
}

// handleScheduler 处理调度器信息请求
func (h *Handler) handleScheduler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	stats := h.scheduler.GetStats()
	queueLength := h.scheduler.GetQueueLength()
	algorithm := h.scheduler.GetAlgorithmName()

	response := map[string]interface{}{
		"algorithm":    algorithm,
		"queue_length": queueLength,
		"stats":        stats,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleHealth 处理健康检查请求
func (h *Handler) handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	response := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().UTC(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
