package websocket

import (
	"bytes"
	"encoding/binary"
	"strings"
	"testing"
)

// TestOpcodeString tests the String method of Opcode.
func TestOpcodeString(t *testing.T) {
	tests := []struct {
		opcode Opcode
		want   string
	}{
		{OpcodeContinuation, "CONTINUATION"},
		{OpcodeText, "TEXT"},
		{OpcodeBinary, "BINARY"},
		{OpcodeClose, "CLOSE"},
		{OpcodePing, "PING"},
		{OpcodePong, "PONG"},
		{Opcode(0xFF), "UNKNOWN(255)"},
	}

	for _, tt := range tests {
		got := tt.opcode.String()
		if got != tt.want {
			t.Errorf("Opcode(%d).String() = %q, want %q", tt.opcode, got, tt.want)
		}
	}
}

// TestCloseStatusCodeString tests the String method of CloseStatusCode.
func TestCloseStatusCodeString(t *testing.T) {
	tests := []struct {
		code CloseStatusCode
		want string
	}{
		{CloseNormalClosure, "Normal Closure"},
		{CloseGoingAway, "Going Away"},
		{CloseProtocolError, "Protocol Error"},
		{CloseMessageTooBig, "Message Too Big"},
		{CloseTLSHandshake, "TLS Handshake Failed"},
		{CloseStatusCode(3000), "Close(3000)"},
	}

	for _, tt := range tests {
		got := tt.code.String()
		if got != tt.want {
			t.Errorf("CloseStatusCode(%d).String() = %q, want %q", tt.code, got, tt.want)
		}
	}
}

// TestFrameIsControl tests whether control frames are correctly identified.
func TestFrameIsControl(t *testing.T) {
	textFrame := &Frame{Opcode: OpcodeText}
	if textFrame.IsControl() {
		t.Error("text frame should not be a control frame")
	}

	closeFrame := &Frame{Opcode: OpcodeClose}
	if !closeFrame.IsControl() {
		t.Error("close frame should be a control frame")
	}

	pingFrame := &Frame{Opcode: OpcodePing}
	if !pingFrame.IsControl() {
		t.Error("ping frame should be a control frame")
	}

	pongFrame := &Frame{Opcode: OpcodePong}
	if !pongFrame.IsControl() {
		t.Error("pong frame should be a control frame")
	}
}

// TestFrameMessageType tests the MessageType method.
func TestFrameMessageType(t *testing.T) {
	finFrame := &Frame{FIN: true, Opcode: OpcodeText}
	if finFrame.MessageType() != "TEXT" {
		t.Errorf("fin text frame type = %q, want TEXT", finFrame.MessageType())
	}

	fragFrame := &Frame{FIN: false, Opcode: OpcodeText}
	if !strings.Contains(fragFrame.MessageType(), "fragmented") {
		t.Errorf("fragmented text frame type = %q, want fragmented", fragFrame.MessageType())
	}
}

// TestCloseFrameCreation tests CloseFrame creation.
func TestCloseFrameCreation(t *testing.T) {
	f := CloseFrame(CloseNormalClosure, "bye")
	if f.Opcode != OpcodeClose {
		t.Errorf("close frame opcode = %v, want OpcodeClose", f.Opcode)
	}
	if !f.FIN {
		t.Error("close frame should have FIN set")
	}
	if len(f.Payload) < 2 {
		t.Error("close frame payload should be at least 2 bytes")
	}
}

// TestPingFrameCreation tests PingFrame creation.
func TestPingFrameCreation(t *testing.T) {
	data := []byte("hello")
	f := PingFrame(data)
	if f.Opcode != OpcodePing {
		t.Errorf("ping frame opcode = %v, want OpcodePing", f.Opcode)
	}
	if !bytes.Equal(f.Payload, data) {
		t.Errorf("ping frame payload = %v, want %v", f.Payload, data)
	}
}

