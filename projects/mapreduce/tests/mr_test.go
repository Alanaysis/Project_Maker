package mr

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func setupTestDirs(t *testing.T) (string, string, string) {
	t.Helper()
	tempDir := t.TempDir()
	inputDir := filepath.Join(tempDir, "input")
	outputDir := filepath.Join(tempDir, "output")
	tempDir2 := filepath.Join(tempDir, "temp")
	os.MkdirAll(inputDir, 0755)
	os.MkdirAll(outputDir, 0755)
	os.MkdirAll(tempDir2, 0755)
	return inputDir, outputDir, tempDir2
}

func createInputFile(t *testing.T, dir, name, content string) string {
	t.Helper()
	filename := filepath.Join(dir, name)
	err := os.WriteFile(filename, []byte(content), 0644)
	if err != nil {
		t.Fatalf("Failed to create input file: %v", err)
	}
	return filename
}

func TestNewMaster(t *testing.T) {
	inputDir, outputDir, tempDir := setupTestDirs(t)
	inputFile := createInputFile(t, inputDir, "test.txt", "hello world\nfoo bar\n")

	master := NewMaster(MasterConfig{
		InputFiles:     []string{inputFile},
		OutputDir:      outputDir,
		TempDir:        tempDir,
		NumReduceTasks: 2,
	})

	if master == nil {
		t.Fatal("NewMaster returned nil")
	}
	if master.numMapTasks != 1 {
		t.Errorf("expected numMapTasks=1, got %d", master.numMapTasks)
	}
	if master.numReduceTasks != 2 {
		t.Errorf("expected numReduceTasks=2, got %d", master.numReduceTasks)
	}
}

func TestMapReduceWordCount(t *testing.T) {
	inputDir, outputDir, tempDir := setupTestDirs(t)

	// Create input files with known content
	file1 := createInputFile(t, inputDir, "file1.txt", "hello world\nhello go\n")
	file2 := createInputFile(t, inputDir, "file2.txt", "world mapreduce\nhello mapreduce\n")

	master := NewMaster(MasterConfig{
		InputFiles:     []string{file1, file2},
		OutputDir:      outputDir,
		TempDir:        tempDir,
		NumReduceTasks: 2,
	})

	worker := master.NewWorker("worker-1")
	worker.SetMapFunc(func(key string, value string) []KeyValue {
		var result []KeyValue
		words := strings.Fields(value)
		for _, word := range words {
			word = strings.ToLower(word)
			result = append(result, KeyValue{Key: word, Value: "1"})
		}
		return result
	})
	worker.SetReduceFunc(func(key string, values []string) string {
		count := 0
		for _, v := range values {
			if v == "1" {
				count++
			}
		}
		return fmt.Sprintf("%d", count)
	})

	master.RunWithWorkers(SingleWorkerMode)

	if !master.IsComplete() {
		t.Error("Master should be complete")
	}

	status := master.GetStatus()
	if status.MapTasksComplete != 2 {
		t.Errorf("expected 2 map tasks complete, got %d", status.MapTasksComplete)
	}
	if status.ReduceTasksComplete != 2 {
		t.Errorf("expected 2 reduce tasks complete, got %d", status.ReduceTasksComplete)
	}
}

func TestHashConsistency(t *testing.T) {
	// Same input should always produce the same hash
	h1 := hash("test-key")
	h2 := hash("test-key")
	if h1 != h2 {
		t.Errorf("hash inconsistency: %d != %d", h1, h2)
	}

	// Different inputs should typically produce different hashes
	h3 := hash("different-key")
	if h1 == h3 {
		t.Errorf("hash collision for different inputs")
	}
}

func TestDefaultPartitioner(t *testing.T) {
	numReduce := 5

	// Same key should always go to the same partition
	p1 := DefaultPartitioner("test-key", numReduce)
	p2 := DefaultPartitioner("test-key", numReduce)
	if p1 != p2 {
		t.Errorf("partitioner inconsistency: %d != %d", p1, p2)
	}

	// All partitions should be reachable
	partitions := make(map[int]bool)
	for i := 0; i < 1000; i++ {
		p := DefaultPartitioner(fmt.Sprintf("key-%d", i), numReduce)
		if p < 0 || p >= numReduce {
			t.Errorf("partition %d out of range [0, %d)", p, numReduce)
		}
		partitions[p] = true
	}

	if len(partitions) != numReduce {
		t.Errorf("expected all %d partitions to be used, got %d", numReduce, len(partitions))
	}
}

