package storage

import (
	"testing"
	"time"
)

func TestStoreAndCount(t *testing.T) {
	s := New()

	if s.Count() != 0 {
		t.Fatalf("expected 0 entries, got %d", s.Count())
	}

	id := s.Store(Entry{
		Timestamp: time.Now(),
		Level:     LevelInfo,
		Message:   "test",
	})

	if id != 1 {
		t.Errorf("expected id 1, got %d", id)
	}
	if s.Count() != 1 {
		t.Errorf("expected 1 entry, got %d", s.Count())
	}
}

func TestStoreMultiple(t *testing.T) {
	s := New()

	for i := 0; i < 100; i++ {
		s.Store(Entry{
			Timestamp: time.Now(),
			Level:     LevelInfo,
			Message:   "test",
		})
	}

	if s.Count() != 100 {
		t.Fatalf("expected 100 entries, got %d", s.Count())
	}
}

func TestQueryByLevel(t *testing.T) {
	s := New()

	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "info1"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelError, Message: "error1"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "info2"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelError, Message: "error2"})

	level := LevelError
	results := s.Query(Query{Level: &level})

	if len(results) != 2 {
		t.Fatalf("expected 2 error entries, got %d", len(results))
	}
	for _, r := range results {
		if r.Level != LevelError {
			t.Errorf("expected error level, got %v", r.Level)
		}
	}
}

func TestQueryByLevels(t *testing.T) {
	s := New()

	s.Store(Entry{Timestamp: time.Now(), Level: LevelDebug, Message: "debug"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "info"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelWarn, Message: "warn"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelError, Message: "error"})

	levels := []Level{LevelWarn, LevelError}
	results := s.Query(Query{Levels: levels})

	if len(results) != 2 {
		t.Fatalf("expected 2 entries, got %d", len(results))
	}
}

func TestQueryByTimeRange(t *testing.T) {
	s := New()

	now := time.Now()
	s.Store(Entry{Timestamp: now.Add(-2 * time.Hour), Level: LevelInfo, Message: "old"})
	s.Store(Entry{Timestamp: now.Add(-1 * time.Hour), Level: LevelInfo, Message: "mid"})
	s.Store(Entry{Timestamp: now, Level: LevelInfo, Message: "new"})

	start := now.Add(-90 * time.Minute)
	end := now.Add(-30 * time.Minute)
	results := s.Query(Query{StartTime: &start, EndTime: &end})

	if len(results) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(results))
	}
	if results[0].Message != "mid" {
		t.Errorf("expected 'mid', got %q", results[0].Message)
	}
}

func TestQueryByMessage(t *testing.T) {
	s := New()

	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "connection established"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelError, Message: "connection timeout"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "request processed"})

	results := s.Query(Query{Message: "connection"})

	if len(results) != 2 {
		t.Fatalf("expected 2 entries, got %d", len(results))
	}
}

func TestQueryByMessageCaseInsensitive(t *testing.T) {
	s := New()

	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "Connection Established"})

	results := s.Query(Query{Message: "connection"})
	if len(results) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(results))
	}
}

func TestQueryBySource(t *testing.T) {
	s := New()

	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "test", Source: "app.log"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "test", Source: "error.log"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "test", Source: "app.log"})

	results := s.Query(Query{Source: "app"})

	if len(results) != 2 {
		t.Fatalf("expected 2 entries, got %d", len(results))
	}
}

func TestQueryByFields(t *testing.T) {
	s := New()

	s.Store(Entry{
		Timestamp: time.Now(),
		Level:     LevelInfo,
		Message:   "test",
		Fields:    map[string]string{"user": "alice", "action": "login"},
	})
	s.Store(Entry{
		Timestamp: time.Now(),
		Level:     LevelInfo,
		Message:   "test",
		Fields:    map[string]string{"user": "bob", "action": "login"},
	})

	results := s.Query(Query{Fields: map[string]string{"user": "alice"}})

	if len(results) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(results))
	}
}

