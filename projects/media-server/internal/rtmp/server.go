package rtmp

import (
	"fmt"
	"net"
	"strings"
	"sync"
	"time"

	log "github.com/sirupsen/logrus"
	"github.com/media-server/internal/stream"
)

// Server represents an RTMP server
type Server struct {
	streamManager *stream.Manager
	clients       sync.Map
	listener      net.Listener
	done          chan struct{}
}

// Client represents a connected RTMP client
type Client struct {
	conn          net.Conn
	handshake     *Handshake
	streamKey     string
	stream        *stream.Stream
	encoder       *MessageEncoder
	decoder       *MessageDecoder
	chunkSize     int
	windowAckSize uint32
	bytesRecv     uint64
	bytesSent     uint64
	done          chan struct{}
	isPublishing  bool
	mu            sync.Mutex
}

// NewServer creates a new RTMP server
func NewServer(streamManager *stream.Manager) *Server {
	return &Server{
		streamManager: streamManager,
		done:          make(chan struct{}),
	}
}

// Serve starts serving RTMP connections
func (s *Server) Serve(listener net.Listener) error {
	s.listener = listener

	for {
		conn, err := listener.Accept()
		if err != nil {
			select {
			case <-s.done:
				return nil
			default:
				return fmt.Errorf("accept error: %w", err)
			}
		}

		go s.handleConnection(conn)
	}
}

// Stop stops the RTMP server
func (s *Server) Stop() {
	close(s.done)
	if s.listener != nil {
		s.listener.Close()
	}
}

// handleConnection handles a new RTMP connection
func (s *Server) handleConnection(conn net.Conn) {
	client := &Client{
		conn:      conn,
		handshake: NewHandshake(),
		encoder:   NewMessageEncoder(),
		decoder:   NewMessageDecoder(),
		chunkSize: DefaultChunkSize,
		done:      make(chan struct{}),
	}

	// Store client
	clientID := fmt.Sprintf("client_%d", time.Now().UnixNano())
	s.clients.Store(clientID, client)
	defer func() {
		s.clients.Delete(clientID)
		conn.Close()
		if client.stream != nil && client.isPublishing {
			client.stream.Unpublish()
		}
	}()

	log.Infof("New RTMP connection from %s", conn.RemoteAddr())

	// Set connection timeout
	conn.SetDeadline(time.Now().Add(30 * time.Second))

	// Perform handshake
	if err := s.handleHandshake(client); err != nil {
		log.Errorf("Handshake failed: %v", err)
		return
	}

	// Reset deadline after handshake
	conn.SetDeadline(time.Time{})

	// Handle RTMP messages
	s.handleMessages(client)
}

// handleHandshake performs the RTMP handshake
func (s *Server) handleHandshake(client *Client) error {
	// Read C0 + C1
	c0c1 := make([]byte, 1+handshakeSize)
	_, err := readFull(client.conn, c0c1)
	if err != nil {
		return fmt.Errorf("read C0+C1: %w", err)
	}

	// Process C0+C1, generate S0+S1+S2
	s0, s1, s2, err := client.handshake.ProcessC0C1(c0c1)
	if err != nil {
		return fmt.Errorf("process C0+C1: %w", err)
	}

	// Send S0 + S1 + S2
	_, err = client.conn.Write(append(append(s0, s1...), s2...))
	if err != nil {
		return fmt.Errorf("send S0+S1+S2: %w", err)
	}

	// Read C2
	c2 := make([]byte, handshakeSize)
	_, err = readFull(client.conn, c2)
	if err != nil {
		return fmt.Errorf("read C2: %w", err)
	}

	// Process C2
	if err := client.handshake.ProcessC2(c2); err != nil {
		return fmt.Errorf("process C2: %w", err)
	}

	log.Debug("Handshake completed")
	return nil
}

// handleMessages handles RTMP messages after handshake
func (s *Server) handleMessages(client *Client) {
	buffer := make([]byte, 4096)

	for {
		n, err := client.conn.Read(buffer)
		if err != nil {
			log.Debugf("Client disconnected: %v", err)
			return
		}

		client.bytesRecv += uint64(n)

		// Process received data
		data := buffer[:n]
		offset := 0

		for offset < len(data) {
			msg, consumed, err := client.decoder.Decode(data[offset:])
			if err != nil {
				log.Errorf("Decode error: %v", err)
				return
			}
			offset += consumed

			if msg != nil {
				if err := s.handleMessage(client, msg); err != nil {
					log.Errorf("Handle message error: %v", err)
					return
				}
			}
		}
	}
}

