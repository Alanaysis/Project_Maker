// Package forwarder implements log forwarding with batching, retry, and backpressure.
package forwarder

import (
	"fmt"
	"net"
	"time"
)

// TCPSender sends log entries over TCP.
type TCPSender struct {
	addr    string
	conn    net.Conn
	healthy bool
}

// NewTCPSender creates a new TCPSender.
func NewTCPSender(addr string) *TCPSender {
	return &TCPSender{
		addr:    addr,
		healthy: true,
	}
}

// connect establishes a TCP connection if not already connected.
func (s *TCPSender) connect() error {
	if s.conn != nil {
		return nil
	}
	conn, err := net.Dial("tcp", s.addr)
	if err != nil {
		s.healthy = false
		return fmt.Errorf("tcp sender: failed to connect to %s: %w", s.addr, err)
	}
	s.conn = conn
	s.healthy = true
	return nil
}

// Send sends a batch of entries over TCP.
func (s *TCPSender) Send(entries []Entry) (int, error) {
	if err := s.connect(); err != nil {
		return 0, err
	}

	var sent int
	for _, entry := range entries {
		line := formatEntry(entry)
		if _, err := s.conn.Write([]byte(line + "\n")); err != nil {
			s.healthy = false
			s.conn.Close()
			s.conn = nil
			return sent, fmt.Errorf("tcp sender: write error after %d entries: %w", sent, err)
		}
		sent++
	}
	return sent, nil
}

// Name returns the destination name.
func (s *TCPSender) Name() string {
	return fmt.Sprintf("tcp:%s", s.addr)
}

// Close closes the TCP connection.
func (s *TCPSender) Close() error {
	if s.conn != nil {
		return s.conn.Close()
	}
	return nil
}

// IsHealthy returns whether the connection is healthy.
func (s *TCPSender) IsHealthy() bool {
	return s.healthy
}

// UDPSender sends log entries over UDP.
type UDPSender struct {
	conn    *net.UDPConn
	addr    string
	healthy bool
}

// NewUDPSender creates a new UDPSender.
func (s *UDPSender) New(addr string) *UDPSender {
	return &UDPSender{
		addr:    addr,
		healthy: true,
	}
}

// Start connects to the UDP address.
func (s *UDPSender) Start() error {
	udpAddr, err := net.ResolveUDPAddr("udp", s.addr)
	if err != nil {
		return err
	}
	conn, err := net.DialUDP("udp", nil, udpAddr)
	if err != nil {
		s.healthy = false
		return err
	}
	s.conn = conn
	return nil
}

// Send sends a batch of entries over UDP.
func (s *UDPSender) Send(entries []Entry) (int, error) {
	if s.conn == nil {
		return 0, fmt.Errorf("udp sender: not connected")
	}

	var sent int
	for _, entry := range entries {
		line := formatEntry(entry)
		if _, err := s.conn.Write([]byte(line + "\n")); err != nil {
			s.healthy = false
			return sent, err
		}
		sent++
	}
	return sent, nil
}

// Name returns the destination name.
func (s *UDPSender) Name() string {
	return fmt.Sprintf("udp:%s", s.addr)
}

// Close closes the UDP connection.
func (s *UDPSender) Close() error {
	if s.conn != nil {
		return s.conn.Close()
	}
	return nil
}

// IsHealthy returns whether the connection is healthy.
func (s *UDPSender) IsHealthy() bool {
	return s.healthy
}

// formatEntry formats an Entry into a log line string.
func formatEntry(entry Entry) string {
	ts := entry.Timestamp.Format("2006-01-02 15:04:05")
	if entry.Timestamp.IsZero() {
		ts = "----/--/-- --:--:--"
	}
	return fmt.Sprintf("%s %-5s [%s:%s] %s", ts, entry.Level, entry.Source, entry.Timestamp.Format("15:04:05"), entry.Message)
}
