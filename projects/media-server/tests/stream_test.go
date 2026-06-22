package tests

import (
	"testing"
	"time"

	"github.com/media-server/internal/stream"
)

func TestNewStream(t *testing.T) {
	s := stream.NewStream("test-id", "test-key")

	if s.ID != "test-id" {
		t.Errorf("Expected stream ID 'test-id', got '%s'", s.ID)
	}

	if s.Key != "test-key" {
		t.Errorf("Expected stream key 'test-key', got '%s'", s.Key)
	}

	if s.State != stream.StreamStateIdle {
		t.Errorf("Expected stream state idle, got %v", s.State)
	}
}

func TestStreamPublish(t *testing.T) {
	s := stream.NewStream("test-id", "test-key")

	// Test publish
	err := s.Publish("publisher-1")
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	if s.State != stream.StreamStatePublishing {
		t.Errorf("Expected stream state publishing, got %v", s.State)
	}

	if s.GetPublisher() == nil {
		t.Error("Expected publisher to be set")
	}

	// Test double publish
	err = s.Publish("publisher-2")
	if err != stream.ErrStreamAlreadyPublishing {
		t.Errorf("Expected ErrStreamAlreadyPublishing, got %v", err)
	}
}

func TestStreamUnpublish(t *testing.T) {
	s := stream.NewStream("test-id", "test-key")

	s.Publish("publisher-1")
	s.Unpublish()

	if s.State != stream.StreamStateIdle {
		t.Errorf("Expected stream state idle, got %v", s.State)
	}

	if s.GetPublisher() != nil {
		t.Error("Expected publisher to be nil")
	}
}

func TestStreamSubscribe(t *testing.T) {
	s := stream.NewStream("test-id", "test-key")

	// Try to subscribe to idle stream
	err := s.Subscribe("subscriber-1")
	if err != stream.ErrStreamNotPublishing {
		t.Errorf("Expected ErrStreamNotPublishing, got %v", err)
	}

	// Publish and subscribe
	s.Publish("publisher-1")
	err = s.Subscribe("subscriber-1")
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	if s.GetSubscriberCount() != 1 {
		t.Errorf("Expected 1 subscriber, got %d", s.GetSubscriberCount())
	}
}

func TestStreamUnsubscribe(t *testing.T) {
	s := stream.NewStream("test-id", "test-key")

	s.Publish("publisher-1")
	s.Subscribe("subscriber-1")
	s.Subscribe("subscriber-2")

	if s.GetSubscriberCount() != 2 {
		t.Errorf("Expected 2 subscribers, got %d", s.GetSubscriberCount())
	}

	s.Unsubscribe("subscriber-1")
	if s.GetSubscriberCount() != 1 {
		t.Errorf("Expected 1 subscriber, got %d", s.GetSubscriberCount())
	}
}

func TestStreamMetadata(t *testing.T) {
	s := stream.NewStream("test-id", "test-key")

	meta := &stream.Metadata{
		Width:     1920,
		Height:    1080,
		FrameRate: 30.0,
	}

	s.UpdateMetadata(meta)

	if s.Metadata.Width != 1920 {
		t.Errorf("Expected width 1920, got %d", s.Metadata.Width)
	}

	if s.Metadata.Height != 1080 {
		t.Errorf("Expected height 1080, got %d", s.Metadata.Height)
	}
}

func TestNewManager(t *testing.T) {
	m := stream.NewManager()

	if m == nil {
		t.Fatal("Expected manager to be created")
	}
}

func TestManagerGetOrCreateStream(t *testing.T) {
	m := stream.NewManager()

	// Create new stream
	s1, err := m.GetOrCreateStream("stream-1")
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	if s1.Key != "stream-1" {
		t.Errorf("Expected stream key 'stream-1', got '%s'", s1.Key)
	}

	// Get existing stream
	s2, err := m.GetOrCreateStream("stream-1")
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	if s1.ID != s2.ID {
		t.Error("Expected same stream ID for same key")
	}
}

func TestManagerGetStream(t *testing.T) {
	m := stream.NewManager()

	// Try to get non-existent stream
	_, err := m.GetStream("non-existent")
	if err != stream.ErrStreamNotFound {
		t.Errorf("Expected ErrStreamNotFound, got %v", err)
	}

	// Create and get stream
	m.GetOrCreateStream("stream-1")
	_, err = m.GetStream("stream-1")
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
}

func TestManagerDeleteStream(t *testing.T) {
	m := stream.NewManager()

	m.GetOrCreateStream("stream-1")
	m.DeleteStream("stream-1")

	_, err := m.GetStream("stream-1")
	if err != stream.ErrStreamNotFound {
		t.Errorf("Expected ErrStreamNotFound, got %v", err)
	}
}

func TestManagerGetStreamList(t *testing.T) {
	m := stream.NewManager()

	m.GetOrCreateStream("stream-1")
	m.GetOrCreateStream("stream-2")
	m.GetOrCreateStream("stream-3")

	list := m.GetStreamList()
	if len(list) != 3 {
		t.Errorf("Expected 3 streams, got %d", len(list))
	}
}

func TestManagerMaxStreams(t *testing.T) {
	config := &stream.ManagerConfig{
		MaxStreams:        2,
		StreamTimeout:     10 * time.Second,
		CleanupInterval:   1 * time.Second,
		BufferSize:        10,
	}

	m := stream.NewManagerWithConfig(config)

	_, err := m.GetOrCreateStream("stream-1")
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	_, err = m.GetOrCreateStream("stream-2")
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	_, err = m.GetOrCreateStream("stream-3")
	if err != stream.ErrMaxStreamsReached {
		t.Errorf("Expected ErrMaxStreamsReached, got %v", err)
	}
}

func TestStreamWritePacket(t *testing.T) {
	s := stream.NewStream("test-id", "test-key")

	// Write to idle stream should fail
	pkt := &stream.MediaPacket{
		Type:      9,
		Timestamp: 1000,
		Data:      []byte{0x17, 0x01, 0x00, 0x00, 0x00},
	}

	err := s.WritePacket(pkt)
	if err != stream.ErrStreamNotPublishing {
		t.Errorf("Expected ErrStreamNotPublishing, got %v", err)
	}

	// Publish and write
	s.Publish("publisher-1")
	err = s.WritePacket(pkt)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
}

func TestStreamStateString(t *testing.T) {
	tests := []struct {
		state    stream.StreamState
		expected string
	}{
		{stream.StreamStateIdle, "idle"},
		{stream.StreamStatePublishing, "publishing"},
		{stream.StreamStatePlaying, "playing"},
		{stream.StreamState(99), "unknown"},
	}

	for _, tt := range tests {
		if got := tt.state.String(); got != tt.expected {
			t.Errorf("Expected '%s', got '%s'", tt.expected, got)
		}
	}
}
