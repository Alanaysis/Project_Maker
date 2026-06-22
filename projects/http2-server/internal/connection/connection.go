// Package connection implements HTTP/2 connection management and multiplexing.
// This is the core of HTTP/2's multiplexing capability.
package connection

import (
	"fmt"
	"io"
	"net"
	"sync"

	"github.com/anthropic/http2-server/internal/frame"
)

// StreamState represents the state of an HTTP/2 stream
type StreamState int

const (
	StreamIdle            StreamState = iota
	StreamReservedLocal
	StreamReservedRemote
	StreamOpen
	StreamHalfClosedLocal
	StreamHalfClosedRemote
	StreamClosed
)

// Stream represents an HTTP/2 stream
type Stream struct {
	ID           uint32
	State        StreamState
	Headers      []frame.HeaderField
	Body         []byte
	ResponseCode int
	ResponseHeaders []frame.HeaderField
	ResponseBody    []byte

	// Flow control
	SendWindow    int32
	ReceiveWindow int32

	// Channels for multiplexing
	dataChan    chan []byte
	headersChan chan []frame.HeaderField
	doneChan    chan struct{}

	mu sync.Mutex
}

// NewStream creates a new stream
func NewStream(id uint32, initialWindowSize int32) *Stream {
	return &Stream{
		ID:            id,
		State:         StreamIdle,
		SendWindow:    initialWindowSize,
		ReceiveWindow: initialWindowSize,
		dataChan:      make(chan []byte, 10),
		headersChan:   make(chan []frame.HeaderField, 10),
		doneChan:      make(chan struct{}),
	}
}

// Connection represents an HTTP/2 connection with multiplexing support
type Connection struct {
	conn    net.Conn
	streams map[uint32]*Stream
	mu      sync.RWMutex

	// Settings
	settings    *frame.Settings
	peerSettings *frame.Settings

	// HPACK encoder/decoder
	encoder *frame.HPACKEncoder // For encoding responses
	decoder *frame.HPACKDecoder // For decoding requests

	// Connection state
	lastStreamID uint32
	closed       bool

	// Flow control
	sendWindowSize    int32
	receiveWindowSize int32

	// Handler for requests
	handler RequestHandler
}

// RequestHandler is a function that handles HTTP/2 requests
type RequestHandler func(stream *Stream) error

// NewConnection creates a new HTTP/2 connection
func NewConnection(conn net.Conn, handler RequestHandler) *Connection {
	settings := frame.DefaultSettings()

	return &Connection{
		conn:              conn,
		streams:           make(map[uint32]*Stream),
		settings:          settings,
		peerSettings:      frame.DefaultSettings(),
		encoder:           frame.NewHPACKEncoder(settings.HeaderTableSize),
		decoder:           frame.NewHPACKDecoder(settings.HeaderTableSize),
		lastStreamID:      0,
		sendWindowSize:    int32(settings.InitialWindowSize),
		receiveWindowSize: int32(settings.InitialWindowSize),
		handler:           handler,
	}
}

// Start begins processing the HTTP/2 connection
func (c *Connection) Start() error {
	// Read client connection preface (magic string + SETTINGS frame)
	if err := c.readClientPreface(); err != nil {
		return fmt.Errorf("failed to read client preface: %w", err)
	}

	// Send our SETTINGS frame
	if err := c.sendSettings(); err != nil {
		return fmt.Errorf("failed to send settings: %w", err)
	}

	// Start reading frames
	return c.readLoop()
}

// readClientPreface reads the HTTP/2 connection preface from the client
// The client preface consists of the magic string followed by a SETTINGS frame
func (c *Connection) readClientPreface() error {
	// Read the 24-byte connection preface magic string
	preface := make([]byte, 24)
	if _, err := io.ReadFull(c.conn, preface); err != nil {
		return fmt.Errorf("failed to read connection preface: %w", err)
	}

	// Verify the magic string
	expectedPreface := "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
	if string(preface) != expectedPreface {
		return fmt.Errorf("invalid connection preface: got %q", string(preface))
	}

	// Read the client's SETTINGS frame
	f, err := frame.ReadFrame(c.conn)
	if err != nil {
		return fmt.Errorf("failed to read client settings: %w", err)
	}

	if f.Type != frame.FrameSettings {
		return fmt.Errorf("expected SETTINGS frame, got type %d", f.Type)
	}

	// Process the client settings
	return c.handleSettings(f)
}

// readLoop continuously reads and processes frames
func (c *Connection) readLoop() error {
	for {
		f, err := frame.ReadFrame(c.conn)
		if err != nil {
			if err == io.EOF {
				return nil
			}
			return fmt.Errorf("failed to read frame: %w", err)
		}

		if err := c.handleFrame(f); err != nil {
			return err
		}
	}
}

