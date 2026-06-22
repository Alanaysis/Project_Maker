package tests

import (
	"strings"
	"testing"

	"github.com/media-server/internal/hls"
)

func TestNewSegmentManager(t *testing.T) {
	sm := hls.NewSegmentManager("test-stream", 5, 6.0)

	if sm == nil {
		t.Fatal("Expected segment manager to be created")
	}
}

func TestSegmentManagerAddData(t *testing.T) {
	sm := hls.NewSegmentManager("test-stream", 5, 6.0)

	// Add some data
	sm.AddData([]byte("test data"), false)

	segments := sm.GetSegments()
	if len(segments) != 0 {
		t.Errorf("Expected 0 segments, got %d", len(segments))
	}
}

func TestSegmentManagerFinalize(t *testing.T) {
	sm := hls.NewSegmentManager("test-stream", 5, 6.0)

	// Add some data
	sm.AddData([]byte("test data"), false)

	// Finalize segment
	sm.FinalizeSegment()

	segments := sm.GetSegments()
	if len(segments) != 1 {
		t.Errorf("Expected 1 segment, got %d", len(segments))
	}

	if string(segments[0].Data) != "test data" {
		t.Errorf("Expected segment data 'test data', got '%s'", string(segments[0].Data))
	}
}

func TestSegmentManagerKeyFrame(t *testing.T) {
	sm := hls.NewSegmentManager("test-stream", 5, 6.0)

	// Add non-keyframe data
	sm.AddData([]byte("data1"), false)

	// Add keyframe data (should trigger segment creation)
	sm.AddData([]byte("data2"), true)

	segments := sm.GetSegments()
	if len(segments) != 1 {
		t.Errorf("Expected 1 segment, got %d", len(segments))
	}
}

func TestSegmentManagerMaxSegments(t *testing.T) {
	sm := hls.NewSegmentManager("test-stream", 3, 6.0)

	// Add more segments than max
	for i := 0; i < 5; i++ {
		sm.AddData([]byte("data"), false)
		sm.FinalizeSegment()
	}

	segments := sm.GetSegments()
	if len(segments) != 3 {
		t.Errorf("Expected 3 segments, got %d", len(segments))
	}
}

func TestSegmentManagerM3U8(t *testing.T) {
	sm := hls.NewSegmentManager("test-stream", 5, 6.0)

	// Add segments
	sm.AddData([]byte("data1"), false)
	sm.FinalizeSegment()

	sm.AddData([]byte("data2"), false)
	sm.FinalizeSegment()

	// Generate playlist
	playlist := sm.GenerateM3U8()

	if !strings.HasPrefix(playlist, "#EXTM3U") {
		t.Error("Expected playlist to start with #EXTM3U")
	}

	if !strings.Contains(playlist, "#EXT-X-VERSION:3") {
		t.Error("Expected playlist to contain version")
	}

	if !strings.Contains(playlist, "#EXT-X-TARGETDURATION:") {
		t.Error("Expected playlist to contain target duration")
	}

	if !strings.Contains(playlist, "#EXT-X-MEDIA-SEQUENCE:") {
		t.Error("Expected playlist to contain media sequence")
	}

	if !strings.Contains(playlist, "segment_0.ts") {
		t.Error("Expected playlist to contain segment_0.ts")
	}

	if !strings.Contains(playlist, "segment_1.ts") {
		t.Error("Expected playlist to contain segment_1.ts")
	}
}

func TestEmptyM3U8(t *testing.T) {
	sm := hls.NewSegmentManager("test-stream", 5, 6.0)

	playlist := sm.GenerateM3U8()

	if !strings.HasPrefix(playlist, "#EXTM3U") {
		t.Error("Expected playlist to start with #EXTM3U")
	}

	if strings.Contains(playlist, "#EXTINF:") {
		t.Error("Expected empty playlist to not contain segments")
	}
}

func TestGetLatestSegments(t *testing.T) {
	sm := hls.NewSegmentManager("test-stream", 5, 6.0)

	// Add 5 segments
	for i := 0; i < 5; i++ {
		sm.AddData([]byte("data"), false)
		sm.FinalizeSegment()
	}

	// Get latest 3
	segments := sm.GetLatestSegments(3)
	if len(segments) != 3 {
		t.Errorf("Expected 3 segments, got %d", len(segments))
	}

	// Should be segments 2, 3, 4
	if segments[0].Sequence != 2 {
		t.Errorf("Expected sequence 2, got %d", segments[0].Sequence)
	}
}

func TestMasterPlaylist(t *testing.T) {
	variants := []hls.Variant{
		{Name: "720p", Bandwidth: 2000000, Width: 1280, Height: 720},
		{Name: "480p", Bandwidth: 1000000, Width: 854, Height: 480},
		{Name: "360p", Bandwidth: 500000, Width: 640, Height: 360},
	}

	playlist := hls.GenerateMasterPlaylist("test-stream", variants)

	if !strings.HasPrefix(playlist, "#EXTM3U") {
		t.Error("Expected playlist to start with #EXTM3U")
	}

	if !strings.Contains(playlist, "720p") {
		t.Error("Expected playlist to contain 720p variant")
	}

	if !strings.Contains(playlist, "480p") {
		t.Error("Expected playlist to contain 480p variant")
	}

	if !strings.Contains(playlist, "360p") {
		t.Error("Expected playlist to contain 360p variant")
	}
}
