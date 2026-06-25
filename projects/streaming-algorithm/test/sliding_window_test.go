package test

import (
	"testing"

	stream "github.com/streaming-algorithm/internal"
)

func TestSlidingWindowAdd(t *testing.T) {
	sw := stream.NewSlidingWindow(3)
	sw.Add(1.0)
	sw.Add(2.0)
	sw.Add(3.0)
	vals := sw.Values()
	if len(vals) != 3 {
		t.Fatalf("expected 3 values, got %d", len(vals))
	}
}

func TestSlidingWindowAverage(t *testing.T) {
	sw := stream.NewSlidingWindow(3)
	sw.Add(10)
	sw.Add(20)
	sw.Add(30)
	avg, ok := sw.Average()
	if !ok {
		t.Fatal("expected average to be available")
	}
	if avg != 20.0 {
		t.Errorf("expected 20.0, got %.1f", avg)
	}
}

func TestSlidingWindowEmpty(t *testing.T) {
	sw := stream.NewSlidingWindow(3)
	_, ok := sw.Average()
	if ok {
		t.Fatal("expected no average for empty window")
	}
}

func TestSlidingWindowWrap(t *testing.T) {
	sw := stream.NewSlidingWindow(3)
	for i := 0; i < 10; i++ {
		sw.Add(float64(i))
	}
	vals := sw.Values()
	if len(vals) != 3 {
		t.Fatalf("expected 3 values, got %d", len(vals))
	}
}

func TestSlidingWindowOverwrite(t *testing.T) {
	sw := stream.NewSlidingWindow(2)
	sw.Add(1)
	sw.Add(2)
	sw.Add(3)
	avg, _ := sw.Average()
	if avg != 2.5 {
		t.Errorf("expected 2.5, got %.1f", avg)
	}
}
