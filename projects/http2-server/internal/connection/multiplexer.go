package connection

import (
	"sync"

	"github.com/anthropic/http2-server/internal/frame"
)

// Multiplexer manages multiple streams on a single connection
// This is the core of HTTP/2's multiplexing capability
type Multiplexer struct {
	streams map[uint32]*Stream
	mu      sync.RWMutex

	// Round-robin scheduling for fair resource allocation
	currentIndex int
	streamOrder  []uint32
}

// NewMultiplexer creates a new multiplexer
func NewMultiplexer() *Multiplexer {
	return &Multiplexer{
		streams: make(map[uint32]*Stream),
	}
}

// AddStream adds a new stream to the multiplexer
func (m *Multiplexer) AddStream(stream *Stream) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.streams[stream.ID] = stream
	m.streamOrder = append(m.streamOrder, stream.ID)
}

// RemoveStream removes a stream from the multiplexer
func (m *Multiplexer) RemoveStream(streamID uint32) {
	m.mu.Lock()
	defer m.mu.Unlock()

	delete(m.streams, streamID)

	// Remove from order
	for i, id := range m.streamOrder {
		if id == streamID {
			m.streamOrder = append(m.streamOrder[:i], m.streamOrder[i+1:]...)
			break
		}
	}
}

// GetStream returns a stream by ID
func (m *Multiplexer) GetStream(streamID uint32) (*Stream, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	stream, exists := m.streams[streamID]
	return stream, exists
}

// GetNextStream returns the next stream in round-robin order
func (m *Multiplexer) GetNextStream() *Stream {
	m.mu.Lock()
	defer m.mu.Unlock()

	if len(m.streamOrder) == 0 {
		return nil
	}

	// Get next stream ID
	streamID := m.streamOrder[m.currentIndex]
	m.currentIndex = (m.currentIndex + 1) % len(m.streamOrder)

	return m.streams[streamID]
}

// GetActiveStreams returns all active streams
func (m *Multiplexer) GetActiveStreams() []*Stream {
	m.mu.RLock()
	defer m.mu.RUnlock()

	streams := make([]*Stream, 0, len(m.streams))
	for _, stream := range m.streams {
		if stream.State == StreamOpen || stream.State == StreamHalfClosedRemote {
			streams = append(streams, stream)
		}
	}
	return streams
}

// InterleaveFrames interleaves frames from multiple streams
// This is the key to HTTP/2 multiplexing - frames from different streams
// can be sent in any order on the same connection
func (m *Multiplexer) InterleaveFrames(streams []*Stream) []*frame.Frame {
	var frames []*frame.Frame

	// Collect one frame from each stream in round-robin order
	for _, stream := range streams {
		// In a real implementation, this would check for available data
		// and create appropriate frames (HEADERS, DATA, etc.)
		// For now, we just demonstrate the concept
		if stream.State == StreamOpen {
			// Create a DATA frame for this stream
			if len(stream.Body) > 0 {
				f := frame.NewFrame(frame.FrameData, 0, stream.ID, stream.Body)
				frames = append(frames, f)
			}
		}
	}

	return frames
}

// FrameQueue manages a queue of frames to be sent
type FrameQueue struct {
	queue []*frame.Frame
	mu    sync.Mutex
}

// NewFrameQueue creates a new frame queue
func NewFrameQueue() *FrameQueue {
	return &FrameQueue{
		queue: make([]*frame.Frame, 0),
	}
}

// Enqueue adds a frame to the queue
func (fq *FrameQueue) Enqueue(f *frame.Frame) {
	fq.mu.Lock()
	defer fq.mu.Unlock()

	fq.queue = append(fq.queue, f)
}

// Dequeue removes and returns the next frame from the queue
func (fq *FrameQueue) Dequeue() *frame.Frame {
	fq.mu.Lock()
	defer fq.mu.Unlock()

	if len(fq.queue) == 0 {
		return nil
	}

	f := fq.queue[0]
	fq.queue = fq.queue[1:]
	return f
}

// Len returns the number of frames in the queue
func (fq *FrameQueue) Len() int {
	fq.mu.Lock()
	defer fq.mu.Unlock()

	return len(fq.queue)
}