// handleMessage handles a single RTMP message
func (s *Server) handleMessage(client *Client, msg *RTMPMessage) error {
	switch msg.TypeID {
	case MsgSetChunkSize:
		return s.handleSetChunkSize(client, msg)
	case MsgWindowAckSize:
		return s.handleWindowAckSize(client, msg)
	case MsgCommandAMF0:
		return s.handleCommand(client, msg)
	case MsgAudio:
		return s.handleAudio(client, msg)
	case MsgVideo:
		return s.handleVideo(client, msg)
	case MsgDataAMF0:
		return s.handleData(client, msg)
	case MsgAck:
		// Acknowledgement, ignore for now
		return nil
	case MsgUserControl:
		// User control message, ignore for now
		return nil
	default:
		log.Debugf("Unhandled message type: %d", msg.TypeID)
		return nil
	}
}

// handleSetChunkSize handles Set Chunk Size message
func (s *Server) handleSetChunkSize(client *Client, msg *RTMPMessage) error {
	size, err := DecodeChunkSize(msg.Payload)
	if err != nil {
		return err
	}
	client.chunkSize = size
	client.decoder.SetChunkSize(size)
	log.Debugf("Chunk size set to %d", size)
	return nil
}

// handleWindowAckSize handles Window Acknowledgement Size message
func (s *Server) handleWindowAckSize(client *Client, msg *RTMPMessage) error {
	if len(msg.Payload) >= 4 {
		client.windowAckSize = uint32(msg.Payload[0])<<24 |
			uint32(msg.Payload[1])<<16 |
			uint32(msg.Payload[2])<<8 |
			uint32(msg.Payload[3])
		log.Debugf("Window ack size set to %d", client.windowAckSize)
	}
	return nil
}

// handleCommand handles AMF0 command messages
func (s *Server) handleCommand(client *Client, msg *RTMPMessage) error {
	name, args, err := DecodeCommand(msg.Payload)
	if err != nil {
		return fmt.Errorf("decode command: %w", err)
	}

	log.Debugf("Command: %s, args: %v", name, args)

	switch name {
	case "connect":
		return s.handleConnect(client, msg, args)
	case "createStream":
		return s.handleCreateStream(client, msg, args)
	case "publish":
		return s.handlePublish(client, msg, args)
	case "play":
		return s.handlePlay(client, msg, args)
	case "deleteStream":
		return s.handleDeleteStream(client, msg, args)
	case "FCPublish":
		return s.handleFCPublish(client, msg, args)
	case "FCUnpublish":
		return s.handleFCUnpublish(client, msg, args)
	case "_checkbw":
		return s.handleCheckBW(client, msg, args)
	default:
		log.Debugf("Unknown command: %s", name)
		return nil
	}
}

// handleConnect handles the connect command
func (s *Server) handleConnect(client *Client, msg *RTMPMessage, args []interface{}) error {
	log.Info("Connect command received")

	// Send Window Acknowledgement Size
	winAckSize := EncodeWindowAckSize(2500000)
	s.sendControlMessage(client, MsgWindowAckSize, 0, winAckSize)

	// Set Peer Bandwidth
	peerBW := EncodeSetPeerBandwidth(2500000, BandwidthLimitDynamic)
	s.sendControlMessage(client, MsgSetPeerBandwidth, 0, peerBW)

	// Send Set Chunk Size
	chunkSizeMsg := EncodeChunkSize(4096)
	s.sendControlMessage(client, MsgSetChunkSize, 0, chunkSizeMsg)
	client.encoder.SetChunkSize(4096)

	// Send _result
	connectResp := map[string]interface{}{
		"fmsVer":       "FMS/3,0,1,123",
		"capabilities": 31,
	}
	props := map[string]interface{}{
		"level":          "status",
		"code":           "NetConnection.Connect.Success",
		"description":     "Connection succeeded.",
		"objectEncoding": 0,
	}

	response, err := EncodeCommand("_result", float64(1), connectResp, props)
	if err != nil {
		return err
	}

	return s.sendMessage(client, MsgCommandAMF0, 0, 0, response)
}

