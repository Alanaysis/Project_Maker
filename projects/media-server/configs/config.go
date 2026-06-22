package configs

import (
	"os"
	"strconv"
	"time"
)

// Config holds server configuration
type Config struct {
	// Server ports
	RTMPPort string
	HTTPPort string

	// Stream settings
	MaxStreams       int
	StreamTimeout    time.Duration
	CleanupInterval  time.Duration
	BufferSize       int

	// HLS settings
	MaxSegments      int
	TargetDuration   float64

	// Transcoder settings
	DefaultVideoBitRate int
	DefaultAudioBitRate int
	DefaultWidth        int
	DefaultHeight       int
	DefaultFrameRate    float64

	// Logging
	LogLevel string
}

// DefaultConfig returns default configuration
func DefaultConfig() *Config {
	return &Config{
		RTMPPort:           "1935",
		HTTPPort:           "8080",
		MaxStreams:         100,
		StreamTimeout:      30 * time.Second,
		CleanupInterval:    10 * time.Second,
		BufferSize:         100,
		MaxSegments:        5,
		TargetDuration:     6.0,
		DefaultVideoBitRate: 1000000,
		DefaultAudioBitRate: 128000,
		DefaultWidth:        1280,
		DefaultHeight:       720,
		DefaultFrameRate:    30.0,
		LogLevel:           "info",
	}
}

// LoadConfig loads configuration from environment variables
func LoadConfig() *Config {
	config := DefaultConfig()

	if port := os.Getenv("RTMP_PORT"); port != "" {
		config.RTMPPort = port
	}

	if port := os.Getenv("HTTP_PORT"); port != "" {
		config.HTTPPort = port
	}

	if val := os.Getenv("MAX_STREAMS"); val != "" {
		if n, err := strconv.Atoi(val); err == nil {
			config.MaxStreams = n
		}
	}

	if val := os.Getenv("STREAM_TIMEOUT"); val != "" {
		if d, err := time.ParseDuration(val); err == nil {
			config.StreamTimeout = d
		}
	}

	if val := os.Getenv("CLEANUP_INTERVAL"); val != "" {
		if d, err := time.ParseDuration(val); err == nil {
			config.CleanupInterval = d
		}
	}

	if val := os.Getenv("BUFFER_SIZE"); val != "" {
		if n, err := strconv.Atoi(val); err == nil {
			config.BufferSize = n
		}
	}

	if val := os.Getenv("MAX_SEGMENTS"); val != "" {
		if n, err := strconv.Atoi(val); err == nil {
			config.MaxSegments = n
		}
	}

	if val := os.Getenv("TARGET_DURATION"); val != "" {
		if f, err := strconv.ParseFloat(val, 64); err == nil {
			config.TargetDuration = f
		}
	}

	if val := os.Getenv("VIDEO_BITRATE"); val != "" {
		if n, err := strconv.Atoi(val); err == nil {
			config.DefaultVideoBitRate = n
		}
	}

	if val := os.Getenv("AUDIO_BITRATE"); val != "" {
		if n, err := strconv.Atoi(val); err == nil {
			config.DefaultAudioBitRate = n
		}
	}

	if val := os.Getenv("VIDEO_WIDTH"); val != "" {
		if n, err := strconv.Atoi(val); err == nil {
			config.DefaultWidth = n
		}
	}

	if val := os.Getenv("VIDEO_HEIGHT"); val != "" {
		if n, err := strconv.Atoi(val); err == nil {
			config.DefaultHeight = n
		}
	}

	if val := os.Getenv("FRAME_RATE"); val != "" {
		if f, err := strconv.ParseFloat(val, 64); err == nil {
			config.DefaultFrameRate = f
		}
	}

	if level := os.Getenv("LOG_LEVEL"); level != "" {
		config.LogLevel = level
	}

	return config
}

// Validate validates the configuration
func (c *Config) Validate() error {
	// Add validation logic here
	return nil
}
