package source

import (
	"bufio"
	"fmt"
	"net"
	"sync"
	"time"

	"github.com/learning/stream-processing/internal/core"
)

// SocketSource reads data from a TCP or UDP socket.
// Each received line becomes an event.
//
// Usage:
//
//	src := NewSocketSource("tcp", "localhost:9999")
//	stream, err := src.Open()
type SocketSource struct {
	network string // "tcp" or "udp"
	address string
	conn    net.Conn
	stopped bool
	mu      sync.Mutex
	stopCh  chan struct{}
}

// NewSocketSource creates a socket source.
// network should be "tcp" or "udp".
func NewSocketSource(network, address string) *SocketSource {
	return &SocketSource{
		network: network,
		address: address,
		stopCh:  make(chan struct{}),
	}
}

func (ss *SocketSource) Name() string {
	return fmt.Sprintf("socket:%s://%s", ss.network, ss.address)
}

// Open connects to the socket and emits received data as events.
func (ss *SocketSource) Open() (*core.Stream, error) {
	conn, err := net.Dial(ss.network, ss.address)
	if err != nil {
		return nil, fmt.Errorf("connect to %s://%s: %w", ss.network, ss.address, err)
	}

	ss.mu.Lock()
	ss.conn = conn
	ss.mu.Unlock()

	stream := core.NewStream(100)

	go func() {
		defer conn.Close()
		defer stream.Close()

		scanner := bufio.NewScanner(conn)

		for scanner.Scan() {
			ss.mu.Lock()
			if ss.stopped {
				ss.mu.Unlock()
				return
			}
			ss.mu.Unlock()

			line := scanner.Text()
			if line == "" {
				continue
			}

			event := core.NewEventWithTime(
				"socket",
				line,
				time.Now(),
			)

			select {
			case <-ss.stopCh:
				return
			default:
				if !stream.Emit(event) {
					return
				}
			}
		}
	}()

	return stream, nil
}

// Stop closes the socket connection.
func (ss *SocketSource) Stop() error {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	if !ss.stopped {
		ss.stopped = true
		close(ss.stopCh)
		if ss.conn != nil {
			return ss.conn.Close()
		}
	}
	return nil
}
