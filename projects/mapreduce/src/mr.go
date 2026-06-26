package mr

// Package mr implements a distributed MapReduce framework.
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
	ID         int
	Type       TaskType
	FileName   string
	TaskNumber int
	NumReduce  int
}

// TaskStatus represents the current status of a task.
type TaskStatus int

const (
	TaskPending TaskStatus = iota
	TaskRunning
	TaskComplete
	TaskFailed
)

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
type Worker struct {
	ID              string
	Address         string
	Status          string
	LastHeartbeat   int64
}

// FileSplit represents a chunk of an input file to be processed by a map task.
type FileSplit struct {
	FileName string
	Offset   int64
	Size     int64
}

// Master is the central coordinator in the master-worker MapReduce model.
// It manages worker registration, task scheduling, and fault tolerance.
type Master struct {
	mu              sync.Mutex
	workers         map[string]*Worker
	taskQueue       chan Task
	mapTasks        []Task
	reduceTasks     []Task
	taskStatus      map[int]TaskStatus
	numMapTasks     int
	numReduceTasks  int
	mapsComplete    int
	reducesComplete int
	inputFiles      []string
	outputDir       string
	tempDir         string
	done            chan bool
}

// MasterConfig holds configuration for creating a Master.
type MasterConfig struct {
	InputFiles     []string
	OutputDir      string
	TempDir        string
	NumReduceTasks int
}

// NewMaster creates a new Master instance.
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

// Run starts the Master's main loop coordinating the entire MapReduce execution.
func (m *Master) Run() {
	m.createMapTasks()
	m.distributeMapTasks()
	m.waitForMapCompletion()
	m.createReduceTasks()
	m.distributeReduceTasks()
	m.waitForReduceCompletion()
	close(m.done)
}

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

func (m *Master) distributeMapTasks() {
	for _, task := range m.mapTasks {
		m.taskQueue <- task
	}
}

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

func (m *Master) distributeReduceTasks() {
	for _, task := range m.reduceTasks {
		m.taskQueue <- task
	}
}

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

func (m *Master) ReportMapComplete(taskID int) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.taskStatus[taskID] = TaskComplete
	m.mapsComplete++
}

func (m *Master) ReportReduceComplete(taskID int) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.taskStatus[taskID] = TaskComplete
	m.reducesComplete++
}

func (m *Master) GetTask(workerID string) *Task {
	m.mu.Lock()
	defer m.mu.Unlock()
	for i := range m.mapTasks {
		if m.taskStatus[i] == TaskPending {
			m.taskStatus[i] = TaskRunning
			return &m.mapTasks[i]
		}
	}
	for i := range m.reduceTasks {
		taskID := m.numMapTasks + i
		if m.taskStatus[taskID] == TaskPending {
			m.taskStatus[taskID] = TaskRunning
			return &m.reduceTasks[i]
		}
	}
	return nil
}

func (m *Master) RegisterWorker(workerID, address string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.workers[workerID] = &Worker{
		ID:   workerID,
		Address: address,
		Status: "active",
	}
}

func (m *Master) UnregisterWorker(workerID string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.workers, workerID)
}

func (m *Master) GetWorkerCount() int {
	m.mu.Lock()
	defer m.mu.Unlock()
	return len(m.workers)
}

// DefaultPartitioner uses hash-based partitioning to distribute keys evenly.
func DefaultPartitioner(key string, numReduceTasks int) int {
	h := hash(key)
	return int(h % uint64(numReduceTasks))
}

func hash(key string) uint64 {
	var h uint64 = 5381
	for i := 0; i < len(key); i++ {
		h = (h << 5) + h + uint64(key[i])
	}
	return h
}

// Worker is a node that executes MapReduce tasks.
type Worker struct {
	ID       string
	master   *Master
	running  bool
	mapFn    MapFunc
	reduceFn ReduceFunc
}

// NewWorker creates a new Worker instance.
func (m *Master) NewWorker(id string) *Worker {
	return &Worker{
		ID:     id,
		master: m,
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
func (w *Worker) Run() {
	for w.running {
		task := w.master.GetTask(w.ID)
		if task == nil {
			return
		}
		switch task.Type {
		case MapTask:
			w.executeMapTask(task)
			w.master.ReportMapComplete(task.ID)
		case ReduceTask:
			w.executeReduceTask(task)
			w.master.ReportReduceComplete(task.ID)
		}
	}
}

// Stop stops the worker.
func (w *Worker) Stop() {
	w.running = false
}

func (w *Worker) executeMapTask(task *Task) {
	kvs := readInputFile(task.FileName)
	var intermediate []KeyValue
	for i, line := range kvs {
		results := w.mapFn(fmt.Sprintf("%s:%d", task.FileName, i), line.Value)
		intermediate = append(intermediate, results...)
	}
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
	for _, pw := range partitionFiles {
		pw.writeToFile(w.master.tempDir, task.TaskNumber)
	}
}

func (w *Worker) executeReduceTask(task *Task) {
	grouped := make(map[string][]string)
	for mapTaskID := 0; mapTaskID < w.master.numMapTasks; mapTaskID++ {
		kvs := readPartitionFile(w.master.tempDir, mapTaskID, task.TaskNumber)
		for _, kv := range kvs {
			grouped[kv.Key] = append(grouped[kv.Key], kv.Value)
		}
	}
	keys := sortedKeys(grouped)
	for _, key := range keys {
		result := w.reduceFn(key, grouped[key])
		writeOutput(w.master.outputDir, task.TaskNumber, key, result)
	}
}

// MasterMode represents how the Master runs the MapReduce job.
type MasterMode int

const (
	SingleWorkerMode MasterMode = iota
	MultiWorkerMode
)

// RunWithWorkers runs the MapReduce job with the specified mode.
func (m *Master) RunWithWorkers(mode MasterMode) {
	switch mode {
	case SingleWorkerMode:
		worker := m.NewWorker("worker-1")
		go m.Run()
		worker.Run()
		m.WaitForCompletion()
	case MultiWorkerMode:
		go m.Run()
		m.WaitForCompletion()
	}
}

// MasterStatus represents the overall status of a MapReduce job.
type MasterStatus struct {
	MapTasksTotal       int
	MapTasksComplete    int
	ReduceTasksTotal    int
	ReduceTasksComplete int
	WorkerCount         int
}

// GetStatus returns the current status of the MapReduce job.
func (m *Master) GetStatus() MasterStatus {
	m.mu.Lock()
	defer m.mu.Unlock()
	return MasterStatus{
		MapTasksTotal:       len(m.mapTasks),
		MapTasksComplete:    m.mapsComplete,
		ReduceTasksTotal:    m.numReduceTasks,
		ReduceTasksComplete: m.reducesComplete,
		WorkerCount:         len(m.workers),
	}
}

// WaitForCompletion blocks until the MapReduce job completes.
func (m *Master) WaitForCompletion() {
	<-m.done
}

// IsComplete returns true if the MapReduce job has completed.
func (m *Master) IsComplete() bool {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.mapsComplete >= len(m.mapTasks) && m.reducesComplete >= m.numReduceTasks
}
