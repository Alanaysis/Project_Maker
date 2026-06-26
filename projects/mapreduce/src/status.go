package mapreduce

// MasterStatus represents the overall status of a MapReduce job.
type MasterStatus struct {
	MapTasksTotal     int
	MapTasksComplete  int
	ReduceTasksTotal  int
	ReduceTasksComplete int
	WorkerCount       int
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

// MasterMode represents how the Master runs the MapReduce job.
type MasterMode int

const (
	// SingleWorkerMode runs the MapReduce job with a single worker (in-process).
	SingleWorkerMode MasterMode = iota
	// MultiWorkerMode runs the MapReduce job with multiple workers.
	MultiWorkerMode
)

// RunWithWorkers runs the MapReduce job with the specified mode.
// In SingleWorkerMode, the Master creates a single worker that executes all tasks.
// In MultiWorkerMode, the Master would coordinate multiple workers (simplified here).
func (m *Master) RunWithWorkers(mode MasterMode) {
	switch mode {
	case SingleWorkerMode:
		// Create a single worker that executes all tasks
		worker := &Worker{
			Master: m,
			running: true,
		}
		// Start master in a goroutine
		go m.Run()
		// Worker picks up tasks from the master
		worker.Run()
		// Wait for completion
		m.WaitForCompletion()
	case MultiWorkerMode:
		// For distributed mode, each worker would connect to the master
		// via RPC. Here we simulate by running tasks in parallel goroutines.
		go m.Run()
		m.WaitForCompletion()
	}
}
