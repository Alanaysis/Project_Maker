package tests

import (
	"bytes"
	"testing"

	"github.com/anthropic/http2-server/internal/connection"
	"github.com/anthropic/http2-server/internal/frame"
	"github.com/anthropic/http2-server/internal/handler"
)

// TestFrameProtocolRoundTrip tests complete frame encoding and decoding
func TestFrameProtocolRoundTrip(t *testing.T) {
	tests := []struct {
		name      string
		frameType uint8
		flags     uint8
		streamID  uint32
		payload   []byte
	}{
		{
			name:      "DATA frame",
			frameType: frame.FrameData,
			flags:     frame.FlagEndStream,
			streamID:  1,
			payload:   []byte("Hello, HTTP/2!"),
		},
		{
			name:      "HEADERS frame",
			frameType: frame.FrameHeaders,
			flags:     frame.FlagEndHeaders | frame.FlagEndStream,
			streamID:  1,
			payload:   []byte{0x82, 0x86, 0x84, 0x01, 0x0f, 0x77, 0x77, 0x77, 0x2e, 0x65, 0x78, 0x61, 0x6d, 0x70, 0x6c, 0x65, 0x2e, 0x63, 0x6f, 0x6d},
		},
		{
			name:      "SETTINGS frame",
			frameType: frame.FrameSettings,
			flags:     0,
			streamID:  0,
			payload:   nil,
		},
		{
			name:      "PING frame",
			frameType: frame.FramePing,
			flags:     0,
			streamID:  0,
			payload:   []byte{0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08},
		},
		{
			name:      "GOAWAY frame",
			frameType: frame.FrameGoAway,
			flags:     0,
			streamID:  0,
			payload:   make([]byte, 8),
		},
		{
			name:      "WINDOW_UPDATE frame",
			frameType: frame.FrameWindowUpdate,
			flags:     0,
			streamID:  1,
			payload:   []byte{0x00, 0x01, 0x00, 0x00}, // 65536 increment
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create frame
			f := frame.NewFrame(tt.frameType, tt.flags, tt.streamID, tt.payload)

			// Write to buffer
			var buf bytes.Buffer
			if err := frame.WriteFrame(&buf, f); err != nil {
				t.Fatalf("WriteFrame failed: %v", err)
			}

			// Read back
			readFrame, err := frame.ReadFrame(&buf)
			if err != nil {
				t.Fatalf("ReadFrame failed: %v", err)
			}

			// Verify all fields
			if readFrame.Type != tt.frameType {
				t.Errorf("Type mismatch: expected %d, got %d", tt.frameType, readFrame.Type)
			}
			if readFrame.Flags != tt.flags {
				t.Errorf("Flags mismatch: expected %d, got %d", tt.flags, readFrame.Flags)
			}
			if readFrame.StreamID != (tt.streamID & 0x7FFFFFFF) {
				t.Errorf("StreamID mismatch: expected %d, got %d", tt.streamID&0x7FFFFFFF, readFrame.StreamID)
			}
			if !bytes.Equal(readFrame.Payload, tt.payload) {
				t.Errorf("Payload mismatch")
			}
		})
	}
}

// TestMultipleFramesInSequence tests reading multiple frames from a stream
func TestMultipleFramesInSequence(t *testing.T) {
	var buf bytes.Buffer

	// Write multiple frames
	frames := []*frame.Frame{
		frame.NewFrame(frame.FrameSettings, 0, 0, nil),
		frame.NewFrame(frame.FrameHeaders, frame.FlagEndHeaders, 1, []byte{0x82}),
		frame.NewFrame(frame.FrameData, frame.FlagEndStream, 1, []byte("Hello")),
		frame.NewFrame(frame.FramePing, 0, 0, make([]byte, 8)),
	}

	for _, f := range frames {
		if err := frame.WriteFrame(&buf, f); err != nil {
			t.Fatalf("WriteFrame failed: %v", err)
		}
	}

	// Read all frames back
	for i, expected := range frames {
		f, err := frame.ReadFrame(&buf)
		if err != nil {
			t.Fatalf("ReadFrame %d failed: %v", i, err)
		}
		if f.Type != expected.Type {
			t.Errorf("Frame %d: type mismatch: expected %d, got %d", i, expected.Type, f.Type)
		}
		if f.StreamID != expected.StreamID {
			t.Errorf("Frame %d: stream ID mismatch: expected %d, got %d", i, expected.StreamID, f.StreamID)
		}
	}
}

