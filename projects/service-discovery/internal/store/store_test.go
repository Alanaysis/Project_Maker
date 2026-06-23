package store

import (
	"context"
	"testing"
	"time"
)

func TestMemStorePutGet(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	// Put a key-value pair
	err := s.Put(ctx, "/test/key1", []byte("value1"), 0)
	if err != nil {
		t.Fatalf("Put failed: %v", err)
	}

	// Get the value
	val, err := s.Get(ctx, "/test/key1")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if string(val) != "value1" {
		t.Errorf("expected 'value1', got '%s'", string(val))
	}
}

func TestMemStoreGetNotFound(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	_, err := s.Get(ctx, "/nonexistent")
	if err != ErrKeyNotFound {
		t.Errorf("expected ErrKeyNotFound, got %v", err)
	}
}

func TestMemStoreDelete(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	s.Put(ctx, "/test/key1", []byte("value1"), 0)

	err := s.Delete(ctx, "/test/key1")
	if err != nil {
		t.Fatalf("Delete failed: %v", err)
	}

	_, err = s.Get(ctx, "/test/key1")
	if err != ErrKeyNotFound {
		t.Errorf("expected ErrKeyNotFound after delete, got %v", err)
	}
}

func TestMemStoreDeleteNotFound(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	err := s.Delete(ctx, "/nonexistent")
	if err != ErrKeyNotFound {
		t.Errorf("expected ErrKeyNotFound, got %v", err)
	}
}

func TestMemStoreList(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	s.Put(ctx, "/services/svc1/id1", []byte("data1"), 0)
	s.Put(ctx, "/services/svc1/id2", []byte("data2"), 0)
	s.Put(ctx, "/services/svc2/id3", []byte("data3"), 0)

	// List all services
	all, err := s.List(ctx, "/services/")
	if err != nil {
		t.Fatalf("List failed: %v", err)
	}
	if len(all) != 3 {
		t.Errorf("expected 3 entries, got %d", len(all))
	}

	// List specific service
	svc1, err := s.List(ctx, "/services/svc1/")
	if err != nil {
		t.Fatalf("List failed: %v", err)
	}
	if len(svc1) != 2 {
		t.Errorf("expected 2 entries for svc1, got %d", len(svc1))
	}
}

func TestMemStoreLease(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	// Create lease
	leaseID, err := s.GrantLease(ctx, 10*time.Second)
	if err != nil {
		t.Fatalf("GrantLease failed: %v", err)
	}
	if leaseID <= 0 {
		t.Errorf("expected positive lease ID, got %d", leaseID)
	}

	// Put with lease
	err = s.Put(ctx, "/test/key1", []byte("value1"), leaseID)
	if err != nil {
		t.Fatalf("Put with lease failed: %v", err)
	}

	// Get should succeed (lease not expired)
	val, err := s.Get(ctx, "/test/key1")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if string(val) != "value1" {
		t.Errorf("expected 'value1', got '%s'", string(val))
	}
}

func TestMemStoreLeaseExpiration(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	// Create short lease
	leaseID, err := s.GrantLease(ctx, 50*time.Millisecond)
	if err != nil {
		t.Fatalf("GrantLease failed: %v", err)
	}

	// Put with lease
	s.Put(ctx, "/test/key1", []byte("value1"), leaseID)

	// Get should succeed immediately
	_, err = s.Get(ctx, "/test/key1")
	if err != nil {
		t.Fatalf("Get should succeed before expiration: %v", err)
	}

	// Wait for lease to expire
	time.Sleep(100 * time.Millisecond)

	// Get should fail after expiration
	_, err = s.Get(ctx, "/test/key1")
	if err != ErrKeyExpired {
		t.Errorf("expected ErrKeyExpired, got %v", err)
	}
}

