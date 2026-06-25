package transaction

import (
	"fmt"
	"sync"
	"time"
)

// TxState 事务状态
type TxState int

const (
	TxStateInit       TxState = iota // 初始状态
	TxStatePreparing                 // 准备中
	TxStatePrepared                  // 已准备
	TxStateCommitting                // 提交中
	TxStateCommitted                 // 已提交
	TxStateAborting                  // 中止中
	TxStateAborted                   // 已中止
)

func (s TxState) String() string {
	switch s {
	case TxStateInit:
		return "INIT"
	case TxStatePreparing:
		return "PREPARING"
	case TxStatePrepared:
		return "PREPARED"
	case TxStateCommitting:
		return "COMMITTING"
	case TxStateCommitted:
		return "COMMITTED"
	case TxStateAborting:
		return "ABORTING"
	case TxStateAborted:
		return "ABORTED"
	default:
		return "UNKNOWN"
	}
}

// Transaction 分布式事务
type Transaction struct {
	ID        string
	State     TxState
	Data      map[string]interface{}
	CreatedAt time.Time
	UpdatedAt time.Time
	mu        sync.RWMutex
}

// NewTransaction 创建新事务
func NewTransaction(id string) *Transaction {
	now := time.Now()
	return &Transaction{
		ID:        id,
		State:     TxStateInit,
		Data:      make(map[string]interface{}),
		CreatedAt: now,
		UpdatedAt: now,
	}
}

// SetData 设置事务数据（线程安全）
func (t *Transaction) SetData(key string, value interface{}) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.Data[key] = value
}

// GetData 获取事务数据（线程安全）
func (t *Transaction) GetData(key string) (interface{}, bool) {
	t.mu.RLock()
	defer t.mu.RUnlock()
	val, ok := t.Data[key]
	return val, ok
}

// GetState 获取事务状态（线程安全）
func (t *Transaction) GetState() TxState {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.State
}

// SetState 设置事务状态（线程安全）
func (t *Transaction) SetState(state TxState) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.State = state
	t.UpdatedAt = time.Now()
}

// String 返回事务的字符串表示
func (t *Transaction) String() string {
	return fmt.Sprintf("Transaction{id=%s, state=%s}", t.ID, t.GetState())
}