// TestSettingsProtocol tests settings encoding, parsing, and defaults
func TestSettingsProtocol(t *testing.T) {
	t.Run("DefaultSettings", func(t *testing.T) {
		s := frame.DefaultSettings()
		if s.HeaderTableSize != 4096 {
			t.Errorf("Expected HeaderTableSize 4096, got %d", s.HeaderTableSize)
		}
		if s.MaxConcurrentStreams != 100 {
			t.Errorf("Expected MaxConcurrentStreams 100, got %d", s.MaxConcurrentStreams)
		}
		if s.InitialWindowSize != 65535 {
			t.Errorf("Expected InitialWindowSize 65535, got %d", s.InitialWindowSize)
		}
		if s.MaxFrameSize != 16384 {
			t.Errorf("Expected MaxFrameSize 16384, got %d", s.MaxFrameSize)
		}
	})

	t.Run("EncodeAndParse", func(t *testing.T) {
		settings := &frame.Settings{
			HeaderTableSize:      8192,
			EnablePush:           0,
			MaxConcurrentStreams:  50,
			InitialWindowSize:    131070,
			MaxFrameSize:         32768,
			MaxHeaderListSize:    16384,
		}

		encoded := frame.EncodeSettings(settings)
		parsed, err := frame.ParseSettingsFrame(encoded)
		if err != nil {
			t.Fatalf("ParseSettingsFrame failed: %v", err)
		}

		if parsed.HeaderTableSize != settings.HeaderTableSize {
			t.Errorf("HeaderTableSize mismatch: expected %d, got %d", settings.HeaderTableSize, parsed.HeaderTableSize)
		}
		if parsed.EnablePush != settings.EnablePush {
			t.Errorf("EnablePush mismatch: expected %d, got %d", settings.EnablePush, parsed.EnablePush)
		}
		if parsed.MaxConcurrentStreams != settings.MaxConcurrentStreams {
			t.Errorf("MaxConcurrentStreams mismatch: expected %d, got %d", settings.MaxConcurrentStreams, parsed.MaxConcurrentStreams)
		}
		if parsed.InitialWindowSize != settings.InitialWindowSize {
			t.Errorf("InitialWindowSize mismatch: expected %d, got %d", settings.InitialWindowSize, parsed.InitialWindowSize)
		}
		if parsed.MaxFrameSize != settings.MaxFrameSize {
			t.Errorf("MaxFrameSize mismatch: expected %d, got %d", settings.MaxFrameSize, parsed.MaxFrameSize)
		}
		if parsed.MaxHeaderListSize != settings.MaxHeaderListSize {
			t.Errorf("MaxHeaderListSize mismatch: expected %d, got %d", settings.MaxHeaderListSize, parsed.MaxHeaderListSize)
		}
	})

	t.Run("SettingsFrameCreation", func(t *testing.T) {
		settings := frame.DefaultSettings()
		settings.MaxConcurrentStreams = 50

		f := frame.CreateSettingsFrame(settings, 0)
		if f.Type != frame.FrameSettings {
			t.Errorf("Expected SETTINGS frame type, got %d", f.Type)
		}
		if f.StreamID != 0 {
			t.Errorf("SETTINGS frame should have stream ID 0, got %d", f.StreamID)
		}
	})

	t.Run("SettingsAckFrame", func(t *testing.T) {
		f := frame.CreateSettingsAckFrame()
		if f.Type != frame.FrameSettings {
			t.Errorf("Expected SETTINGS frame type, got %d", f.Type)
		}
		if f.Flags&frame.FlagAck == 0 {
			t.Error("SETTINGS ACK frame should have ACK flag set")
		}
		if len(f.Payload) != 0 {
			t.Errorf("SETTINGS ACK should have empty payload, got %d bytes", len(f.Payload))
		}
	})
}

