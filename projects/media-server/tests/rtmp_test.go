package tests

import (
	"testing"

	"github.com/media-server/internal/rtmp"
)

func TestHandshake(t *testing.T) {
	h := rtmp.NewHandshake()

	if h.GetState() != rtmp.HandshakeStateInit {
		t.Errorf("Expected initial state, got %v", h.GetState())
	}

	// Generate C0+C1
	c0c1 := rtmp.GenerateC0C1()
	if len(c0c1) != 1+1536 {
		t.Errorf("Expected C0+C1 length 1537, got %d", len(c0c1))
	}

	// Check C0 version
	if c0c1[0] != 3 {
		t.Errorf("Expected C0 version 3, got %d", c0c1[0])
	}

	// Process C0+C1
	s0, s1, s2, err := h.ProcessC0C1(c0c1)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	// Check S0
	if len(s0) != 1 || s0[0] != 3 {
		t.Errorf("Expected S0 version 3")
	}

	// Check S1
	if len(s1) != 1536 {
		t.Errorf("Expected S1 length 1536, got %d", len(s1))
	}

	// Check S2
	if len(s2) != 1536 {
		t.Errorf("Expected S2 length 1536, got %d", len(s2))
	}

	// Process C2
	c2 := rtmp.GenerateC2(s1)
	err = h.ProcessC2(c2)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	if !h.IsDone() {
		t.Error("Expected handshake to be done")
	}
}

func TestAMFEncoding(t *testing.T) {
	// Test string encoding
	encoder := rtmp.NewAMFEncoder()
	err := encoder.Encode("test")
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	// Test number encoding
	encoder = rtmp.NewAMFEncoder()
	err = encoder.Encode(42.0)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	// Test boolean encoding
	encoder = rtmp.NewAMFEncoder()
	err = encoder.Encode(true)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	// Test null encoding
	encoder = rtmp.NewAMFEncoder()
	err = encoder.Encode(nil)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
}

func TestAMFObjectEncoding(t *testing.T) {
	encoder := rtmp.NewAMFEncoder()

	obj := rtmp.AMFObject{
		"key1": "value1",
		"key2": 42.0,
		"key3": true,
	}

	err := encoder.Encode(obj)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	data := encoder.Bytes()
	if len(data) == 0 {
		t.Error("Expected non-empty encoded data")
	}
}

func TestAMFDecoding(t *testing.T) {
	// Encode and decode a string
	encoder := rtmp.NewAMFEncoder()
	encoder.Encode("hello")

	decoder := rtmp.NewAMFDecoder(encoder.Bytes())
	val, err := decoder.Decode()
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	if str, ok := val.(string); !ok || str != "hello" {
		t.Errorf("Expected 'hello', got '%v'", val)
	}
}

func TestAMFCommandEncoding(t *testing.T) {
	data, err := rtmp.EncodeCommand("connect", float64(1), nil, rtmp.AMFObject{
		"app": "live",
	})
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	name, args, err := rtmp.DecodeCommand(data)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	if name != "connect" {
		t.Errorf("Expected command 'connect', got '%s'", name)
	}

	if len(args) != 3 {
		t.Errorf("Expected 3 arguments, got %d", len(args))
	}
}

func TestMessageEncoding(t *testing.T) {
	encoder := rtmp.NewMessageEncoder()

	msg := &rtmp.RTMPMessage{
		ChunkStreamID: 3,
		Timestamp:     1000,
		TypeID:        rtmp.MsgVideo,
		StreamID:      1,
		Payload:       []byte{0x17, 0x01, 0x00, 0x00, 0x00},
	}

	data, err := encoder.Encode(msg)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	if len(data) == 0 {
		t.Error("Expected non-empty encoded data")
	}
}

func TestChunkSizeEncoding(t *testing.T) {
	data := rtmp.EncodeChunkSize(4096)

	size, err := rtmp.DecodeChunkSize(data)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}

	if size != 4096 {
		t.Errorf("Expected chunk size 4096, got %d", size)
	}
}

func TestWindowAckSizeEncoding(t *testing.T) {
	data := rtmp.EncodeWindowAckSize(2500000)

	if len(data) != 4 {
		t.Errorf("Expected 4 bytes, got %d", len(data))
	}
}

func TestSetPeerBandwidthEncoding(t *testing.T) {
	data := rtmp.EncodeSetPeerBandwidth(2500000, rtmp.BandwidthLimitDynamic)

	if len(data) != 5 {
		t.Errorf("Expected 5 bytes, got %d", len(data))
	}

	if data[4] != rtmp.BandwidthLimitDynamic {
		t.Errorf("Expected limit type %d, got %d", rtmp.BandwidthLimitDynamic, data[4])
	}
}
