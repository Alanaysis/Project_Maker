package core

import (
	"testing"
)

func TestStreamEmitAndRead(t *testing.T) {
	s := NewStream(10)

	go func() {
		s.Emit(NewEvent("a", 1))
		s.Emit(NewEvent("b", 2))
		s.Close()
	}()

	var results []Event
	for e := range s.Events() {
		results = append(results, e)
	}

	if len(results) != 2 {
		t.Fatalf("expected 2 events, got %d", len(results))
	}
	if results[0].Key != "a" || results[0].Value != 1 {
		t.Errorf("unexpected first event: %+v", results[0])
	}
	if results[1].Key != "b" || results[1].Value != 2 {
		t.Errorf("unexpected second event: %+v", results[1])
	}
}

func TestStreamEmitAfterClose(t *testing.T) {
	s := NewStream(1)
	s.Close()

	ok := s.Emit(NewEvent("x", 1))
	if ok {
		t.Error("expected Emit to return false after Close")
	}
}
