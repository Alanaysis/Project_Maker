package storage

import (
	"fmt"
	"sync"
)

// Storage 存储接口
type Storage interface {
	// 日志存储
	AppendLog(entries []LogEntry) error
	GetLog(index int64) (*LogEntry, error)
	GetLogs(start, end int64) ([]LogEntry, error)
	TruncateLog(index int64) error

	// 状态存储
	SaveState(state HardState) error
	LoadState() (*HardState, error)
}

// LogEntry 日志条目
type LogEntry struct {
	Term    int64
	Index   int64
	Command []byte
}

// HardState 持久化状态
type HardState struct {
	CurrentTerm int64
	VotedFor    int64
}

// MemoryStorage 内存存储实现
type MemoryStorage struct {
	mu       sync.RWMutex
	log      []LogEntry
	hardState HardState
}

// NewMemoryStorage 创建新的内存存储
func NewMemoryStorage() *MemoryStorage {
	return &MemoryStorage{
		log: make([]LogEntry, 1), // 索引 0 是空的
		hardState: HardState{
			CurrentTerm: 0,
			VotedFor:    -1,
		},
	}
}

// AppendLog 追加日志条目
func (ms *MemoryStorage) AppendLog(entries []LogEntry) error {
	ms.mu.Lock()
	defer ms.mu.Unlock()
	ms.log = append(ms.log, entries...)
	return nil
}

// GetLog 获取指定索引的日志条目
func (ms *MemoryStorage) GetLog(index int64) (*LogEntry, error) {
	ms.mu.RLock()
	defer ms.mu.RUnlock()
	if index < 1 || int(index) >= len(ms.log) {
		return nil, fmt.Errorf("index out of range: %d", index)
	}
	return &ms.log[index], nil
}

// GetLogs 获取指定范围的日志条目
func (ms *MemoryStorage) GetLogs(start, end int64) ([]LogEntry, error) {
	ms.mu.RLock()
	defer ms.mu.RUnlock()
	if start < 1 {
		start = 1
	}
	if int(end) > len(ms.log) {
		end = int64(len(ms.log))
	}
	if start >= end {
		return nil, nil
	}
	result := make([]LogEntry, end-start)
	copy(result, ms.log[start:end])
	return result, nil
}

// TruncateLog 从指定索引开始截断日志
func (ms *MemoryStorage) TruncateLog(index int64) error {
	ms.mu.Lock()
	defer ms.mu.Unlock()
	if int(index) < len(ms.log) {
		ms.log = ms.log[:index]
	}
	return nil
}

// SaveState 保存持久化状态
func (ms *MemoryStorage) SaveState(state HardState) error {
	ms.mu.Lock()
	defer ms.mu.Unlock()
	ms.hardState = state
	return nil
}

// LoadState 加载持久化状态
func (ms *MemoryStorage) LoadState() (*HardState, error) {
	ms.mu.RLock()
	defer ms.mu.RUnlock()
	return &ms.hardState, nil
}

// GetLastLogIndex 获取最后一个日志条目的索引
func (ms *MemoryStorage) GetLastLogIndex() int64 {
	ms.mu.RLock()
	defer ms.mu.RUnlock()
	return int64(len(ms.log) - 1)
}

// GetLastLogTerm 获取最后一个日志条目的任期号
func (ms *MemoryStorage) GetLastLogTerm() int64 {
	ms.mu.RLock()
	defer ms.mu.RUnlock()
	if len(ms.log) <= 1 {
		return 0
	}
	return ms.log[len(ms.log)-1].Term
}