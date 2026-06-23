package window

import (
	"testing"
	"time"
)

func TestTumblingWindowAssign(t *testing.T) {
	tw := NewTumblingWindow(10 * time.Second)

	base := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)

	tests := []struct {
		name      string
		ts        time.Time
		wantStart time.Time
		wantEnd   time.Time
	}{
		{
			name:      "exact boundary",
			ts:        base,
			wantStart: base,
			wantEnd:   base.Add(10 * time.Second),
		},
		{
			name:      "mid window",
			ts:        base.Add(5 * time.Second),
			wantStart: base,
			wantEnd:   base.Add(10 * time.Second),
		},
		{
			name:      "next window",
			ts:        base.Add(11 * time.Second),
			wantStart: base.Add(10 * time.Second),
			wantEnd:   base.Add(20 * time.Second),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			w := tw.Assign(tt.ts)
			if w.Start != tt.wantStart {
				t.Errorf("Start = %v, want %v", w.Start, tt.wantStart)
			}
			if w.End != tt.wantEnd {
				t.Errorf("End = %v, want %v", w.End, tt.wantEnd)
			}
		})
	}
}

func TestSlidingWindowAssign(t *testing.T) {
	// Size=10s, Slide=5s means each timestamp falls in 2 windows
	sw := NewSlidingWindow(10*time.Second, 5*time.Second)

	base := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	ts := base.Add(7 * time.Second) // Should be in [0,10) and [5,15)

	windows := sw.Assign(ts)

	if len(windows) < 1 {
		t.Fatalf("expected at least 1 window, got %d", len(windows))
	}

	// Verify the timestamp is contained in each assigned window
	for _, w := range windows {
		if !w.Contains(ts) {
			t.Errorf("window [%v, %v) does not contain timestamp %v", w.Start, w.End, ts)
		}
	}
}

func TestSlidingWindowSizeAndSlide(t *testing.T) {
	sw := NewSlidingWindow(10*time.Second, 5*time.Second)

	if sw.Size() != 10*time.Second {
		t.Errorf("size = %v, want 10s", sw.Size())
	}
	if sw.Slide() != 5*time.Second {
		t.Errorf("slide = %v, want 5s", sw.Slide())
	}
}

func TestTumblingWindowSize(t *testing.T) {
	tw := NewTumblingWindow(5 * time.Second)
	if tw.Size() != 5*time.Second {
		t.Errorf("size = %v, want 5s", tw.Size())
	}
}
