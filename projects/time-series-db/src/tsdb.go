// Package tsdb implements a simple time series database for learning purposes.
//
// Time Series Database Learning Project
// =====================================
//
// Time series data is data points indexed by time. Unlike traditional databases,
// time series databases optimize for:
//
//   - High write throughput (sensor data, metrics, logs)
//   - Efficient range queries (time-based filtering)
//   - Data compression (correlated values over time)
//   - Downsampling and aggregation (avg, min, max, sum over intervals)
//
// Core Data Flow:
//   Data Write -> Time Index -> Compressed Storage -> Aggregation Query
//   数据写入 -> 时间索引 -> 压缩存储 -> 聚合查询
//
// Key Concepts:
//   1. Series: A named collection of time-ordered data points with shared tags
//   2. Time Index: B-tree or sorted structure for O(log n) timestamp lookups
//   3. Delta Encoding: Store differences between consecutive timestamps
//   4. Delta-of-Delta: Store differences of differences (great for regular intervals)
//   5. RLE (Run-Length Encoding): Compress repeated values
package tsdb

import (
	"bufio"
	"encoding/binary"
	"fmt"
	"math"
	"os"
	"sort"
	"sync"
	"time"
)

// ---------- Data Model ----------

// Point represents a single time series data point.
type Point struct {
	Timestamp int64   // Unix nanosecond timestamp
	Value     float64 // Numeric value
	Tags      map[string]string // Optional key-value tags for labeling
}

// Series represents a named collection of time-ordered data points.
type Series struct {
	ID       string      // Unique series identifier (e.g., "cpu.usage.host1")
	Name     string      // Human-readable name
	Points   []Point     // All data points, kept sorted by timestamp
	MinTime  int64       // Earliest timestamp for quick range checks
	MaxTime  int64       // Latest timestamp for quick range checks
	TagKeys  []string    // All unique tag keys in this series
}

// ---------- Sorted Time Index ----------

// TimeIndex provides efficient timestamp-based lookups within a series.
// It maintains a sorted index of (timestamp -> point index) pairs.
type TimeIndex struct {
	timestamps []int64 // Sorted timestamps
	pointIdx   []int   // Corresponding point array indices
}

// NewTimeIndex builds a time index from a series.
func NewTimeIndex(s *Series) *TimeIndex {
	idx := &TimeIndex{
		timestamps: make([]int64, len(s.Points)),
		pointIdx:   make([]int, len(s.Points)),
	}
	for i := range s.Points {
		idx.timestamps[i] = s.Points[i].Timestamp
		idx.pointIdx[i] = i
	}
	return idx
}

// FindRange returns indices into the points array for timestamps in [start, end].
// Uses binary search for O(log n) range lookup.
func (ti *TimeIndex) FindRange(start, end int64) (int, int) {
	left := sort.Search(len(ti.timestamps), func(i int) bool {
		return ti.timestamps[i] >= start
	})
	right := sort.Search(len(ti.timestamps), func(i int) bool {
		return ti.timestamps[i] > end
	})
	return left, right
}

// FindBefore returns the index of the latest point with timestamp <= ts.
func (ti *TimeIndex) FindBefore(ts int64) int {
	i := sort.Search(len(ti.timestamps), func(i int) bool {
		return ti.timestamps[i] > ts
	})
	return i - 1
}

// FindAfter returns the index of the earliest point with timestamp >= ts.
func (ti *TimeIndex) FindAfter(ts int64) int {
	return sort.Search(len(ti.timestamps), func(i int) bool {
		return ti.timestamps[i] >= ts
	})
}

// ---------- Compression: Delta Encoding ----------