// handleFrame processes a single frame
func (c *Connection) handleFrame(f *frame.Frame) error {
	switch f.Type {
	case frame.FrameSettings:
		return c.handleSettings(f)
	case frame.FrameHeaders:
		return c.handleHeaders(f)
	case frame.FrameData:
		return c.handleData(f)
	case frame.FrameWindowUpdate:
		return c.handleWindowUpdate(f)
	case frame.FramePing:
		return c.handlePing(f)
	case frame.FrameGoAway:
		return c.handleGoAway(f)
	case frame.FrameRSTStream:
		return c.handleRSTStream(f)
	default:
		// Ignore unknown frame types
		return nil
	}
}

// handleSettings processes a SETTINGS frame
func (c *Connection) handleSettings(f *frame.Frame) error {
	if f.Flags&frame.FlagAck != 0 {
		// SETTINGS ACK - nothing to do
		return nil
	}

	settings, err := frame.ParseSettingsFrame(f.Payload)
	if err != nil {
		return fmt.Errorf("failed to parse settings: %w", err)
	}

	c.mu.Lock()
	c.peerSettings = settings
	c.mu.Unlock()

	// Update decoder table size if needed
	if settings.HeaderTableSize != c.encoder.MaxSize() {
		// In a real implementation, we'd update the encoder/decoder
	}

	// Send SETTINGS ACK
	ack := frame.CreateSettingsAckFrame()
	return frame.WriteFrame(c.conn, ack)
}

// handleHeaders processes a HEADERS frame (start of a new request)
func (c *Connection) handleHeaders(f *frame.Frame) error {
	streamID := f.StreamID

	// Validate stream ID
	if streamID%2 == 0 {
		return fmt.Errorf("client stream ID must be odd, got %d", streamID)
	}

	c.mu.Lock()
	if streamID <= c.lastStreamID {
		c.mu.Unlock()
		return fmt.Errorf("stream ID %d is not greater than last %d", streamID, c.lastStreamID)
	}
	c.lastStreamID = streamID

	// Create new stream
	stream := NewStream(streamID, int32(c.peerSettings.InitialWindowSize))
	stream.State = StreamOpen
	c.streams[streamID] = stream
	c.mu.Unlock()

	// Decode headers
	headers, err := c.decoder.DecodeHeaders(f.Payload)
	if err != nil {
		return fmt.Errorf("failed to decode headers: %w", err)
	}

	stream.mu.Lock()
	stream.Headers = headers
	stream.mu.Unlock()

	// If END_HEADERS is set, we have all headers
	if f.Flags&frame.FlagEndHeaders != 0 {
		// If END_STREAM is also set, this is a GET request with no body
		if f.Flags&frame.FlagEndStream != 0 {
			stream.State = StreamHalfClosedRemote
			go c.processRequest(stream)
		}
	}

	return nil
}

// handleData processes a DATA frame
func (c *Connection) handleData(f *frame.Frame) error {
	streamID := f.StreamID

	c.mu.RLock()
	stream, exists := c.streams[streamID]
	c.mu.RUnlock()

	if !exists {
		return fmt.Errorf("stream %d not found", streamID)
	}

	stream.mu.Lock()
	stream.Body = append(stream.Body, f.Payload...)
	stream.mu.Unlock()

	// Update flow control window
	c.mu.Lock()
	c.receiveWindowSize -= int32(f.Length)
	stream.ReceiveWindow -= int32(f.Length)
	c.mu.Unlock()

	// Send WINDOW_UPDATE if needed
	if c.receiveWindowSize < int32(c.settings.InitialWindowSize)/2 {
		c.sendWindowUpdate(0, int32(c.settings.InitialWindowSize)-c.receiveWindowSize)
	}

	// If END_STREAM, process the request
	if f.Flags&frame.FlagEndStream != 0 {
		stream.State = StreamHalfClosedRemote
		go c.processRequest(stream)
	}

	return nil
}

// handleWindowUpdate processes a WINDOW_UPDATE frame
func (c *Connection) handleWindowUpdate(f *frame.Frame) error {
	if len(f.Payload) < 4 {
		return fmt.Errorf("invalid WINDOW_UPDATE frame")
	}

	// Parse window size increment
	increment := int32(f.Payload[0])<<24 | int32(f.Payload[1])<<16 |
		int32(f.Payload[2])<<8 | int32(f.Payload[3])

	if f.StreamID == 0 {
		// Connection-level window update
		c.mu.Lock()
		c.sendWindowSize += increment
		c.mu.Unlock()
	} else {
		// Stream-level window update
		c.mu.RLock()
		stream, exists := c.streams[f.StreamID]
		c.mu.RUnlock()

		if exists {
			stream.mu.Lock()
			stream.SendWindow += increment
			stream.mu.Unlock()
		}
	}

	return nil
}

