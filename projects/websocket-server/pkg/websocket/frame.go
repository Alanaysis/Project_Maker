// Package websocket implements the WebSocket protocol as defined in RFC 6455.
// This file handles WebSocket frame encoding and decoding.
package websocket

import (
	"encoding/binary"
	"errors"
	"io"
)

// WebSocket frame opcodes as defined in RFC 6455 Section 11.8
const (
	OpcodeContinuation = 0x0
	OpcodeText         = 0x1
	OpcodeBinary       = 0x2
	OpcodeClose        = 0x8
	OpcodePing         = 0x9
	OpcodePong         = 0xA
)

// Maximum payload size for control frames (ping/pong/close)
const maxControlPayloadSize = 125

// Frame represents a WebSocket frame
// ⭐ Key structure - Understanding this is crucial for WebSocket protocol
type Frame struct {
	Fin     bool   // Final fragment flag
	Opcode  byte   // Frame opcode
	Masked  bool   // Whether payload is masked
	Payload []byte // Frame payload data
}

// Common errors
var (
	ErrFrameTooLarge    = errors.New("frame payload exceeds maximum size")
	ErrControlFrameTooLarge = errors.New("control frame payload exceeds 125 bytes")
	ErrInvalidOpcode    = errors.New("invalid opcode")
	ErrReservedBitsSet  = errors.New("reserved bits are set")
)

// ReadFrame reads a single WebSocket frame from the reader
// ⭐ This is the core of WebSocket protocol parsing
//
// WebSocket frame format (RFC 6455):
//  0                   1                   2                   3
//  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
// +-+-+-+-+-------+-+-------------+-------------------------------+
// |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
// |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
// |N|V|V|V|       |S|             |   (if payload len==126/127)   |
// | |1|2|3|       |K|             |                               |
// +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
// |     Extended payload length continued, if payload len == 127  |
// + - - - - - - - - - - - - - - - +-------------------------------+
// |                               |Masking-key, if MASK set to 1  |
// +-------------------------------+-------------------------------+
// | Masking-key (continued)       |          Payload Data         |
// +-------------------------------- - - - - - - - - - - - - - - - +
// :                     Payload Data continued ...                :
// + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
// |                     Payload Data continued ...                |
// +---------------------------------------------------------------+
func ReadFrame(r io.Reader) (*Frame, error) {
	// Read first two bytes (fin, opcode, mask, initial payload length)
	header := make([]byte, 2)
	if _, err := io.ReadFull(r, header); err != nil {
		return nil, err
	}

	f := &Frame{}

	// Parse first byte: FIN bit and opcode
	f.Fin = (header[0] & 0x80) != 0
	f.Opcode = header[0] & 0x0F

	// Check reserved bits (RSV1, RSV2, RSV3 must be 0)
	if header[0]&0x70 != 0 {
		return nil, ErrReservedBitsSet
	}

	// Parse second byte: MASK bit and payload length
	f.Masked = (header[1] & 0x80) != 0
	payloadLen := uint64(header[1] & 0x7F)

	// Handle extended payload length
	// 0-125: payload length is the value itself
	// 126: next 2 bytes are the payload length (16-bit unsigned)
	// 127: next 8 bytes are the payload length (64-bit unsigned)
	switch payloadLen {
	case 126:
		extLen := make([]byte, 2)
		if _, err := io.ReadFull(r, extLen); err != nil {
			return nil, err
		}
		payloadLen = uint64(binary.BigEndian.Uint16(extLen))
	case 127:
		extLen := make([]byte, 8)
		if _, err := io.ReadFull(r, extLen); err != nil {
			return nil, err
		}
		payloadLen = binary.BigEndian.Uint64(extLen)
	}

	// Read masking key if present
	var maskKey [4]byte
	if f.Masked {
		if _, err := io.ReadFull(r, maskKey[:]); err != nil {
			return nil, err
		}
	}

	// Read payload
	f.Payload = make([]byte, payloadLen)
	if _, err := io.ReadFull(r, f.Payload); err != nil {
		return nil, err
	}

	// Unmask payload if masked
	if f.Masked {
		for i := range f.Payload {
			f.Payload[i] ^= maskKey[i%4]
		}
	}

	return f, nil
}

// WriteFrame writes a WebSocket frame to the writer
// ⭐ Server frames are NOT masked (only client->server frames are masked)
func WriteFrame(w io.Writer, f *Frame) error {
	// Validate control frames
	if f.Opcode >= 0x8 {
		if len(f.Payload) > maxControlPayloadSize {
			return ErrControlFrameTooLarge
		}
		if !f.Fin {
			return errors.New("control frames must not be fragmented")
		}
	}

	// Build header
	var header []byte

	// First byte: FIN + opcode
	b0 := f.Opcode
	if f.Fin {
		b0 |= 0x80
	}
	header = append(header, b0)

	// Second byte: MASK (always 0 for server) + payload length
	if len(f.Payload) <= 125 {
		header = append(header, byte(len(f.Payload)))
	} else if len(f.Payload) <= 65535 {
		header = append(header, 126)
		extLen := make([]byte, 2)
		binary.BigEndian.PutUint16(extLen, uint16(len(f.Payload)))
		header = append(header, extLen...)
	} else {
		header = append(header, 127)
		extLen := make([]byte, 8)
		binary.BigEndian.PutUint64(extLen, uint64(len(f.Payload)))
		header = append(header, extLen...)
	}

	// Write header
	if _, err := w.Write(header); err != nil {
		return err
	}

	// Write payload
	if len(f.Payload) > 0 {
		if _, err := w.Write(f.Payload); err != nil {
			return err
		}
	}

	return nil
}

// NewTextFrame creates a new text frame
func NewTextFrame(payload string) *Frame {
	return &Frame{
		Fin:     true,
		Opcode:  OpcodeText,
		Payload: []byte(payload),
	}
}

// NewBinaryFrame creates a new binary frame
func NewBinaryFrame(payload []byte) *Frame {
	return &Frame{
		Fin:     true,
		Opcode:  OpcodeBinary,
		Payload: payload,
	}
}

// NewCloseFrame creates a close frame with optional status code and reason
func NewCloseFrame(statusCode uint16, reason string) *Frame {
	payload := make([]byte, 2)
	binary.BigEndian.PutUint16(payload, statusCode)
	payload = append(payload, []byte(reason)...)

	return &Frame{
		Fin:     true,
		Opcode:  OpcodeClose,
		Payload: payload,
	}
}

// NewPingFrame creates a ping frame
func NewPingFrame(payload string) *Frame {
	return &Frame{
		Fin:     true,
		Opcode:  OpcodePing,
		Payload: []byte(payload),
	}
}

// NewPongFrame creates a pong frame
func NewPongFrame(payload string) *Frame {
	return &Frame{
		Fin:     true,
		Opcode:  OpcodePong,
		Payload: []byte(payload),
	}
}
