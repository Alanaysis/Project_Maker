package hls

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	log "github.com/sirupsen/logrus"
	"github.com/media-server/internal/stream"
)

// Server represents an HLS HTTP server
type Server struct {
	streamManager *stream.Manager
	segments      map[string]*SegmentManager
}

// NewServer creates a new HLS server
func NewServer(streamManager *stream.Manager) *Server {
	return &Server{
		streamManager: streamManager,
		segments:      make(map[string]*SegmentManager),
	}
}

// HandleHLS handles HLS requests (playlists and segments)
func (s *Server) HandleHLS(w http.ResponseWriter, r *http.Request) {
	// Parse URL: /live/<stream_key>/...
	path := strings.TrimPrefix(r.URL.Path, "/live/")
	parts := strings.Split(path, "/")

	if len(parts) < 1 {
		http.Error(w, "Invalid path", http.StatusBadRequest)
		return
	}

	streamKey := parts[0]

	// Check if requesting a segment
	if len(parts) >= 2 && strings.HasSuffix(parts[1], ".ts") {
		s.handleSegment(w, r, streamKey, parts[1])
		return
	}

	// Otherwise, serve playlist
	s.handlePlaylist(w, r, streamKey)
}

// handlePlaylist handles M3U8 playlist requests
func (s *Server) handlePlaylist(w http.ResponseWriter, r *http.Request, streamKey string) {
	// Get stream
 strm, err := s.streamManager.GetStream(streamKey)
	if err != nil {
		http.Error(w, "Stream not found", http.StatusNotFound)
		return
	}

	// Check if stream is publishing
	if !strm.IsPublishing() {
		http.Error(w, "Stream not active", http.StatusServiceUnavailable)
		return
	}

	// Get or create segment manager
	sm := s.getOrCreateSegmentManager(streamKey)

	// Generate playlist
	playlist := sm.GenerateM3U8()

	// Set headers
	w.Header().Set("Content-Type", "application/vnd.apple.mpegurl")
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	// Write playlist
	w.Write([]byte(playlist))
}

// handleSegment handles TS segment requests
func (s *Server) handleSegment(w http.ResponseWriter, r *http.Request, streamKey string, segmentName string) {
	// Get segment manager
	sm, exists := s.segments[streamKey]
	if !exists {
		http.Error(w, "Stream not found", http.StatusNotFound)
		return
	}

	// Parse segment name (segment_0.ts)
	var seq int
	_, err := fmt.Sscanf(segmentName, "segment_%d.ts", &seq)
	if err != nil {
		http.Error(w, "Invalid segment name", http.StatusBadRequest)
		return
	}

	// Find segment
	segments := sm.GetSegments()
	for _, seg := range segments {
		if seg.Sequence == seq {
			// Set headers
			w.Header().Set("Content-Type", "video/mp2t")
			w.Header().Set("Cache-Control", "max-age=3600")
			w.Header().Set("Access-Control-Allow-Origin", "*")

			// Write segment data
			w.Write(seg.Data)
			return
		}
	}

	http.Error(w, "Segment not found", http.StatusNotFound)
}

// HandleStreamList handles requests for active streams
func (s *Server) HandleStreamList(w http.ResponseWriter, r *http.Request) {
	streams := s.streamManager.GetStreamList()

	// Set headers
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	// Encode response
	if err := json.NewEncoder(w).Encode(streams); err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}
}

// getOrCreateSegmentManager gets or creates a segment manager for a stream
func (s *Server) getOrCreateSegmentManager(streamKey string) *SegmentManager {
	if sm, exists := s.segments[streamKey]; exists {
		return sm
	}

	sm := NewSegmentManager(streamKey, 5, 6.0)
	s.segments[streamKey] = sm
	return sm
}

// StartSegmentWriter starts writing segments from the stream
func (s *Server) StartSegmentWriter(streamKey string) {
	go func() {
		// Get stream
		strm, err := s.streamManager.GetStream(streamKey)
		if err != nil {
			log.Errorf("Failed to get stream for segment writer: %v", err)
			return
		}

		// Get segment manager
		sm := s.getOrCreateSegmentManager(streamKey)

		// Read packets and write segments
		for {
			pkt, err := strm.ReadPacket()
			if err != nil {
				log.Debugf("Stream ended: %v", err)
				return
			}

			// Check for keyframe (for segment splitting)
			isKeyFrame := false
			if pkt.Type == 9 && len(pkt.Data) > 0 { // Video
				frameType := (pkt.Data[0] >> 4) & 0x0F
				if frameType == 1 {
					isKeyFrame = true
				}
			}

			// Add data to segment manager
			sm.AddData(pkt.Data, isKeyFrame)
		}
	}()

	// Start periodic segment finalization
	go func() {
		sm := s.getOrCreateSegmentManager(streamKey)
		ticker := time.NewTicker(6 * time.Second)
		defer ticker.Stop()

		for range ticker.C {
			sm.FinalizeSegment()
		}
	}()
}

// CleanupSegments cleans up segment managers for stopped streams
func (s *Server) CleanupSegments() {
	for key, sm := range s.segments {
		segments := sm.GetSegments()
		if len(segments) == 0 {
			delete(s.segments, key)
		}
	}
}