// DeltaEncode encodes a sequence of int64 values using delta encoding.
// Instead of storing full timestamps, we store the difference between
// consecutive values. This is effective because timestamps are usually
// close together in time series data.
//
// Example:
//   Original:  [1000, 1010, 1020, 1035]
//   Deltas:     [1000,   10,   10,   15]
//
// The first value is stored as-is (the base), then all subsequent values
// are the delta from the previous one.
func DeltaEncode(values []int64) []int64 {
	if len(values) == 0 {
		return nil
	}
	deltas := make([]int64, len(values))
	deltas[0] = values[0] // Base value
	for i := 1; i < len(values); i++ {
		deltas[i] = values[i] - values[i-1]
	}
	return deltas
}

// DeltaDecode reverses delta encoding.
func DeltaDecode(deltas []int64) []int64 {
	if len(deltas) == 0 {
		return nil
	}
	values := make([]int64, len(deltas))
	values[0] = deltas[0]
	for i := 1; i < len(deltas); i++ {
		values[i] = values[i-1] + deltas[i]
	}
	return values
}

// ---------- Compression: Delta-of-Delta Encoding ----------

// DeltaOfDeltaEncode encodes timestamps for data with regular intervals.
// When data points are at regular intervals (e.g., every 10 seconds),
// the deltas themselves are nearly constant, allowing further compression.
//
// Example (10-second intervals):
//   Original:  [1000, 1010, 1020, 1030, 1040]
//   Deltas:     [1000,   10,   10,   10,   10]
//   D-of-D:     [1000,   10,    0,    0,    0]
//
// The second-level deltas are all 0, which compresses extremely well.
func DeltaOfDeltaEncode(values []int64) []int64 {
	if len(values) == 0 {
		return nil
	}
	deltas := DeltaEncode(values)
	return DeltaEncode(deltas)
}

// DeltaOfDeltaDecode reverses delta-of-delta encoding.
func DeltaOfDeltaDecode(dod []int64) []int64 {
	deltas := DeltaDecode(dod)
	return DeltaDecode(deltas)
}

// ---------- Compression: RLE for Values ----------

// RLEEncode compresses a float64 slice using Run-Length Encoding.
// RLE is effective when values repeat (e.g., a constant sensor reading).
// Each run is stored as (value, count) pair.
//
// Example:
//   Original:  [1.0, 1.0, 1.0, 2.5, 2.5, 3.0]
//   RLE:       [1.0, 3, 2.5, 2, 3.0, 1]
func RLEEncode(values []float64) []interface{} {
	if len(values) == 0 {
		return nil
	}
	var encoded []interface{}
	runVal := values[0]
	runCount := 1
	for i := 1; i < len(values); i++ {
		if values[i] == runVal {
			runCount++
		} else {
			encoded = append(encoded, runVal, runCount)
			runVal = values[i]
			runCount = 1
		}
	}
	encoded = append(encoded, runVal, runCount)
	return encoded
}

// RLEDecode reverses RLE encoding.
func RLEDecode(encoded []interface{}) []float64 {
	if len(encoded) == 0 {
		return nil
	}
	var decoded []float64
	for i := 0; i < len(encoded); i += 2 {
		val := encoded[i].(float64)
		count := encoded[i+1].(int)
		for j := 0; j < count; j++ {
			decoded = append(decoded, val)
		}
	}
	return decoded
}

// CompressionRatio calculates the compression ratio of encoded data.
// A ratio > 1 means the original was larger; < 1 means compression made it smaller.
func CompressionRatio(originalLen, encodedLen int) float64 {
	if encodedLen == 0 {
		return 0
	}
	return float64(originalLen) / float64(encodedLen)
}

// ---------- Chunked Data Block ----------

// DataBlock represents a compressed chunk of a series' data.
type DataBlock struct {
	BaseTime   int64         // Base timestamp for delta encoding
	BaseValue  float64       // Base value for RLE
	Timestamps []int64       // Compressed timestamps (delta-encoded)
	Values     []interface{} // Compressed values (RLE)
	Count      int           // Number of original data points in this block
}

