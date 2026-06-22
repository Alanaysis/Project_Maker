package frame

import (
	"bytes"
	"testing"
)

func TestFrameReadWrite(t *testing.T) {
	// Create a test frame
	payload := []byte("Hello, HTTP/2!")
	frame := NewFrame(FrameData, FlagEndStream, 1, payload)

	// Write frame to buffer
	var buf bytes.Buffer
	if err := WriteFrame(&buf, frame); err != nil {
		t.Fatalf("WriteFrame failed: %v", err)
	}

	// Read frame back
	readFrame, err := ReadFrame(&buf)
	if err != nil {
		t.Fatalf("ReadFrame failed: %v", err)
	}

	// Verify frame fields
	if readFrame.Type != FrameData {
		t.Errorf("Expected type %d, got %d", FrameData, readFrame.Type)
	}
	if readFrame.Flags != FlagEndStream {
		t.Errorf("Expected flags %d, got %d", FlagEndStream, readFrame.Flags)
	}
	if readFrame.StreamID != 1 {
		t.Errorf("Expected stream ID 1, got %d", readFrame.StreamID)
	}
	if !bytes.Equal(readFrame.Payload, payload) {
		t.Errorf("Payload mismatch: expected %q, got %q", payload, readFrame.Payload)
	}
}

func TestFrameLargePayload(t *testing.T) {
	// Test with maximum frame size
	payload := make([]byte, MaxFrameSize)
	for i := range payload {
		payload[i] = byte(i % 256)
	}

	frame := NewFrame(FrameData, 0, 1, payload)

	var buf bytes.Buffer
	if err := WriteFrame(&buf, frame); err != nil {
		t.Fatalf("WriteFrame failed: %v", err)
	}

	readFrame, err := ReadFrame(&buf)
	if err != nil {
		t.Fatalf("ReadFrame failed: %v", err)
	}

	if !bytes.Equal(readFrame.Payload, payload) {
		t.Error("Large payload mismatch")
	}
}

func TestFrameStreamIDMasking(t *testing.T) {
	// Stream ID should be masked to 31 bits
	frame := NewFrame(FrameHeaders, 0, 0x80000001, nil)
	if frame.StreamID != 1 {
		t.Errorf("Expected stream ID 1, got %d", frame.StreamID)
	}
}

func TestSettingsFrame(t *testing.T) {
	settings := DefaultSettings()
	settings.MaxConcurrentStreams = 50
	settings.InitialWindowSize = 131070

	payload := EncodeSettings(settings)
	parsed, err := ParseSettingsFrame(payload)
	if err != nil {
		t.Fatalf("ParseSettingsFrame failed: %v", err)
	}

	if parsed.MaxConcurrentStreams != 50 {
		t.Errorf("Expected MaxConcurrentStreams 50, got %d", parsed.MaxConcurrentStreams)
	}
	if parsed.InitialWindowSize != 131070 {
		t.Errorf("Expected InitialWindowSize 131070, got %d", parsed.InitialWindowSize)
	}
}

func TestHPACK(t *testing.T) {
	encoder := NewHPACKEncoder(4096)
	decoder := NewHPACKDecoder(4096)

	headers := []HeaderField{
		{Name: ":method", Value: "GET"},
		{Name: ":path", Value: "/test"},
		{Name: ":scheme", Value: "https"},
		{Name: "host", Value: "example.com"},
		{Name: "accept", Value: "text/html"},
	}

	// Encode headers
	encoded, err := encoder.EncodeHeaders(headers)
	if err != nil {
		t.Fatalf("EncodeHeaders failed: %v", err)
	}

	// Decode headers
	decoded, err := decoder.DecodeHeaders(encoded)
	if err != nil {
		t.Fatalf("DecodeHeaders failed: %v", err)
	}

	// Verify decoded headers match original
	if len(decoded) != len(headers) {
		t.Fatalf("Expected %d headers, got %d", len(headers), len(decoded))
	}

	for i, h := range decoded {
		if h.Name != headers[i].Name || h.Value != headers[i].Value {
			t.Errorf("Header %d mismatch: expected %s: %s, got %s: %s",
				i, headers[i].Name, headers[i].Value, h.Name, h.Value)
		}
	}
}

func TestHPACKStaticTable(t *testing.T) {
	// Test encoding with static table entries
	encoder := NewHPACKEncoder(4096)
	decoder := NewHPACKDecoder(4096)

	// These should be in static table
	headers := []HeaderField{
		{Name: ":method", Value: "GET"},
		{Name: ":path", Value: "/"},
		{Name: ":scheme", Value: "http"},
		{Name: ":status", Value: "200"},
	}

	encoded, err := encoder.EncodeHeaders(headers)
	if err != nil {
		t.Fatalf("EncodeHeaders failed: %v", err)
	}

	decoded, err := decoder.DecodeHeaders(encoded)
	if err != nil {
		t.Fatalf("DecodeHeaders failed: %v", err)
	}

	if len(decoded) != len(headers) {
		t.Fatalf("Expected %d headers, got %d", len(headers), len(decoded))
	}
}

func TestHPACKDynamicTable(t *testing.T) {
	encoder := NewHPACKEncoder(256) // Small table size
	decoder := NewHPACKDecoder(256)

	// First request
	headers1 := []HeaderField{
		{Name: "custom-header", Value: "value1"},
	}
	encoded1, err := encoder.EncodeHeaders(headers1)
	if err != nil {
		t.Fatalf("First encode failed: %v", err)
	}
	_, err = decoder.DecodeHeaders(encoded1)
	if err != nil {
		t.Fatalf("First decode failed: %v", err)
	}

	// Second request with same header - should be more efficient
	headers2 := []HeaderField{
		{Name: "custom-header", Value: "value1"},
	}
	encoded2, err := encoder.EncodeHeaders(headers2)
	if err != nil {
		t.Fatalf("Second encode failed: %v", err)
	}
	decoded2, err := decoder.DecodeHeaders(encoded2)
	if err != nil {
		t.Fatalf("Second decode failed: %v", err)
	}

	if decoded2[0].Name != "custom-header" || decoded2[0].Value != "value1" {
		t.Errorf("Dynamic table decode failed: got %v", decoded2[0])
	}
}