func TestSortedKeys(t *testing.T) {
	m := map[string][]string{
		"zebra": {"1"},
		"apple": {"1"},
		"mango": {"1"},
	}

	keys := sortedKeys(m)
	expected := []string{"apple", "mango", "zebra"}

	if len(keys) != len(expected) {
		t.Fatalf("expected %d keys, got %d", len(expected), len(keys))
	}
	for i, k := range keys {
		if k != expected[i] {
			t.Errorf("expected key[%d]=%s, got %s", i, expected[i], k)
		}
	}
}

func TestTaskStatusString(t *testing.T) {
	tests := []struct {
		status TaskStatus
		expect string
	}{
		{TaskPending, "Pending"},
		{TaskRunning, "Running"},
		{TaskComplete, "Complete"},
		{TaskFailed, "Failed"},
		{TaskStatus(99), "Unknown"},
	}

	for _, tt := range tests {
		if got := tt.status.String(); got != tt.expect {
			t.Errorf("TaskStatus(%d).String() = %s, want %s", tt.status, got, tt.expect)
		}
	}
}

func TestTaskTypeString(t *testing.T) {
	if got := MapTask.String(); got != "Map" {
		t.Errorf("MapTask.String() = %s, want Map", got)
	}
	if got := ReduceTask.String(); got != "Reduce" {
		t.Errorf("ReduceTask.String() = %s, want Reduce", got)
	}
}

func TestRegisterAndUnregisterWorker(t *testing.T) {
	_, outputDir, tempDir := setupTestDirs(t)
	createInputFile(t, filepath.Join(outputDir, "placeholder"), "dummy.txt", "test")

	master := NewMaster(MasterConfig{
		InputFiles:     []string{filepath.Join(outputDir, "placeholder")},
		OutputDir:      outputDir,
		TempDir:        tempDir,
		NumReduceTasks: 1,
	})

	master.RegisterWorker("w1", "localhost:8080")
	if master.GetWorkerCount() != 1 {
		t.Errorf("expected 1 worker, got %d", master.GetWorkerCount())
	}

	master.RegisterWorker("w2", "localhost:8081")
	if master.GetWorkerCount() != 2 {
		t.Errorf("expected 2 workers, got %d", master.GetWorkerCount())
	}

	master.UnregisterWorker("w1")
	if master.GetWorkerCount() != 1 {
		t.Errorf("expected 1 worker after unregister, got %d", master.GetWorkerCount())
	}
}

func TestMultipleMapTasks(t *testing.T) {
	inputDir, outputDir, tempDir := setupTestDirs(t)

	files := make([]string, 5)
	for i := 0; i < 5; i++ {
		files[i] = createInputFile(t, inputDir, fmt.Sprintf("file-%d.txt", i), "hello world\n")
	}

	master := NewMaster(MasterConfig{
		InputFiles:     files,
		OutputDir:      outputDir,
		TempDir:        tempDir,
		NumReduceTasks: 3,
	})

	worker := master.NewWorker("worker-1")
	worker.SetMapFunc(func(key string, value string) []KeyValue {
		return []KeyValue{{Key: value, Value: "1"}}
	})
	worker.SetReduceFunc(func(key string, values []string) string {
		return fmt.Sprintf("%d", len(values))
	})

	master.RunWithWorkers(SingleWorkerMode)

	status := master.GetStatus()
	if status.MapTasksComplete != 5 {
		t.Errorf("expected 5 map tasks complete, got %d", status.MapTasksComplete)
	}
	if status.ReduceTasksComplete != 3 {
		t.Errorf("expected 3 reduce tasks complete, got %d", status.ReduceTasksComplete)
	}
}

func TestEmptyInput(t *testing.T) {
	inputDir, outputDir, tempDir := setupTestDirs(t)

	// Create file with only whitespace
	createInputFile(t, inputDir, "empty.txt", "   \n\n  \n")

	master := NewMaster(MasterConfig{
		InputFiles:     []string{filepath.Join(inputDir, "empty.txt")},
		OutputDir:      outputDir,
		TempDir:        tempDir,
		NumReduceTasks: 2,
	})

	worker := master.NewWorker("worker-1")
	worker.SetMapFunc(func(key string, value string) []KeyValue {
		if strings.TrimSpace(value) == "" {
			return nil
		}
		return []KeyValue{{Key: value, Value: "1"}}
	})
	worker.SetReduceFunc(func(key string, values []string) string {
		return fmt.Sprintf("%d", len(values))
	})

	master.RunWithWorkers(SingleWorkerMode)

	status := master.GetStatus()
	if status.MapTasksComplete != 1 {
		t.Errorf("expected 1 map task complete, got %d", status.MapTasksComplete)
	}
}
