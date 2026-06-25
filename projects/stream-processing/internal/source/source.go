package source

import (
	"github.com/learning/stream-processing/internal/core"
)

// Source represents a data source that produces events into a stream.
// Implementations include FileSource, SocketSource, and KafkaSource.
type Source interface {
	// Name returns the source identifier.
	Name() string

	// Open starts producing events into the returned stream.
	// The stream is closed when the source is exhausted or stopped.
	Open() (*core.Stream, error)

	// Stop signals the source to stop producing events.
	Stop() error
}