// NewDataBlock creates a compressed block from raw points.
func NewDataBlock(points []Point) *DataBlock {
	if len(points) == 0 {
		return nil
	}
	ts := make([]int64, len(points))
	vals := make([]float64, len(points))
	for i, p := range points {
		ts[i] = p.Timestamp
		vals[i] = p.Value
	}
	return &DataBlock{
		BaseTime:   ts[0],
		BaseValue:  vals[0],
		Timestamps: DeltaEncode(ts),
		Values:     RLEEncode(vals),
		Count:      len(points),
	}
}

// ---------- In-Memory Storage ----------

// Storage is an in-memory time series storage engine.
type Storage struct {
	mu      sync.RWMutex
	series  map[string]*Series // series ID -> series data
	indexes map[string]*TimeIndex
	blocks  map[string][]*DataBlock // series ID -> blocks
}

// NewStorage creates a new in-memory storage.
func NewStorage() *Storage {
	return &Storage{
		series:  make(map[string]*Series),
		indexes: make(map[string]*TimeIndex),
		blocks:  make(map[string][]*DataBlock),
	}
}

// CreateSeries registers a new time series.
func (s *Storage) CreateSeries(id, name string) *Series {
	s.mu.Lock()
	defer s.mu.Unlock()
	ser := &Series{
		ID:     id,
		Name:   name,
		Points: make([]Point, 0),
	}
	s.series[id] = ser
	s.indexes[id] = NewTimeIndex(ser)
	s.blocks[id] = make([]*DataBlock, 0)
	return ser
}

// WritePoints adds data points to a series.
// Points are kept sorted by timestamp.
func (s *Storage) WritePoints(id string, points []Point) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	ser, ok := s.series[id]
	if !ok {
		return fmt.Errorf("series %q not found", id)
	}

	ser.Points = append(ser.Points, points...)
	sort.Slice(ser.Points, func(i, j int) bool {
		return ser.Points[i].Timestamp < ser.Points[j].Timestamp
	})

	// Update min/max time
	ser.MinTime = ser.Points[0].Timestamp
	ser.MaxTime = ser.Points[len(ser.Points)-1].Timestamp

	// Rebuild index
	s.indexes[id] = NewTimeIndex(ser)

	// Create a new block for this batch
	block := NewDataBlock(points)
	s.blocks[id] = append(s.blocks[id], block)

	return nil
}

// QueryRange returns points within a time range.
func (s *Storage) QueryRange(id string, start, end time.Time) ([]Point, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	ser, ok := s.series[id]
	if !ok {
		return nil, fmt.Errorf("series %q not found", id)
	}

	startTs := start.UnixNano()
	endTs := end.UnixNano()

	// Quick check if range overlaps with series time span
	if endTs < ser.MinTime || startTs > ser.MaxTime {
		return nil, nil
	}

	_, idx := s.indexes[id].FindRange(startTs, endTs)
	result := make([]Point, 0, idx)
	for i := 0; i < idx; i++ {
		if ser.Points[i].Timestamp >= startTs && ser.Points[i].Timestamp <= endTs {
			result = append(result, ser.Points[i])
		}
	}
	return result, nil
}

// QueryAll returns all points in a series.
func (s *Storage) QueryAll(id string) ([]Point, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	ser, ok := s.series[id]
	if !ok {
		return nil, fmt.Errorf("series %q not found", id)
	}
	return ser.Points, nil
}

// ---------- Aggregation Queries ----------

// AggregationType defines the type of aggregation operation.
type AggregationType string

const (
	AggAvg AggregationType = "avg"
	AggMin AggregationType = "min"
	AggMax AggregationType = "max"
	AggSum AggregationType = "sum"
)

// DownsampleResult holds the result of a downsampling query.
type DownsampleResult struct {
	AggType  AggregationType
	Interval time.Duration
	Results  []struct {
		StartTime time.Time
		EndTime   time.Time
		Value     float64
	}
}

