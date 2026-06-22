package connection

import (
	"bytes"
	"net"
	"sync"
	"testing"
	"time"

	"github.com/anthropic/http2-server/internal/frame"
)

// mockConn implements net.Conn for testing
type mockConn struct {
	readBuf  *bytes.Buffer
	writeBuf *bytes.Buffer
	mu       sync.Mutex
}

func newMockConn() *mockConn {
	return &mockConn{
		readBuf:  &bytes.Buffer{},
		writeBuf: &bytes.Buffer{},
	}
}

func (m *mockConn) Read(b []byte) (n int, err error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.readBuf.Read(b)
}

func (m *mockConn) Write(b []byte) (n int, err error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.writeBuf.Write(b)
}

func (m *mockConn) Close() error                       { return nil }
func (m *mockConn) LocalAddr() net.Addr                { return &net.TCPAddr{} }
func (m *mockConn) RemoteAddr() net.Addr               { return &net.TCPAddr{} }
func (m *mockConn) SetDeadline(t time.Time) error      { return nil }
func (m *mockConn) SetReadDeadline(t time.Time) error  { return nil }
func (m *mockConn) SetWriteDeadline(t time.Time) error { return nil }

func TestNewStream(t *testing.T) {
	stream := NewStream(1, 65535)

	if stream.ID != 1 {
		t.Errorf("Expected stream ID 1, got %d", stream.ID)
	}
	if stream.State != StreamIdle {
		t.Errorf("Expected state Idle, got %d", stream.State)
	}
	if stream.SendWindow != 65535 {
		t.Errorf("Expected send window 65535, got %d", stream.SendWindow)
	}
	if stream.ReceiveWindow != 65535 {
		t.Errorf("Expected receive window 65535, got %d", stream.ReceiveWindow)
	}
}

func TestNewConnection(t *testing.T) {
	mock := newMockConn()
	handler := func(stream *Stream) error { return nil }

	conn := NewConnection(mock, handler)

	if conn.conn != mock {
		t.Error("Connection should store the conn")
	}
	if conn.handler == nil {
		t.Error("Connection should store the handler")
	}
	if conn.settings == nil {
		t.Error("Connection should have settings")
	}
	if conn.peerSettings == nil {
		t.Error("Connection should have peer settings")
	}
}

func TestStreamStateTransitions(t *testing.T) {
	stream := NewStream(1, 65535)

	// Test state transitions
	if stream.State != StreamIdle {
		t.Errorf("Initial state should be Idle, got %d", stream.State)
	}

	stream.State = StreamOpen
	if stream.State != StreamOpen {
		t.Errorf("State should be Open, got %d", stream.State)
	}

	stream.State = StreamHalfClosedRemote
	if stream.State != StreamHalfClosedRemote {
		t.Errorf("State should be HalfClosedRemote, got %d", stream.State)
	}

	stream.State = StreamClosed
	if stream.State != StreamClosed {
		t.Errorf("State should be Closed, got %d", stream.State)
	}
}

func TestMultiplexerAddRemove(t *testing.T) {
	mux := NewMultiplexer()

	// Add streams
	stream1 := NewStream(1, 65535)
	stream2 := NewStream(3, 65535)
	stream3 := NewStream(5, 65535)

	mux.AddStream(stream1)
	mux.AddStream(stream2)
	mux.AddStream(stream3)

	// Get stream
	s, exists := mux.GetStream(3)
	if !exists {
		t.Error("Stream 3 should exist")
	}
	if s.ID != 3 {
		t.Errorf("Expected stream ID 3, got %d", s.ID)
	}

	// Remove stream
	mux.RemoveStream(3)
	_, exists = mux.GetStream(3)
	if exists {
		t.Error("Stream 3 should not exist after removal")
	}

	// Verify remaining streams
	s1, exists := mux.GetStream(1)
	if !exists || s1.ID != 1 {
		t.Error("Stream 1 should still exist")
	}
	s3, exists := mux.GetStream(5)
	if !exists || s3.ID != 5 {
		t.Error("Stream 5 should still exist")
	}
}

func TestMultiplexerRoundRobin(t *testing.T) {
	mux := NewMultiplexer()

	// Add streams
	mux.AddStream(NewStream(1, 65535))
	mux.AddStream(NewStream(3, 65535))
	mux.AddStream(NewStream(5, 65535))

	// Test round-robin
	s1 := mux.GetNextStream()
	s2 := mux.GetNextStream()
	s3 := mux.GetNextStream()
	s4 := mux.GetNextStream() // Should wrap around

	if s1.ID != 1 {
		t.Errorf("Expected stream 1, got %d", s1.ID)
	}
	if s2.ID != 3 {
		t.Errorf("Expected stream 3, got %d", s2.ID)
	}
	if s3.ID != 5 {
		t.Errorf("Expected stream 5, got %d", s3.ID)
	}
	if s4.ID != 1 {
		t.Errorf("Expected stream 1 (wrap around), got %d", s4.ID)
	}
}

func TestFrameQueue(t *testing.T) {
	queue := NewFrameQueue()

	// Test empty queue
	if queue.Len() != 0 {
		t.Errorf("Empty queue length should be 0, got %d", queue.Len())
	}
	if f := queue.Dequeue(); f != nil {
		t.Error("Dequeue on empty queue should return nil")
	}

	// Add frames
	f1 := frame.NewFrame(frame.FrameData, 0, 1, []byte("frame1"))
	f2 := frame.NewFrame(frame.FrameHeaders, 0, 3, []byte("frame2"))
	f3 := frame.NewFrame(frame.FrameData, 0, 5, []byte("frame3"))

	queue.Enqueue(f1)
	queue.Enqueue(f2)
	queue.Enqueue(f3)

	if queue.Len() != 3 {
		t.Errorf("Queue length should be 3, got %d", queue.Len())
	}

	// Dequeue in order
	d1 := queue.Dequeue()
	d2 := queue.Dequeue()
	d3 := queue.Dequeue()

	if d1.StreamID != 1 {
		t.Errorf("Expected stream 1, got %d", d1.StreamID)
	}
	if d2.StreamID != 3 {
		t.Errorf("Expected stream 3, got %d", d2.StreamID)
	}
	if d3.StreamID != 5 {
		t.Errorf("Expected stream 5, got %d", d3.StreamID)
	}

	if queue.Len() != 0 {
		t.Errorf("Queue should be empty, got length %d", queue.Len())
	}
}

func TestMultiplexerGetActiveStreams(t *testing.T) {
	mux := NewMultiplexer()

	// Add streams with different states
	s1 := NewStream(1, 65535)
	s1.State = StreamOpen
	mux.AddStream(s1)

	s2 := NewStream(3, 65535)
	s2.State = StreamHalfClosedRemote
	mux.AddStream(s2)

	s3 := NewStream(5, 65535)
	s3.State = StreamClosed
	mux.AddStream(s3)

	s4 := NewStream(7, 65535)
	s4.State = StreamIdle
	mux.AddStream(s4)

	active := mux.GetActiveStreams()
	if len(active) != 2 {
		t.Errorf("Expected 2 active streams, got %d", len(active))
	}

	// Verify active streams are Open and HalfClosedRemote
	foundOpen := false
	foundHalfClosed := false
	for _, s := range active {
		if s.State == StreamOpen {
			foundOpen = true
		}
		if s.State == StreamHalfClosedRemote {
			foundHalfClosed = true
		}
	}

	if !foundOpen {
		t.Error("Should find Open stream")
	}
	if !foundHalfClosed {
		t.Error("Should find HalfClosedRemote stream")
	}
}
