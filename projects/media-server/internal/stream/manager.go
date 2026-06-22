package stream

import (
	"fmt"
	"sync"
	"time"

	log "github.com/sirupsen/logrus"
)

// Manager manages all active streams
type Manager struct {
	mu      sync.RWMutex
	streams map[string]*Stream
	config  *ManagerConfig

	// Statistics
	totalStreamsCreated int64
	totalBytesIn        int64
	totalBytesOut       int64
}

// ManagerConfig holds configuration for the stream manager
type ManagerConfig struct {
	MaxStreams        int           // Maximum concurrent streams
	StreamTimeout     time.Duration // Timeout for idle streams
	CleanupInterval   time.Duration // Interval for cleanup goroutine
	BufferSize        int           // Media packet buffer size
}

// DefaultManagerConfig returns a default configuration
func DefaultManagerConfig() *ManagerConfig {
	return &ManagerConfig{
		MaxStreams:      100,
		StreamTimeout:   30 * time.Second,
		CleanupInterval: 10 * time.Second,
		BufferSize:      100,
	}
}

// NewManager creates a new stream manager
func NewManager() *Manager {
	return NewManagerWithConfig(DefaultManagerConfig())
}

// NewManagerWithConfig creates a new stream manager with custom config
func NewManagerWithConfig(config *ManagerConfig) *Manager {
	m := &Manager{
		streams: make(map[string]*Stream),
		config:  config,
	}

	// Start cleanup goroutine
	go m.cleanupLoop()

	return m
}

// GetOrCreateStream gets an existing stream or creates a new one
func (m *Manager) GetOrCreateStream(key string) (*Stream, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Check if stream already exists
	if stream, ok := m.streams[key]; ok {
		return stream, nil
	}

	// Check limit
	if len(m.streams) >= m.config.MaxStreams {
		return nil, ErrMaxStreamsReached
	}

	// Create new stream
	streamID := fmt.Sprintf("stream_%d", time.Now().UnixNano())
	stream := NewStream(streamID, key)
	m.streams[key] = stream
	m.totalStreamsCreated++

	log.Infof("Stream created: key=%s, id=%s", key, streamID)

	return stream, nil
}

// GetStream returns a stream by key
func (m *Manager) GetStream(key string) (*Stream, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	stream, ok := m.streams[key]
	if !ok {
		return nil, ErrStreamNotFound
	}

	return stream, nil
}

// DeleteStream removes a stream
func (m *Manager) DeleteStream(key string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if stream, ok := m.streams[key]; ok {
		stream.Close()
		delete(m.streams, key)
		log.Infof("Stream deleted: key=%s", key)
	}
}

// GetStreamList returns a list of all active streams
func (m *Manager) GetStreamList() []StreamInfo {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]StreamInfo, 0, len(m.streams))
	for key, stream := range m.streams {
		info := StreamInfo{
			Key:       key,
			ID:        stream.ID,
			State:     stream.State,
			CreatedAt: stream.createdAt,
			UpdatedAt: stream.updatedAt,
		}

		if pub := stream.GetPublisher(); pub != nil {
			info.PublisherID = pub.ID
			info.PublisherStartTime = pub.StartTime
		}

		info.SubscriberCount = stream.GetSubscriberCount()

		if stream.Metadata != nil {
			info.Width = stream.Metadata.Width
			info.Height = stream.Metadata.Height
			info.FrameRate = stream.Metadata.FrameRate
		}

		result = append(result, info)
	}

	return result
}

// StreamInfo represents public stream information
type StreamInfo struct {
	Key                string      `json:"key"`
	ID                 string      `json:"id"`
	State              StreamState `json:"state"`
	PublisherID        string      `json:"publisher_id,omitempty"`
	PublisherStartTime time.Time   `json:"publisher_start_time,omitempty"`
	SubscriberCount    int         `json:"subscriber_count"`
	Width              int         `json:"width,omitempty"`
	Height             int         `json:"height,omitempty"`
	FrameRate          float64     `json:"frame_rate,omitempty"`
	CreatedAt          time.Time   `json:"created_at"`
	UpdatedAt          time.Time   `json:"updated_at"`
}

// GetStats returns overall statistics
func (m *Manager) GetStats() ManagerStats {
	m.mu.RLock()
	defer m.mu.RUnlock()

	stats := ManagerStats{
		TotalStreams:      len(m.streams),
		TotalCreated:      m.totalStreamsCreated,
		TotalBytesIn:      m.totalBytesIn,
		TotalBytesOut:     m.totalBytesOut,
	}

	for _, stream := range m.streams {
		switch stream.State {
		case StreamStatePublishing:
			stats.PublishingStreams++
		case StreamStatePlaying:
			stats.PublishingStreams++ // Still has a publisher
			stats.PlayingStreams++
			stats.TotalSubscribers += stream.GetSubscriberCount()
		}
	}

	return stats
}

// ManagerStats holds overall statistics
type ManagerStats struct {
	TotalStreams      int   `json:"total_streams"`
	PublishingStreams int   `json:"publishing_streams"`
	PlayingStreams    int   `json:"playing_streams"`
	TotalSubscribers  int   `json:"total_subscribers"`
	TotalCreated      int64 `json:"total_created"`
	TotalBytesIn      int64 `json:"total_bytes_in"`
	TotalBytesOut     int64 `json:"total_bytes_out"`
}

// StopAll stops all streams
func (m *Manager) StopAll() {
	m.mu.Lock()
	defer m.mu.Unlock()

	for key, stream := range m.streams {
		stream.Close()
		delete(m.streams, key)
	}

	log.Info("All streams stopped")
}

// cleanupLoop periodically cleans up idle streams
func (m *Manager) cleanupLoop() {
	ticker := time.NewTicker(m.config.CleanupInterval)
	defer ticker.Stop()

	for range ticker.C {
		m.cleanup()
	}
}

// cleanup removes idle streams that have timed out
func (m *Manager) cleanup() {
	m.mu.Lock()
	defer m.mu.Unlock()

	now := time.Now()
	for key, stream := range m.streams {
		stream.mu.RLock()
		idle := stream.State == StreamStateIdle
		updatedAt := stream.updatedAt
		stream.mu.RUnlock()

		if idle && now.Sub(updatedAt) > m.config.StreamTimeout {
			stream.Close()
			delete(m.streams, key)
			log.Infof("Stream cleaned up: key=%s (idle timeout)", key)
		}
	}
}
