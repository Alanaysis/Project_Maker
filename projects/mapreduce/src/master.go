package mapreduce

// Package mapreduce implements a distributed MapReduce framework.
//
// MapReduce is a programming model for processing large datasets in parallel
// across a cluster of machines. The core idea is to split the input data into
// independent chunks, process each chunk with a Map function, then combine
// the intermediate results with a Reduce function.
//
// The framework follows the classic MapReduce architecture:
//   1. Input Splitting: Split input files into splits
//   2. Map Phase: Distribute map tasks to workers
//   3. Shuffle Phase: Group intermediate key-value pairs by key
//   4. Reduce Phase: Distribute reduce tasks to workers
//   5. Output: Write final results to output files
//
// Key concepts:
//   - Map function: transforms input key-value pairs into intermediate key-value pairs
//   - Reduce function: aggregates all values for a given intermediate key
//   - Partitioning: determines which reduce task handles which key
//   - Fault tolerance: workers send heartbeats; failed tasks are reassigned
//
// This implementation uses a master-worker model where:
//   - The Master coordinates task scheduling and worker management
//   - Workers execute map and reduce tasks assigned by the Master
//   - Intermediate data is stored in files for the shuffle phase

import (
	"fmt"
	"sync"
)

// MapFunc is the type of the map function.
// It processes an input key-value pair and returns intermediate key-value pairs.
// The intermediate data is partitioned by key for the shuffle phase.
// Common use cases: tokenizing text, extracting fields, computing counts.
type MapFunc func(key string, value string) []KeyValue

// ReduceFunc is the type of the reduce function.
// It receives a key and all intermediate values associated with that key,
// and returns the final aggregated result.
// Common use cases: counting, summing, averaging, sorting.
type ReduceFunc func(key string, values []string) string

// PartitionFunc determines which reduce task handles a given intermediate key.
// The default partitioner uses hash(key) % numReduceTasks.
type PartitionFunc func(key string, numReduceTasks int) int

// TaskType represents the type of task in the MapReduce pipeline.
type TaskType int

const (
	// MapTask represents a map task that processes an input split.
	MapTask TaskType = iota
	// ReduceTask represents a reduce task that aggregates intermediate data.
	ReduceTask
)

// String returns a string representation of the task type.
func (t TaskType) String() string {
	switch t {
	case MapTask:
		return "Map"
	case ReduceTask:
		return "Reduce"
	default:
		return "Unknown"
	}
}

// Task represents a unit of work in the MapReduce framework.
// Each task has a unique ID, type, associated file, and task number.
type Task struct {
	ID         int       `json:"id"`
	Type       TaskType  `json:"type"`
	FileName   string    `json:"file_name"`
	TaskNumber int       `json:"task_number"`
	NumReduce  int       `json:"num_reduce"`
}

// TaskStatus represents the current status of a task.
type TaskStatus int

const (
	// TaskPending means the task has been created but not yet assigned.
	TaskPending TaskStatus = iota
	// TaskRunning means the task is currently being executed by a worker.
	TaskRunning
	// TaskComplete means the task has finished successfully.
	TaskComplete
	// TaskFailed means the task failed and needs to be reassigned.
	TaskFailed
)

// String returns a string representation of the task status.
func (s TaskStatus) String() string {
	switch s {
	case TaskPending:
		return "Pending"
	case TaskRunning:
		return "Running"
	case TaskComplete:
		return "Complete"
	case TaskFailed:
		return "Failed"
	default:
		return "Unknown"
	}
}

// KeyValue represents a key-value pair in the MapReduce pipeline.
type KeyValue struct {
	Key   string
	Value string
}

// Worker represents a worker node in the cluster.
// Workers execute tasks assigned by the Master and report their status.
type Worker struct {
	ID        string
	Address   string
	Status    string
	LastHeartbeat int64
}

// FileSplit represents a chunk of an input file to be processed by a map task.
// Each split corresponds to one map task.
type FileSplit struct {
	FileName string
	Offset   int64
	Size     int64
}

// Master is the central coordinator in the master-worker MapReduce model.
// It manages worker registration, task scheduling, and fault tolerance.
//
// The Master's responsibilities:
//   - Register and track workers
//   - Split input files into splits
//   - Create and distribute map tasks
//   - After all map tasks complete, create reduce tasks
//   - Distribute reduce tasks
//   - Monitor task progress and handle failures
//   - Collect and finalize results
type Master struct {
	mu             sync.Mutex
	workers        map[string]*Worker
	taskQueue      chan Task
	mapTasks       []Task
	reduceTasks    []Task
	taskStatus     map[int]TaskStatus
	numMapTasks    int
	numReduceTasks int
	mapsComplete   int
	reducesComplete int
	inputFiles     []string
	outputDir      string
	tempDir        string
	done           chan bool
}