// handlePing processes a PING frame
func (c *Connection) handlePing(f *frame.Frame) error {
	if f.Flags&frame.FlagAck != 0 {
		// PING ACK - nothing to do
		return nil
	}

	// Send PING ACK with same payload
	ack := frame.NewFrame(frame.FramePing, frame.FlagAck, 0, f.Payload)
	return frame.WriteFrame(c.conn, ack)
}

// handleGoAway processes a GOAWAY frame
func (c *Connection) handleGoAway(f *frame.Frame) error {
	c.mu.Lock()
	c.closed = true
	c.mu.Unlock()
	return nil
}

// handleRSTStream processes a RST_STREAM frame
func (c *Connection) handleRSTStream(f *frame.Frame) error {
	c.mu.Lock()
	if stream, exists := c.streams[f.StreamID]; exists {
		stream.State = StreamClosed
		close(stream.doneChan)
	}
	c.mu.Unlock()
	return nil
}

// sendSettings sends the initial SETTINGS frame
func (c *Connection) sendSettings() error {
	settings := frame.CreateSettingsFrame(c.settings, 0)
	return frame.WriteFrame(c.conn, settings)
}

// sendWindowUpdate sends a WINDOW_UPDATE frame
func (c *Connection) sendWindowUpdate(streamID uint32, increment int32) error {
	payload := make([]byte, 4)
	payload[0] = byte(increment >> 24)
	payload[1] = byte(increment >> 16)
	payload[2] = byte(increment >> 8)
	payload[3] = byte(increment)

	wu := frame.NewFrame(frame.FrameWindowUpdate, 0, streamID, payload)
	return frame.WriteFrame(c.conn, wu)
}

// processRequest handles a complete request
func (c *Connection) processRequest(stream *Stream) error {
	if c.handler != nil {
		if err := c.handler(stream); err != nil {
			return c.sendError(stream.ID, err)
		}
	}

	// Send the response back to the client
	if err := c.SendResponse(stream); err != nil {
		return fmt.Errorf("failed to send response: %w", err)
	}

	return nil
}

// SendResponse sends an HTTP/2 response
func (c *Connection) SendResponse(stream *Stream) error {
	// Encode response headers
	encoder := frame.NewHPACKEncoder(c.peerSettings.HeaderTableSize)
	encoded, err := encoder.EncodeHeaders(stream.ResponseHeaders)
	if err != nil {
		return fmt.Errorf("failed to encode headers: %w", err)
	}

	// Send HEADERS frame
	headersFrame := frame.NewFrame(frame.FrameHeaders, frame.FlagEndHeaders, stream.ID, encoded)
	if err := frame.WriteFrame(c.conn, headersFrame); err != nil {
		return err
	}

	// Send DATA frame if there's a body
	if len(stream.ResponseBody) > 0 {
		flags := frame.FlagEndStream
		dataFrame := frame.NewFrame(frame.FrameData, flags, stream.ID, stream.ResponseBody)
		if err := frame.WriteFrame(c.conn, dataFrame); err != nil {
			return err
		}
	} else {
		// Send empty DATA frame with END_STREAM
		dataFrame := frame.NewFrame(frame.FrameData, frame.FlagEndStream, stream.ID, nil)
		if err := frame.WriteFrame(c.conn, dataFrame); err != nil {
			return err
		}
	}

	// Update stream state
	stream.mu.Lock()
	stream.State = StreamHalfClosedLocal
	stream.mu.Unlock()

	return nil
}

// sendError sends an error response
func (c *Connection) sendError(streamID uint32, err error) error {
	// Send RST_STREAM
	payload := make([]byte, 4)
	payload[0] = 0x00
	payload[1] = 0x00
	payload[2] = 0x00
	payload[3] = 0x02 // INTERNAL_ERROR

	rst := frame.NewFrame(frame.FrameRSTStream, 0, streamID, payload)
	return frame.WriteFrame(c.conn, rst)
}

// Close closes the connection
func (c *Connection) Close() error {
	// Send GOAWAY
	payload := make([]byte, 8)
	payload[0] = byte(c.lastStreamID >> 24)
	payload[1] = byte(c.lastStreamID >> 16)
	payload[2] = byte(c.lastStreamID >> 8)
	payload[3] = byte(c.lastStreamID)
	payload[4] = 0 // NO_ERROR
	payload[5] = 0
	payload[6] = 0
	payload[7] = 0

	goaway := frame.NewFrame(frame.FrameGoAway, 0, 0, payload)
	if err := frame.WriteFrame(c.conn, goaway); err != nil {
		return err
	}

	return c.conn.Close()
}
