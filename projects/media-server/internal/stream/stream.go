package stream

import (
	"sync"
	"time"
)

// StreamState represents the current state of a stream
type StreamState int

const (
	StreamStateIdle       StreamState = iota // Stream is idle, no publisher
	StreamStatePublishing                    // Stream is being published
	StreamStatePlaying                       // Stream is being played
)

// String returns a human-readable representation of the stream state
func (s StreamState) String() string {
	switch s {
	case StreamStateIdle:
		return "idle"
	case StreamStatePublishing:
		return "publishing"
	case StreamStatePlaying:
		return "playing"
	default:
		return "unknown"
	}
}

// AudioConfig holds audio codec configuration
type AudioConfig struct {
	Codec       string // aac, mp3, etc.
	SampleRate  int    // 44100, 22050, etc.
	Channels    int    // 1 (mono), 2 (stereo)
	BitRate     int    // in bps
}

// VideoConfig holds video codec configuration
type VideoConfig struct {
	Codec      string // h264, h265, etc.
	Width      int    // in pixels
	Height     int    // in pixels
	FrameRate  float64
	BitRate    int // in bps
	GopSize    int // Group of Pictures size
}

// Metadata holds stream metadata
type Metadata struct {
	Width       int     `json:"width"`
	Height      int     `json:"height"`
	FrameRate   float64 `json:"frame_rate"`
	VideoBitRate int    `json:"video_bit_rate"`
	AudioBitRate int    `json:"audio_bit_rate"`
	SampleRate  int     `json:"sample_rate"`
	Channels    int     `json:"channels"`
	Codec       string  `json:"codec"`
	CreatedAt   time.Time `json:"created_at"`
}

// Stream represents a single media stream
type Stream struct {
	mu          sync.RWMutex
	ID          string
	Key         string
	State       StreamState
	Metadata    *Metadata
	AudioConfig *AudioConfig
	VideoConfig *VideoConfig

	// Publisher connection
	publisher   *Publisher

	// Subscribers (players)
	subscribers map[string]*Subscriber

	// Media data channel for broadcasting
	dataCh      chan *MediaPacket

	// Timestamps
	createdAt   time.Time
	updatedAt   time.Time
	lastKeyFrame time.Time
}

// Publisher represents a publishing client
type Publisher struct {
	ID        string
	StartTime time.Time
	BytesSent int64
}

// Subscriber represents a subscribing (playing) client
type Subscriber struct {
	ID         string
	StartTime  time.Time
	BytesRecv  int64
	Active     bool
	LastAccess time.Time
}

// MediaPacket represents a media data packet
type MediaPacket struct {
	Type      byte   // 8=audio, 9=video, 18=metadata
	Timestamp uint32 // in milliseconds
	Data      []byte
	StreamID  uint32
}

// NewStream creates a new stream with the given ID and key
func NewStream(id, key string) *Stream {
	return &Stream{
		ID:          id,
		Key:         key,
		State:       StreamStateIdle,
		subscribers: make(map[string]*Subscriber),
		dataCh:      make(chan *MediaPacket, 100),
		createdAt:   time.Now(),
		updatedAt:   time.Now(),
	}
}

// Publish sets the stream to publishing state
func (s *Stream) Publish(publisherID string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.State == StreamStatePublishing {
		return ErrStreamAlreadyPublishing
	}

	s.State = StreamStatePublishing
	s.publisher = &Publisher{
		ID:        publisherID,
		StartTime: time.Now(),
	}
	s.updatedAt = time.Now()

	return nil
}

// Unpublish sets the stream back to idle state
func (s *Stream) Unpublish() {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.State = StreamStateIdle
	s.publisher = nil
	s.updatedAt = time.Now()

	// Clear subscribers
	for _, sub := range s.subscribers {
		sub.Active = false
	}
}

// Subscribe adds a new subscriber to the stream
func (s *Stream) Subscribe(subscriberID string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.State != StreamStatePublishing && s.State != StreamStatePlaying {
		return ErrStreamNotPublishing
	}

	s.subscribers[subscriberID] = &Subscriber{
		ID:         subscriberID,
		StartTime:  time.Now(),
		Active:     true,
		LastAccess: time.Now(),
	}

	if s.State == StreamStatePublishing {
		s.State = StreamStatePlaying
	}

	s.updatedAt = time.Now()
	return nil
}

// Unsubscribe removes a subscriber from the stream
func (s *Stream) Unsubscribe(subscriberID string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	delete(s.subscribers, subscriberID)
	s.updatedAt = time.Now()
}

// GetSubscribers returns a copy of the subscriber list
func (s *Stream) GetSubscribers() map[string]*Subscriber {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make(map[string]*Subscriber, len(s.subscribers))
	for k, v := range s.subscribers {
		sub := *v
		result[k] = &sub
	}
	return result
}

// GetSubscriberCount returns the number of active subscribers
func (s *Stream) GetSubscriberCount() int {
	s.mu.RLock()
	defer s.mu.RUnlock()

	count := 0
	for _, sub := range s.subscribers {
		if sub.Active {
			count++
		}
	}
	return count
}

// UpdateMetadata updates the stream metadata
func (s *Stream) UpdateMetadata(meta *Metadata) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.Metadata = meta
	s.updatedAt = time.Now()
}

// UpdateAudioConfig updates the audio configuration
func (s *Stream) UpdateAudioConfig(config *AudioConfig) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.AudioConfig = config
	s.updatedAt = time.Now()
}

// UpdateVideoConfig updates the video configuration
func (s *Stream) UpdateVideoConfig(config *VideoConfig) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.VideoConfig = config
	s.updatedAt = time.Now()
}

// WritePacket writes a media packet to the stream
func (s *Stream) WritePacket(pkt *MediaPacket) error {
	s.mu.RLock()
	if s.State != StreamStatePublishing && s.State != StreamStatePlaying {
		s.mu.RUnlock()
		return ErrStreamNotPublishing
	}
	s.mu.RUnlock()

	select {
	case s.dataCh <- pkt:
		return nil
	default:
		return ErrBufferFull
	}
}

// ReadPacket reads a media packet from the stream (blocking)
func (s *Stream) ReadPacket() (*MediaPacket, error) {
	pkt, ok := <-s.dataCh
	if !ok {
		return nil, ErrStreamClosed
	}
	return pkt, nil
}

// GetPublisher returns the current publisher
func (s *Stream) GetPublisher() *Publisher {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if s.publisher == nil {
		return nil
	}
	pub := *s.publisher
	return &pub
}

// UpdateLastKeyFrame updates the last keyframe timestamp
func (s *Stream) UpdateLastKeyFrame() {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.lastKeyFrame = time.Now()
}

// GetLastKeyFrame returns the last keyframe timestamp
func (s *Stream) GetLastKeyFrame() time.Time {
	s.mu.RLock()
	defer s.mu.RUnlock()

	return s.lastKeyFrame
}

// IsPublishing returns true if the stream is being published
func (s *Stream) IsPublishing() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()

	return s.State == StreamStatePublishing || s.State == StreamStatePlaying
}

// Close closes the stream and cleans up resources
func (s *Stream) Close() {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.State = StreamStateIdle
	s.publisher = nil
	close(s.dataCh)
	s.updatedAt = time.Now()
}