// MasterConfig holds configuration for creating a Master.
type MasterConfig struct {
	InputFiles     []string
	OutputDir      string
	TempDir        string
	NumReduceTasks int
}

// NewMaster creates a new Master instance.
// It initializes the Master with the given configuration and returns it ready to run.
func NewMaster(cfg MasterConfig) *Master {
	return &Master{
		workers:        make(map[string]*Worker),
		taskQueue:      make(chan Task, 100),
		taskStatus:     make(map[int]TaskStatus),
		numMapTasks:    len(cfg.InputFiles),
		numReduceTasks: cfg.NumReduceTasks,
		inputFiles:     cfg.InputFiles,
		outputDir:      cfg.OutputDir,
		tempDir:        cfg.TempDir,
		done:           make(chan bool),
	}
}

// Run starts the Master's main loop.
// It coordinates the entire MapReduce execution:
//   1. Create map tasks from input splits
//   2. Distribute map tasks to workers
//   3. Wait for all map tasks to complete
//   4. Create reduce tasks
//   5. Distribute reduce tasks to workers
//   6. Wait for all reduce tasks to complete
//   7. Signal completion
func (m *Master) Run() {
	// Phase 1: Create and distribute map tasks
	m.createMapTasks()
	m.distributeMapTasks()

	// Wait for all map tasks to complete
	m.waitForMapCompletion()

	// Phase 2: Create and distribute reduce tasks
	m.createReduceTasks()
	m.distributeReduceTasks()

	// Wait for all reduce tasks to complete
	m.waitForReduceCompletion()

	// Signal completion
	close(m.done)
}

// createMapTasks creates map tasks from input file splits.
// Each input file becomes one map task. This is the simplest splitting strategy.
// For large files, you could split each file into multiple splits.
func (m *Master) createMapTasks() {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.mapTasks = make([]Task, len(m.inputFiles))
	for i, file := range m.inputFiles {
		m.mapTasks[i] = Task{
			ID:         i,
			Type:       MapTask,
			FileName:   file,
			TaskNumber: i,
			NumReduce:  m.numReduceTasks,
		}
		m.taskStatus[i] = TaskPending
	}
}

// distributeMapTasks sends map tasks to the task queue for workers to pick up.
func (m *Master) distributeMapTasks() {
	for _, task := range m.mapTasks {
		m.taskQueue <- task
	}
}

// waitForMapCompletion blocks until all map tasks complete or a timeout occurs.
func (m *Master) waitForMapCompletion() {
	m.mu.Lock()
	total := len(m.mapTasks)
	m.mu.Unlock()

	for {
		m.mu.Lock()
		if m.mapsComplete >= total {
			m.mu.Unlock()
			return
		}
		m.mu.Unlock()
	}
}

// createReduceTasks creates reduce tasks after all map tasks complete.
// Each reduce task handles a partition of the intermediate key space.
func (m *Master) createReduceTasks() {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.reduceTasks = make([]Task, m.numReduceTasks)
	for i := 0; i < m.numReduceTasks; i++ {
		m.reduceTasks[i] = Task{
			ID:         m.numMapTasks + i,
			Type:       ReduceTask,
			TaskNumber: i,
			NumReduce:  m.numReduceTasks,
		}
		m.taskStatus[m.numMapTasks+i] = TaskPending
	}
}

// distributeReduceTasks sends reduce tasks to the task queue.
func (m *Master) distributeReduceTasks() {
	for _, task := range m.reduceTasks {
		m.taskQueue <- task
	}
}

// waitForReduceCompletion blocks until all reduce tasks complete or a timeout occurs.
func (m *Master) waitForReduceCompletion() {
	m.mu.Lock()
	total := m.numReduceTasks
	m.mu.Unlock()

	for {
		m.mu.Lock()
		if m.reducesComplete >= total {
			m.mu.Unlock()
			return
		}
		m.mu.Unlock()
	}
}

// ReportMapComplete is called by a worker when it finishes a map task.
func (m *Master) ReportMapComplete(taskID int) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.taskStatus[taskID] = TaskComplete
	m.mapsComplete++
}

// ReportReduceComplete is called by a worker when it finishes a reduce task.
func (m *Master) ReportReduceComplete(taskID int) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.taskStatus[taskID] = TaskComplete
	m.reducesComplete++
}

// GetTask retrieves the next available task for a worker.
// Returns nil if no tasks are available (all completed).
func (m *Master) GetTask(workerID string) *Task {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Try to assign a pending map task
	for i := range m.mapTasks {
		if m.taskStatus[i] == TaskPending {
			m.taskStatus[i] = TaskRunning
			return &m.mapTasks[i]
		}
	}

	// Try to assign a pending reduce task
	for i := range m.reduceTasks {
		taskID := m.numMapTasks + i
		if m.taskStatus[taskID] == TaskPending {
			m.taskStatus[taskID] = TaskRunning
			return &m.reduceTasks[i]
		}
	}

	return nil
}

