// Package transport implements network-based log transport.
//
// It provides TCP and UDP receivers for collecting logs over the network,
// and a file writer for outputting logs to files.
package transport

import (
	"bufio"
	"fmt"
	"net"
	"sync"
)

// RawLog represents a raw log line received over the network.
type RawLog struct {
	Line   string // The raw log line
	Source string // Source identifier (e.g., "tcp:192.168.1.1:12345")
	Addr   string // Remote address
}

// TCPReceiver listens on a TCP port and sends received log lines to an output channel.
type TCPReceiver struct {
	addr     string
	output   chan RawLog
	listener net.Listener
	done     chan struct{}
	wg       sync.WaitGroup
	stopOnce sync.Once
}

// NewTCPReceiver creates a new TCP receiver that listens on the given address.
// The address should be in the form "host:port" (e.g., ":5514" or "0.0.0.0:5514").
func NewTCPReceiver(addr string, output chan RawLog) *TCPReceiver {
	return &TCPReceiver{
		addr:   addr,
		output: output,
		done:   make(chan struct{}),
	}
}

// Start begins listening for TCP connections.
func (r *TCPReceiver) Start() error {
	ln, err := net.Listen("tcp", r.addr)
	if err != nil {
		return fmt.Errorf("tcp receiver: failed to listen on %s: %w", r.addr, err)
	}
	r.listener = ln

	r.wg.Add(1)
	go r.accept()

	return nil
}

// Addr returns the address the receiver is listening on.
func (r *TCPReceiver) Addr() string {
	if r.listener != nil {
		return r.listener.Addr().String()
	}
	return r.addr
}

// Done returns a channel that is closed when the receiver stops.
func (r *TCPReceiver) Done() <-chan struct{} {
	return r.done
}

// Stop signals the receiver to stop and waits for completion.
func (r *TCPReceiver) Stop() {
	r.stopOnce.Do(func() {
		close(r.done)
		if r.listener != nil {
			r.listener.Close()
		}
	})
	r.wg.Wait()
}

// accept accepts incoming TCP connections.
func (r *TCPReceiver) accept() {
	defer r.wg.Done()

	for {
		conn, err := r.listener.Accept()
		if err != nil {
			select {
			case <-r.done:
				return
			default:
				// Log error and continue
				continue
			}
		}

		r.wg.Add(1)
		go r.handleConn(conn)
	}
}

// handleConn reads log lines from a single TCP connection.
func (r *TCPReceiver) handleConn(conn net.Conn) {
	defer r.wg.Done()
	defer conn.Close()

	addr := conn.RemoteAddr().String()
	scanner := bufio.NewScanner(conn)
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)

	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}

		rawLog := RawLog{
			Line:   line,
			Source: fmt.Sprintf("tcp:%s", addr),
			Addr:   addr,
		}

		select {
		case r.output <- rawLog:
		case <-r.done:
			return
		}
	}
}