// Downsample performs an aggregation query over time intervals.
// This is the core of time series downsampling: grouping points into
// fixed-width buckets and computing an aggregate per bucket.
func (s *Storage) Downsample(id string, agg AggregationType, interval time.Duration, start, end time.Time) (*DownsampleResult, error) {
	points, err := s.QueryRange(id, start, end)
	if err != nil {
		return nil, err
	}
	if len(points) == 0 {
		return &DownsampleResult{AggType: agg, Interval: interval}, nil
	}

	result := &DownsampleResult{
		AggType:  agg,
		Interval: interval,
		Results:  make([]struct {
			StartTime time.Time
			EndTime   time.Time
			Value     float64
		}, 0),
	}

	// Align bucket start to interval boundaries
	bucketStart := start.Truncate(interval)
	for bucketStart.Before(end) {
		bucketEnd := bucketStart.Add(interval)

		// Collect points in this bucket
		var bucketValues []float64
		for _, p := range points {
			pt := p.Timestamp
			if pt >= bucketStart.UnixNano() && pt < bucketEnd.UnixNano() {
				bucketValues = append(bucketValues, p.Value)
			}
		}

		if len(bucketValues) > 0 {
			var aggVal float64
			switch agg {
			case AggAvg:
				aggVal = avg(bucketValues)
			case AggMin:
				aggVal = minVal(bucketValues)
			case AggMax:
				aggVal = maxVal(bucketValues)
			case AggSum:
				aggVal = sumVal(bucketValues)
			}
			result.Results = append(result.Results, struct {
				StartTime time.Time
				EndTime   time.Time
				Value     float64
			}{
				StartTime: bucketStart,
				EndTime:   bucketEnd,
				Value:     aggVal,
			})
		}

		bucketStart = bucketEnd
	}

	return result, nil
}

func avg(vals []float64) float64 {
	if len(vals) == 0 {
		return 0
	}
	var s float64
	for _, v := range vals {
		s += v
	}
	return s / float64(len(vals))
}

func minVal(vals []float64) float64 {
	if len(vals) == 0 {
		return 0
	}
	m := vals[0]
	for _, v := range vals[1:] {
		if v < m {
			m = v
		}
	}
	return m
}

func maxVal(vals []float64) float64 {
	if len(vals) == 0 {
		return 0
	}
	m := vals[0]
	for _, v := range vals[1:] {
		if v > m {
			m = v
		}
	}
	return m
}

func sumVal(vals []float64) float64 {
	var s float64
	for _, v := range vals {
		s += v
	}
	return s
}

// ---------- Tag-Based Filtering ----------

// QueryByTag returns series IDs that have a specific tag key-value pair.
func (s *Storage) QueryByTag(tagKey, tagValue string) []string {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var matches []string
	for id, ser := range s.series {
		for _, p := range ser.Points {
			if v, ok := p.Tags[tagKey]; ok && v == tagValue {
				matches = append(matches, id)
				break
			}
		}
	}
	return matches
}

// ---------- Persistence ----------

// Persist writes all series data to a binary file.
func (s *Storage) Persist(path string) error {
	s.mu.RLock()
	defer s.mu.RUnlock()

	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	w := bufio.NewWriter(f)

	// Write magic header
	fmt.Fprintf(w, "TSDB\x01\n")

	// Write series count
	fmt.Fprintf(w, "SERIES:%d\n", len(s.series))

	// Write each series
	for id, ser := range s.series {
		fmt.Fprintf(w, "SERIES_START:%s\n", id)
		fmt.Fprintf(w, "NAME:%s\n", ser.Name)
		fmt.Fprintf(w, "COUNT:%d\n", len(ser.Points))
		fmt.Fprintf(w, "MIN_TIME:%d\n", ser.MinTime)
		fmt.Fprintf(w, "MAX_TIME:%d\n", ser.MaxTime)

		for _, p := range ser.Points {
			fmt.Fprintf(w, "POINT:%d:%.6f", p.Timestamp, p.Value)
			// Write tags
			for k, v := range p.Tags {
				fmt.Fprintf(w, "|%s=%s", k, v)
			}
			fmt.Fprintln(w)
		}
		fmt.Fprintln(w, "SERIES_END")
	}

	return w.Flush()
}

