package integration

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"tsdb/src"
)

// TestFullWorkflow tests the complete time series workflow:
// create series -> write data -> query -> compress -> aggregate -> persist -> load
func TestFullWorkflow(t *testing.T) {
	storage := tsdb.NewStorage()

	// 1. Create series
	storage.CreateSeries("test.cpu", "CPU Usage")
	storage.CreateSeries("test.mem", "Memory Usage")

	// 2. Write data
	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	cpuPoints := make([]tsdb.Point, 60)
	memPoints := make([]tsdb.Point, 60)
	for i := 0; i < 60; i++ {
		ts := start.Add(time.Duration(i) * time.Minute)
		cpuPoints[i] = tsdb.Point{
			Timestamp: ts.UnixNano(),
			Value:     50 + float64(i)*0.5,
			Tags:      map[string]string{"host": "server1", "metric": "cpu"},
		}
		memPoints[i] = tsdb.Point{
			Timestamp: ts.UnixNano(),
			Value:     2048 + float64(i)*10,
			Tags:      map[string]string{"host": "server1", "metric": "mem"},
		}
	}
	storage.WritePoints("test.cpu", cpuPoints)
	storage.WritePoints("test.mem", memPoints)

	// 3. Query all
	cpuAll, _ := storage.QueryAll("test.cpu")
	if len(cpuAll) != 60 {
		t.Errorf("Expected 60 cpu points, got %d", len(cpuAll))
	}

	// 4. Query range
	rangePts, _ := storage.QueryRange("test.cpu", start, start.Add(30*time.Minute))
	if len(rangePts) == 0 {
		t.Error("Expected points in range, got none")
	}

	// 5. Downsample
	downsampled, _ := storage.Downsample("test.cpu", tsdb.AggAvg, 15*time.Minute, start, start.Add(time.Hour))
	if len(downsampled.Results) == 0 {
		t.Error("Expected downsample results, got none")
	}

	// 6. Persist
	tmpDir := t.TempDir()
	persistPath := filepath.Join(tmpDir, "test.bin")
	if err := storage.Persist(persistPath); err != nil {
		t.Fatalf("Persist failed: %v", err)
	}

	// Verify file exists
	if _, err := os.Stat(persistPath); os.IsNotExist(err) {
		t.Fatal("Persist file was not created")
	}

	// 7. Load
	storage2 := tsdb.NewStorage()
	if err := storage2.Load(persistPath); err != nil {
		t.Fatalf("Load failed: %v", err)
	}

	// 8. Verify loaded data
	loaded, _ := storage2.QueryAll("test.cpu")
	if len(loaded) != 60 {
		t.Errorf("Expected 60 loaded cpu points, got %d", len(loaded))
	}

	fmt.Printf("Full workflow: %d points written, %d queried, %d downsampled, %d persisted, %d loaded\n",
		len(cpuPoints), len(cpuAll), len(downsampled.Results), len(loaded), len(loaded))
}

// TestCompressionEffectiveness tests that compression produces valid results
func TestCompressionEffectiveness(t *testing.T) {
	storage := tsdb.NewStorage()
	storage.CreateSeries("comp.test", "Compression Test")

	// Create data with regular intervals (good for delta encoding)
	points := make([]tsdb.Point, 100)
	baseTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	for i := 0; i < 100; i++ {
		points[i] = tsdb.Point{
			Timestamp: baseTime.Add(time.Duration(i*10) * time.Second).UnixNano(),
			Value:     float64(100 + i),
		}
	}
	storage.WritePoints("comp.test", points)

	// Check delta stats
	pts, _ := storage.QueryAll("comp.test")
	deltaStats := tsdb.ComputeDeltaStats(pts)

	if deltaStats.UniqueDeltas != 2 {
		t.Errorf("Expected 2 unique deltas (base + constant), got %d", deltaStats.UniqueDeltas)
	}

	fmt.Printf("Compression: %d points, %d unique deltas, ratio %.2fx\n",
		len(pts), deltaStats.UniqueDeltas, deltaStats.CompressionRatio)
}

// TestSeriesManagerWorkflow tests series management operations
func TestSeriesManagerWorkflow(t *testing.T) {
	storage := tsdb.NewStorage()
	manager := tsdb.NewSeriesManager(storage)

	// Register series
	manager.RegisterSeries("s1", "Series 1")
	manager.RegisterSeries("s2", "Series 2")
	manager.RegisterSeries("s3", "Series 3")

	// List series
	ids := manager.ListSeries()
	if len(ids) != 3 {
		t.Errorf("Expected 3 series, got %d", len(ids))
	}

	// Batch write
	batch := make(map[string][]tsdb.Point)
	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	for i := 0; i < 3; i++ {
		id := fmt.Sprintf("s%d", i+1)
		batch[id] = []tsdb.Point{
			{Timestamp: start.UnixNano(), Value: float64(i * 10)},
		}
	}
	if err := manager.WriteBatch(batch); err != nil {
		t.Fatalf("WriteBatch failed: %v", err)
	}

	// Query across series
	results, err := manager.QueryAcrossSeries([]string{"s1", "s2", "s3"}, start, start.Add(time.Hour))
	if err != nil {
		t.Fatalf("QueryAcrossSeries failed: %v", err)
	}
	if len(results) != 3 {
		t.Errorf("Expected 3 results, got %d", len(results))
	}

	// Get individual series
	ser, err := manager.GetSeries("s1")
	if err != nil {
		t.Fatalf("GetSeries failed: %v", err)
	}
	if ser.ID != "s1" {
		t.Errorf("Expected ID s1, got %s", ser.ID)
	}
}

// TestEdgeCases tests edge cases and error handling
func TestEdgeCases(t *testing.T) {
	storage := tsdb.NewStorage()

	// Write to nonexistent series
	err := storage.WritePoints("nonexistent", []tsdb.Point{{Timestamp: 100, Value: 1.0}})
	if err == nil {
		t.Error("Expected error writing to nonexistent series")
	}

	// Query nonexistent series
	_, err = storage.QueryRange("nonexistent", time.Time{}, time.Now())
	if err == nil {
		t.Error("Expected error querying nonexistent series")
	}

	// Downsample nonexistent series
	_, err = storage.Downsample("nonexistent", tsdb.AggAvg, time.Minute, time.Time{}, time.Now())
	if err == nil {
		t.Error("Expected error downsampling nonexistent series")
	}

	// Empty series operations
	storage.CreateSeries("empty", "Empty Series")
	pts, _ := storage.QueryAll("empty")
	if len(pts) != 0 {
		t.Errorf("Expected 0 points in empty series, got %d", len(pts))
	}

	// Query with no overlap
	pts, _ = storage.QueryRange("empty", time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC), time.Date(2024, 1, 2, 0, 0, 0, 0, time.UTC))
	if pts != nil {
		t.Error("Expected nil for no-overlap query")
	}
}
