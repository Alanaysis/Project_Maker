package rtmp

import (
	"encoding/binary"
	"fmt"
	"math/rand"
	"time"
)

// RTMP handshake constants
const (
	rtmpVersion     = 3
	handshakeSize   = 1536
	rtmpDefaultPort = 1935
)

// Handshake state
type HandshakeState int

const (
	HandshakeStateInit HandshakeState = iota
	HandshakeStateC0Received
	HandshakeStateS0Sent
	HandshakeStateC1Received
	HandshakeStateS1Sent
	HandshakeStateC2Received
	HandshakeStateS2Sent
	HandshakeStateDone
)

// HandshakeMessage represents an RTMP handshake message
type HandshakeMessage struct {
	Version  byte
	Time     uint32
	Zero     uint32
	Random   [handshakeSize - 8]byte
}

// Handshake handles the RTMP handshake process
type Handshake struct {
	state     HandshakeState
	c1        *HandshakeMessage
	s1        *HandshakeMessage
	startTime time.Time
}

// NewHandshake creates a new handshake handler
func NewHandshake() *Handshake {
	return &Handshake{
		state:     HandshakeStateInit,
		startTime: time.Now(),
	}
}

// GetState returns the current handshake state
func (h *Handshake) GetState() HandshakeState {
	return h.state
}

// ProcessC0C1 processes the C0 and C1 handshake messages
// Returns S0, S1, S2 data to send back
func (h *Handshake) ProcessC0C1(data []byte) ([]byte, []byte, []byte, error) {
	if len(data) < 1+handshakeSize {
		return nil, nil, nil, fmt.Errorf("invalid C0+C1 data length: %d", len(data))
	}

	// Parse C0 (1 byte)
	c0 := data[0]
	if c0 != rtmpVersion {
		return nil, nil, nil, fmt.Errorf("unsupported RTMP version: %d", c0)
	}

	// Parse C1 (1536 bytes)
	c1Data := data[1 : 1+handshakeSize]
	h.c1 = parseHandshakeMessage(c1Data)
	h.state = HandshakeStateC0Received

	// Generate S0
	s0 := []byte{rtmpVersion}

	// Generate S1
	s1 := h.generateS1()

	// Generate S2 (echo of C1)
	s2 := h.generateS2()

	h.state = HandshakeStateS0Sent

	return s0, s1, s2, nil
}

// ProcessC2 processes the C2 handshake message
func (h *Handshake) ProcessC2(data []byte) error {
	if len(data) < handshakeSize {
		return fmt.Errorf("invalid C2 data length: %d", len(data))
	}

	// C2 should echo S1
	// In a real implementation, we would verify this
	h.state = HandshakeStateDone

	return nil
}

// IsDone returns true if the handshake is complete
func (h *Handshake) IsDone() bool {
	return h.state == HandshakeStateDone
}

// parseHandshakeMessage parses a handshake message from bytes
func parseHandshakeMessage(data []byte) *HandshakeMessage {
	msg := &HandshakeMessage{}
	msg.Version = 0
	msg.Time = binary.BigEndian.Uint32(data[0:4])
	msg.Zero = binary.BigEndian.Uint32(data[4:8])
	copy(msg.Random[:], data[8:])
	return msg
}

// generateS1 generates the S1 handshake message
func (h *Handshake) generateS1() []byte {
	data := make([]byte, handshakeSize)

	// Time (4 bytes)
	elapsed := uint32(time.Since(h.startTime).Milliseconds())
	binary.BigEndian.PutUint32(data[0:4], elapsed)

	// Zero (4 bytes)
	binary.BigEndian.PutUint32(data[4:8], 0)

	// Random data (1528 bytes)
	rand.Read(data[8:])

	return data
}

// generateS2 generates the S2 handshake message (echo of C1)
func (h *Handshake) generateS2() []byte {
	data := make([]byte, handshakeSize)

	// Echo C1 time
	if h.c1 != nil {
		binary.BigEndian.PutUint32(data[0:4], h.c1.Time)
	} else {
		binary.BigEndian.PutUint32(data[0:4], uint32(time.Now().UnixMilli()))
	}

	// Server time (4 bytes)
	serverTime := uint32(time.Since(h.startTime).Milliseconds())
	binary.BigEndian.PutUint32(data[4:8], serverTime)

	// Echo C1 random data
	if h.c1 != nil {
		copy(data[8:], h.c1.Random[:])
	} else {
		rand.Read(data[8:])
	}

	return data
}

// GenerateC0C1 generates C0 and C1 for client-side handshake
func GenerateC0C1() []byte {
	data := make([]byte, 1+handshakeSize)

	// C0
	data[0] = rtmpVersion

	// C1
	elapsed := uint32(time.Now().UnixMilli())
	binary.BigEndian.PutUint32(data[1:5], elapsed)
	binary.BigEndian.PutUint32(data[5:9], 0)
	rand.Read(data[9 : 1+handshakeSize])

	return data
}

// GenerateC2 generates C2 for client-side handshake
func GenerateC2(s1 []byte) []byte {
	data := make([]byte, handshakeSize)

	// Echo S1 time
	binary.BigEndian.PutUint32(data[0:4], binary.BigEndian.Uint32(s1[0:4]))

	// Client time
	binary.BigEndian.PutUint32(data[4:8], uint32(time.Now().UnixMilli()))

	// Echo S1 random data
	copy(data[8:], s1[8:])

	return data
}