// RegisterWorker adds a worker to the cluster.
func (m *Master) RegisterWorker(workerID, address string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.workers[workerID] = &Worker{
		ID:   workerID,
		Address: address,
		Status: "active",
	}
}

// UnregisterWorker removes a worker from the cluster.
func (m *Master) UnregisterWorker(workerID string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.workers, workerID)
}

// GetWorkerCount returns the number of registered workers.
func (m *Master) GetWorkerCount() int {
	m.mu.Lock()
	defer m.mu.Unlock()
	return len(m.workers)
}

// DefaultPartitioner is the standard partition function.
// It uses a simple hash-based partitioning to distribute keys evenly.
// This ensures that all values for the same key go to the same reduce task.
func DefaultPartitioner(key string, numReduceTasks int) int {
	h := hash(key)
	return int(h % uint64(numReduceTasks))
}

// hash is a simple hash function for partitioning keys.
// It produces a consistent hash value for the same input string.
func hash(key string) uint64 {
	var h uint64 = 5381
	for i := 0; i < len(key); i++ {
		h = (h << 5) + h + uint64(key[i])
	}
	return h
}

// Worker is a node that executes MapReduce tasks.
// It connects to the Master, requests tasks, executes them, and reports completion.
type Worker struct {
	ID       string
	Master   *Master
	running  bool
	mapFn    MapFunc
	reduceFn ReduceFunc
}

// NewWorker creates a new Worker instance.
func NewWorker(id string, master *Master) *Worker {
	return &Worker{
		ID:     id,
		Master: master,
		running: true,
	}
}

// SetMapFunc sets the map function for this worker.
func (w *Worker) SetMapFunc(fn MapFunc) {
	w.mapFn = fn
}

// SetReduceFunc sets the reduce function for this worker.
func (w *Worker) SetReduceFunc(fn ReduceFunc) {
	w.reduceFn = fn
}

// Run starts the worker's main loop.
// The worker continuously requests tasks from the Master and executes them.
func (w *Worker) Run() {
	for w.running {
		task := w.Master.GetTask(w.ID)
		if task == nil {
			// No more tasks available
			return
		}

		switch task.Type {
		case MapTask:
			w.executeMapTask(task)
			w.Master.ReportMapComplete(task.ID)
		case ReduceTask:
			w.executeReduceTask(task)
			w.Master.ReportReduceComplete(task.ID)
		}
	}
}

// Stop stops the worker.
func (w *Worker) Stop() {
	w.running = false
}

// executeMapTask processes an input file split using the map function.
// It reads the input file, applies the map function to each line,
// and writes intermediate key-value pairs to partitioned temporary files.
func (w *Worker) executeMapTask(task *Task) {
	// Read and process input file
	kvs := readInputFile(task.FileName)

	// Apply map function to each line
	var intermediate []KeyValue
	for i, line := range kvs {
		results := w.mapFn(fmt.Sprintf("%s:%d", task.FileName, i), line.Value)
		intermediate = append(intermediate, results...)
	}

	// Partition intermediate data and write to temp files
	// Each reduce task gets its own file containing only the keys it will process
	partitionFiles := make(map[int]*PartitionWriter)
	for _, kv := range intermediate {
		partition := DefaultPartitioner(kv.Key, task.NumReduce)
		if partitionFiles[partition] == nil {
			partitionFiles[partition] = &PartitionWriter{
				partition: partition,
				tasks:     make(map[string][]string),
			}
		}
		partitionFiles[partition].add(kv.Key, kv.Value)
	}

	// Write partitioned files to temp directory
	for _, pw := range partitionFiles {
		pw.writeToFile(w.Master.TempDir, task.TaskNumber)
	}
}

// executeReduceTask processes a reduce task.
// It reads all intermediate files, groups values by key,
// and applies the reduce function to produce the final output.
func (w *Worker) executeReduceTask(task *Task) {
	// Collect all intermediate files for this reduce task
	// and group values by key
	grouped := make(map[string][]string)

	// Read intermediate files from all map tasks
	for mapTaskID := 0; mapTaskID < w.Master.NumMapTasks(); mapTaskID++ {
		// Read the intermediate file for this map task and this reduce task
		kvs := readPartitionFile(w.Master.TempDir, mapTaskID, task.TaskNumber)
		for _, kv := range kvs {
			grouped[kv.Key] = append(grouped[kv.Key], kv.Value)
		}
	}

	// Sort keys for deterministic output
	keys := sortedKeys(grouped)

	// Apply reduce function and write output
	for _, key := range keys {
		result := w.reduceFn(key, grouped[key])
		writeOutput(w.Master.OutputDir, task.TaskNumber, key, result)
	}
}

// Master helper methods
func (m *Master) NumMapTasks() int {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.numMapTasks
}

func (m *Master) TempDir() string {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.tempDir
}

func (m *Master) OutputDir() string {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.outputDir
}
