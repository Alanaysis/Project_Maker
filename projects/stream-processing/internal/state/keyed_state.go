package state

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// KeyedState manages per-key state for operators.
// Each key has its own isolated state that can be independently
// accessed and checkpointed.
//
// This is used for:
// - Per-user session tracking
// - Per-sensor aggregation
// - Per-key window buffers
type KeyedState struct {
	mu       sync.RWMutex
	states   map[string]*StateStore
	metadata map[string]KeyMetadata
}

// KeyMetadata tracks when a key was last accessed.
type KeyMetadata struct {
	LastAccess time.Time
	LastUpdate time.Time
	Created    time.Time
}

// NewKeyedState creates a new keyed state manager.
func NewKeyedState() *KeyedState {
	return &KeyedState{
		states:   make(map[string]*StateStore),
		metadata: make(map[string]KeyMetadata),
	}
}

// GetState returns the state store for a specific key.
// Creates a new store if the key doesn't exist.
func (ks *KeyedState) GetState(key string) *StateStore {
	ks.mu.Lock()
	defer ks.mu.Unlock()

	if store, ok := ks.states[key]; ok {
		ks.metadata[key] = KeyMetadata{
			LastAccess: time.Now(),
			LastUpdate: ks.metadata[key].LastUpdate,
			Created:    ks.metadata[key].Created,
		}
		return store
	}

	store := NewStateStore()
	ks.states[key] = store
	ks.metadata[key] = KeyMetadata{
		LastAccess: time.Now(),
		LastUpdate: time.Now(),
		Created:    time.Now(),
	}
	return store
}

// Put stores a value under the given key and sub-key.
func (ks *KeyedState) Put(key, subKey string, value interface{}) {
	store := ks.GetState(key)
	store.Put(subKey, value)

	ks.mu.Lock()
	ks.metadata[key] = KeyMetadata{
		LastAccess: time.Now(),
		LastUpdate: time.Now(),
		Created:    ks.metadata[key].Created,
	}
	ks.mu.Unlock()
}

// Get retrieves a value by key and sub-key.
func (ks *KeyedState) Get(key, subKey string) (interface{}, bool) {
	store := ks.GetState(key)
	return store.Get(subKey)
}

// Delete removes a key's state entirely.
func (ks *KeyedState) Delete(key string) {
	ks.mu.Lock()
	defer ks.mu.Unlock()
	delete(ks.states, key)
	delete(ks.metadata, key)
}

// Keys returns all active keys.
func (ks *KeyedState) Keys() []string {
	ks.mu.RLock()
	defer ks.mu.RUnlock()

	keys := make([]string, 0, len(ks.states))
	for k := range ks.states {
		keys = append(keys, k)
	}
	return keys
}

// Size returns the number of active keys.
func (ks *KeyedState) Size() int {
	ks.mu.RLock()
	defer ks.mu.RUnlock()
	return len(ks.states)
}

// Expire removes keys that haven't been accessed within maxAge.
func (ks *KeyedState) Expire(maxAge time.Duration) int {
	ks.mu.Lock()
	defer ks.mu.Unlock()

	now := time.Now()
	expired := 0

	for key, meta := range ks.metadata {
		if now.Sub(meta.LastAccess) > maxAge {
			delete(ks.states, key)
			delete(ks.metadata, key)
			expired++
		}
	}
	return expired
}

// Snapshot creates a serializable snapshot of all keyed state.
func (ks *KeyedState) Snapshot() (*KeyedStateSnapshot, error) {
	ks.mu.RLock()
	defer ks.mu.RUnlock()

	snapshot := &KeyedStateSnapshot{
		Timestamp: time.Now(),
		States:    make(map[string]map[string]interface{}),
	}

	for key, store := range ks.states {
		data := make(map[string]interface{})
		for _, subKey := range store.Keys() {
			if val, ok := store.Get(subKey); ok {
				data[subKey] = val
			}
		}
		snapshot.States[key] = data
	}

	return snapshot, nil
}

// Restore restores state from a snapshot.
func (ks *KeyedState) Restore(snapshot *KeyedStateSnapshot) error {
	ks.mu.Lock()
	defer ks.mu.Unlock()

	ks.states = make(map[string]*StateStore)
	ks.metadata = make(map[string]KeyMetadata)

	for key, data := range snapshot.States {
		store := NewStateStore()
		for subKey, val := range data {
			store.Put(subKey, val)
		}
		ks.states[key] = store
		ks.metadata[key] = KeyMetadata{
			LastAccess: time.Now(),
			LastUpdate: time.Now(),
			Created:    snapshot.Timestamp,
		}
	}

	return nil
}

