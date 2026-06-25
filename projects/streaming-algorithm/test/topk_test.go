package test

import (
	"testing"

	stream "github.com/streaming-algorithm/internal"
)

func TestTopKAdd(t *testing.T) {
	tk := stream.NewTopK(3)
	tk.Add("a")
	tk.Add("b")
	tk.Add("c")
	top := tk.Top()
	if len(top) != 3 {
		t.Fatalf("expected 3 items, got %d", len(top))
	}
}

func TestTopKOrder(t *testing.T) {
	tk := stream.NewTopK(3)
	items := []string{"a", "a", "a", "b", "b", "c"}
	for _, item := range items {
		tk.Add(item)
	}
	top := tk.Top()
	if len(top) > 0 && top[0].Item != "a" {
		t.Errorf("expected 'a' as top, got %s", top[0].Item)
	}
}

func TestTopKCapacity(t *testing.T) {
	tk := stream.NewTopK(2)
	items := []string{"a", "b", "c", "a", "b", "c", "a", "b"}
	for _, item := range items {
		tk.Add(item)
	}
	top := tk.Top()
	if len(top) > 2 {
		t.Errorf("expected at most 2 items, got %d", len(top))
	}
}

func TestTopKEmpty(t *testing.T) {
	tk := stream.NewTopK(3)
	top := tk.Top()
	if len(top) != 0 {
		t.Errorf("expected empty, got %d items", len(top))
	}
}

func TestTopKLessThanK(t *testing.T) {
	tk := stream.NewTopK(5)
	tk.Add("x")
	tk.Add("y")
	top := tk.Top()
	if len(top) != 2 {
		t.Errorf("expected 2 items, got %d", len(top))
	}
}
