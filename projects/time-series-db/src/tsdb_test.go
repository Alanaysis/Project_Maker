package tsdb

import (
	"math"
	"testing"
	"time"
)

func TestDeltaEncodeDecode(t *testing.T) {
	original := []int64{1000, 1010, 1020, 1035, 1050}
	deltas := DeltaEncode(original)

	decoded := DeltaDecode(deltas)

	for i := range original {
		if decoded[i] != original[i] {
			t.Errorf("Delta decode mismatch at %d: got %d, want %d", i, decoded[i], original[i])
		}
	}

	// Test empty
	if got := DeltaEncode(nil); got != nil {
		t.Errorf("DeltaEncode(nil) = %v, want nil", got)
	}
	if got := DeltaDecode(nil); got != nil {
		t.Errorf("DeltaDecode(nil) = %v, want nil", got)
	}
}

func TestDeltaOfDeltaEncodeDecode(t *testing.T) {
	// Regular intervals should produce all zeros in delta-of-delta
	original := []int64{1000, 1010, 1020, 1030, 1040}
	dod := DeltaOfDeltaEncode(original)
	decoded := DeltaOfDeltaDecode(dod)

	for i := range original {
		if decoded[i] != original[i] {
			t.Errorf("DeltaOfDelta decode mismatch at %d: got %d, want %d", i, decoded[i], original[i])
		}
	}
}

func TestRLEEncodeDecode(t *testing.T) {
	original := []float64{1.0, 1.0, 1.0, 2.5, 2.5, 3.0, 3.0, 3.0, 3.0}
	encoded := RLEEncode(original)
	decoded := RLEDecode(encoded)

	if len(decoded) != len(original) {
		t.Errorf("RLE decode length mismatch: got %d, want %d", len(decoded), len(original))
	}

	for i := range original {
		if math.Abs(decoded[i]-original[i]) > 0.0001 {
			t.Errorf("RLE decode mismatch at %d: got %f, want %f", i, decoded[i], original[i])
		}
	}

	// Test empty
	if got := RLEEncode(nil); got != nil {
		t.Errorf("RLEEncode(nil) = %v, want nil", got)
	}
	if got := RLEDecode(nil); got != nil {
		t.Errorf("RLEDecode(nil) = %v, want nil", got)
	}
}

func TestCompressionRatio(t *testing.T) {
	// Original is larger than encoded
	ratio := CompressionRatio(100, 50)
	if ratio != 2.0 {
		t.Errorf("CompressionRatio(100, 50) = %f, want 2.0", ratio)
	}

	// Division by zero protection
	ratio = CompressionRatio(100, 0)
	if ratio != 0 {
		t.Errorf("CompressionRatio(100, 0) = %f, want 0", ratio)
	}
}

func TestTimeIndexFindRange(t *testing.T) {
	points := []Point{
		{Timestamp: 100, Value: 1.0},
		{Timestamp: 200, Value: 2.0},
		{Timestamp: 300, Value: 3.0},
		{Timestamp: 400, Value: 4.0},
		{Timestamp: 500, Value: 5.0},
	}

	ser := &Series{
		ID:     "test",
		Name:   "test",
		Points: points,
		MinTime: 100,
		MaxTime: 500,
	}
	idx := NewTimeIndex(ser)

	start, end := idx.FindRange(150, 350)
	if start != 1 {
		t.Errorf("FindRange start = %d, want 1", start)
	}
	if end != 3 {
		t.Errorf("FindRange end = %d, want 3", end)
	}
}

func TestTimeIndexFindBeforeAfter(t *testing.T) {
	points := []Point{
		{Timestamp: 100, Value: 1.0},
		{Timestamp: 200, Value: 2.0},
		{Timestamp: 300, Value: 3.0},
	}

	ser := &Series{
		ID:     "test",
		Name:   "test",
		Points: points,
		MinTime: 100,
		MaxTime: 300,
	}
	idx := NewTimeIndex(ser)

	// FindBefore
	before := idx.FindBefore(250)
	if before != 1 {
		t.Errorf("FindBefore(250) = %d, want 1", before)
	}

	// FindAfter
	after := idx.FindAfter(150)
	if after != 1 {
		t.Errorf("FindAfter(150) = %d, want 1", after)
	}
}

