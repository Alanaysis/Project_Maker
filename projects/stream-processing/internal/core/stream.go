package core

// Stream is a channel-based data stream that carries events.
type Stream struct {
	events chan Event
	done   chan struct{}
}

// NewStream creates a new stream with the given buffer size.
func NewStream(bufferSize int) *Stream {
	return &Stream{
		events: make(chan Event, bufferSize),
		done:   make(chan struct{}),
	}
}

// Events returns the underlying event channel for reading.
func (s *Stream) Events() <-chan Event {
	return s.events
}

// Emit sends an event into the stream.
// Returns false if the stream is closed.
func (s *Stream) Emit(e Event) bool {
	// Check done first to avoid sending on a closed events channel.
	select {
	case <-s.done:
		return false
	default:
	}
	select {
	case <-s.done:
		return false
	case s.events <- e:
		return true
	}
}

// Close signals that no more events will be emitted.
func (s *Stream) Close() {
	close(s.done)
	close(s.events)
}

// Done returns a channel that is closed when the stream is finished.
func (s *Stream) Done() <-chan struct{} {
	return s.done
}