// KeyedStateSnapshot represents a serializable state snapshot.
type KeyedStateSnapshot struct {
	Timestamp time.Time                       `json:"timestamp"`
	States    map[string]map[string]interface{} `json:"states"`
}

// MarshalJSON serializes the snapshot to JSON.
func (s *KeyedStateSnapshot) MarshalJSON() ([]byte, error) {
	type Alias KeyedStateSnapshot
	return json.Marshal(struct {
		Alias
	}{
		Alias: Alias(*s),
	})
}

// CheckpointManager manages periodic state checkpointing.
type CheckpointManager struct {
	mu              sync.Mutex
	stores          []Checkpointable
	interval        time.Duration
	retention       int
	checkpoints     []*Checkpoint
	stopCh          chan struct{}
	lastCheckpoint  time.Time
}

// Checkpointable is an interface for state that can be checkpointed.
type Checkpointable interface {
	Snapshot() (*KeyedStateSnapshot, error)
	Restore(*KeyedStateSnapshot) error
}

// Checkpoint represents a point-in-time state snapshot.
type Checkpoint struct {
	ID        int64
	Timestamp time.Time
	State     *KeyedStateSnapshot
}

// NewCheckpointManager creates a checkpoint manager.
// interval is how often to checkpoint, retention is how many to keep.
func NewCheckpointManager(interval time.Duration, retention int) *CheckpointManager {
	return &CheckpointManager{
		interval:    interval,
		retention:   retention,
		checkpoints: make([]*Checkpoint, 0, retention),
		stopCh:      make(chan struct{}),
	}
}

// Register adds a checkpointable store to the manager.
func (cm *CheckpointManager) Register(store Checkpointable) {
	cm.mu.Lock()
	defer cm.mu.Unlock()
	cm.stores = append(cm.stores, store)
}

// Start begins periodic checkpointing. Returns a channel that
// receives checkpoint IDs when completed.
func (cm *CheckpointManager) Start() <-chan int64 {
	ch := make(chan int64, 1)

	go func() {
		defer close(ch)

		ticker := time.NewTicker(cm.interval)
		defer ticker.Stop()

		var checkpointID int64

		for {
			select {
			case <-cm.stopCh:
				return
			case <-ticker.C:
				checkpointID++
				if err := cm.doCheckpoint(checkpointID); err == nil {
					ch <- checkpointID
				}
			}
		}
	}()

	return ch
}

// Stop stops the checkpoint manager.
func (cm *CheckpointManager) Stop() {
	close(cm.stopCh)
}

// TriggerCheckpoint manually triggers a checkpoint.
func (cm *CheckpointManager) TriggerCheckpoint() (int64, error) {
	cm.mu.Lock()
	id := cm.nextID()
	cm.mu.Unlock()

	return id, cm.doCheckpoint(id)
}

func (cm *CheckpointManager) nextID() int64 {
	if len(cm.checkpoints) == 0 {
		return 1
	}
	return cm.checkpoints[len(cm.checkpoints)-1].ID + 1
}

func (cm *CheckpointManager) doCheckpoint(id int64) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Create a combined snapshot
	combined := &KeyedStateSnapshot{
		Timestamp: time.Now(),
		States:    make(map[string]map[string]interface{}),
	}

	for _, store := range cm.stores {
		snapshot, err := store.Snapshot()
		if err != nil {
			return fmt.Errorf("snapshot failed: %w", err)
		}
		for k, v := range snapshot.States {
			combined.States[fmt.Sprintf("store_%p_%s", store, k)] = v
		}
	}

	checkpoint := &Checkpoint{
		ID:        id,
		Timestamp: time.Now(),
		State:     combined,
	}

	cm.checkpoints = append(cm.checkpoints, checkpoint)

	// Enforce retention
	if len(cm.checkpoints) > cm.retention {
		cm.checkpoints = cm.checkpoints[len(cm.checkpoints)-cm.retention:]
	}

	cm.lastCheckpoint = time.Now()
	return nil
}

// LatestCheckpoint returns the most recent checkpoint.
func (cm *CheckpointManager) LatestCheckpoint() *Checkpoint {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if len(cm.checkpoints) == 0 {
		return nil
	}
	return cm.checkpoints[len(cm.checkpoints)-1]
}

// CheckpointCount returns the number of stored checkpoints.
func (cm *CheckpointManager) CheckpointCount() int {
	cm.mu.Lock()
	defer cm.mu.Unlock()
	return len(cm.checkpoints)
}
