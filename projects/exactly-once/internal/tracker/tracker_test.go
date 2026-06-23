package tracker

import (
	"testing"
	"time"

	"github.com/anthropic/exactly-once/internal/message"
)

func TestTrackerTrack(t *testing.T) {
	tr := New()

	msg := message.New("msg-001", []byte("test"))
	tr.Track(msg)

	if tr.Size() != 1 {
		t.Errorf("expected size 1, got %d", tr.Size())
	}

	record := tr.GetRecord("msg-001")
	if record == nil {
		t.Fatal("expected non-nil record")
	}
	if record.MessageID != "msg-001" {
		t.Errorf("expected MessageID 'msg-001', got '%s'", record.MessageID)
	}
	if record.CurrentState != message.StatePending {
		t.Errorf("expected PENDING, got %s", record.CurrentState)
	}
	if len(record.Events) != 1 {
		t.Errorf("expected 1 event, got %d", len(record.Events))
	}
}

func TestTrackerTrackDuplicate(t *testing.T) {
	tr := New()

	msg := message.New("msg-001", []byte("test"))
	tr.Track(msg)
	tr.Track(msg) // Should be no-op

	if tr.Size() != 1 {
		t.Errorf("expected size 1, got %d", tr.Size())
	}

	record := tr.GetRecord("msg-001")
	if len(record.Events) != 1 {
		t.Errorf("expected 1 event, got %d", len(record.Events))
	}
}

func TestTrackerUpdate(t *testing.T) {
	tr := New()

	msg := message.New("msg-001", []byte("test"))
	tr.Track(msg)

	// Transition to processing
	msg.MarkProcessing()
	tr.Update(msg)

	record := tr.GetRecord("msg-001")
	if record.CurrentState != message.StateProcessing {
		t.Errorf("expected PROCESSING, got %s", record.CurrentState)
	}
	if len(record.Events) != 2 {
		t.Errorf("expected 2 events, got %d", len(record.Events))
	}

	// Transition to completed
	msg.MarkCompleted([]byte("result"))
	tr.Update(msg)

	record = tr.GetRecord("msg-001")
	if record.CurrentState != message.StateCompleted {
		t.Errorf("expected COMPLETED, got %s", record.CurrentState)
	}
	if len(record.Events) != 3 {
		t.Errorf("expected 3 events, got %d", len(record.Events))
	}
}

func TestTrackerUpdateAutoTrack(t *testing.T) {
	tr := New()

	// Update without prior Track should auto-track
	msg := message.New("msg-001", []byte("test"))
	msg.MarkProcessing()
	tr.Update(msg)

	if tr.Size() != 1 {
		t.Errorf("expected size 1, got %d", tr.Size())
	}
}

func TestTrackerGetEvents(t *testing.T) {
	tr := New()

	msg := message.New("msg-001", []byte("test"))
	tr.Track(msg)
	msg.MarkProcessing()
	tr.Update(msg)
	msg.MarkCompleted([]byte("done"))
	tr.Update(msg)

	events := tr.GetEvents("msg-001")
	if len(events) != 3 {
		t.Fatalf("expected 3 events, got %d", len(events))
	}

	// Verify event order
	if events[0].ToState != message.StatePending {
		t.Errorf("expected first event to PENDING, got %s", events[0].ToState)
	}
	if events[1].ToState != message.StateProcessing {
		t.Errorf("expected second event to PROCESSING, got %s", events[1].ToState)
	}
	if events[2].ToState != message.StateCompleted {
		t.Errorf("expected third event to COMPLETED, got %s", events[2].ToState)
	}
}

func TestTrackerGetEventsNotFound(t *testing.T) {
	tr := New()

	events := tr.GetEvents("nonexistent")
	if events != nil {
		t.Error("expected nil for nonexistent message")
	}
}

func TestTrackerGetRecordNotFound(t *testing.T) {
	tr := New()

	record := tr.GetRecord("nonexistent")
	if record != nil {
		t.Error("expected nil for nonexistent message")
	}
}