func TestQueryLimit(t *testing.T) {
	s := New()

	for i := 0; i < 50; i++ {
		s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "test"})
	}

	results := s.Query(Query{Limit: 10})

	if len(results) != 10 {
		t.Fatalf("expected 10 entries, got %d", len(results))
	}
}

func TestQueryOffset(t *testing.T) {
	s := New()

	for i := 0; i < 10; i++ {
		s.Store(Entry{
			Timestamp: time.Now(),
			Level:     LevelInfo,
			Message:   "msg",
			Fields:    map[string]string{"index": string(rune('0' + i))},
		})
	}

	results := s.Query(Query{Offset: 5, Limit: 3})

	if len(results) != 3 {
		t.Fatalf("expected 3 entries, got %d", len(results))
	}
}

func TestQueryReverse(t *testing.T) {
	s := New()

	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "first"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "second"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "third"})

	results := s.Query(Query{Reverse: true})

	if len(results) != 3 {
		t.Fatalf("expected 3 entries, got %d", len(results))
	}
	if results[0].Message != "third" {
		t.Errorf("expected 'third' first, got %q", results[0].Message)
	}
	if results[2].Message != "first" {
		t.Errorf("expected 'first' last, got %q", results[2].Message)
	}
}

func TestGetByID(t *testing.T) {
	s := New()

	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "first"})
	s.Store(Entry{Timestamp: time.Now(), Level: LevelError, Message: "second"})

	entry, err := s.GetByID(2)
	if err != nil {
		t.Fatalf("GetByID(2) error: %v", err)
	}
	if entry.Message != "second" {
		t.Errorf("expected 'second', got %q", entry.Message)
	}
}

func TestGetByIDNotFound(t *testing.T) {
	s := New()

	_, err := s.GetByID(1)
	if err == nil {
		t.Fatal("expected error for non-existent entry")
	}
}

func TestClear(t *testing.T) {
	s := New()

	s.Store(Entry{Timestamp: time.Now(), Level: LevelInfo, Message: "test"})
	s.Clear()

	if s.Count() != 0 {
		t.Fatalf("expected 0 entries after clear, got %d", s.Count())
	}
}

func TestStats(t *testing.T) {
	s := New()

	now := time.Now()
	s.Store(Entry{Timestamp: now.Add(-time.Hour), Level: LevelInfo, Message: "test", Source: "app.log"})
	s.Store(Entry{Timestamp: now, Level: LevelError, Message: "test", Source: "error.log"})
	s.Store(Entry{Timestamp: now, Level: LevelInfo, Message: "test", Source: "app.log"})

	stats := s.Stats()

	if stats.TotalEntries != 3 {
		t.Errorf("TotalEntries = %d, want 3", stats.TotalEntries)
	}
	if stats.LevelCounts["INFO"] != 2 {
		t.Errorf("INFO count = %d, want 2", stats.LevelCounts["INFO"])
	}
	if stats.LevelCounts["ERROR"] != 1 {
		t.Errorf("ERROR count = %d, want 1", stats.LevelCounts["ERROR"])
	}
	if stats.SourceCounts["app.log"] != 2 {
		t.Errorf("app.log count = %d, want 2", stats.SourceCounts["app.log"])
	}
	if stats.OldestEntry.IsZero() {
		t.Error("OldestEntry should not be zero")
	}
}

func TestQueryCombinedFilters(t *testing.T) {
	s := New()

	now := time.Now()
	s.Store(Entry{Timestamp: now, Level: LevelInfo, Message: "ok", Source: "app.log"})
	s.Store(Entry{Timestamp: now, Level: LevelError, Message: "fail", Source: "app.log"})
	s.Store(Entry{Timestamp: now, Level: LevelError, Message: "crash", Source: "error.log"})

	level := LevelError
	results := s.Query(Query{
		Level:   &level,
		Source:  "app",
		Message: "fail",
	})

	if len(results) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(results))
	}
	if results[0].Message != "fail" {
		t.Errorf("expected 'fail', got %q", results[0].Message)
	}
}
