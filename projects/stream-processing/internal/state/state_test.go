package state

import (
	"sync"
	"testing"
	"time"

	"github.com/learning/stream-processing/internal/core"
)

func TestStateStoreBasicOperations(t *testing.T) {
	s := NewStateStore()

	// Put and Get
	s.Put("key1", 42)
	val, ok := s.Get("key1")
	if !ok || val != 42 {
		t.Errorf("Get(key1) = %v, %v; want 42, true", val, ok)
	}

	// Get missing key
	_, ok = s.Get("nonexistent")
	if ok {
		t.Error("expected false for missing key")
	}

	// Overwrite
	s.Put("key1", 99)
	val, _ = s.Get("key1")
	if val != 99 {
		t.Errorf("after overwrite, Get(key1) = %v, want 99", val)
	}

	// Delete
	s.Delete("key1")
	_, ok = s.Get("key1")
	if ok {
		t.Error("expected false after Delete")
	}
}

func TestStateStoreKeys(t *testing.T) {
	s := NewStateStore()
	s.Put("a", 1)
	s.Put("b", 2)
	s.Put("c", 3)

	keys := s.Keys()
	if len(keys) != 3 {
		t.Errorf("expected 3 keys, got %d", len(keys))
	}
}

func TestStateStoreSize(t *testing.T) {
	s := NewStateStore()
	if s.Size() != 0 {
		t.Errorf("empty store size = %d, want 0", s.Size())
	}

	s.Put("a", 1)
	s.Put("b", 2)
	if s.Size() != 2 {
		t.Errorf("size = %d, want 2", s.Size())
	}
}

func TestStateStoreClear(t *testing.T) {
	s := NewStateStore()
	s.Put("a", 1)
	s.Put("b", 2)
	s.Clear()

	if s.Size() != 0 {
		t.Errorf("after Clear, size = %d, want 0", s.Size())
	}
}

func TestStateStoreGetOrDefault(t *testing.T) {
	s := NewStateStore()

	val := s.GetOrDefault("missing", "default")
	if val != "default" {
		t.Errorf("GetOrDefault = %v, want 'default'", val)
	}

	s.Put("exists", "value")
	val = s.GetOrDefault("exists", "default")
	if val != "value" {
		t.Errorf("GetOrDefault = %v, want 'value'", val)
	}
}

func TestStateStoreUpdate(t *testing.T) {
	s := NewStateStore()

	// Update on missing key (nil -> value)
	s.Put("counter", 0)
	s.Update("counter", func(current interface{}) interface{} {
		return current.(int) + 1
	})

	val, _ := s.Get("counter")
	if val != 1 {
		t.Errorf("after Update, counter = %v, want 1", val)
	}

	// Update existing
	s.Update("counter", func(current interface{}) interface{} {
		return current.(int) + 10
	})

	val, _ = s.Get("counter")
	if val != 11 {
		t.Errorf("after second Update, counter = %v, want 11", val)
	}
}

func TestStateStoreConcurrency(t *testing.T) {
	s := NewStateStore()
	var wg sync.WaitGroup

	// Concurrent writes
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			key := "key"
			s.Update(key, func(current interface{}) interface{} {
				if current == nil {
					return n
				}
				return current.(int) + n
			})
		}(i)
	}

	wg.Wait()

	val, _ := s.Get("key")
	total := val.(int)

	// Sum of 0..99 = 4950
	if total != 4950 {
		t.Errorf("concurrent sum = %d, want 4950", total)
	}
}

func TestWindowState(t *testing.T) {
	ws := NewWindowState(1 * time.Hour)

	w := core.Window{
		Start: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		End:   time.Date(2024, 1, 1, 0, 1, 0, 0, time.UTC),
	}

	// GetState creates a new store
	store := ws.GetState(w)
	store.Put("count", 5)

	// GetState returns same store
	store2 := ws.GetState(w)
	val, _ := store2.Get("count")
	if val != 5 {
		t.Errorf("expected count=5, got %v", val)
	}

	if ws.Count() != 1 {
		t.Errorf("Count = %d, want 1", ws.Count())
	}
}

func TestWindowStateExpire(t *testing.T) {
	ws := NewWindowState(30 * time.Second)

	old := core.Window{
		Start: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		End:   time.Date(2024, 1, 1, 0, 1, 0, 0, time.UTC), // ends at 00:01
	}
	recent := core.Window{
		Start: time.Date(2024, 1, 1, 0, 0, 50, 0, time.UTC),
		End:   time.Date(2024, 1, 1, 0, 1, 50, 0, time.UTC), // ends at 00:01:50
	}

	ws.GetState(old).Put("k", 1)
	ws.GetState(recent).Put("k", 2)

	// Expire windows older than 30s from "now"
	// old ended at 00:01:00, now=00:01:40 -> elapsed 40s > 30s -> expired
	// recent ended at 00:01:50, now=00:01:40 -> elapsed -10s -> NOT expired
	now := time.Date(2024, 1, 1, 0, 1, 40, 0, time.UTC)
	expired := ws.Expire(now)

	if expired != 1 {
		t.Errorf("expired = %d, want 1", expired)
	}
	if ws.Count() != 1 {
		t.Errorf("remaining = %d, want 1", ws.Count())
	}
}

func TestWindowStateClear(t *testing.T) {
	ws := NewWindowState(1 * time.Hour)
	w := core.Window{
		Start: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		End:   time.Date(2024, 1, 1, 0, 1, 0, 0, time.UTC),
	}
	ws.GetState(w)

	ws.Clear()
	if ws.Count() != 0 {
		t.Errorf("after Clear, Count = %d, want 0", ws.Count())
	}
}