func TestTrackerGetByState(t *testing.T) {
	tr := New()

	msg1 := message.New("msg-001", []byte("test"))
	tr.Track(msg1)

	msg2 := message.New("msg-002", []byte("test"))
	msg2.MarkProcessing()
	tr.Track(msg2)

	msg3 := message.New("msg-003", []byte("test"))
	msg3.MarkCompleted([]byte("done"))
	tr.Track(msg3)

	pending := tr.GetByState(message.StatePending)
	if len(pending) != 1 || pending[0] != "msg-001" {
		t.Errorf("expected [msg-001], got %v", pending)
	}

	completed := tr.GetByState(message.StateCompleted)
	if len(completed) != 1 || completed[0] != "msg-003" {
		t.Errorf("expected [msg-003], got %v", completed)
	}
}

func TestTrackerGetFailedMessages(t *testing.T) {
	tr := New()

	msg1 := message.New("msg-001", []byte("test"))
	msg1.MarkFailed("error")
	tr.Track(msg1)

	msg2 := message.New("msg-002", []byte("test"))
	tr.Track(msg2)

	failed := tr.GetFailedMessages()
	if len(failed) != 1 || failed[0] != "msg-001" {
		t.Errorf("expected [msg-001], got %v", failed)
	}
}

func TestTrackerGetCompletedMessages(t *testing.T) {
	tr := New()

	msg1 := message.New("msg-001", []byte("test"))
	msg1.MarkCompleted([]byte("done"))
	tr.Track(msg1)

	msg2 := message.New("msg-002", []byte("test"))
	tr.Track(msg2)

	completed := tr.GetCompletedMessages()
	if len(completed) != 1 || completed[0] != "msg-001" {
		t.Errorf("expected [msg-001], got %v", completed)
	}
}

func TestTrackerStats(t *testing.T) {
	tr := New()

	msg1 := message.New("msg-001", []byte("test"))
	tr.Track(msg1)

	msg2 := message.New("msg-002", []byte("test"))
	msg2.MarkCompleted([]byte("done"))
	tr.Track(msg2)

	msg3 := message.New("msg-003", []byte("test"))
	msg3.MarkFailed("error")
	tr.Track(msg3)

	stats := tr.StatsSnapshot()
	if stats.TotalTracked != 3 {
		t.Errorf("expected TotalTracked 3, got %d", stats.TotalTracked)
	}
	if stats.InProgress != 1 {
		t.Errorf("expected InProgress 1, got %d", stats.InProgress)
	}
	if stats.Completed != 1 {
		t.Errorf("expected Completed 1, got %d", stats.Completed)
	}
	if stats.Failed != 1 {
		t.Errorf("expected Failed 1, got %d", stats.Failed)
	}
}

func TestTrackerClear(t *testing.T) {
	tr := New()

	msg := message.New("msg-001", []byte("test"))
	tr.Track(msg)

	tr.Clear()

	if tr.Size() != 0 {
		t.Errorf("expected size 0, got %d", tr.Size())
	}
	stats := tr.StatsSnapshot()
	if stats.TotalTracked != 0 {
		t.Errorf("expected TotalTracked 0, got %d", stats.TotalTracked)
	}
}

func TestTrackerCleanup(t *testing.T) {
	tr := New()

	msg := message.New("msg-001", []byte("test"))
	tr.Track(msg)

	// Manually set LastUpdated to the past
	tr.mu.Lock()
	tr.records["msg-001"].LastUpdated = time.Now().Add(-2 * time.Hour)
	tr.mu.Unlock()

	removed := tr.Cleanup(1 * time.Hour)
	if removed != 1 {
		t.Errorf("expected 1 removed, got %d", removed)
	}
	if tr.Size() != 0 {
		t.Errorf("expected size 0, got %d", tr.Size())
	}
}

func TestTrackerGetRecordCopy(t *testing.T) {
	tr := New()

	msg := message.New("msg-001", []byte("test"))
	tr.Track(msg)

	record1 := tr.GetRecord("msg-001")
	record2 := tr.GetRecord("msg-001")

	// Modifying one should not affect the other
	record1.Events = append(record1.Events, Event{Message: "modified"})

	if len(record2.Events) != 1 {
		t.Error("expected records to be independent copies")
	}
}