// Load reads all series data from a binary file.
func (s *Storage) Load(path string) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)

	var currentSeries *Series
	var currentPoints []Point

	for scanner.Scan() {
		line := scanner.Text()

		if len(line) >= 13 && line[:13] == "SERIES_START:" {
			// Parse series ID from "SERIES_START:cpu.temp.host1"
			id := line[13:]
			currentSeries = s.CreateSeries(id, id)
			currentPoints = nil
			continue
		}

		if line == "SERIES_END" {
			if currentSeries != nil && len(currentPoints) > 0 {
				currentSeries.Points = append(currentSeries.Points, currentPoints...)
				sort.Slice(currentSeries.Points, func(i, j int) bool {
					return currentSeries.Points[i].Timestamp < currentSeries.Points[j].Timestamp
				})
				currentSeries.MinTime = currentSeries.Points[0].Timestamp
				currentSeries.MaxTime = currentSeries.Points[len(currentSeries.Points)-1].Timestamp
				s.indexes[currentSeries.ID] = NewTimeIndex(currentSeries)
			}
			currentSeries = nil
			currentPoints = nil
			continue
		}

		if currentSeries == nil {
			continue
		}

		if len(line) >= 6 && line[:6] == "POINT:" {
			data := line[6:]
			// Parse timestamp and value from "POINT:1704067200000000000:45.000000|host=server1"
			// Find the colon after timestamp
			colonIdx := -1
			for i, c := range data {
				if c == ':' {
					colonIdx = i
					break
				}
			}
			if colonIdx == -1 {
				continue
			}
			var ts int64
			var rest string
			fmt.Sscanf(data[:colonIdx], "%d", &ts)
			rest = data[colonIdx+1:]

			// Parse value (first float before any '|')
			valStr := rest
			if pipeIdx := indexOf(rest, '|'); pipeIdx != -1 {
				valStr = rest[:pipeIdx]
			}
			var val float64
			fmt.Sscanf(valStr, "%f", &val)

			point := Point{
				Timestamp: ts,
				Value:     val,
				Tags:      make(map[string]string),
			}

			// Parse tags from rest
			if pipeIdx := indexOf(rest, '|'); pipeIdx != -1 {
				tagStr := rest[pipeIdx+1:]
				for _, tagPart := range splitTags(tagStr) {
					parts := splitKV(tagPart)
					if len(parts) == 2 {
						point.Tags[parts[0]] = parts[1]
					}
				}
			}

			currentPoints = append(currentPoints, point)
		}
	}

	return scanner.Err()
}

func splitTags(s string) []string {
	var tags []string
	var current string
	for _, c := range s {
		if c == '|' {
			tags = append(tags, current)
			current = ""
		} else {
			current += string(c)
		}
	}
	if current != "" {
		tags = append(tags, current)
	}
	return tags
}

func indexOf(s string, b byte) int {
	for i := 0; i < len(s); i++ {
		if s[i] == b {
			return i
		}
	}
	return -1
}

func splitKV(s string) []string {
	for i, c := range s {
		if c == '=' {
			return []string{s[:i], s[i+1:]}
		}
	}
	return []string{s}
}

// ---------- Block-Level Compression Utilities ----------

// CompressBlock creates a compressed DataBlock from raw points.
func CompressBlock(points []Point) *DataBlock {
	return NewDataBlock(points)
}

