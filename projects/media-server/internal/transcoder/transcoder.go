package transcoder

import (
	"fmt"
	"sync"

	log "github.com/sirupsen/logrus"
	"github.com/media-server/internal/stream"
)

// Transcoder handles media transcoding
type Transcoder struct {
	mu       sync.RWMutex
	streams  map[string]*TranscodeStream
	config   *Config
}

// Config holds transcoder configuration
type Config struct {
	DefaultVideoBitRate int    // Default video bitrate in bps
	DefaultAudioBitRate int    // Default audio bitrate in bps
	DefaultWidth        int    // Default width
	DefaultHeight       int    // Default height
	DefaultFrameRate    float64 // Default frame rate
}

// DefaultConfig returns default transcoder configuration
func DefaultConfig() *Config {
	return &Config{
		DefaultVideoBitRate: 1000000, // 1 Mbps
		DefaultAudioBitRate: 128000,  // 128 Kbps
		DefaultWidth:        1280,
		DefaultHeight:       720,
		DefaultFrameRate:    30.0,
	}
}

// TranscodeStream represents a stream being transcoded
type TranscodeStream struct {
	mu          sync.Mutex
	streamKey   string
	videoConfig *stream.VideoConfig
	audioConfig *stream.AudioConfig
	packetCount int64
	keyFrameCount int64
}

// NewTranscoder creates a new transcoder
func NewTranscoder(config *Config) *Transcoder {
	if config == nil {
		config = DefaultConfig()
	}

	return &Transcoder{
		streams: make(map[string]*TranscodeStream),
		config:  config,
	}
}

// RegisterStream registers a stream for transcoding
func (t *Transcoder) RegisterStream(streamKey string) {
	t.mu.Lock()
	defer t.mu.Unlock()

	if _, exists := t.streams[streamKey]; exists {
		return
	}

	ts := &TranscodeStream{
		streamKey: streamKey,
		videoConfig: &stream.VideoConfig{
			Codec:     "h264",
			Width:     t.config.DefaultWidth,
			Height:    t.config.DefaultHeight,
			FrameRate: t.config.DefaultFrameRate,
			BitRate:   t.config.DefaultVideoBitRate,
		},
		audioConfig: &stream.AudioConfig{
			Codec:      "aac",
			SampleRate: 44100,
			Channels:   2,
			BitRate:    t.config.DefaultAudioBitRate,
		},
	}

	t.streams[streamKey] = ts
	log.Infof("Stream registered for transcoding: %s", streamKey)
}

// UnregisterStream unregisters a stream
func (t *Transcoder) UnregisterStream(streamKey string) {
	t.mu.Lock()
	defer t.mu.Unlock()

	delete(t.streams, streamKey)
	log.Infof("Stream unregistered from transcoding: %s", streamKey)
}

// ProcessPacket processes a media packet for transcoding
func (t *Transcoder) ProcessPacket(streamKey string, pkt *stream.MediaPacket) (*stream.MediaPacket, error) {
	t.mu.RLock()
	ts, exists := t.streams[streamKey]
	t.mu.RUnlock()

	if !exists {
		return pkt, nil
	}

	ts.mu.Lock()
	ts.packetCount++
	ts.mu.Unlock()

	// In a real implementation, this would:
	// 1. Decode the packet
	// 2. Apply transformations (resize, re-encode, etc.)
	// 3. Encode to target format

	// For now, we just pass through
	return pkt, nil
}

// UpdateVideoConfig updates the video configuration for a stream
func (t *Transcoder) UpdateVideoConfig(streamKey string, config *stream.VideoConfig) error {
	t.mu.RLock()
	ts, exists := t.streams[streamKey]
	t.mu.RUnlock()

	if !exists {
		return fmt.Errorf("stream not registered: %s", streamKey)
	}

	ts.mu.Lock()
	ts.videoConfig = config
	ts.mu.Unlock()

	log.Infof("Video config updated for stream %s: %dx%d @ %.1f fps",
		streamKey, config.Width, config.Height, config.FrameRate)

	return nil
}

// UpdateAudioConfig updates the audio configuration for a stream
func (t *Transcoder) UpdateAudioConfig(streamKey string, config *stream.AudioConfig) error {
	t.mu.RLock()
	ts, exists := t.streams[streamKey]
	t.mu.RUnlock()

	if !exists {
		return fmt.Errorf("stream not registered: %s", streamKey)
	}

	ts.mu.Lock()
	ts.audioConfig = config
	ts.mu.Unlock()

	log.Infof("Audio config updated for stream %s: %d Hz, %d channels",
		streamKey, config.SampleRate, config.Channels)

	return nil
}