func TestStorageCreateAndWrite(t *testing.T) {
	storage := NewStorage()
	ser := storage.CreateSeries("cpu.temp", "CPU Temperature")

	if ser.ID != "cpu.temp" {
		t.Errorf("Series ID = %s, want cpu.temp", ser.ID)
	}

	points := []Point{
		{Timestamp: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC).UnixNano(), Value: 45.2},
		{Timestamp: time.Date(2024, 1, 1, 0, 1, 0, 0, time.UTC).UnixNano(), Value: 46.1},
		{Timestamp: time.Date(2024, 1, 1, 0, 2, 0, 0, time.UTC).UnixNano(), Value: 47.3},
	}

	if err := storage.WritePoints("cpu.temp", points); err != nil {
		t.Fatalf("WritePoints failed: %v", err)
	}

	// Verify points were stored
	ser, ok := storage.series["cpu.temp"]
	if !ok {
		t.Fatal("Series not found after write")
	}
	if len(ser.Points) != 3 {
		t.Errorf("Points count = %d, want 3", len(ser.Points))
	}
}

func TestStorageQueryRange(t *testing.T) {
	storage := NewStorage()
	storage.CreateSeries("cpu.temp", "CPU Temperature")

	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	end := time.Date(2024, 1, 1, 0, 5, 0, 0, time.UTC)

	points := []Point{
		{Timestamp: start.Add(0 * time.Minute).UnixNano(), Value: 45.0},
		{Timestamp: start.Add(1 * time.Minute).UnixNano(), Value: 46.0},
		{Timestamp: start.Add(2 * time.Minute).UnixNano(), Value: 47.0},
		{Timestamp: start.Add(3 * time.Minute).UnixNano(), Value: 48.0},
		{Timestamp: start.Add(4 * time.Minute).UnixNano(), Value: 49.0},
	}

	storage.WritePoints("cpu.temp", points)

	// Query full range
	result, err := storage.QueryRange("cpu.temp", start, end)
	if err != nil {
		t.Fatalf("QueryRange failed: %v", err)
	}
	if len(result) != 5 {
		t.Errorf("QueryRange full = %d points, want 5", len(result))
	}

	// Query partial range
	subStart := start.Add(1 * time.Minute)
	subEnd := start.Add(3 * time.Minute)
	result, err = storage.QueryRange("cpu.temp", subStart, subEnd)
	if err != nil {
		t.Fatalf("QueryRange partial failed: %v", err)
	}
	if len(result) != 3 {
		t.Errorf("QueryRange partial = %d points, want 3", len(result))
	}
}

func TestStorageQueryNonexistentSeries(t *testing.T) {
	storage := NewStorage()
	_, err := storage.QueryRange("nonexistent", time.Time{}, time.Now())
	if err == nil {
		t.Error("Expected error for nonexistent series")
	}
}

func TestStorageDownsample(t *testing.T) {
	storage := NewStorage()
	storage.CreateSeries("cpu.temp", "CPU Temperature")

	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	end := start.Add(10 * time.Minute)

	// Create 10 data points, 1 per minute
	points := make([]Point, 10)
	for i := 0; i < 10; i++ {
		points[i] = Point{
			Timestamp: start.Add(time.Duration(i) * time.Minute).UnixNano(),
			Value:     float64(40 + i),
			Tags:      map[string]string{"host": "server1"},
		}
	}
	storage.WritePoints("cpu.temp", points)

	// Downsample with 5-minute intervals (2 buckets)
	result, err := storage.Downsample("cpu.temp", AggAvg, 5*time.Minute, start, end)
	if err != nil {
		t.Fatalf("Downsample failed: %v", err)
	}

	if len(result.Results) == 0 {
		t.Error("Downsample returned no results")
	}
}

