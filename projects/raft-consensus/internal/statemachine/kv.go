package statemachine

import (
	"fmt"
	"strings"
	"sync"
)

// StateMachine 状态机接口
type StateMachine interface {
	// Apply 应用命令到状态机
	Apply(command interface{}) interface{}
	// Snapshot 获取状态机快照
	Snapshot() []byte
	// Restore 从快照恢复状态机
	Restore(data []byte) error
}

// KVStateMachine KV 状态机实现
type KVStateMachine struct {
	mu   sync.RWMutex
	data map[string]string
}

// NewKVStateMachine 创建新的 KV 状态机
func NewKVStateMachine() *KVStateMachine {
	return &KVStateMachine{
		data: make(map[string]string),
	}
}

// Apply 应用命令到状态机
func (kv *KVStateMachine) Apply(command interface{}) interface{} {
	kv.mu.Lock()
	defer kv.mu.Unlock()

	cmd, ok := command.(string)
	if !ok {
		return fmt.Errorf("invalid command type: %T", command)
	}

	// 解析命令
	parts := strings.SplitN(cmd, " ", 3)
	if len(parts) < 2 {
		return fmt.Errorf("invalid command format: %s", cmd)
	}

	op := strings.ToUpper(parts[0])
	key := parts[1]

	switch op {
	case "PUT":
		if len(parts) < 3 {
			return fmt.Errorf("PUT command requires value")
		}
		value := parts[2]
		kv.data[key] = value
		return fmt.Sprintf("OK: %s = %s", key, value)

	case "GET":
		value, exists := kv.data[key]
		if !exists {
			return fmt.Sprintf("KEY_NOT_FOUND: %s", key)
		}
		return fmt.Sprintf("OK: %s = %s", key, value)

	case "DELETE":
		if _, exists := kv.data[key]; exists {
			delete(kv.data, key)
			return fmt.Sprintf("OK: deleted %s", key)
		}
		return fmt.Sprintf("KEY_NOT_FOUND: %s", key)

	default:
		return fmt.Errorf("unknown command: %s", op)
	}
}

// Snapshot 获取状态机快照
func (kv *KVStateMachine) Snapshot() []byte {
	kv.mu.RLock()
	defer kv.mu.RUnlock()

	var result strings.Builder
	for key, value := range kv.data {
		result.WriteString(fmt.Sprintf("%s=%s\n", key, value))
	}
	return []byte(result.String())
}

// Restore 从快照恢复状态机
func (kv *KVStateMachine) Restore(data []byte) error {
	kv.mu.Lock()
	defer kv.mu.Unlock()

	kv.data = make(map[string]string)
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			return fmt.Errorf("invalid snapshot line: %s", line)
		}
		kv.data[parts[0]] = parts[1]
	}
	return nil
}

// Get 获取键值
func (kv *KVStateMachine) Get(key string) (string, bool) {
	kv.mu.RLock()
	defer kv.mu.RUnlock()
	value, exists := kv.data[key]
	return value, exists
}

// Size 获取键值对数量
func (kv *KVStateMachine) Size() int {
	kv.mu.RLock()
	defer kv.mu.RUnlock()
	return len(kv.data)
}