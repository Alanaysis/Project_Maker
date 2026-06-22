package rtmp

import (
	"encoding/binary"
	"fmt"
)

// RTMP message types
const (
	MsgSetChunkSize      = 1
	MsgAbort             = 2
	MsgAck               = 3
	MsgUserControl       = 4
	MsgWindowAckSize     = 5
	MsgSetPeerBandwidth  = 6
	MsgAudio             = 8
	MsgVideo             = 9
	MsgDataAMF0          = 18
	MsgCommandAMF0       = 20
)

// RTMP chunk header format types
const (
	ChunkHeaderFmt0 = 0 // 11 bytes: timestamp(3) + msg_length(3) + msg_type(1) + stream_id(4)
	ChunkHeaderFmt1 = 1 // 7 bytes: timestamp_delta(3) + msg_length(3) + msg_type(1)
	ChunkHeaderFmt2 = 2 // 3 bytes: timestamp_delta(3)
	ChunkHeaderFmt3 = 3 // 0 bytes
)

// Default chunk size
const DefaultChunkSize = 128

// RTMPMessage represents a complete RTMP message
type RTMPMessage struct {
	ChunkStreamID  int
	Timestamp      uint32
	TypeID         byte
	StreamID       uint32
	Payload        []byte
	IsExtendedTS   bool
}

// RTMPChunk represents an RTMP chunk
type RTMPChunk struct {
	Format       byte   // 0-3
	ChunkStreamID int
	Timestamp    uint32
	MsgLength    uint32
	MsgTypeID    byte
	MsgStreamID  uint32
	Data         []byte
	HasExtendedTS bool
}

// MessageEncoder encodes RTMP messages into chunks
type MessageEncoder struct {
	chunkSize int
}

// NewMessageEncoder creates a new message encoder
func NewMessageEncoder() *MessageEncoder {
	return &MessageEncoder{
		chunkSize: DefaultChunkSize,
	}
}

// SetChunkSize sets the chunk size for encoding
func (e *MessageEncoder) SetChunkSize(size int) {
	e.chunkSize = size
}

// Encode encodes an RTMP message into chunks
func (e *MessageEncoder) Encode(msg *RTMPMessage) ([]byte, error) {
	var result []byte

	// Encode chunk header (Format 0)
	chunkHeader := e.encodeChunkHeader(msg, 0)
	result = append(result, chunkHeader...)

	// Split payload into chunks
	payload := msg.Payload
	offset := 0

	for offset < len(payload) {
		// Calculate chunk data length
		chunkLen := e.chunkSize
		if offset+chunkLen > len(payload) {
			chunkLen = len(payload) - offset
		}

		// Add chunk data
		result = append(result, payload[offset:offset+chunkLen]...)
		offset += chunkLen

		// If there's more data, add Format 3 header
		if offset < len(payload) {
			result = append(result, e.encodeChunkHeaderContinuation(msg)...)
		}
	}

	return result, nil
}

// encodeChunkHeader encodes a chunk header
func (e *MessageEncoder) encodeChunkHeader(msg *RTMPMessage, format byte) []byte {
	// Format 0: 11 bytes
	header := make([]byte, 12) // max header size
	headerLen := 0

	// First byte: format (2 bits) + chunk stream id (6 bits)
	header[0] = (format << 6) | byte(msg.ChunkStreamID&0x3F)
	headerLen++

	// Timestamp (3 bytes) - Format 0
	if msg.Timestamp < 0xFFFFFF {
		binary.BigEndian.PutUint32(header[headerLen:headerLen+4], msg.Timestamp)
		headerLen += 3 // Only use 3 bytes
	} else {
		// Extended timestamp
		binary.BigEndian.PutUint32(header[headerLen:headerLen+4], 0xFFFFFF)
		headerLen += 3
	}

	// Message length (3 bytes)
	binary.BigEndian.PutUint32(header[headerLen:headerLen+4], uint32(len(msg.Payload)))
	headerLen += 3

	// Message type (1 byte)
	header[headerLen] = msg.TypeID
	headerLen++

	// Stream ID (4 bytes) - little endian
	binary.LittleEndian.PutUint32(header[headerLen:headerLen+4], msg.StreamID)
	headerLen += 4

	// Extended timestamp (4 bytes) if needed
	if msg.Timestamp >= 0xFFFFFF {
		binary.BigEndian.PutUint32(header[headerLen:headerLen+4], msg.Timestamp)
		headerLen += 4
	}

	return header[:headerLen]
}

// encodeChunkHeaderContinuation encodes a Format 3 continuation header
func (e *MessageEncoder) encodeChunkHeaderContinuation(msg *RTMPMessage) []byte {
	// Format 3: just the first byte
	header := make([]byte, 1)
	header[0] = (ChunkHeaderFmt3 << 6) | byte(msg.ChunkStreamID&0x3F)

	// Add extended timestamp if needed
	if msg.Timestamp >= 0xFFFFFF {
		extTS := make([]byte, 4)
		binary.BigEndian.PutUint32(extTS, msg.Timestamp)
		header = append(header, extTS...)
	}

	return header
}

// MessageDecoder decodes RTMP chunks into messages
type MessageDecoder struct {
	chunkSize    int
	chunkStreams map[int]*partialMessage
}

// partialMessage represents a message being assembled from chunks
type partialMessage struct {
	msg       *RTMPMessage
	received  int
	complete  bool
}

// NewMessageDecoder creates a new message decoder
func NewMessageDecoder() *MessageDecoder {
	return &MessageDecoder{
		chunkSize:    DefaultChunkSize,
		chunkStreams: make(map[int]*partialMessage),
	}
}