func TestStorageDownsampleAggregations(t *testing.T) {
	storage := NewStorage()
	storage.CreateSeries("test", "test")

	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	end := start.Add(10 * time.Minute)

	points := make([]Point, 10)
	for i := 0; i < 10; i++ {
		points[i] = Point{
			Timestamp: start.Add(time.Duration(i) * time.Minute).UnixNano(),
			Value:     float64(10 + i*5),
		}
	}
	storage.WritePoints("test", points)

	aggTypes := []AggregationType{AggAvg, AggMin, AggMax, AggSum}
	for _, agg := range aggTypes {
		result, err := storage.Downsample("test", agg, 5*time.Minute, start, end)
		if err != nil {
			t.Fatalf("Downsample %s failed: %v", agg, err)
		}
		if len(result.Results) == 0 {
			t.Errorf("Downsample %s returned no results", agg)
		}
	}
}

func TestStorageByTag(t *testing.T) {
	storage := NewStorage()
	storage.CreateSeries("cpu.temp.host1", "CPU Temp Host 1")
	storage.CreateSeries("cpu.temp.host2", "CPU Temp Host 2")

	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)

	points1 := []Point{
		{Timestamp: start.UnixNano(), Value: 45.0, Tags: map[string]string{"host": "host1", "region": "us-east"}},
	}
	points2 := []Point{
		{Timestamp: start.UnixNano(), Value: 50.0, Tags: map[string]string{"host": "host2", "region": "us-west"}},
	}

	storage.WritePoints("cpu.temp.host1", points1)
	storage.WritePoints("cpu.temp.host2", points2)

	matches := storage.QueryByTag("host", "host1")
	if len(matches) != 1 {
		t.Errorf("QueryByTag host=host1 = %d matches, want 1", len(matches))
	}
}

func TestDeltaStats(t *testing.T) {
	points := []Point{
		{Timestamp: 1000, Value: 1.0},
		{Timestamp: 1010, Value: 2.0},
		{Timestamp: 1020, Value: 3.0},
		{Timestamp: 1030, Value: 4.0},
	}

	stats := ComputeDeltaStats(points)
	if stats == nil {
		t.Fatal("ComputeDeltaStats returned nil")
	}
	// First delta is the base (1000), rest are 10
	if stats.UniqueDeltas != 2 {
		t.Errorf("UniqueDeltas = %d, want 2 (base 1000 + delta 10)", stats.UniqueDeltas)
	}
	if stats.MaxDelta != 1000 {
		t.Errorf("MaxDelta = %d, want 1000 (base value)", stats.MaxDelta)
	}
	if stats.MinDelta != 10 {
		t.Errorf("MinDelta = %d, want 10", stats.MinDelta)
	}
}

func TestValueStats(t *testing.T) {
	points := []Point{
		{Timestamp: 1000, Value: 5.0},
		{Timestamp: 1010, Value: 5.0},
		{Timestamp: 1020, Value: 5.0},
		{Timestamp: 1030, Value: 5.0},
	}

	stats := ComputeValueStats(points)
	if stats == nil {
		t.Fatal("ComputeValueStats returned nil")
	}
	if stats.UniqueValues != 1 {
		t.Errorf("UniqueValues = %d, want 1 (all values are 5)", stats.UniqueValues)
	}
}

func TestFormatBytes(t *testing.T) {
	tests := []struct {
		input    int
		expected string
	}{
		{500, "500 B"},
		{1024, "1.0 KB"},
		{1024 * 1024, "1.0 MB"},
	}

	for _, tt := range tests {
		result := FormatBytes(tt.input)
		if result != tt.expected {
			t.Errorf("FormatBytes(%d) = %s, want %s", tt.input, result, tt.expected)
		}
	}
}

func TestFormatFloat(t *testing.T) {
	tests := []struct {
		input    float64
		expected string
	}{
		{0.0001, "1.000000e-04"},
		{1500.0, "1500.00"},
		{3.14159, "3.1416"},
	}

	for _, tt := range tests {
		result := FormatFloat(tt.input)
		if result != tt.expected {
			t.Errorf("FormatFloat(%f) = %s, want %s", tt.input, result, tt.expected)
		}
	}
}

