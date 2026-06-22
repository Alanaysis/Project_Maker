package hls

import (
	"fmt"
	"sync"
	"time"
)

// Segment represents an HLS media segment
type Segment struct {
	Sequence  int       // Sequence number
	Duration  float64   // Duration in seconds
	Data      []byte    // TS data
	StartTime time.Time // When segment started
	EndTime   time.Time // When segment ended
	KeyFrame  bool      // Whether this segment starts with a keyframe
}

// SegmentManager manages HLS segments for a stream
type SegmentManager struct {
	mu           sync.RWMutex
	segments     []*Segment
	maxSegments  int
	targetDuration float64
	sequence     int
	currentData  []byte
	segmentStart time.Time
	streamKey    string
}

// NewSegmentManager creates a new segment manager
func NewSegmentManager(streamKey string, maxSegments int, targetDuration float64) *SegmentManager {
	return &SegmentManager{
		segments:       make([]*Segment, 0, maxSegments),
		maxSegments:    maxSegments,
		targetDuration: targetDuration,
		streamKey:      streamKey,
		segmentStart:   time.Now(),
	}
}

// AddData adds media data to the current segment
func (m *SegmentManager) AddData(data []byte, isKeyFrame bool) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// If we have a keyframe and enough data, start a new segment
	if isKeyFrame && len(m.currentData) > 0 {
		m.finalizeSegment()
	}

	m.currentData = append(m.currentData, data...)
}

// FinalizeSegment forces the current segment to be finalized
func (m *SegmentManager) FinalizeSegment() {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.finalizeSegment()
}

// finalizeSegment creates a segment from current data (must be called with lock held)
func (m *SegmentManager) finalizeSegment() {
	if len(m.currentData) == 0 {
		return
	}

	now := time.Now()
	duration := now.Sub(m.segmentStart).Seconds()

	// Create new segment
	segment := &Segment{
		Sequence:  m.sequence,
		Duration:  duration,
		Data:      m.currentData,
		StartTime: m.segmentStart,
		EndTime:   now,
	}

	m.segments = append(m.segments, segment)
	m.sequence++

	// Remove oldest segment if we exceed max
	if len(m.segments) > m.maxSegments {
		m.segments = m.segments[1:]
	}

	// Reset for next segment
	m.currentData = nil
	m.segmentStart = now
}

// GetSegments returns all available segments
func (m *SegmentManager) GetSegments() []*Segment {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*Segment, len(m.segments))
	copy(result, m.segments)
	return result
}

// GetLatestSegments returns the latest n segments
func (m *SegmentManager) GetLatestSegments(n int) []*Segment {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if n > len(m.segments) {
		n = len(m.segments)
	}

	result := make([]*Segment, n)
	copy(result, m.segments[len(m.segments)-n:])
	return result
}

// GetSequence returns the current sequence number
func (m *SegmentManager) GetSequence() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.sequence
}

// GenerateM3U8 generates an M3U8 playlist
func (m *SegmentManager) GenerateM3U8() string {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// If no segments, return minimal playlist
	if len(m.segments) == 0 {
		return m.generateEmptyPlaylist()
	}

	// Calculate target duration
	maxDuration := 0.0
	for _, seg := range m.segments {
		if seg.Duration > maxDuration {
			maxDuration = seg.Duration
		}
	}

	// Build playlist
	playlist := "#EXTM3U\n"
	playlist += "#EXT-X-VERSION:3\n"
	playlist += fmt.Sprintf("#EXT-X-TARGETDURATION:%d\n", int(maxDuration)+1)

	// Use the sequence of the first segment
	firstSeq := m.segments[0].Sequence
	playlist += fmt.Sprintf("#EXT-X-MEDIA-SEQUENCE:%d\n", firstSeq)

	playlist += "\n"

	// Add segments
	for _, seg := range m.segments {
		playlist += fmt.Sprintf("#EXTINF:%.3f,\n", seg.Duration)
		playlist += fmt.Sprintf("segment_%d.ts\n", seg.Sequence)
	}

	return playlist
}

// generateEmptyPlaylist generates an empty playlist
func (m *SegmentManager) generateEmptyPlaylist() string {
	playlist := "#EXTM3U\n"
	playlist += "#EXT-X-VERSION:3\n"
	playlist += fmt.Sprintf("#EXT-X-TARGETDURATION:%d\n", int(m.targetDuration))
	playlist += "#EXT-X-MEDIA-SEQUENCE:0\n"
	return playlist
}

// GenerateMasterPlaylist generates a master playlist for adaptive bitrate
func GenerateMasterPlaylist(streamKey string, variants []Variant) string {
	playlist := "#EXTM3U\n"
	playlist += "#EXT-X-VERSION:3\n\n"

	for _, v := range variants {
		playlist += fmt.Sprintf("#EXT-X-STREAM-INF:BANDWIDTH=%d,RESOLUTION=%dx%d\n",
			v.Bandwidth, v.Width, v.Height)
		playlist += fmt.Sprintf("%s/%s/index.m3u8\n", streamKey, v.Name)
	}

	return playlist
}

// Variant represents a bitrate variant
type Variant struct {
	Name      string
	Bandwidth int
	Width     int
	Height    int
}