// handleCreateStream handles the createStream command
func (s *Server) handleCreateStream(client *Client, msg *RTMPMessage, args []interface{}) error {
	log.Info("CreateStream command received")

	// Send _result with stream ID 1
	response, err := EncodeCommand("_result", getTransactionID(args), nil, float64(1))
	if err != nil {
		return err
	}

	return s.sendMessage(client, MsgCommandAMF0, 0, 0, response)
}

// handlePublish handles the publish command
func (s *Server) handlePublish(client *Client, msg *RTMPMessage, args []interface{}) error {
	if len(args) < 3 {
		return fmt.Errorf("invalid publish arguments")
	}

	// Get stream key from arguments
	streamKey, ok := args[3].(string)
	if !ok || streamKey == "" {
		return fmt.Errorf("invalid stream key")
	}

	// Clean stream key
	streamKey = strings.TrimPrefix(streamKey, "/")
	client.streamKey = streamKey

	// Get or create stream
 strm, err := s.streamManager.GetOrCreateStream(streamKey)
	if err != nil {
		return fmt.Errorf("create stream: %w", err)
	}

	// Start publishing
	if err := strm.Publish(client.conn.RemoteAddr().String()); err != nil {
		return fmt.Errorf("publish: %w", err)
	}

	client.stream = strm
	client.isPublishing = true

	log.Infof("Stream publishing started: %s", streamKey)

	// Send onStatus
	status := map[string]interface{}{
		"level":       "status",
		"code":        "NetStream.Publish.Start",
		"description": "Publishing " + streamKey,
	}

	response, err := EncodeCommand("onStatus", float64(0), nil, status)
	if err != nil {
		return err
	}

	return s.sendMessage(client, MsgCommandAMF0, 0, 1, response)
}

// handlePlay handles the play command
func (s *Server) handlePlay(client *Client, msg *RTMPMessage, args []interface{}) error {
	if len(args) < 3 {
		return fmt.Errorf("invalid play arguments")
	}

	// Get stream key
	streamKey, ok := args[3].(string)
	if !ok || streamKey == "" {
		return fmt.Errorf("invalid stream key")
	}

	streamKey = strings.TrimPrefix(streamKey, "/")

	// Get stream
	strm, err := s.streamManager.GetStream(streamKey)
	if err != nil {
		return fmt.Errorf("stream not found: %w", err)
	}

	// Subscribe to stream
	if err := strm.Subscribe(client.conn.RemoteAddr().String()); err != nil {
		return fmt.Errorf("subscribe: %w", err)
	}

	client.stream = strm
	client.isPublishing = false

	log.Infof("Stream play started: %s", streamKey)

	// Send onStatus
	status := map[string]interface{}{
		"level":       "status",
		"code":        "NetStream.Play.Start",
		"description": "Playing " + streamKey,
	}

	response, err := EncodeCommand("onStatus", float64(0), nil, status)
	if err != nil {
		return err
	}

	return s.sendMessage(client, MsgCommandAMF0, 0, 1, response)
}

// handleDeleteStream handles the deleteStream command
func (s *Server) handleDeleteStream(client *Client, msg *RTMPMessage, args []interface{}) error {
	log.Info("DeleteStream command received")

	if client.stream != nil {
		if client.isPublishing {
			client.stream.Unpublish()
		} else {
			client.stream.Unsubscribe(client.conn.RemoteAddr().String())
		}
		client.stream = nil
	}

	return nil
}

// handleFCPublish handles the FCPublish command
func (s *Server) handleFCPublish(client *Client, msg *RTMPMessage, args []interface{}) error {
	log.Debug("FCPublish command received")
	// Response is not required for FCPublish
	return nil
}

// handleFCUnpublish handles the FCUnpublish command
func (s *Server) handleFCUnpublish(client *Client, msg *RTMPMessage, args []interface{}) error {
	log.Debug("FCUnpublish command received")
	return nil
}

// handleCheckBW handles the _checkbw command
func (s *Server) handleCheckBW(client *Client, msg *RTMPMessage, args []interface{}) error {
	log.Debug("_checkbw command received")
	return nil
}