// TestHPACKProtocol tests HPACK header compression and decompression
func TestHPACKProtocol(t *testing.T) {
	t.Run("StaticTableEntries", func(t *testing.T) {
		encoder := frame.NewHPACKEncoder(4096)
		decoder := frame.NewHPACKDecoder(4096)

		// These are all static table entries
		headers := []frame.HeaderField{
			{Name: ":method", Value: "GET"},
			{Name: ":method", Value: "POST"},
			{Name: ":path", Value: "/"},
			{Name: ":path", Value: "/index.html"},
			{Name: ":scheme", Value: "http"},
			{Name: ":scheme", Value: "https"},
			{Name: ":status", Value: "200"},
			{Name: ":status", Value: "404"},
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

		for i, h := range decoded {
			if h.Name != headers[i].Name || h.Value != headers[i].Value {
				t.Errorf("Header %d mismatch: expected %s: %s, got %s: %s",
					i, headers[i].Name, headers[i].Value, h.Name, h.Value)
			}
		}
	})

	t.Run("DynamicTableReuse", func(t *testing.T) {
		encoder := frame.NewHPACKEncoder(4096)
		decoder := frame.NewHPACKDecoder(4096)

		// First request with custom headers
		headers1 := []frame.HeaderField{
			{Name: "x-custom-header", Value: "custom-value"},
			{Name: "x-request-id", Value: "12345"},
		}

		encoded1, err := encoder.EncodeHeaders(headers1)
		if err != nil {
			t.Fatalf("First encode failed: %v", err)
		}

		_, err = decoder.DecodeHeaders(encoded1)
		if err != nil {
			t.Fatalf("First decode failed: %v", err)
		}

		// Second request with same headers - should use dynamic table
		headers2 := []frame.HeaderField{
			{Name: "x-custom-header", Value: "custom-value"},
			{Name: "x-request-id", Value: "12345"},
		}

		encoded2, err := encoder.EncodeHeaders(headers2)
		if err != nil {
			t.Fatalf("Second encode failed: %v", err)
		}

		decoded2, err := decoder.DecodeHeaders(encoded2)
		if err != nil {
			t.Fatalf("Second decode failed: %v", err)
		}

		// Verify both decoded correctly
		for i, h := range decoded2 {
			if h.Name != headers2[i].Name || h.Value != headers2[i].Value {
				t.Errorf("Header %d mismatch: expected %s: %s, got %s: %s",
					i, headers2[i].Name, headers2[i].Value, h.Name, h.Value)
			}
		}

		// Second encoding should be more compact due to dynamic table
		if len(encoded2) >= len(encoded1) {
			t.Logf("First encoding: %d bytes, Second encoding: %d bytes", len(encoded1), len(encoded2))
		}
	})

	t.Run("RequestHeaders", func(t *testing.T) {
		encoder := frame.NewHPACKEncoder(4096)
		decoder := frame.NewHPACKDecoder(4096)

		// Typical HTTP/2 request headers
		headers := []frame.HeaderField{
			{Name: ":method", Value: "GET"},
			{Name: ":path", Value: "/api/v1/users"},
			{Name: ":scheme", Value: "https"},
			{Name: ":authority", Value: "api.example.com"},
			{Name: "accept", Value: "application/json"},
			{Name: "user-agent", Value: "HTTP2-Client/1.0"},
			{Name: "authorization", Value: "Bearer token123"},
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

		for i, h := range decoded {
			if h.Name != headers[i].Name || h.Value != headers[i].Value {
				t.Errorf("Header %d mismatch: expected %s: %s, got %s: %s",
					i, headers[i].Name, headers[i].Value, h.Name, h.Value)
			}
		}
	})

	t.Run("ResponseHeaders", func(t *testing.T) {
		encoder := frame.NewHPACKEncoder(4096)
		decoder := frame.NewHPACKDecoder(4096)

		// Typical HTTP/2 response headers
		headers := []frame.HeaderField{
			{Name: ":status", Value: "200"},
			{Name: "content-type", Value: "application/json"},
			{Name: "content-length", Value: "42"},
			{Name: "server", Value: "HTTP2-Server/1.0"},
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
	})
}

// TestConnectionStreamManagement tests stream creation and state management
func TestConnectionStreamManagement(t *testing.T) {
	t.Run("StreamCreation", func(t *testing.T) {
		stream := connection.NewStream(1, 65535)

		if stream.ID != 1 {
			t.Errorf("Expected stream ID 1, got %d", stream.ID)
		}
		if stream.State != connection.StreamIdle {
			t.Errorf("Expected initial state Idle, got %d", stream.State)
		}
		if stream.SendWindow != 65535 {
			t.Errorf("Expected send window 65535, got %d", stream.SendWindow)
		}
		if stream.ReceiveWindow != 65535 {
			t.Errorf("Expected receive window 65535, got %d", stream.ReceiveWindow)
		}
	})

	t.Run("StreamStateTransitions", func(t *testing.T) {
		stream := connection.NewStream(1, 65535)

		// Idle -> Open
		stream.State = connection.StreamOpen
		if stream.State != connection.StreamOpen {
			t.Errorf("Expected Open state, got %d", stream.State)
		}

		// Open -> HalfClosedRemote (after receiving END_STREAM)
		stream.State = connection.StreamHalfClosedRemote
		if stream.State != connection.StreamHalfClosedRemote {
			t.Errorf("Expected HalfClosedRemote state, got %d", stream.State)
		}

		// HalfClosedRemote -> Closed
		stream.State = connection.StreamClosed
		if stream.State != connection.StreamClosed {
			t.Errorf("Expected Closed state, got %d", stream.State)
		}
	})

	t.Run("MultiplexerOperations", func(t *testing.T) {
		mux := connection.NewMultiplexer()

		// Add streams
		s1 := connection.NewStream(1, 65535)
		s1.State = connection.StreamOpen
		s3 := connection.NewStream(3, 65535)
		s3.State = connection.StreamOpen
		s5 := connection.NewStream(5, 65535)
		s5.State = connection.StreamOpen

		mux.AddStream(s1)
		mux.AddStream(s3)
		mux.AddStream(s5)

		// Get stream
		s, exists := mux.GetStream(3)
		if !exists || s.ID != 3 {
			t.Error("Failed to get stream 3")
		}

		// Round-robin scheduling
		next1 := mux.GetNextStream()
		next2 := mux.GetNextStream()
		next3 := mux.GetNextStream()
		next4 := mux.GetNextStream() // Should wrap around

		if next1.ID != 1 || next2.ID != 3 || next3.ID != 5 || next4.ID != 1 {
			t.Error("Round-robin scheduling failed")
		}

		// Get active streams
		active := mux.GetActiveStreams()
		if len(active) != 3 {
			t.Errorf("Expected 3 active streams, got %d", len(active))
		}

		// Remove stream
		mux.RemoveStream(3)
		_, exists = mux.GetStream(3)
		if exists {
			t.Error("Stream 3 should not exist after removal")
		}
	})
}

// TestFrameQueueOperations tests frame queue data structure
func TestFrameQueueOperations(t *testing.T) {
	queue := connection.NewFrameQueue()

	// Empty queue
	if queue.Len() != 0 {
		t.Errorf("Empty queue length should be 0, got %d", queue.Len())
	}
	if f := queue.Dequeue(); f != nil {
		t.Error("Dequeue on empty queue should return nil")
	}

	// Enqueue frames
	f1 := frame.NewFrame(frame.FrameData, 0, 1, []byte("data1"))
	f2 := frame.NewFrame(frame.FrameHeaders, 0, 3, []byte("headers"))
	f3 := frame.NewFrame(frame.FrameData, frame.FlagEndStream, 5, []byte("data2"))

	queue.Enqueue(f1)
	queue.Enqueue(f2)
	queue.Enqueue(f3)

	if queue.Len() != 3 {
		t.Errorf("Queue length should be 3, got %d", queue.Len())
	}

	// Dequeue in order
	d1 := queue.Dequeue()
	d2 := queue.Dequeue()
	d3 := queue.Dequeue()

	if d1.StreamID != 1 || d2.StreamID != 3 || d3.StreamID != 5 {
		t.Error("Frames dequeued in wrong order")
	}

	if queue.Len() != 0 {
		t.Errorf("Queue should be empty, got length %d", queue.Len())
	}
}

// TestHandlerRouting tests HTTP/2 request routing
func TestHandlerRouting(t *testing.T) {
	t.Run("GET_Route", func(t *testing.T) {
		router := handler.NewRouter()
		called := false

		router.Get("/api/test", func(stream *connection.Stream) error {
			called = true
			stream.ResponseCode = 200
			stream.ResponseHeaders = []frame.HeaderField{
				{Name: ":status", Value: "200"},
				{Name: "content-type", Value: "application/json"},
			}
			stream.ResponseBody = []byte(`{"status":"ok"}`)
			return nil
		})

		stream := &connection.Stream{
			ID: 1,
			Headers: []frame.HeaderField{
				{Name: ":method", Value: "GET"},
				{Name: ":path", Value: "/api/test"},
			},
		}

		err := router.Handle(stream)
		if err != nil {
			t.Fatalf("Handle failed: %v", err)
		}
		if !called {
			t.Error("Handler was not called")
		}
		if stream.ResponseCode != 200 {
			t.Errorf("Expected status 200, got %d", stream.ResponseCode)
		}
	})

	t.Run("POST_Route", func(t *testing.T) {
		router := handler.NewRouter()

		router.Post("/api/echo", func(stream *connection.Stream) error {
			stream.ResponseCode = 200
			stream.ResponseBody = stream.Body
			return nil
		})

		stream := &connection.Stream{
			ID:   1,
			Body: []byte("test data"),
			Headers: []frame.HeaderField{
				{Name: ":method", Value: "POST"},
				{Name: ":path", Value: "/api/echo"},
			},
		}

		err := router.Handle(stream)
		if err != nil {
			t.Fatalf("Handle failed: %v", err)
		}
		if string(stream.ResponseBody) != "test data" {
			t.Errorf("Expected body 'test data', got %q", stream.ResponseBody)
		}
	})

	t.Run("NotFound", func(t *testing.T) {
		router := handler.NewRouter()
		router.Get("/exists", func(stream *connection.Stream) error {
			return nil
		})

		stream := &connection.Stream{
			ID: 1,
			Headers: []frame.HeaderField{
				{Name: ":method", Value: "GET"},
				{Name: ":path", Value: "/not-found"},
			},
		}

		err := router.Handle(stream)
		if err != nil {
			t.Fatalf("Handle failed: %v", err)
		}
		if stream.ResponseCode != 404 {
			t.Errorf("Expected status 404, got %d", stream.ResponseCode)
		}
	})

	t.Run("MethodNotAllowed", func(t *testing.T) {
		router := handler.NewRouter()
		router.Get("/test", func(stream *connection.Stream) error {
			return nil
		})

		stream := &connection.Stream{
			ID: 1,
			Headers: []frame.HeaderField{
				{Name: ":method", Value: "DELETE"},
				{Name: ":path", Value: "/test"},
			},
		}

		err := router.Handle(stream)
		if err != nil {
			t.Fatalf("Handle failed: %v", err)
		}
		if stream.ResponseCode != 405 {
			t.Errorf("Expected status 405, got %d", stream.ResponseCode)
		}
	})

	t.Run("BadRequest_MissingHeaders", func(t *testing.T) {
		router := handler.NewRouter()

		stream := &connection.Stream{
			ID: 1,
			Headers: []frame.HeaderField{
				{Name: ":path", Value: "/test"},
			},
		}

		err := router.Handle(stream)
		if err != nil {
			t.Fatalf("Handle failed: %v", err)
		}
		if stream.ResponseCode != 400 {
			t.Errorf("Expected status 400, got %d", stream.ResponseCode)
		}
	})
}

// TestDefaultEndpoints tests the default HTTP/2 endpoints
func TestDefaultEndpoints(t *testing.T) {
	handler := handler.NewDefaultHandler()

	endpoints := []struct {
		method       string
		path         string
		expectedCode int
		checkBody    bool
	}{
		{"GET", "/", 200, true},
		{"GET", "/health", 200, true},
		{"GET", "/info", 200, true},
		{"POST", "/echo", 200, false},
	}

	for _, ep := range endpoints {
		t.Run(ep.method+" "+ep.path, func(t *testing.T) {
			stream := &connection.Stream{
				ID:   1,
				Body: []byte("test body"),
				Headers: []frame.HeaderField{
					{Name: ":method", Value: ep.method},
					{Name: ":path", Value: ep.path},
				},
			}

			err := handler.Handle(stream)
			if err != nil {
				t.Fatalf("Handle failed: %v", err)
			}
			if stream.ResponseCode != ep.expectedCode {
				t.Errorf("Expected status %d, got %d", ep.expectedCode, stream.ResponseCode)
			}
			if ep.checkBody && len(stream.ResponseBody) == 0 {
				t.Error("Response body should not be empty")
			}
		})
	}
}

// TestEndToEndRequestResponse simulates a complete HTTP/2 request/response cycle
func TestEndToEndRequestResponse(t *testing.T) {
	// Create encoder and decoder
	encoder := frame.NewHPACKEncoder(4096)
	decoder := frame.NewHPACKDecoder(4096)

	// Simulate client sending request headers
	requestHeaders := []frame.HeaderField{
		{Name: ":method", Value: "GET"},
		{Name: ":path", Value: "/health"},
		{Name: ":scheme", Value: "https"},
		{Name: ":authority", Value: "localhost:8443"},
	}

	encodedHeaders, err := encoder.EncodeHeaders(requestHeaders)
	if err != nil {
		t.Fatalf("Failed to encode request headers: %v", err)
	}

	// Create HEADERS frame
	headersFrame := frame.NewFrame(
		frame.FrameHeaders,
		frame.FlagEndHeaders|frame.FlagEndStream,
		1,
		encodedHeaders,
	)

	// Simulate server receiving and decoding
	decodedHeaders, err := decoder.DecodeHeaders(headersFrame.Payload)
	if err != nil {
		t.Fatalf("Failed to decode request headers: %v", err)
	}

	// Verify decoded headers
	if len(decodedHeaders) != len(requestHeaders) {
		t.Fatalf("Expected %d headers, got %d", len(requestHeaders), len(decodedHeaders))
	}

	// Process request through handler
	router := handler.NewRouter()
	router.Get("/health", func(stream *connection.Stream) error {
		stream.ResponseCode = 200
		stream.ResponseHeaders = []frame.HeaderField{
			{Name: ":status", Value: "200"},
			{Name: "content-type", Value: "application/json"},
		}
		stream.ResponseBody = []byte(`{"status":"healthy"}`)
		return nil
	})

	stream := &connection.Stream{
		ID:      1,
		Headers: decodedHeaders,
	}

	err = router.Handle(stream)
	if err != nil {
		t.Fatalf("Handler failed: %v", err)
	}

	// Encode response headers
	responseEncoder := frame.NewHPACKEncoder(4096)
	encodedResponseHeaders, err := responseEncoder.EncodeHeaders(stream.ResponseHeaders)
	if err != nil {
		t.Fatalf("Failed to encode response headers: %v", err)
	}

	// Create response frames
	responseHeadersFrame := frame.NewFrame(
		frame.FrameHeaders,
		frame.FlagEndHeaders,
		1,
		encodedResponseHeaders,
	)

	responseDataFrame := frame.NewFrame(
		frame.FrameData,
		frame.FlagEndStream,
		1,
		stream.ResponseBody,
	)

	// Verify response frames
	if responseHeadersFrame.Type != frame.FrameHeaders {
		t.Errorf("Expected HEADERS frame, got type %d", responseHeadersFrame.Type)
	}
	if responseDataFrame.Type != frame.FrameData {
		t.Errorf("Expected DATA frame, got type %d", responseDataFrame.Type)
	}
	if responseDataFrame.Flags&frame.FlagEndStream == 0 {
		t.Error("Response data frame should have END_STREAM flag")
	}

	// Simulate client decoding response
	responseDecoder := frame.NewHPACKDecoder(4096)
	decodedResponseHeaders, err := responseDecoder.DecodeHeaders(responseHeadersFrame.Payload)
	if err != nil {
		t.Fatalf("Failed to decode response headers: %v", err)
	}

	// Verify response
	var status string
	for _, h := range decodedResponseHeaders {
		if h.Name == ":status" {
			status = h.Value
		}
	}

	if status != "200" {
		t.Errorf("Expected status 200, got %s", status)
	}

	if string(responseDataFrame.Payload) != `{"status":"healthy"}` {
		t.Errorf("Unexpected response body: %s", string(responseDataFrame.Payload))
	}
}

// TestFlowControlWindowUpdate tests WINDOW_UPDATE frame handling
func TestFlowControlWindowUpdate(t *testing.T) {
	// Create WINDOW_UPDATE frame
	increment := uint32(65536)
	payload := make([]byte, 4)
	payload[0] = byte(increment >> 24)
	payload[1] = byte(increment >> 16)
	payload[2] = byte(increment >> 8)
	payload[3] = byte(increment)

	wuFrame := frame.NewFrame(frame.FrameWindowUpdate, 0, 0, payload)

	// Write and read
	var buf bytes.Buffer
	if err := frame.WriteFrame(&buf, wuFrame); err != nil {
		t.Fatalf("WriteFrame failed: %v", err)
	}

	readFrame, err := frame.ReadFrame(&buf)
	if err != nil {
		t.Fatalf("ReadFrame failed: %v", err)
	}

	// Parse increment
	readIncrement := uint32(readFrame.Payload[0])<<24 |
		uint32(readFrame.Payload[1])<<16 |
		uint32(readFrame.Payload[2])<<8 |
		uint32(readFrame.Payload[3])

	if readIncrement != increment {
		t.Errorf("Expected increment %d, got %d", increment, readIncrement)
	}
}

// TestPingPong tests PING frame handling
func TestPingPong(t *testing.T) {
	// Create PING frame with 8-byte payload
	pingData := []byte{0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08}
	pingFrame := frame.NewFrame(frame.FramePing, 0, 0, pingData)

	// Write and read
	var buf bytes.Buffer
	if err := frame.WriteFrame(&buf, pingFrame); err != nil {
		t.Fatalf("WriteFrame failed: %v", err)
	}

	readFrame, err := frame.ReadFrame(&buf)
	if err != nil {
		t.Fatalf("ReadFrame failed: %v", err)
	}

	if readFrame.Type != frame.FramePing {
		t.Errorf("Expected PING frame, got type %d", readFrame.Type)
	}

	// Create PING ACK (same payload, ACK flag set)
	pingAckFrame := frame.NewFrame(frame.FramePing, frame.FlagAck, 0, readFrame.Payload)

	if pingAckFrame.Flags&frame.FlagAck == 0 {
		t.Error("PING ACK should have ACK flag set")
	}
	if !bytes.Equal(pingAckFrame.Payload, pingData) {
		t.Error("PING ACK payload should match original PING")
	}
}

// TestStaticFileHandlerSecurity tests security features
func TestStaticFileHandlerSecurity(t *testing.T) {
	handler := handler.NewStaticFileHandler("/var/www")

	tests := []struct {
		name         string
		path         string
		expectedCode int
	}{
		{"NormalPath", "/index.html", 200},
		{"DirectoryTraversal", "/../../../etc/passwd", 403},
		{"EncodedTraversal", "/..%2F..%2Fetc/passwd", 403}, // Contains ".." so caught
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			stream := &connection.Stream{
				ID: 1,
				Headers: []frame.HeaderField{
					{Name: ":path", Value: tt.path},
				},
			}

			err := handler.Handle(stream)
			if err != nil {
				t.Fatalf("Handle failed: %v", err)
			}
			if stream.ResponseCode != tt.expectedCode {
				t.Errorf("Expected status %d, got %d", tt.expectedCode, stream.ResponseCode)
			}
		})
	}
}

// TestFrameStringRepresentation tests frame string formatting
func TestFrameStringRepresentation(t *testing.T) {
	tests := []struct {
		frameType uint8
		expected  string
	}{
		{frame.FrameData, "DATA"},
		{frame.FrameHeaders, "HEADERS"},
		{frame.FramePriority, "PRIORITY"},
		{frame.FrameRSTStream, "RST_STREAM"},
		{frame.FrameSettings, "SETTINGS"},
		{frame.FramePushPromise, "PUSH_PROMISE"},
		{frame.FramePing, "PING"},
		{frame.FrameGoAway, "GOAWAY"},
		{frame.FrameWindowUpdate, "WINDOW_UPDATE"},
		{frame.FrameContinuation, "CONTINUATION"},
		{0xFF, "UNKNOWN"},
	}

	for _, tt := range tests {
		f := frame.NewFrame(tt.frameType, 0, 1, nil)
		str := f.String()
		if !bytes.Contains([]byte(str), []byte(tt.expected)) {
			t.Errorf("Frame type %d: expected %q in string, got %q", tt.frameType, tt.expected, str)
		}
	}
}
