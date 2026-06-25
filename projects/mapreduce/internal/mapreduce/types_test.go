package mapreduce

import (
	"testing"
)

func TestIHash(t *testing.T) {
	tests := []struct {
		key      string
		expected int
	}{
		{"hello", 1234}, // 示例值，实际值取决于 FNV 哈希
		{"world", 5678},
	}

	for _, tt := range tests {
		t.Run(tt.key, func(t *testing.T) {
			result := IHash(tt.key)
			if result < 0 {
				t.Errorf("IHash(%s) = %d, expected non-negative", tt.key, result)
			}
		})
	}
}

func TestIHashConsistency(t *testing.T) {
	// 相同的 key 应该产生相同的 hash
	key := "test-key"
	hash1 := IHash(key)
	hash2 := IHash(key)

	if hash1 != hash2 {
		t.Errorf("IHash(%s) inconsistent: %d != %d", key, hash1, hash2)
	}
}

func TestDefaultPartition(t *testing.T) {
	nReduce := 10
	key := "test-key"

	partition := DefaultPartition(key, nReduce)

	if partition < 0 || partition >= nReduce {
		t.Errorf("DefaultPartition(%s, %d) = %d, out of range", key, nReduce, partition)
	}
}

func TestPhaseString(t *testing.T) {
	tests := []struct {
		phase    Phase
		expected string
	}{
		{MapPhase, "MapPhase"},
		{ReducePhase, "ReducePhase"},
		{AllDone, "AllDone"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			if tt.phase.String() != tt.expected {
				t.Errorf("Phase(%d).String() = %s, expected %s", tt.phase, tt.phase.String(), tt.expected)
			}
		})
	}
}

func TestTaskStatusString(t *testing.T) {
	tests := []struct {
		status   TaskStatus
		expected string
	}{
		{TaskIdle, "Idle"},
		{TaskInProgress, "InProgress"},
		{TaskCompleted, "Completed"},
		{TaskFailed, "Failed"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			if tt.status.String() != tt.expected {
				t.Errorf("TaskStatus(%d).String() = %s, expected %s", tt.status, tt.status.String(), tt.expected)
			}
		})
	}
}