// handleAudio handles audio data
func (s *Server) handleAudio(client *Client, msg *RTMPMessage) error {
	if client.stream == nil || !client.isPublishing {
		return nil
	}

	// Create media packet
	pkt := &stream.MediaPacket{
		Type:      MsgAudio,
		Timestamp: msg.Timestamp,
		Data:      msg.Payload,
		StreamID:  msg.StreamID,
	}

	return client.stream.WritePacket(pkt)
}

// handleVideo handles video data
func (s *Server) handleVideo(client *Client, msg *RTMPMessage) error {
	if client.stream == nil || !client.isPublishing {
		return nil
	}

	// Check for keyframe
	if len(msg.Payload) > 0 {
		frameType := (msg.Payload[0] >> 4) & 0x0F
		if frameType == 1 { // Keyframe
			client.stream.UpdateLastKeyFrame()
		}
	}

	// Create media packet
	pkt := &stream.MediaPacket{
		Type:      MsgVideo,
		Timestamp: msg.Timestamp,
		Data:      msg.Payload,
		StreamID:  msg.StreamID,
	}

	return client.stream.WritePacket(pkt)
}

// handleData handles data messages (metadata)
func (s *Server) handleData(client *Client, msg *RTMPMessage) error {
	log.Debug("Data message received")

	// Parse metadata
	if len(msg.Payload) > 0 {
		_, args, err := DecodeCommand(msg.Payload)
		if err == nil && len(args) > 0 {
			if meta, ok := args[0].(AMFObject); ok {
				s.processMetadata(client, meta)
			}
		}
	}

	return nil
}

// processMetadata processes stream metadata
func (s *Server) processMetadata(client *Client, meta AMFObject) {
	if client.stream == nil {
		return
	}

	metadata := &stream.Metadata{
		CreatedAt: time.Now(),
	}

	if v, ok := meta["width"].(float64); ok {
		metadata.Width = int(v)
	}
	if v, ok := meta["height"].(float64); ok {
		metadata.Height = int(v)
	}
	if v, ok := meta["framerate"].(float64); ok {
		metadata.FrameRate = v
	}
	if v, ok := meta["videodatarate"].(float64); ok {
		metadata.VideoBitRate = int(v * 1000) // kbps to bps
	}
	if v, ok := meta["audiodatarate"].(float64); ok {
		metadata.AudioBitRate = int(v * 1000)
	}
	if v, ok := meta["audiosamplerate"].(float64); ok {
		metadata.SampleRate = int(v)
	}
	if v, ok := meta["audiocodecid"].(float64); ok {
		metadata.Codec = fmt.Sprintf("%d", int(v))
	}

	client.stream.UpdateMetadata(metadata)

	log.Infof("Metadata updated: %dx%d @ %.1f fps", metadata.Width, metadata.Height, metadata.FrameRate)
}

// sendControlMessage sends a control message
func (s *Server) sendControlMessage(client *Client, msgType byte, streamID uint32, payload []byte) {
	s.sendMessage(client, msgType, 0, streamID, payload)
}

// sendMessage sends an RTMP message
func (s *Server) sendMessage(client *Client, msgType byte, timestamp uint32, streamID uint32, payload []byte) error {
	msg := &RTMPMessage{
		ChunkStreamID: 3, // Default for commands
		Timestamp:     timestamp,
		TypeID:        msgType,
		StreamID:      streamID,
		Payload:       payload,
	}

	data, err := client.encoder.Encode(msg)
	if err != nil {
		return fmt.Errorf("encode message: %w", err)
	}

	_, err = client.conn.Write(data)
	if err != nil {
		return fmt.Errorf("write message: %w", err)
	}

	client.bytesSent += uint64(len(data))
	return nil
}

// getTransactionID extracts the transaction ID from command arguments
func getTransactionID(args []interface{}) float64 {
	if len(args) > 0 {
		if id, ok := args[0].(float64); ok {
			return id
		}
	}
	return 0
}

// readFull reads exactly len(buf) bytes from the connection
func readFull(conn net.Conn, buf []byte) (int, error) {
	total := 0
	for total < len(buf) {
		n, err := conn.Read(buf[total:])
		if err != nil {
			return total, err
		}
		total += n
	}
	return total, nil
}
