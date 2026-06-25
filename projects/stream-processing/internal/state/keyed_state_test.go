package state

import (
	"testing"
	"time"
)

func TestKeyedState(t *testing.T) {
	t.Run("BasicOperations", func(t *testing.T) {
		ks := NewKeyedState()

		// Put and Get
		ks.Put("user1", "name", "Alice")
		ks.Put("user1", "age", 30)
		ks.Put("user2", "name", "Bob")

		name, ok := ks.Get("user1", "name")
		if !ok || name.(string) != "Alice" {
			t.Errorf("Expected 'Alice', got %v", name)
		}

		age, ok := ks.Get("user1", "age")
		if !ok || age.(int) != 30 {
			t.Errorf("Expected 30, got %v", age)
		}
	})

	t.Run("GetState", func(t *testing.T) {
		ks := NewKeyedState()

		store := ks.GetState("user1")
		store.Put("name", "Alice")

		// Get same state
		store2 := ks.GetState("user1")
		name, _ := store2.Get("name")
		if name.(string) != "Alice" {
			t.Errorf("Expected 'Alice', got %v", name)
		}
	})

	t.Run("Keys", func(t *testing.T) {
		ks := NewKeyedState()

		ks.Put("user1", "name", "Alice")
		ks.Put("user2", "name", "Bob")
		ks.Put("user3", "name", "Charlie")

		keys := ks.Keys()
		if len(keys) != 3 {
			t.Errorf("Expected 3 keys, got %d", len(keys))
		}
	})

	t.Run("Size", func(t *testing.T) {
		ks := NewKeyedState()

		ks.Put("user1", "name", "Alice")
		ks.Put("user2", "name", "Bob")

		if ks.Size() != 2 {
			t.Errorf("Expected size 2, got %d", ks.Size())
		}
	})

	t.Run("Delete", func(t *testing.T) {
		ks := NewKeyedState()

		ks.Put("user1", "name", "Alice")
		ks.Delete("user1")

		if ks.Size() != 0 {
			t.Errorf("Expected size 0, got %d", ks.Size())
		}
	})

	t.Run("Expire", func(t *testing.T) {
		ks := NewKeyedState()

		ks.Put("user1", "name", "Alice")
		time.Sleep(10 * time.Millisecond)

		// Expire keys older than 5ms
		expired := ks.Expire(5 * time.Millisecond)
		if expired != 1 {
			t.Errorf("Expected 1 expired, got %d", expired)
		}

		if ks.Size() != 0 {
			t.Errorf("Expected size 0, got %d", ks.Size())
		}
	})
}

func TestKeyedStateSnapshot(t *testing.T) {
	t.Run("SnapshotAndRestore", func(t *testing.T) {
		ks := NewKeyedState()

		ks.Put("user1", "name", "Alice")
		ks.Put("user1", "age", 30)
		ks.Put("user2", "name", "Bob")

		// Create snapshot
		snapshot, err := ks.Snapshot()
		if err != nil {
			t.Fatalf("Failed to create snapshot: %v", err)
		}

		// Modify state
		ks.Put("user1", "name", "Modified")

		// Restore from snapshot
		ks2 := NewKeyedState()
		if err := ks2.Restore(snapshot); err != nil {
			t.Fatalf("Failed to restore snapshot: %v", err)
		}

		name, _ := ks2.Get("user1", "name")
		if name.(string) != "Alice" {
			t.Errorf("Expected 'Alice', got %v", name)
		}

		if ks2.Size() != 2 {
			t.Errorf("Expected size 2, got %d", ks2.Size())
		}
	})
}

func TestCheckpointManager(t *testing.T) {
	t.Run("ManualCheckpoint", func(t *testing.T) {
		cm := NewCheckpointManager(time.Hour, 5)

		ks := NewKeyedState()
		ks.Put("key1", "subkey", "value1")

		cm.Register(ks)

		id, err := cm.TriggerCheckpoint()
		if err != nil {
			t.Fatalf("Failed to trigger checkpoint: %v", err)
		}

		if id != 1 {
			t.Errorf("Expected checkpoint ID 1, got %d", id)
		}

		if cm.CheckpointCount() != 1 {
			t.Errorf("Expected 1 checkpoint, got %d", cm.CheckpointCount())
		}

		latest := cm.LatestCheckpoint()
		if latest == nil {
			t.Fatal("Expected non-nil checkpoint")
		}

		if latest.ID != 1 {
			t.Errorf("Expected checkpoint ID 1, got %d", latest.ID)
		}
	})

	t.Run("Retention", func(t *testing.T) {
		cm := NewCheckpointManager(time.Hour, 2)

		ks := NewKeyedState()
		cm.Register(ks)

		// Create 3 checkpoints
		cm.TriggerCheckpoint()
		cm.TriggerCheckpoint()
		cm.TriggerCheckpoint()

		// Should only keep 2
		if cm.CheckpointCount() != 2 {
			t.Errorf("Expected 2 checkpoints, got %d", cm.CheckpointCount())
		}

		latest := cm.LatestCheckpoint()
		if latest.ID != 3 {
			t.Errorf("Expected checkpoint ID 3, got %d", latest.ID)
		}
	})

	t.Run("AutoCheckpoint", func(t *testing.T) {
		cm := NewCheckpointManager(50*time.Millisecond, 5)

		ks := NewKeyedState()
		ks.Put("key1", "subkey", "value1")
		cm.Register(ks)

		ch := cm.Start()

		// Wait for at least one checkpoint
		select {
		case id := <-ch:
			if id < 1 {
				t.Errorf("Expected positive checkpoint ID, got %d", id)
			}
		case <-time.After(500 * time.Millisecond):
			t.Error("Timeout waiting for checkpoint")
		}

		cm.Stop()
	})
}