func TestMemStoreKeepAlive(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	leaseID, _ := s.GrantLease(ctx, 100*time.Millisecond)
	s.Put(ctx, "/test/key1", []byte("value1"), leaseID)

	// Keep alive before expiration
	time.Sleep(50 * time.Millisecond)
	err := s.KeepAlive(ctx, leaseID)
	if err != nil {
		t.Fatalf("KeepAlive failed: %v", err)
	}

	// Should still be accessible
	time.Sleep(60 * time.Millisecond)
	_, err = s.Get(ctx, "/test/key1")
	if err != nil {
		t.Errorf("Get should succeed after KeepAlive: %v", err)
	}
}

func TestMemStoreRevokeLease(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	leaseID, _ := s.GrantLease(ctx, 10*time.Second)
	s.Put(ctx, "/test/key1", []byte("value1"), leaseID)
	s.Put(ctx, "/test/key2", []byte("value2"), leaseID)

	// Revoke lease
	err := s.RevokeLease(ctx, leaseID)
	if err != nil {
		t.Fatalf("RevokeLease failed: %v", err)
	}

	// Keys should be deleted
	_, err = s.Get(ctx, "/test/key1")
	if err != ErrKeyNotFound {
		t.Errorf("expected ErrKeyNotFound after revoke, got %v", err)
	}
	_, err = s.Get(ctx, "/test/key2")
	if err != ErrKeyNotFound {
		t.Errorf("expected ErrKeyNotFound after revoke, got %v", err)
	}
}

func TestMemStoreWatch(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	ch, err := s.Watch(ctx, "/test/")
	if err != nil {
		t.Fatalf("Watch failed: %v", err)
	}

	// Put should trigger event
	s.Put(ctx, "/test/key1", []byte("value1"), 0)

	select {
	case event := <-ch:
		if event.Type != EventPut {
			t.Errorf("expected EventPut, got %v", event.Type)
		}
		if event.Key != "/test/key1" {
			t.Errorf("expected key '/test/key1', got '%s'", event.Key)
		}
	case <-time.After(time.Second):
		t.Fatal("timeout waiting for watch event")
	}

	// Delete should trigger event
	s.Delete(ctx, "/test/key1")

	select {
	case event := <-ch:
		if event.Type != EventDelete {
			t.Errorf("expected EventDelete, got %v", event.Type)
		}
	case <-time.After(time.Second):
		t.Fatal("timeout waiting for watch event")
	}
}

func TestMemStoreWatchCancel(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx, cancel := context.WithCancel(context.Background())

	ch, err := s.Watch(ctx, "/test/")
	if err != nil {
		t.Fatalf("Watch failed: %v", err)
	}

	// Cancel should close channel
	cancel()
	time.Sleep(50 * time.Millisecond)

	// Channel should be closed
	_, ok := <-ch
	if ok {
		t.Error("expected channel to be closed after cancel")
	}
}

func TestMemStoreExpireLeases(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	leaseID, _ := s.GrantLease(ctx, 50*time.Millisecond)
	s.Put(ctx, "/test/key1", []byte("value1"), leaseID)

	time.Sleep(100 * time.Millisecond)

	// Expire leases manually
	s.ExpireLeases()

	// Key should be deleted
	_, err := s.Get(ctx, "/test/key1")
	if err != ErrKeyNotFound {
		t.Errorf("expected ErrKeyNotFound after expire, got %v", err)
	}
}

func TestMemStoreConcurrent(t *testing.T) {
	s := NewMemStore()
	defer s.Close()
	ctx := context.Background()

	// Concurrent writes
	done := make(chan bool)
	for i := 0; i < 10; i++ {
		go func(n int) {
			key := "/test/key" + string(rune('0'+n))
			s.Put(ctx, key, []byte("value"), 0)
			done <- true
		}(i)
	}

	for i := 0; i < 10; i++ {
		<-done
	}

	// Verify all keys exist
	for i := 0; i < 10; i++ {
		key := "/test/key" + string(rune('0'+i))
		_, err := s.Get(ctx, key)
		if err != nil {
			t.Errorf("Get failed for %s: %v", key, err)
		}
	}
}