// GetVideoConfig returns the video configuration for a stream
func (t *Transcoder) GetVideoConfig(streamKey string) (*stream.VideoConfig, error) {
	t.mu.RLock()
	ts, exists := t.streams[streamKey]
	t.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("stream not registered: %s", streamKey)
	}

	ts.mu.Lock()
	defer ts.mu.Unlock()

	return ts.videoConfig, nil
}

// GetAudioConfig returns the audio configuration for a stream
func (t *Transcoder) GetAudioConfig(streamKey string) (*stream.AudioConfig, error) {
	t.mu.RLock()
	ts, exists := t.streams[streamKey]
	t.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("stream not registered: %s", streamKey)
	}

	ts.mu.Lock()
	defer ts.mu.Unlock()

	return ts.audioConfig, nil
}

// GetStats returns transcoding statistics for a stream
func (t *Transcoder) GetStats(streamKey string) (*TranscodeStats, error) {
	t.mu.RLock()
	ts, exists := t.streams[streamKey]
	t.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("stream not registered: %s", streamKey)
	}

	ts.mu.Lock()
	defer ts.mu.Unlock()

	return &TranscodeStats{
		StreamKey:      streamKey,
		PacketCount:    ts.packetCount,
		KeyFrameCount:  ts.keyFrameCount,
		VideoBitRate:   ts.videoConfig.BitRate,
		AudioBitRate:   ts.audioConfig.BitRate,
		Width:          ts.videoConfig.Width,
		Height:         ts.videoConfig.Height,
		FrameRate:      ts.videoConfig.FrameRate,
	}, nil
}

// TranscodeStats holds transcoding statistics
type TranscodeStats struct {
	StreamKey      string  `json:"stream_key"`
	PacketCount    int64   `json:"packet_count"`
	KeyFrameCount  int64   `json:"key_frame_count"`
	VideoBitRate   int     `json:"video_bit_rate"`
	AudioBitRate   int     `json:"audio_bit_rate"`
	Width          int     `json:"width"`
	Height         int     `json:"height"`
	FrameRate      float64 `json:"frame_rate"`
}

// DetectKeyFrame detects if a video packet is a keyframe
func DetectKeyFrame(data []byte, codec string) bool {
	if len(data) == 0 {
		return false
	}

	switch codec {
	case "h264":
		// Check NAL unit type
		// In FLV video tags, first byte contains frame type and codec info
		if len(data) > 0 {
			frameType := (data[0] >> 4) & 0x0F
			return frameType == 1 // Keyframe
		}
	case "h265":
		// Similar check for H.265
		if len(data) > 0 {
			frameType := (data[0] >> 4) & 0x0F
			return frameType == 1
		}
	}

	return false
}

// ParseVideoHeader parses video configuration from header data
func ParseVideoHeader(data []byte) (*stream.VideoConfig, error) {
	if len(data) < 5 {
		return nil, fmt.Errorf("invalid video header")
	}

	config := &stream.VideoConfig{
		Codec: "h264",
	}

	// Parse AVCDecoderConfigurationRecord
	// This is a simplified version
	if data[0] == 0x17 && data[1] == 0x00 {
		// Keyframe, AVC sequence header
		// Version
		version := data[5]
		if version != 1 {
			return nil, fmt.Errorf("unsupported AVC version: %d", version)
		}

		// Profile, compatibility, level
		// data[6], data[7], data[8]

		// SPS and PPS parsing would go here
		// For now, use defaults
		config.Width = 1280
		config.Height = 720
		config.FrameRate = 30.0
	}

	return config, nil
}

// ParseAudioHeader parses audio configuration from header data
func ParseAudioHeader(data []byte) (*stream.AudioConfig, error) {
	if len(data) < 2 {
		return nil, fmt.Errorf("invalid audio header")
	}

	config := &stream.AudioConfig{
		Codec: "aac",
	}

	// Parse AudioSpecificConfig
	// Format: 5 bits (freq) + 4 bits (channel) + 4 bits (frame length) + 3 bits (depends on config)
	soundFormat := (data[0] >> 4) & 0x0F

	switch soundFormat {
	case 10: // AAC
		config.Codec = "aac"
		// Parse AAC specific config
		if len(data) > 2 {
			freqIndex := ((data[2] & 0x07) << 1) | ((data[3] >> 7) & 0x01)
			switch freqIndex {
			case 0:
				config.SampleRate = 96000
			case 1:
				config.SampleRate = 88200
			case 2:
				config.SampleRate = 64000
			case 3:
				config.SampleRate = 48000
			case 4:
				config.SampleRate = 44100
			case 5:
				config.SampleRate = 32000
			default:
				config.SampleRate = 44100
			}
			config.Channels = int(((data[3] >> 3) & 0x0F))
			if config.Channels == 0 {
				config.Channels = 2
			}
		}
	default:
		config.Codec = "unknown"
		config.SampleRate = 44100
		config.Channels = 2
	}

	return config, nil
}