func TestPersistAndLoad(t *testing.T) {
	storage := NewStorage()
	storage.CreateSeries("test.series", "Test Series")

	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	points := []Point{
		{Timestamp: start.UnixNano(), Value: 10.5, Tags: map[string]string{"host": "server1"}},
		{Timestamp: start.Add(time.Minute).UnixNano(), Value: 11.2, Tags: map[string]string{"host": "server1"}},
		{Timestamp: start.Add(2 * time.Minute).UnixNano(), Value: 12.0, Tags: map[string]string{"host": "server1"}},
	}
	storage.WritePoints("test.series", points)

	// Persist
	tmpFile := "/tmp/tsdb-test-persist.bin"
	if err := storage.Persist(tmpFile); err != nil {
		t.Fatalf("Persist failed: %v", err)
	}

	// Load into new storage
	storage2 := NewStorage()
	if err := storage2.Load(tmpFile); err != nil {
		t.Fatalf("Load failed: %v", err)
	}

	// Verify loaded data
	pts, err := storage2.QueryAll("test.series")
	if err != nil {
		t.Fatalf("QueryAll after load failed: %v", err)
	}
	if len(pts) != 3 {
		t.Errorf("Loaded points count = %d, want 3", len(pts))
	}
}

func TestBlockCompressionDecompression(t *testing.T) {
	points := []Point{
		{Timestamp: 1000, Value: 1.0},
		{Timestamp: 1010, Value: 2.0},
		{Timestamp: 1020, Value: 3.0},
		{Timestamp: 1030, Value: 4.0},
	}

	block := CompressBlock(points)
	decoded := DecompressBlock(block, block.BaseTime, block.BaseValue)

	if len(decoded) != len(points) {
		t.Errorf("Decompressed count = %d, want %d", len(decoded), len(points))
	}
}

func TestBinaryBlockEncodeDecode(t *testing.T) {
	points := []Point{
		{Timestamp: 1000, Value: 1.0},
		{Timestamp: 1010, Value: 2.0},
		{Timestamp: 1020, Value: 3.0},
	}

	block := CompressBlock(points)
	encoded := EncodeBlockToBytes(block)
	decoded, err := DecodeBlockFromBytes(encoded)
	if err != nil {
		t.Fatalf("DecodeBlockFromBytes failed: %v", err)
	}

	if decoded.BaseTime != block.BaseTime {
		t.Errorf("BaseTime mismatch: got %d, want %d", decoded.BaseTime, block.BaseTime)
	}
}

func TestStorageWritePointsSorted(t *testing.T) {
	storage := NewStorage()
	storage.CreateSeries("test", "test")

	// Write out of order
	points := []Point{
		{Timestamp: 300, Value: 3.0},
		{Timestamp: 100, Value: 1.0},
		{Timestamp: 200, Value: 2.0},
	}
	storage.WritePoints("test", points)

	pts, _ := storage.QueryAll("test")
	for i := 1; i < len(pts); i++ {
		if pts[i].Timestamp < pts[i-1].Timestamp {
			t.Errorf("Points not sorted at index %d", i)
		}
	}
}

func TestSeriesManager(t *testing.T) {
	storage := NewStorage()
	manager := NewSeriesManager(storage)

	manager.RegisterSeries("s1", "Series 1")
	manager.RegisterSeries("s2", "Series 2")

	ids := manager.ListSeries()
	if len(ids) != 2 {
		t.Errorf("ListSeries = %d, want 2", len(ids))
	}

	// Write batch
	batch := map[string][]Point{
		"s1": {{Timestamp: 100, Value: 1.0}},
		"s2": {{Timestamp: 200, Value: 2.0}},
	}
	if err := manager.WriteBatch(batch); err != nil {
		t.Fatalf("WriteBatch failed: %v", err)
	}

	// Query across series
	start := time.Unix(0, 0)
	end := time.Unix(0, 1000)
	result, err := manager.QueryAcrossSeries([]string{"s1", "s2"}, start, end)
	if err != nil {
		t.Fatalf("QueryAcrossSeries failed: %v", err)
	}
	if len(result) != 2 {
		t.Errorf("QueryAcrossSeries = %d, want 2", len(result))
	}
}