// TestPongFrameCreation tests PongFrame creation.
func TestPongFrameCreation(t *testing.T) {
	data := []byte("pong data")
	f := PongFrame(data)
	if f.Opcode != OpcodePong {
		t.Errorf("pong frame opcode = %v, want OpcodePong", f.Opcode)
	}
	if !bytes.Equal(f.Payload, data) {
		t.Errorf("pong frame payload = %v, want %v", f.Payload, data)
	}
}

// TestTextFrameCreation tests TextFrame creation.
func TestTextFrameCreation(t *testing.T) {
	data := []byte("hello world")
	f := TextFrame(data)
	if f.Opcode != OpcodeText {
		t.Errorf("text frame opcode = %v, want OpcodeText", f.Opcode)
	}
	if !bytes.Equal(f.Payload, data) {
		t.Errorf("text frame payload = %v, want %v", f.Payload, data)
	}
}

// TestBinaryFrameCreation tests BinaryFrame creation.
func TestBinaryFrameCreation(t *testing.T) {
	data := []byte{0x00, 0x01, 0x02, 0x03}
	f := BinaryFrame(data)
	if f.Opcode != OpcodeBinary {
		t.Errorf("binary frame opcode = %v, want OpcodeBinary", f.Opcode)
	}
	if !bytes.Equal(f.Payload, data) {
		t.Errorf("binary frame payload = %v, want %v", f.Payload, data)
	}
}

// TestFrameMarshalUnmarshal tests frame serialization and deserialization.
func TestFrameMarshalUnmarshal(t *testing.T) {
	tests := []struct {
		name  string
		frame *Frame
	}{
		{"text frame", TextFrame([]byte("hello"))},
		{"binary frame", BinaryFrame([]byte{0x00, 0x01, 0x02})},
		{"close frame", CloseFrame(CloseNormalClosure, "goodbye")},
		{"ping frame", PingFrame([]byte("ping data"))},
		{"empty frame", TextFrame([]byte{})},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			data, err := tt.frame.Marshal()
			if err != nil {
				t.Fatalf("marshal error: %v", err)
			}

			reader := bytes.NewReader(data)
			parsed, err := ParseFrame(reader)
			if err != nil {
				t.Fatalf("parse error: %v", err)
			}

			if parsed.FIN != tt.frame.FIN {
				t.Errorf("FIN = %v, want %v", parsed.FIN, tt.frame.FIN)
			}
			if parsed.Opcode != tt.frame.Opcode {
				t.Errorf("Opcode = %v, want %v", parsed.Opcode, tt.frame.Opcode)
			}
			if !bytes.Equal(parsed.Payload, tt.frame.Payload) {
				t.Errorf("Payload = %v, want %v", parsed.Payload, tt.frame.Payload)
			}
		})
	}
}

// TestFrameMarshalLargePayload tests marshaling with extended payload lengths.
func TestFrameMarshalLargePayload(t *testing.T) {
	// Test 126-byte payload (uses 2-byte extended length)
	data126 := make([]byte, 126)
	for i := range data126 {
		data126[i] = byte(i)
	}
	f126 := TextFrame(data126)
	out126, err := f126.Marshal()
	if err != nil {
		t.Fatalf("marshal 126-byte payload: %v", err)
	}
	reader126 := bytes.NewReader(out126)
	parsed126, err := ParseFrame(reader126)
	if err != nil {
		t.Fatalf("parse 126-byte payload: %v", err)
	}
	if len(parsed126.Payload) != 126 {
		t.Errorf("parsed payload length = %d, want 126", len(parsed126.Payload))
	}

	// Test 65535-byte payload (uses 2-byte extended length)
	data64k := make([]byte, 65535)
	for i := range data64k {
		data64k[i] = byte(i % 256)
	}
	f64k := TextFrame(data64k)
	out64k, err := f64k.Marshal()
	if err != nil {
		t.Fatalf("marshal 64KB payload: %v", err)
	}
	reader64k := bytes.NewReader(out64k)
	parsed64k, err := ParseFrame(reader64k)
	if err != nil {
		t.Fatalf("parse 64KB payload: %v", err)
	}
	if len(parsed64k.Payload) != 65535 {
		t.Errorf("parsed payload length = %d, want 65535", len(parsed64k.Payload))
	}
}