// DecompressBlock decompresses a DataBlock back to raw points.
func DecompressBlock(block *DataBlock, baseTs int64, baseVal float64) []Point {
	if block == nil {
		return nil
	}

	// Decompress timestamps
	rawTS := DeltaDecode(block.Timestamps)
	// The first delta is the base, so subtract it to get relative
	for i := range rawTS {
		rawTS[i] = rawTS[i] - baseTs
	}

	// Decompress values
	rawVals := RLEDecode(block.Values)

	points := make([]Point, len(rawVals))
	for i := range rawVals {
		points[i] = Point{
			Timestamp: baseTs + rawTS[i],
			Value:     baseVal + rawVals[i],
			Tags:      make(map[string]string),
		}
	}
	return points
}

// ---------- Delta Encoding Statistics ----------

// DeltaStats holds statistics about delta encoding effectiveness.
type DeltaStats struct {
	OriginalSize      int     // Original byte size
	EncodedSize       int     // Encoded byte size
	CompressionRatio  float64 // Ratio of original to encoded
	UniqueDeltas      int     // Number of unique delta values
	MaxDelta          int64   // Largest delta
	MinDelta          int64   // Smallest delta
	AvgDelta          float64 // Average delta
}

// ComputeDeltaStats analyzes the effectiveness of delta encoding on timestamps.
func ComputeDeltaStats(points []Point) *DeltaStats {
	if len(points) == 0 {
		return nil
	}

	timestamps := make([]int64, len(points))
	for i, p := range points {
		timestamps[i] = p.Timestamp
	}

	deltas := DeltaEncode(timestamps)
	uniqueDeltas := make(map[int64]bool)
	var maxD, minD, sumD int64
	for _, d := range deltas {
		uniqueDeltas[d] = true
		if d > maxD || maxD == 0 {
			maxD = d
		}
		if d < minD || minD == 0 {
			minD = d
		}
		sumD += d
	}

	// Original size: 8 bytes per int64
	originalSize := len(timestamps) * 8
	// Encoded size: 8 bytes per delta
	encodedSize := len(deltas) * 8

	return &DeltaStats{
		OriginalSize:     originalSize,
		EncodedSize:      encodedSize,
		CompressionRatio: float64(originalSize) / float64(encodedSize),
		UniqueDeltas:     len(uniqueDeltas),
		MaxDelta:         maxD,
		MinDelta:         minD,
		AvgDelta:         float64(sumD) / float64(len(deltas)),
	}
}

// ---------- Value Compression Stats ----------

// ValueStats holds statistics about value compression effectiveness.
type ValueStats struct {
	OriginalSize     int
	EncodedSize      int
	CompressionRatio float64
	UniqueValues     int
	MaxValue         float64
	MinValue         float64
}

// ComputeValueStats analyzes the effectiveness of RLE on values.
func ComputeValueStats(points []Point) *ValueStats {
	if len(points) == 0 {
		return nil
	}

	values := make([]float64, len(points))
	for i, p := range points {
		values[i] = p.Value
	}

	encoded := RLEEncode(values)
	uniqueVals := make(map[float64]bool)
	var maxV, minV float64
	for _, v := range values {
		uniqueVals[v] = true
		if v > maxV || maxV == 0 {
			maxV = v
		}
		if v < minV || minV == 0 {
			minV = v
		}
	}

	originalSize := len(values) * 8
	// Each RLE entry is (float64 + int) = 16 bytes
	encodedSize := len(encoded) / 2 * 16

	return &ValueStats{
		OriginalSize:     originalSize,
		EncodedSize:      encodedSize,
		CompressionRatio: float64(originalSize) / float64(encodedSize),
		UniqueValues:     len(uniqueVals),
		MaxValue:         maxV,
		MinValue:         minV,
	}
}

// ---------- Utility ----------

// FormatDuration formats a duration for display.
func FormatDuration(d time.Duration) string {
	if d < time.Millisecond {
		return fmt.Sprintf("%dns", d.Nanoseconds())
	}
	if d < time.Second {
		return fmt.Sprintf("%.0fms", float64(d.Microseconds())/1000)
	}
	if d < time.Minute {
		return fmt.Sprintf("%.2fs", d.Seconds())
	}
	return fmt.Sprintf("%.2fm", d.Minutes())
}

