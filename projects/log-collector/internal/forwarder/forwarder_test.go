package forwarder

import (
	"fmt"
	"testing"
	"time"
)

// TestBatchSizeDefaults verifies default batch size configuration.
func TestBatchSizeDefaults(t *testing.T) {
	bs := DefaultBatchSize()
	if bs.MaxEntries != 100 {
		t.Errorf("expected MaxEntries=100, got %d", bs.MaxEntries)
	}
	if bs.MaxBytes != 102400 {
		t.Errorf("expected MaxBytes=102400, got %d", bs.MaxBytes)
	}
	if bs.FlushInterval != time.Second {
		t.Errorf("expected FlushInterval=1s, got %v", bs.FlushInterval)
	}
}

// TestRetryConfigDefaults verifies default retry configuration.
func TestRetryConfigDefaults(t *testing.T) {
	rc := DefaultRetryConfig()
	if rc.MaxRetries != 3 {
		t.Errorf("expected MaxRetries=3, got %d", rc.MaxRetries)
	}
	if rc.InitialInterval != 100*time.Millisecond {
		t.Errorf("expected InitialInterval=100ms, got %v", rc.InitialInterval)
	}
	if rc.MaxInterval != 10*time.Second {
		t.Errorf("expected MaxInterval=10s, got %v", rc.MaxInterval)
	}
	if rc.BackoffMultiplier != 2.0 {
		t.Errorf("expected BackoffMultiplier=2.0, got %f", rc.BackoffMultiplier)
	}
}

// TestCalculateBatchSize verifies batch size calculation.
func TestCalculateBatchSize(t *testing.T) {
	entries := []Entry{
		{Raw: "hello world", Message: "hello world", Source: "test"},
		{Raw: "foo bar", Message: "foo bar", Source: "test", Fields: map[string]string{"key": "value"}},
	}
	size := CalculateBatchSize(entries)
	if size <= 0 {
		t.Errorf("expected positive batch size, got %d", size)
	}
}

// TestExponentialBackoff verifies exponential backoff calculation.
func TestExponentialBackoff(t *testing.T) {
	eb := NewExponentialBackoff(100*time.Millisecond, 10*time.Second, 2.0)

	tests := []struct {
		attempt    int
		minExpected time.Duration
		maxExpected time.Duration
	}{
		{0, 100 * time.Millisecond, 100 * time.Millisecond},
		{1, 200 * time.Millisecond, 200 * time.Millisecond},
		{2, 400 * time.Millisecond, 400 * time.Millisecond},
		{10, 10 * time.Second, 10 * time.Second},
	}

	for _, tc := range tests {
		interval := eb.NextInterval(tc.attempt)
		if interval < tc.minExpected || interval > tc.maxExpected {
			t.Errorf("attempt=%d: expected interval in [%v, %v], got %v",
				tc.attempt, tc.minExpected, tc.maxExpected, interval)
		}
	}
}

// TestBackpressureMonitor verifies backpressure monitoring.
func TestBackpressureMonitor(t *testing.T) {
	bm := NewBackpressureMonitor(1000)

	// At 50% capacity, not backpressured
	if bm.Check(500) {
		t.Error("expected no backpressure at 50% capacity")
	}

	// At 85% capacity, backpressured
	if !bm.Check(850) {
		t.Error("expected backpressure at 85% capacity")
	}

	// Check ratio
	ratio := bm.GetBackpressureRatio()
	if ratio < 0.8 || ratio > 0.9 {
		t.Errorf("expected ratio ~0.85, got %f", ratio)
	}
}

// TestNewExponentialBackoffNegative verifies negative attempt handling.
func TestNewExponentialBackoffNegative(t *testing.T) {
	eb := NewExponentialBackoff(100*time.Millisecond, 10*time.Second, 2.0)
	interval := eb.NextInterval(-1)
	if interval != 100*time.Millisecond {
		t.Errorf("expected 100ms for negative attempt, got %v", interval)
	}
}

// TestCalculateBatchSizeEmpty verifies empty batch calculation.
func TestCalculateBatchSizeEmpty(t *testing.T) {
	size := CalculateBatchSize(nil)
	if size != 0 {
		t.Errorf("expected batch size 0 for empty slice, got %d", size)
	}
}

// TestCalculateBatchSizeWithFields verifies batch size with fields.
func TestCalculateBatchSizeWithFields(t *testing.T) {
	entries := []Entry{
		{
			Raw:     "test",
			Message: "test message",
			Source:  "test-source",
			Fields: map[string]string{
				"key1": "value1",
				"key2": "value2",
				"key3": "value3",
			},
		},
	}
	size := CalculateBatchSize(entries)
	// At minimum: len("test") + len("test message") + len("test-source") + len("key1")+len("value1") + len("key2")+len("value2") + len("key3")+len("value3")
	// = 4 + 12 + 11 + 4+6 + 4+6 + 4+6 = 57
	if size < 50 {
		t.Errorf("expected batch size >= 50, got %d", size)
	}
}

// TestBackpressureMonitorZeroCap verifies behavior with zero capacity.
func TestBackpressureMonitorZeroCap(t *testing.T) {
	bm := NewBackpressureMonitor(0)
	ratio := bm.GetBackpressureRatio()
	if ratio != 0 {
		t.Errorf("expected ratio 0 for zero capacity, got %f", ratio)
	}
}

// TestDefaultRetryConfig verifies all default values.
func TestDefaultRetryConfig(t *testing.T) {
	rc := DefaultRetryConfig()
	expected := RetryConfig{
		MaxRetries:        3,
		InitialInterval:   100 * time.Millisecond,
		MaxInterval:       10 * time.Second,
		BackoffMultiplier: 2.0,
	}
	if rc != expected {
		t.Errorf("expected %+v, got %+v", expected, rc)
	}
}

// TestDefaultBatchSize verifies all default values.
func TestDefaultBatchSize(t *testing.T) {
	bs := DefaultBatchSize()
	expected := BatchSize{
		MaxEntries:    100,
		MaxBytes:      102400,
		FlushInterval: 1 * time.Second,
	}
	if bs != expected {
		t.Errorf("expected %+v, got %+v", expected, bs)
	}
}

// TestExponentialBackoffMaxInterval verifies cap at max interval.
func TestExponentialBackoffMaxInterval(t *testing.T) {
	eb := NewExponentialBackoff(1*time.Second, 5*time.Second, 3.0)
	// After enough attempts, should cap at max
	interval := eb.NextInterval(10)
	if interval != 5*time.Second {
		t.Errorf("expected capped at 5s, got %v", interval)
	}
}

// TestBackpressureMonitorCheck verifies backpressure threshold.
func TestBackpressureMonitorCheck(t *testing.T) {
	bm := NewBackpressureMonitor(100)

	// Exactly at 80% should not trigger (80/100 = 80%)
	if bm.Check(80) {
		t.Error("expected no backpressure at exactly 80%")
	}

	// One above 80% should trigger
	if !bm.Check(81) {
		t.Error("expected backpressure at 81%")
	}
}
