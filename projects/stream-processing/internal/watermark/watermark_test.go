package watermark

import (
	"testing"
	"time"
)

func TestWatermark(t *testing.T) {
	t.Run("BasicUpdate", func(t *testing.T) {
		wm := NewWatermark(5 * time.Second)
		base := time.Now()

		// Update with event time
		wm.Update(base)

		expected := base.Add(-5 * time.Second)
		if !wm.Current().Equal(expected) {
			t.Errorf("Expected watermark %v, got %v", expected, wm.Current())
		}
	})

	t.Run("ForwardOnly", func(t *testing.T) {
		wm := NewWatermark(5 * time.Second)
		base := time.Now()

		// Update with later time
		wm.Update(base.Add(10 * time.Second))
		wm1 := wm.Current()

		// Update with earlier time (should not move backward)
		wm.Update(base.Add(5 * time.Second))
		wm2 := wm.Current()

		if !wm1.Equal(wm2) {
			t.Errorf("Watermark should not move backward: %v -> %v", wm1, wm2)
		}
	})

	t.Run("IsLate", func(t *testing.T) {
		wm := NewWatermark(5 * time.Second)
		base := time.Now()

		wm.Update(base.Add(10 * time.Second))

		// Event before watermark
		if !wm.IsLate(base) {
			t.Error("Expected event to be late")
		}

		// Event after watermark
		if wm.IsLate(base.Add(20 * time.Second)) {
			t.Error("Expected event to not be late")
		}
	})

	t.Run("MaxOutOfOrderness", func(t *testing.T) {
		wm := NewWatermark(10 * time.Second)
		if wm.GetMaxOutOfOrderness() != 10*time.Second {
			t.Errorf("Expected 10s, got %v", wm.GetMaxOutOfOrderness())
		}
	})
}

func TestBoundedOutOfOrdernessPolicy(t *testing.T) {
	policy := NewBoundedOutOfOrdernessPolicy(5 * time.Second)

	timestamps := []time.Time{
		time.Now(),
		time.Now().Add(-2 * time.Second),
		time.Now().Add(-1 * time.Second),
		time.Now().Add(-3 * time.Second),
	}

	wm := policy.ComputeWatermark(timestamps)

	// Should be max(timestamps) - 5s
	maxTs := timestamps[0]
	for _, ts := range timestamps[1:] {
		if ts.After(maxTs) {
			maxTs = ts
		}
	}
	expected := maxTs.Add(-5 * time.Second)

	if !wm.Equal(expected) {
		t.Errorf("Expected %v, got %v", expected, wm)
	}
}

func TestPeriodicWatermarkGenerator(t *testing.T) {
	wm := NewWatermark(5 * time.Second)
	base := time.Now()
	wm.Update(base.Add(10 * time.Second))

	gen := NewPeriodicWatermarkGenerator(100*time.Millisecond, wm)
	ch := gen.Start()

	// Should receive at least one watermark
	select {
	case ts := <-ch:
		expected := base.Add(10 * time.Second).Add(-5 * time.Second)
		if !ts.Equal(expected) {
			t.Errorf("Expected %v, got %v", expected, ts)
		}
	case <-time.After(500 * time.Millisecond):
		t.Error("Timeout waiting for watermark")
	}

	gen.Stop()
}
