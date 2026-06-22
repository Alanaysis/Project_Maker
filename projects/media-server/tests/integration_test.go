package tests

import (
	"testing"
	"time"

	"github.com/media-server/internal/stream"
)

func TestStreamLifecycle(t *testing.T) {
	// Create manager
	m := stream.NewManager()

	// Create stream
	s, err := m.GetOrCreateStream("test-stream")
	if err != nil {
		t.Fatalf("Failed to create stream: %v", err)
	}

	// Publish
	err = s.Publish("publisher-1")
	if err != nil {
		t.Fatalf("Failed to publish: %v", err)
	}

	// Subscribe
	err = s.Subscribe("subscriber-1")
	if err != nil {
		t.Fatalf("Failed to subscribe: %v", err)
	}

	// Check state
	if s.State != stream.StreamStatePlaying {
		t.Errorf("Expected state playing, got %v", s.State)
	}

	// Write packet
	pkt := &stream.MediaPacket{
		Type:      9,
		Timestamp: 1000,
		Data:      []byte{0x17, 0x01, 0x00, 0x00, 0x00},
	}

	err = s.WritePacket(pkt)
	if err != nil {
		t.Fatalf("Failed to write packet: %v", err)
	}

	// Unsubscribe
	s.Unsubscribe("subscriber-1")
	if s.GetSubscriberCount() != 0 {
		t.Errorf("Expected 0 subscribers, got %d", s.GetSubscriberCount())
	}

	// Unpublish
	s.Unpublish()
	if s.State != stream.StreamStateIdle {
		t.Errorf("Expected state idle, got %v", s.State)
	}

	// Delete stream
	m.DeleteStream("test-stream")

	// Verify deletion
	_, err = m.GetStream("test-stream")
	if err != stream.ErrStreamNotFound {
		t.Errorf("Expected stream not found, got %v", err)
	}
}

func TestMultipleStreams(t *testing.T) {
	m := stream.NewManager()

	// Create multiple streams
	for i := 0; i < 5; i++ {
		key := "stream-" + string(rune('a'+i))
		_, err := m.GetOrCreateStream(key)
		if err != nil {
			t.Fatalf("Failed to create stream %s: %v", key, err)
		}
	}

	// Get stream list
	list := m.GetStreamList()
	if len(list) != 5 {
		t.Errorf("Expected 5 streams, got %d", len(list))
	}

	// Stop all
	m.StopAll()

	// Verify all stopped
	list = m.GetStreamList()
	if len(list) != 0 {
		t.Errorf("Expected 0 streams, got %d", len(list))
	}
}

func TestStreamConcurrency(t *testing.T) {
	m := stream.NewManager()

	s, _ := m.GetOrCreateStream("concurrent-stream")
	s.Publish("publisher-1")

	// Concurrent subscribers
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(id int) {
			subID := "subscriber-" + string(rune('a'+id))
			err := s.Subscribe(subID)
			if err != nil {
				t.Errorf("Failed to subscribe: %v", err)
			}
			done <- true
		}(i)
	}

	// Wait for all subscribers
	for i := 0; i < 10; i++ {
		<-done
	}

	if s.GetSubscriberCount() != 10 {
		t.Errorf("Expected 10 subscribers, got %d", s.GetSubscriberCount())
	}
}

func TestStreamCleanup(t *testing.T) {
	config := &stream.ManagerConfig{
		MaxStreams:        100,
		StreamTimeout:     100 * time.Millisecond,
		CleanupInterval:   50 * time.Millisecond,
		BufferSize:        10,
	}

	m := stream.NewManagerWithConfig(config)

	// Create idle stream
	m.GetOrCreateStream("idle-stream")

	// Wait for cleanup
	time.Sleep(200 * time.Millisecond)

	// Stream should be cleaned up
	_, err := m.GetStream("idle-stream")
	if err != stream.ErrStreamNotFound {
		t.Errorf("Expected stream to be cleaned up, got %v", err)
	}
}

func TestStreamStats(t *testing.T) {
	m := stream.NewManager()

	// Create and publish streams
	s1, _ := m.GetOrCreateStream("stream-1")
	s1.Publish("pub-1")
	s1.Subscribe("sub-1")

	s2, _ := m.GetOrCreateStream("stream-2")
	s2.Publish("pub-2")

	stats := m.GetStats()

	if stats.TotalStreams != 2 {
		t.Errorf("Expected 2 total streams, got %d", stats.TotalStreams)
	}

	if stats.PublishingStreams != 2 {
		t.Errorf("Expected 2 publishing streams, got %d", stats.PublishingStreams)
	}

	if stats.TotalSubscribers != 1 {
		t.Errorf("Expected 1 subscriber, got %d", stats.TotalSubscribers)
	}
}