// SetChunkSize sets the chunk size for decoding
func (d *MessageDecoder) SetChunkSize(size int) {
	d.chunkSize = size
}

// Decode decodes an RTMP message from raw data
// Returns the message and number of bytes consumed
func (d *MessageDecoder) Decode(data []byte) (*RTMPMessage, int, error) {
	if len(data) < 1 {
		return nil, 0, fmt.Errorf("not enough data for chunk header")
	}

	offset := 0

	// Parse first byte
	firstByte := data[offset]
	offset++

	format := (firstByte >> 6) & 0x03
	chunkStreamID := int(firstByte & 0x3F)

	// Handle 2-byte chunk stream ID
	if chunkStreamID == 0 {
		if len(data) < offset+1 {
			return nil, 0, fmt.Errorf("not enough data for extended chunk stream ID")
		}
		chunkStreamID = int(data[offset]) + 64
		offset++
	} else if chunkStreamID == 1 {
		if len(data) < offset+2 {
			return nil, 0, fmt.Errorf("not enough data for extended chunk stream ID")
		}
		chunkStreamID = int(data[offset]) + int(data[offset+1])*256 + 64
		offset += 2
	}

	// Get or create partial message for this chunk stream
	pm, exists := d.chunkStreams[chunkStreamID]
	if !exists {
		pm = &partialMessage{
			msg: &RTMPMessage{
				ChunkStreamID: chunkStreamID,
			},
		}
		d.chunkStreams[chunkStreamID] = pm
	}

	// Parse header based on format
	switch format {
	case ChunkHeaderFmt0:
		if len(data) < offset+11 {
			return nil, 0, fmt.Errorf("not enough data for format 0 header")
		}

		// Timestamp (3 bytes)
		pm.msg.Timestamp = uint32(data[offset])<<16 | uint32(data[offset+1])<<8 | uint32(data[offset+2])
		offset += 3

		// Message length (3 bytes)
		pm.msg.StreamID = binary.BigEndian.Uint32(data[offset : offset+4])
		pm.msg.Payload = make([]byte, 0)
		offset += 3

		// Message type (1 byte)
		pm.msg.TypeID = data[offset]
		offset++

		// Stream ID (4 bytes) - little endian
		pm.msg.StreamID = binary.LittleEndian.Uint32(data[offset : offset+4])
		offset += 4

		// Extended timestamp
		if pm.msg.Timestamp == 0xFFFFFF {
			if len(data) < offset+4 {
				return nil, 0, fmt.Errorf("not enough data for extended timestamp")
			}
			pm.msg.Timestamp = binary.BigEndian.Uint32(data[offset : offset+4])
			offset += 4
			pm.msg.IsExtendedTS = true
		}

	case ChunkHeaderFmt1:
		if len(data) < offset+7 {
			return nil, 0, fmt.Errorf("not enough data for format 1 header")
		}

		// Timestamp delta (3 bytes)
		tsDelta := uint32(data[offset])<<16 | uint32(data[offset+1])<<8 | uint32(data[offset+2])
		pm.msg.Timestamp += tsDelta
		offset += 3

		// Message length (3 bytes)
		offset += 3

		// Message type (1 byte)
		pm.msg.TypeID = data[offset]
		offset++

	case ChunkHeaderFmt2:
		if len(data) < offset+3 {
			return nil, 0, fmt.Errorf("not enough data for format 2 header")
		}

		// Timestamp delta (3 bytes)
		tsDelta := uint32(data[offset])<<16 | uint32(data[offset+1])<<8 | uint32(data[offset+2])
		pm.msg.Timestamp += tsDelta
		offset += 3

	case ChunkHeaderFmt3:
		// No additional header
	}

	// Read chunk data
	chunkDataLen := d.chunkSize
	if offset+chunkDataLen > len(data) {
		chunkDataLen = len(data) - offset
	}

	if chunkDataLen > 0 {
		pm.msg.Payload = append(pm.msg.Payload, data[offset:offset+chunkDataLen]...)
		offset += chunkDataLen
	}

	// Check if message is complete
	pm.received = len(pm.msg.Payload)
	if pm.received >= chunkDataLen {
		pm.complete = true
	}

	if pm.complete {
		msg := pm.msg
		delete(d.chunkStreams, chunkStreamID)
		return msg, offset, nil
	}

	// Return nil if message is not complete yet
	return nil, offset, nil
}

// EncodeChunkSize encodes a Set Chunk Size message
func EncodeChunkSize(size int) []byte {
	data := make([]byte, 4)
	binary.BigEndian.PutUint32(data, uint32(size))
	return data
}

// DecodeChunkSize decodes a Set Chunk Size message
func DecodeChunkSize(data []byte) (int, error) {
	if len(data) < 4 {
		return 0, fmt.Errorf("invalid chunk size data")
	}
	return int(binary.BigEndian.Uint32(data)), nil
}

// EncodeWindowAckSize encodes a Window Acknowledgement Size message
func EncodeWindowAckSize(size int) []byte {
	data := make([]byte, 4)
	binary.BigEndian.PutUint32(data, uint32(size))
	return data
}

// EncodeSetPeerBandwidth encodes a Set Peer Bandwidth message
func EncodeSetPeerBandwidth(size int, limitType byte) []byte {
	data := make([]byte, 5)
	binary.BigEndian.PutUint32(data[0:4], uint32(size))
	data[4] = limitType
	return data
}

// Bandwidth limit types
const (
	BandwidthLimitHard   = 0
	BandwidthLimitSoft   = 1
	BandwidthLimitDynamic = 2
)