// TestMaskedFrame tests client-masked frame parsing.
func TestMaskedFrame(t *testing.T) {
	// Create a masked frame manually
	maskingKey := [4]byte{0x37, 0xFA, 0x2B, 0x5C}
	payload := []byte("hello")

	// Build masked payload
	masked := make([]byte, len(payload))
	for i := range payload {
		masked[i] = payload[i] ^ maskingKey[i%4]
	}

	// Build frame bytes: FIN=1, Opcode=TEXT, MASK=1
	buf := make([]byte, 0, 2+len(masked))
	buf = append(buf, 0x81)            // FIN + TEXT
	buf = append(buf, 0x80|byte(len(masked))) // MASK + length
	buf = append(buf, maskingKey[:]...)
	buf = append(buf, masked...)

	reader := bytes.NewReader(buf)
	f, err := ParseFrame(reader)
	if err != nil {
		t.Fatalf("parse masked frame: %v", err)
	}

	if !f.Masked {
		t.Error("frame should be marked as masked")
	}
	if !bytes.Equal(f.Payload, payload) {
		t.Errorf("unmasked payload = %v, want %v", f.Payload, payload)
	}
}

// TestCloseMessage tests CloseMessage extraction.
func TestCloseMessage(t *testing.T) {
	payload := make([]byte, 2+len("goodbye"))
	binary.BigEndian.PutUint16(payload, 1000)
	copy(payload[2:], "goodbye")

	code, reason := CloseMessage(payload)
	if code != CloseNormalClosure {
		t.Errorf("code = %d, want %d", code, CloseNormalClosure)
	}
	if reason != "goodbye" {
		t.Errorf("reason = %q, want %q", reason, "goodbye")
	}
}

// TestCloseMessageShortPayload tests CloseMessage with short payload.
func TestCloseMessageShortPayload(t *testing.T) {
	payload := []byte{0x01}
	code, reason := CloseMessage(payload)
	if code != CloseNoStatusReceived {
		t.Errorf("code = %d, want %d", code, CloseNoStatusReceived)
	}
	if reason != "" {
		t.Errorf("reason = %q, want empty", reason)
	}
}

// TestErrCloseSent tests ErrCloseSent error.
func TestErrCloseSent(t *testing.T) {
	if ErrCloseSent.Error() != "close frame already sent" {
		t.Error("ErrCloseSent message mismatch")
	}
}

// TestErrMessageTooBig tests ErrMessageTooBig error.
func TestErrMessageTooBig(t *testing.T) {
	if ErrMessageTooBig.Error() != "message too big" {
		t.Error("ErrMessageTooBig message mismatch")
	}
}

// TestMultipleFrames tests parsing multiple consecutive frames.
func TestMultipleFrames(t *testing.T) {
	f1 := TextFrame([]byte("first"))
	f2 := TextFrame([]byte("second"))
	f3 := CloseFrame(CloseNormalClosure, "")

	out1, _ := f1.Marshal()
	out2, _ := f2.Marshal()
	out3, _ := f3.Marshal()

	combined := append(out1, out2...)
	combined = append(combined, out3...)

	reader := bytes.NewReader(combined)

	for i, expected := range []*Frame{f1, f2, f3} {
		parsed, err := ParseFrame(reader)
		if err != nil {
			t.Fatalf("frame %d parse error: %v", i, err)
		}
		if parsed.Opcode != expected.Opcode {
			t.Errorf("frame %d opcode = %v, want %v", i, parsed.Opcode, expected.Opcode)
		}
	}
}

// TestFrameMarshalZeroPayload tests marshaling a frame with zero payload.
func TestFrameMarshalZeroPayload(t *testing.T) {
	f := PingFrame(nil)
	data, err := f.Marshal()
	if err != nil {
		t.Fatalf("marshal zero payload: %v", err)
	}

	reader := bytes.NewReader(data)
	parsed, err := ParseFrame(reader)
	if err != nil {
		t.Fatalf("parse zero payload: %v", err)
	}
	if len(parsed.Payload) != 0 {
		t.Errorf("payload length = %d, want 0", len(parsed.Payload))
	}
}