// FormatBytes formats a byte count for display.
func FormatBytes(b int) string {
	if b < 1024 {
		return fmt.Sprintf("%d B", b)
	}
	if b < 1024*1024 {
		return fmt.Sprintf("%.1f KB", float64(b)/1024)
	}
	return fmt.Sprintf("%.1f MB", float64(b)/(1024*1024))
}

// FormatFloat formats a float for display with appropriate precision.
func FormatFloat(v float64) string {
	if math.Abs(v) < 0.001 && v != 0 {
		return fmt.Sprintf("%.6e", v)
	}
	if math.Abs(v) >= 1000 {
		return fmt.Sprintf("%.2f", v)
	}
	return fmt.Sprintf("%.4f", v)
}

// FormatTime formats a timestamp for display.
func FormatTime(ts int64) string {
	return time.Unix(0, ts).UTC().Format("2006-01-02 15:04:05.000")
}

// ---------- Binary Block Encoding ----------

// EncodeBlockToBytes serializes a DataBlock to bytes.
func EncodeBlockToBytes(block *DataBlock) []byte {
	var buf []byte
	// Base time (8 bytes)
	buf = append(buf, int64ToBytes(block.BaseTime)...)
	// Base value (8 bytes)
	buf = append(buf, float64ToBytes(block.BaseValue)...)
	// Count (4 bytes)
	buf = append(buf, int32ToBytes(int32(block.Count))...)
	// Timestamp count (4 bytes)
	buf = append(buf, int32ToBytes(int32(len(block.Timestamps)))...)
	// Timestamp deltas (8 bytes each)
	for _, ts := range block.Timestamps {
		buf = append(buf, int64ToBytes(ts)...)
	}
	// Value count (4 bytes)
	buf = append(buf, int32ToBytes(int32(len(block.Values)))...)
	// Values (variable - simplified: store as float64 pairs)
	for i := 0; i < len(block.Values); i += 2 {
		if i+1 < len(block.Values) {
			buf = append(buf, float64ToBytes(block.Values[i].(float64))...)
			buf = append(buf, int32ToBytes(int32(block.Values[i+1].(int)))...)
		}
	}
	return buf
}

// DecodeBlockFromBytes deserializes a DataBlock from bytes.
func DecodeBlockFromBytes(data []byte) (*DataBlock, error) {
	if len(data) < 20 {
		return nil, fmt.Errorf("data too short")
	}
	block := &DataBlock{
		BaseTime:   bytesToInt64(data[0:8]),
		BaseValue:  bytesToFloat64(data[8:16]),
		Count:      int(data[16]),
		Timestamps: make([]int64, int(data[17])),
		Values:     make([]interface{}, 0),
	}
	offset := 20
	for i := 0; i < len(block.Timestamps); i++ {
		block.Timestamps[i] = bytesToInt64(data[offset : offset+8])
		offset += 8
	}
	valCount := int(data[offset])
	offset += 4
	for i := 0; i < valCount; i++ {
		block.Values = append(block.Values, bytesToFloat64(data[offset:offset+8]))
		offset += 8
		block.Values = append(block.Values, int(data[offset]))
		offset += 4
	}
	return block, nil
}

func int64ToBytes(v int64) []byte {
	b := make([]byte, 8)
	binary.LittleEndian.PutUint64(b, uint64(v))
	return b
}

func float64ToBytes(v float64) []byte {
	b := make([]byte, 8)
	binary.LittleEndian.PutUint64(b, math.Float64bits(v))
	return b
}

func int32ToBytes(v int32) []byte {
	b := make([]byte, 4)
	binary.LittleEndian.PutUint32(b, uint32(v))
	return b
}

func bytesToInt64(b []byte) int64 {
	return int64(binary.LittleEndian.Uint64(b))
}

func bytesToFloat64(b []byte) float64 {
	return math.Float64frombits(binary.LittleEndian.Uint64(b))
}
