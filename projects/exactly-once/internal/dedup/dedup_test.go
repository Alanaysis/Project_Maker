package dedup

import (
	"testing"
	"time"
)

func TestDeduplicatorNewMessage(t *testing.T) {
	d := New()

	result := d.Check("key-001")
	if result != ResultNew {
		t.Errorf("expected NEW, got %s", result)
	}

	stats := d.StatsSnapshot()
	if stats.NewMessages != 1 {
		t.Errorf("expected 1 new message, got %d", stats.NewMessages)
	}
}

func TestDeduplicatorDuplicate(t *testing.T) {
	d := New()

	// First check - new
	d.Check("key-001")
	d.MarkCompleted("key-001", []byte("done"))

	// Second check - duplicate
	result := d.Check("key-001")
	if result != ResultDuplicate {
		t.Errorf("expected DUPLICATE, got %s", result)
	}

	stats := d.StatsSnapshot()
	if stats.Duplicates != 1 {
		t.Errorf("expected 1 duplicate, got %d", stats.Duplicates)
	}
}

func TestDeduplicatorInProgress(t *testing.T) {
	d := New()

	// First check - starts processing
	d.Check("key-001")

	// Second check - still in progress
	result := d.Check("key-001")
	if result != ResultInProgress {
		t.Errorf("expected IN_PROGRESS, got %s", result)
	}
}

func TestDeduplicatorReset(t *testing.T) {
	d := New()

	d.Check("key-001")
	d.MarkCompleted("key-001", []byte("done"))

	// Reset allows reprocessing
	d.Reset("key-001")

	result := d.Check("key-001")
	if result != ResultNew {
		t.Errorf("expected NEW after reset, got %s", result)
	}
}

func TestDeduplicatorTTL(t *testing.T) {
	d := New(WithTTL(50 * time.Millisecond))

	d.Check("key-001")
	d.MarkCompleted("key-001", []byte("done"))

	// Before TTL - duplicate
	result := d.Check("key-001")
	if result != ResultDuplicate {
		t.Errorf("expected DUPLICATE before TTL, got %s", result)
	}

	// Wait for TTL to expire
	time.Sleep(60 * time.Millisecond)

	// After TTL - treated as new
	result = d.Check("key-001")
	if result != ResultNew {
		t.Errorf("expected NEW after TTL, got %s", result)
	}
}

func TestDeduplicatorMaxEntries(t *testing.T) {
	d := New(WithMaxEntries(3))

	d.Check("key-001")
	d.Check("key-002")
	d.Check("key-003")

	if d.Size() != 3 {
		t.Errorf("expected size 3, got %d", d.Size())
	}
}

func TestDeduplicatorIsSeen(t *testing.T) {
	d := New()

	if d.IsSeen("key-001") {
		t.Error("expected IsSeen=false for unseen key")
	}

	d.Check("key-001")

	if !d.IsSeen("key-001") {
		t.Error("expected IsSeen=true for seen key")
	}
}

func TestDeduplicatorGetEntry(t *testing.T) {
	d := New()

	// Non-existent key
	entry := d.GetEntry("key-001")
	if entry != nil {
		t.Error("expected nil for non-existent key")
	}

	// Existing key
	d.Check("key-001")
	entry = d.GetEntry("key-001")
	if entry == nil {
		t.Fatal("expected non-nil entry")
	}
	if entry.Key != "key-001" {
		t.Errorf("expected key 'key-001', got '%s'", entry.Key)
	}
	if entry.SeenCount != 1 {
		t.Errorf("expected SeenCount 1, got %d", entry.SeenCount)
	}
}

func TestDeduplicatorCleanup(t *testing.T) {
	d := New(WithTTL(50 * time.Millisecond))

	d.Check("key-001")
	d.Check("key-002")

	time.Sleep(60 * time.Millisecond)

	removed := d.Cleanup()
	if removed != 2 {
		t.Errorf("expected 2 removed, got %d", removed)
	}
	if d.Size() != 0 {
		t.Errorf("expected size 0 after cleanup, got %d", d.Size())
	}
}

func TestDeduplicatorClear(t *testing.T) {
	d := New()

	d.Check("key-001")
	d.Check("key-002")

	d.Clear()

	if d.Size() != 0 {
		t.Errorf("expected size 0 after clear, got %d", d.Size())
	}
	stats := d.StatsSnapshot()
	if stats.TotalChecks != 0 {
		t.Errorf("expected TotalChecks 0 after clear, got %d", stats.TotalChecks)
	}
}

func TestDeduplicatorMarkFailed(t *testing.T) {
	d := New()

	d.Check("key-001")
	d.MarkFailed("key-001", "timeout")

	entry := d.GetEntry("key-001")
	if entry.State != "failed" {
		t.Errorf("expected state 'failed', got '%s'", entry.State)
	}
	if entry.Error != "timeout" {
		t.Errorf("expected error 'timeout', got '%s'", entry.Error)
	}

	// Failed messages are still duplicates
	result := d.Check("key-001")
	if result != ResultDuplicate {
		t.Errorf("expected DUPLICATE for failed message, got %s", result)
	}
}

func TestDeduplicatorConcurrency(t *testing.T) {
	d := New()

	// Concurrent checks should not race
	done := make(chan bool, 100)
	for i := 0; i < 100; i++ {
		go func(id int) {
			key := "key-shared"
			result := d.Check(key)
			if result == ResultNew {
				d.MarkCompleted(key, []byte("done"))
			}
			done <- true
		}(i)
	}

	for i := 0; i < 100; i++ {
		<-done
	}

	// Exactly one should have been new
	stats := d.StatsSnapshot()
	if stats.NewMessages != 1 {
		t.Errorf("expected 1 new message in concurrent test, got %d", stats.NewMessages)
	}
}

func TestResultString(t *testing.T) {
	tests := []struct {
		result   Result
		expected string
	}{
		{ResultNew, "NEW"},
		{ResultDuplicate, "DUPLICATE"},
		{ResultInProgress, "IN_PROGRESS"},
		{Result(99), "UNKNOWN"},
	}

	for _, tt := range tests {
		if got := tt.result.String(); got != tt.expected {
			t.Errorf("Result(%d).String() = %q, want %q", int(tt.result), got, tt.expected)
		}
	}
}

func TestDeduplicatorStats(t *testing.T) {
	d := New()

	d.Check("key-001") // new (TotalChecks=1)
	d.MarkCompleted("key-001", nil)
	d.Check("key-001") // duplicate (TotalChecks=2)
	d.Check("key-002") // new (TotalChecks=3)
	d.Check("key-002") // in progress (TotalChecks=4)

	stats := d.StatsSnapshot()
	if stats.TotalChecks != 4 {
		t.Errorf("expected TotalChecks 4, got %d", stats.TotalChecks)
	}
	if stats.NewMessages != 2 {
		t.Errorf("expected NewMessages 2, got %d", stats.NewMessages)
	}
	if stats.Duplicates != 1 {
		t.Errorf("expected Duplicates 1, got %d", stats.Duplicates)
	}
	if stats.InProgress != 1 {
		t.Errorf("expected InProgress 1, got %d", stats.InProgress)
	}
}
