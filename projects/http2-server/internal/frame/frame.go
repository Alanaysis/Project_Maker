// Package frame implements HTTP/2 frame parsing and serialization.
// HTTP/2 frames are the basic unit of communication in the protocol.
package frame

import (
	"encoding/binary"
	"fmt"
	"io"
)

// Frame types as defined in RFC 7540
const (
	FrameData         uint8 = 0x0
	FrameHeaders      uint8 = 0x1
	FramePriority     uint8 = 0x2
	FrameRSTStream    uint8 = 0x3
	FrameSettings     uint8 = 0x4
	FramePushPromise  uint8 = 0x5
	FramePing         uint8 = 0x6
	FrameGoAway       uint8 = 0x7
	FrameWindowUpdate uint8 = 0x8
	FrameContinuation uint8 = 0x9
)

// Frame flags
const (
	FlagEndStream  uint8 = 0x1
	FlagEndHeaders uint8 = 0x4
	FlagPadded     uint8 = 0x8
	FlagPriority   uint8 = 0x20
	FlagAck        uint8 = 0x1
)

// Maximum frame size constants
const (
	MaxFrameSize      = 16384 // Default max frame size (16KB)
	MinFrameSize      = 16384
	MaxFrameSizeLimit = 16777215 // 2^24 - 1
)

// Frame represents an HTTP/2 frame
type Frame struct {
	Length   uint32 // 24 bits
	Type     uint8  // 8 bits
	Flags    uint8  // 8 bits
	StreamID uint32 // 31 bits (R bit excluded)
	Payload  []byte
}

// FrameHeaderSize is the size of the frame header (9 bytes)
const FrameHeaderSize = 9

// NewFrame creates a new frame with the given parameters
func NewFrame(frameType uint8, flags uint8, streamID uint32, payload []byte) *Frame {
	return &Frame{
		Length:   uint32(len(payload)),
		Type:     frameType,
		Flags:    flags,
		StreamID: streamID & 0x7FFFFFFF, // Mask to 31 bits
		Payload:  payload,
	}
}

// ReadFrame reads a complete frame from the reader
func ReadFrame(r io.Reader) (*Frame, error) {
	// Read the 9-byte frame header
	header := make([]byte, FrameHeaderSize)
	if _, err := io.ReadFull(r, header); err != nil {
		return nil, fmt.Errorf("failed to read frame header: %w", err)
	}

	// Parse the header
	length := uint32(header[0])<<16 | uint32(header[1])<<8 | uint32(header[2])
	frameType := header[3]
	flags := header[4]
	streamID := binary.BigEndian.Uint32(header[5:9]) & 0x7FFFFFFF

	// Validate frame size
	if length > MaxFrameSizeLimit {
		return nil, fmt.Errorf("frame too large: %d bytes (max %d)", length, MaxFrameSizeLimit)
	}

	// Read the payload
	payload := make([]byte, length)
	if length > 0 {
		if _, err := io.ReadFull(r, payload); err != nil {
			return nil, fmt.Errorf("failed to read frame payload: %w", err)
		}
	}

	return &Frame{
		Length:   length,
		Type:     frameType,
		Flags:    flags,
		StreamID: streamID,
		Payload:  payload,
	}, nil
}

// WriteFrame writes a frame to the writer
func WriteFrame(w io.Writer, f *Frame) error {
	// Create the 9-byte header
	header := make([]byte, FrameHeaderSize)

	// Length (24 bits)
	header[0] = byte(f.Length >> 16)
	header[1] = byte(f.Length >> 8)
	header[2] = byte(f.Length)

	// Type (8 bits)
	header[3] = f.Type

	// Flags (8 bits)
	header[4] = f.Flags

	// Stream ID (31 bits, R bit is 0)
	binary.BigEndian.PutUint32(header[5:9], f.StreamID&0x7FFFFFFF)

	// Write header
	if _, err := w.Write(header); err != nil {
		return fmt.Errorf("failed to write frame header: %w", err)
	}

	// Write payload if present
	if len(f.Payload) > 0 {
		if _, err := w.Write(f.Payload); err != nil {
			return fmt.Errorf("failed to write frame payload: %w", err)
		}
	}

	return nil
}

// String returns a human-readable representation of the frame
func (f *Frame) String() string {
	typeName := "UNKNOWN"
	switch f.Type {
	case FrameData:
		typeName = "DATA"
	case FrameHeaders:
		typeName = "HEADERS"
	case FramePriority:
		typeName = "PRIORITY"
	case FrameRSTStream:
		typeName = "RST_STREAM"
	case FrameSettings:
		typeName = "SETTINGS"
	case FramePushPromise:
		typeName = "PUSH_PROMISE"
	case FramePing:
		typeName = "PING"
	case FrameGoAway:
		typeName = "GOAWAY"
	case FrameWindowUpdate:
		typeName = "WINDOW_UPDATE"
	case FrameContinuation:
		typeName = "CONTINUATION"
	}

	return fmt.Sprintf("Frame{Type: %s, Flags: 0x%02x, StreamID: %d, Length: %d}",
		typeName, f.Flags, f.StreamID, f.Length)
}
