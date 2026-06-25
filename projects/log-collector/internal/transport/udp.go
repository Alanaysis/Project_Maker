package transport

import (
	"fmt"
	"net"
	"strings"
	"sync"
)

// UDPReceiver listens on a UDP port and sends received log lines to an output channel.
// Each UDP packet is treated as one log line.
type UDPReceiver struct {
	addr   string
	output chan RawLog
	conn   *net.UDPConn
	done   chan struct{}
	wg     sync.WaitGroup
	stopOnce sync.Once
}

// NewUDPReceiver creates a new UDP receiver that listens on the given address.
// The address should be in the form "host:port" (e.g., ":5514").
func NewUDPReceiver(addr string, output chan RawLog) *UDPReceiver {
	return &UDPReceiver{
		addr:   addr,
		output: output,
		done:   make(chan struct{}),
	}
}

// Start begins listening for UDP packets.
func (r *UDPReceiver) Start() error {
	udpAddr, err := net.ResolveUDPAddr("udp", r.addr)
	if err != nil {
		return fmt.Errorf("udp receiver: failed to resolve address %s: %w", r.addr, err)
	}

	conn, err := net.ListenUDP("udp", udpAddr)
	if err != nil {
		return fmt.Errorf("udp receiver: failed to listen on %s: %w", r.addr, err)
	}
	r.conn = conn

	r.wg.Add(1)
	go r.receive()

	return nil
}

// Addr returns the address the receiver is listening on.
func (r *UDPReceiver) Addr() string {
	if r.conn != nil {
		return r.conn.LocalAddr().String()
	}
	return r.addr
}

// Done returns a channel that is closed when the receiver stops.
func (r *UDPReceiver) Done() <-chan struct{} {
	return r.done
}

// Stop signals the receiver to stop and waits for completion.
func (r *UDPReceiver) Stop() {
	r.stopOnce.Do(func() {
		close(r.done)
		if r.conn != nil {
			r.conn.Close()
		}
	})
	r.wg.Wait()
}

// receive reads UDP packets and sends them to the output channel.
func (r *UDPReceiver) receive() {
	defer r.wg.Done()

	buf := make([]byte, 65535) // Max UDP packet size

	for {
		select {
		case <-r.done:
			return
		default:
		}

		n, addr, err := r.conn.ReadFromUDP(buf)
		if err != nil {
			select {
			case <-r.done:
				return
			default:
				continue
			}
		}

		if n == 0 {
			continue
		}

		line := strings.TrimSpace(string(buf[:n]))
		if line == "" {
			continue
		}

		rawLog := RawLog{
			Line:   line,
			Source: fmt.Sprintf("udp:%s", addr.String()),
			Addr:   addr.String(),
		}

		select {
		case r.output <- rawLog:
		case <-r.done:
			return
		}
	}
}
