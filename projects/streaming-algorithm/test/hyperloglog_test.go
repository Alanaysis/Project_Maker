package test

import (
	"math"
	"testing"

	stream "github.com/streaming-algorithm/internal"
)

func TestHyperLogLogAdd(t *testing.T) {
	hll := stream.NewHyperLogLog(0.01)
	hll.Add("test")
	if hll.Count() <= 0 {
		t.Error("count should be positive after adding an item")
	}
}

func TestHyperLogLogCountUnique(t *testing.T) {
	hll := stream.NewHyperLogLog(0.05)
	for i := 0; i < 10000; i++ {
		hll.Add(string(rune(i)))
	}
	est := hll.Count()
	if math.Abs(est-10000) > 3000 {
		t.Errorf("expected ~10000, got %.0f", est)
	}
}

func TestHyperLogLogMerge(t *testing.T) {
	hll1 := stream.NewHyperLogLog(0.05)
	hll2 := stream.NewHyperLogLog(0.05)
	for i := 0; i < 5000; i++ {
		hll1.Add(string(rune(i)))
	}
	for i := 5000; i < 10000; i++ {
		hll2.Add(string(rune(i)))
	}
	hll1.Merge(hll2)
	est := hll1.Count()
	if math.Abs(est-10000) > 3000 {
		t.Errorf("merged expected ~10000, got %.0f", est)
	}
}

func TestHyperLogLogDuplicate(t *testing.T) {
	hll := stream.NewHyperLogLog(0.05)
	for i := 0; i < 100; i++ {
		hll.Add("same")
	}
	est := hll.Count()
	if est > 10 {
		t.Errorf("duplicates should give ~1, got %.0f", est)
	}
}

func TestHyperLogLogMergeDifferentSize(t *testing.T) {
	hll1 := stream.NewHyperLogLog(0.05)
	hll2 := stream.NewHyperLogLog(0.1)
	hll1.Merge(hll2)
}
