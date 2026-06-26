package stream

import (
	"testing"
	"time"

	"stream-processing/src"
)

// ---------------------------------------------------------------------------
// Event tests
// ---------------------------------------------------------------------------

func TestEventString(t *testing.T) {
	e := stream.Event{
		ID:            1,
		Payload:       "hello",
		EventTime:     time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		ProcessingTime: time.Date(2024, 1, 1, 0, 0, 1, 0, time.UTC),
		Partition:     0,
	}
	s := e.String()
	if s == "" {
		t.Error("Event.String() should not return empty string")
	}
}

// ---------------------------------------------------------------------------
// Window tests
// ---------------------------------------------------------------------------

func TestWindowContains(t *testing.T) {
	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	end := start.Add(10 * time.Second)
	w := stream.Window{Start: start, End: end, Type: stream.WindowTumbling}

	// Inside window
	ts := start.Add(5 * time.Second)
	if !w.Contains(ts) {
		t.Error("Window should contain event at t+5s")
	}

	// At start (inclusive)
	if !w.Contains(start) {
		t.Error("Window should contain event at start")
	}

	// At end (exclusive)
	if w.Contains(end) {
		t.Error("Window should NOT contain event at end")
	}

	// Before window
	before := start.Add(-1 * time.Second)
	if w.Contains(before) {
		t.Error("Window should NOT contain event before start")
	}

	// After window
	after := end.Add(1 * time.Second)
	if w.Contains(after) {
		t.Error("Window should NOT contain event after end")
	}
}

func TestWindowDuration(t *testing.T) {
	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	end := start.Add(10 * time.Second)
	w := stream.Window{Start: start, End: end, Type: stream.WindowTumbling}
	if w.Duration() != 10*time.Second {
		t.Errorf("Expected duration 10s, got %v", w.Duration())
	}
}

// ---------------------------------------------------------------------------
// Tumbling window assigner tests
// ---------------------------------------------------------------------------

func TestTumblingWindowAssigner(t *testing.T) {
	assigner := &stream.TumblingWindowAssigner{Size: 10 * time.Second}

	tests := []struct {
		eventTime time.Time
		wantCount int
	}{
		{
			eventTime: time.Date(2024, 1, 1, 0, 0, 3, 0, time.UTC),
			wantCount: 1,
		},
		{
			eventTime: time.Date(2024, 1, 1, 0, 0, 10, 0, time.UTC),
			wantCount: 1,
		},
		{
			eventTime: time.Date(2024, 1, 1, 0, 0, 9, 599999999, time.UTC),
			wantCount: 1,
		},
	}

	for _, tt := range tests {
		windows := assigner.AssignWindows(tt.eventTime, tt.eventTime)
		if len(windows) != tt.wantCount {
			t.Errorf("AssignWindows(%s) = %d windows, want %d",
				tt.eventTime.Format(time.RFC3339), len(windows), tt.wantCount)
			continue
		}
		if windows[0].Type != stream.WindowTumbling {
			t.Errorf("Window type = %v, want %v", windows[0].Type, stream.WindowTumbling)
		}
	}
}

// ---------------------------------------------------------------------------
// Sliding window assigner tests
// ---------------------------------------------------------------------------

func TestSlidingWindowAssigner(t *testing.T) {
	assigner := &stream.SlidingWindowAssigner{Size: 10 * time.Second, Slide: 5 * time.Second}

	windows := assigner.AssignWindows(
		time.Date(2024, 1, 1, 0, 0, 3, 0, time.UTC),
		time.Date(2024, 1, 1, 0, 0, 3, 0, time.UTC),
	)

	if len(windows) < 1 {
		t.Errorf("Expected at least 1 window, got %d", len(windows))
	}

	if len(windows) > 0 && windows[0].Type != stream.WindowSliding {
		t.Errorf("Window type = %v, want %v", windows[0].Type, stream.WindowSliding)
	}
}

// ---------------------------------------------------------------------------
// Window type string tests
// ---------------------------------------------------------------------------

func TestWindowTypeString(t *testing.T) {
	tests := []struct {
		ty   stream.WindowType
		want string
	}{
		{stream.WindowTumbling, "tumbling"},
		{stream.WindowSliding, "sliding"},
		{stream.WindowSession, "session"},
		{stream.WindowType(99), "unknown"},
	}

	for _, tt := range tests {
		got := tt.ty.String()
		if got != tt.want {
			t.Errorf("WindowType(%d).String() = %q, want %q", tt.ty, got, tt.want)
		}
	}
}

// ---------------------------------------------------------------------------
// Aggregator tests
// ---------------------------------------------------------------------------

func TestSumAggregator(t *testing.T) {
	agg := &stream.SumAggregator{}
	events := []stream.Event{
		{ID: 1, Payload: 10.0},
		{ID: 2, Payload: 20.0},
		{ID: 3, Payload: 30.0},
	}
	for _, e := range events {
		agg.Add(e)
	}
	result := agg.Result().(float64)
	if result != 60.0 {
		t.Errorf("Sum = %v, want 60.0", result)
	}
}

func TestSumAggregatorEmpty(t *testing.T) {
	agg := &stream.SumAggregator{}
	result := agg.Result().(float64)
	if result != 0.0 {
		t.Errorf("Empty sum = %v, want 0.0", result)
	}
}

func TestCountAggregator(t *testing.T) {
	agg := &stream.CountAggregator{}
	events := []stream.Event{
		{ID: 1, Payload: "a"},
		{ID: 2, Payload: "b"},
		{ID: 3, Payload: "c"},
	}
	for _, e := range events {
		agg.Add(e)
	}
	result := agg.Result().(int64)
	if result != 3 {
		t.Errorf("Count = %v, want 3", result)
	}
}

func TestAvgAggregator(t *testing.T) {
	agg := &stream.AvgAggregator{}
	events := []stream.Event{
		{ID: 1, Payload: 10.0},
		{ID: 2, Payload: 20.0},
		{ID: 3, Payload: 30.0},
	}
	for _, e := range events {
		agg.Add(e)
	}
	result := agg.Result().(float64)
	if result != 20.0 {
		t.Errorf("Avg = %v, want 20.0", result)
	}
}

func TestMinAggregator(t *testing.T) {
	agg := &stream.MinAggregator{}
	events := []stream.Event{
		{ID: 1, Payload: 30.0},
		{ID: 2, Payload: 10.0},
		{ID: 3, Payload: 20.0},
	}
	for _, e := range events {
		agg.Add(e)
	}
	result := agg.Result().(float64)
	if result != 10.0 {
		t.Errorf("Min = %v, want 10.0", result)
	}
}

func TestMaxAggregator(t *testing.T) {
	agg := &stream.MaxAggregator{}
	events := []stream.Event{
		{ID: 1, Payload: 10.0},
		{ID: 2, Payload: 30.0},
		{ID: 3, Payload: 20.0},
	}
	for _, e := range events {
		agg.Add(e)
	}
	result := agg.Result().(float64)
	if result != 30.0 {
		t.Errorf("Max = %v, want 30.0", result)
	}
}

func TestAggregatorCopy(t *testing.T) {
	// Test SumAggregator copy via Result.
	orig := &stream.SumAggregator{}
	orig.Add(stream.Event{ID: 1, Payload: 42.0})
	copied := orig.Copy().(*stream.SumAggregator)
	if copied.Result().(float64) != orig.Result().(float64) {
		t.Errorf("Copy sum = %v, want %v", copied.Result(), orig.Result())
	}

	// Test CountAggregator copy via Result.
	orig2 := &stream.CountAggregator{}
	orig2.Add(stream.Event{ID: 1, Payload: "a"})
	orig2.Add(stream.Event{ID: 2, Payload: "b"})
	copied2 := orig2.Copy().(*stream.CountAggregator)
	if copied2.Result().(int64) != orig2.Result().(int64) {
		t.Errorf("Copy count = %v, want %v", copied2.Result(), orig2.Result())
	}

	// Test AvgAggregator copy via Result.
	orig3 := &stream.AvgAggregator{}
	orig3.Add(stream.Event{ID: 1, Payload: 50.0})
	copied3 := orig3.Copy().(*stream.AvgAggregator)
	if copied3.Result().(float64) != orig3.Result().(float64) {
		t.Errorf("Copy avg mismatch")
	}
}

// ---------------------------------------------------------------------------
// Watermark tests
// ---------------------------------------------------------------------------

func TestWatermarkUpdate(t *testing.T) {
	wm := stream.NewWatermark(10 * time.Second)

	wm.Update(time.Unix(5, 0))
	if !wm.WatermarkTime.Equal(time.Unix(0, 0)) {
		t.Errorf("Watermark = %v, want epoch zero", wm.WatermarkTime)
	}

	wm.Update(time.Unix(20, 0))
	if !wm.WatermarkTime.Equal(time.Unix(10, 0)) {
		t.Errorf("Watermark = %v, want t=10s", wm.WatermarkTime)
	}

	// Event at t=15s should NOT reduce watermark.
	wm.Update(time.Unix(15, 0))
	if !wm.WatermarkTime.Equal(time.Unix(10, 0)) {
		t.Errorf("Watermark still = %v, want t=10s (no reduction)", wm.WatermarkTime)
	}

	wm.Update(time.Unix(30, 0))
	if !wm.WatermarkTime.Equal(time.Unix(20, 0)) {
		t.Errorf("Watermark = %v, want t=20s", wm.WatermarkTime)
	}
}

func TestWatermarkIsLate(t *testing.T) {
	wm := stream.NewWatermark(10 * time.Second)
	wm.Update(time.Unix(20, 0))

	if !wm.IsLate(time.Unix(5, 0)) {
		t.Error("Event at t=5s should be late (watermark=t=10s)")
	}

	if wm.IsLate(time.Unix(15, 0)) {
		t.Error("Event at t=15s should NOT be late")
	}
}

func TestWatermarkIsTooLate(t *testing.T) {
	wm := stream.NewWatermark(10 * time.Second)
	wm.Lateness = 5 * time.Minute
	wm.Update(time.Unix(100, 0)) // watermark = 90s

	// IsTooLate checks: eventTime < watermark - lateness = 90s - 300s = -210s
	// So t=50s is NOT too late (50 > -210)
	if wm.IsTooLate(time.Unix(50, 0)) {
		t.Error("Event at t=50s should NOT be too late (watermark=90s, lateness=300s, threshold=-210s)")
	}

	// t=200s is definitely not too late
	if wm.IsTooLate(time.Unix(200, 0)) {
		t.Error("Event at t=200s should NOT be too late")
	}

	// Test with a higher watermark to get a positive threshold.
	wm2 := stream.NewWatermark(10 * time.Second)
	wm2.Lateness = 5 * time.Minute
	wm2.Update(time.Unix(500, 0)) // watermark = 490s
	// threshold = 490s - 300s = 190s
	if !wm2.IsTooLate(time.Unix(100, 0)) {
		t.Error("Event at t=100s should be too late (threshold=190s)")
	}
}

// ---------------------------------------------------------------------------
// StateManager tests
// ---------------------------------------------------------------------------

func TestStateManagerGet(t *testing.T) {
	sm := stream.NewStateManager()
	w := stream.Window{Start: time.Unix(0, 0), End: time.Unix(10, 0), Type: stream.WindowTumbling}

	agg := sm.Get(w, 0, func() stream.Aggregator { return &stream.SumAggregator{} })
	agg.Add(stream.Event{ID: 1, Payload: 10.0})
	agg.Add(stream.Event{ID: 2, Payload: 20.0})

	result, ok := sm.GetResult(w, 0)
	if !ok {
		t.Fatal("GetResult should return ok=true")
	}
	sum := result.(float64)
	if sum != 30.0 {
		t.Errorf("Sum = %v, want 30.0", sum)
	}
}

func TestStateManagerClearWindow(t *testing.T) {
	sm := stream.NewStateManager()
	w := stream.Window{Start: time.Unix(0, 0), End: time.Unix(10, 0), Type: stream.WindowTumbling}

	_ = sm.Get(w, 0, func() stream.Aggregator { return &stream.SumAggregator{} })
	_ = sm.Get(w, 1, func() stream.Aggregator { return &stream.CountAggregator{} })

	if sm.Size() != 2 {
		t.Errorf("Size should be 2, got %d", sm.Size())
	}

	sm.ClearWindow(w)
	if sm.Size() != 0 {
		t.Errorf("Size after ClearWindow = %d, want 0", sm.Size())
	}
}

func TestStateManagerClearAll(t *testing.T) {
	sm := stream.NewStateManager()
	sm.Get(stream.Window{Start: time.Unix(0, 0), End: time.Unix(10, 0), Type: stream.WindowTumbling}, 0, func() stream.Aggregator {
		return &stream.SumAggregator{}
	})
	sm.Get(stream.Window{Start: time.Unix(10, 0), End: time.Unix(20, 0), Type: stream.WindowSliding}, 0, func() stream.Aggregator {
		return &stream.CountAggregator{}
	})

	if sm.Size() != 2 {
		t.Errorf("Size = %d, want 2", sm.Size())
	}

	sm.ClearAll()
	if sm.Size() != 0 {
		t.Errorf("Size after ClearAll = %d, want 0", sm.Size())
	}
}

// ---------------------------------------------------------------------------
// Trigger tests
// ---------------------------------------------------------------------------

func TestCountTrigger(t *testing.T) {
	trigger := &stream.CountTrigger{Count: 3}
	state := &stream.TriggerState{}
	w := stream.Window{Start: time.Unix(0, 0), End: time.Unix(10, 0), Type: stream.WindowTumbling}

	for i := int64(1); i <= 2; i++ {
		event := stream.Event{ID: i, Payload: float64(i)}
		fired := trigger.OnEvent(state, event, w)
		if fired {
			t.Errorf("Event %d should not trigger fire", i)
		}
	}

	event := stream.Event{ID: 3, Payload: 3.0}
	fired := trigger.OnEvent(state, event, w)
	if !fired {
		t.Error("Event 3 should trigger fire")
	}
	if state.Count != 3 {
		t.Errorf("Count = %d, want 3", state.Count)
	}
}

func TestCountTriggerClear(t *testing.T) {
	trigger := &stream.CountTrigger{Count: 3}
	state := &stream.TriggerState{Count: 5, Fired: true}
	w := stream.Window{Start: time.Unix(0, 0), End: time.Unix(10, 0), Type: stream.WindowTumbling}

	trigger.Clear(state, w)
	if state.Count != 0 {
		t.Errorf("Count after clear = %d, want 0", state.Count)
	}
	if state.Fired {
		t.Error("Fired should be false after clear")
	}
}

func TestWatermarkTrigger(t *testing.T) {
	trigger := &stream.WatermarkTrigger{}
	state := &stream.TriggerState{}
	w := stream.Window{Start: time.Unix(0, 0), End: time.Unix(10, 0), Type: stream.WindowTumbling}

	event := stream.Event{ID: 1, Payload: 1.0}
	if trigger.OnEvent(state, event, w) {
		t.Error("OnEvent should not fire for WatermarkTrigger")
	}

	if !trigger.OnTimer(state, w) {
		t.Error("OnTimer should fire")
	}
	if !state.Fired {
		t.Error("State should be fired after OnTimer")
	}
}

// ---------------------------------------------------------------------------
// Source tests
// ---------------------------------------------------------------------------

func TestSliceSource(t *testing.T) {
	events := []stream.Event{
		{ID: 1, Payload: "a"},
		{ID: 2, Payload: "b"},
		{ID: 3, Payload: "c"},
	}
	source := stream.NewSliceSource(events, "test")

	for i := 0; i < 3; i++ {
		event, ok := source.Read()
		if !ok {
			t.Errorf("Read %d: expected ok=true", i)
			break
		}
		if event.ID != int64(i+1) {
			t.Errorf("Event ID = %d, want %d", event.ID, i+1)
		}
	}

	_, ok := source.Read()
	if ok {
		t.Error("Read should return ok=false after exhaustion")
	}
}

func TestSliceSourceName(t *testing.T) {
	source := stream.NewSliceSource(nil, "my-source")
	if source.Name() != "my-source" {
		t.Errorf("Name = %q, want %q", source.Name(), "my-source")
	}
}

// ---------------------------------------------------------------------------
// Session window tests
// ---------------------------------------------------------------------------

func TestSessionWindow(t *testing.T) {
	baseTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)

	event1 := stream.Event{
		ID: 1, Payload: 10.0,
		EventTime: baseTime, ProcessingTime: baseTime, Partition: 0,
	}

	session := stream.NewSessionWindow(event1)
	if !session.Active {
		t.Error("New session should be active")
	}

	event2 := stream.Event{
		ID: 2, Payload: 20.0,
		EventTime: baseTime.Add(3 * time.Second), ProcessingTime: baseTime.Add(3 * time.Second), Partition: 0,
	}
	result := session.AddEvent(event2, 5*time.Second)
	if !result {
		t.Error("Event within gap should be added to session")
	}
	if session.Aggreg.Result().(float64) != 30.0 {
		t.Errorf("Session sum = %v, want 30.0", session.Aggreg.Result())
	}

	event3 := stream.Event{
		ID: 3, Payload: 30.0,
		EventTime: baseTime.Add(10 * time.Second), ProcessingTime: baseTime.Add(10 * time.Second), Partition: 0,
	}
	result = session.AddEvent(event3, 5*time.Second)
	if result {
		t.Error("Event outside gap should NOT be added to session")
	}
	if session.Active {
		t.Error("Session should be inactive after event outside gap")
	}
}

func TestSessionManager(t *testing.T) {
	gap := 5 * time.Second
	manager := stream.NewSessionManager(gap)
	baseTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)

	event1 := stream.Event{ID: 1, Payload: 10.0, EventTime: baseTime, ProcessingTime: baseTime, Partition: 0}
	s1 := manager.ProcessEvent(event1)
	if s1 == nil {
		t.Fatal("First event should create a session")
	}
	if !s1.Active {
		t.Error("Session should be active")
	}

	event2 := stream.Event{ID: 2, Payload: 20.0, EventTime: baseTime.Add(1 * time.Second), ProcessingTime: baseTime.Add(1 * time.Second), Partition: 0}
	s2 := manager.ProcessEvent(event2)
	if s1 != s2 {
		t.Error("Events within gap should belong to same session")
	}

	event3 := stream.Event{ID: 3, Payload: 30.0, EventTime: baseTime.Add(10 * time.Second), ProcessingTime: baseTime.Add(10 * time.Second), Partition: 0}
	s3 := manager.ProcessEvent(event3)
	if s1 == s3 {
		t.Error("Events outside gap should create new session")
	}

	// After event3, s1 is inactive (event outside gap). s2 is still active.
	// So ActiveCount should be 1 (only s2).
	if manager.ActiveCount() != 1 {
		t.Errorf("Active sessions = %d, want 1", manager.ActiveCount())
	}
}

// ---------------------------------------------------------------------------
// WindowedStream tests
// ---------------------------------------------------------------------------

func TestWindowedStreamProcess(t *testing.T) {
	baseTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	events := []stream.Event{
		{ID: 1, Payload: 10.0, EventTime: baseTime, ProcessingTime: baseTime, Partition: 0},
		{ID: 2, Payload: 20.0, EventTime: baseTime.Add(2 * time.Second), ProcessingTime: baseTime.Add(2 * time.Second), Partition: 0},
		{ID: 3, Payload: 30.0, EventTime: baseTime.Add(4 * time.Second), ProcessingTime: baseTime.Add(4 * time.Second), Partition: 0},
	}

	source := stream.NewSliceSource(events, "test")
	assigner := &stream.TumblingWindowAssigner{Size: 5 * time.Second}
	streamProc := stream.NewWindowedStream(source, assigner,
		func() stream.Aggregator { return &stream.SumAggregator{} },
		&stream.WatermarkTrigger{})

	results := streamProc.Process()

	if len(results) != 1 {
		t.Errorf("Expected 1 result, got %d", len(results))
	}

	if len(results) > 0 {
		sum := results[0].Result.(float64)
		if sum != 60.0 {
			t.Errorf("Sum = %v, want 60.0", sum)
		}
	}
}

func TestWindowedStreamEmptySource(t *testing.T) {
	source := stream.NewSliceSource(nil, "empty")
	assigner := &stream.TumblingWindowAssigner{Size: 5 * time.Second}
	streamProc := stream.NewWindowedStream(source, assigner,
		func() stream.Aggregator { return &stream.SumAggregator{} },
		&stream.WatermarkTrigger{})

	results := streamProc.Process()
	if len(results) != 0 {
		t.Errorf("Expected 0 results for empty source, got %d", len(results))
	}
}

// ---------------------------------------------------------------------------
// ComputeStats tests
// ---------------------------------------------------------------------------

func TestComputeStats(t *testing.T) {
	values := []float64{10.0, 20.0, 30.0, 40.0, 50.0}
	stats := stream.ComputeStats(values)

	if stats.Sum != 150.0 {
		t.Errorf("Sum = %v, want 150.0", stats.Sum)
	}
	if stats.Count != 5 {
		t.Errorf("Count = %v, want 5", stats.Count)
	}
	if stats.Avg != 30.0 {
		t.Errorf("Avg = %v, want 30.0", stats.Avg)
	}
	if stats.Min != 10.0 {
		t.Errorf("Min = %v, want 10.0", stats.Min)
	}
	if stats.Max != 50.0 {
		t.Errorf("Max = %v, want 50.0", stats.Max)
	}
}

func TestComputeStatsEmpty(t *testing.T) {
	stats := stream.ComputeStats(nil)
	if stats.Count != 0 {
		t.Errorf("Empty stats count = %v, want 0", stats.Count)
	}
}

func TestComputeStatsSingle(t *testing.T) {
	stats := stream.ComputeStats([]float64{42.0})
	if stats.Sum != 42.0 || stats.Avg != 42.0 || stats.Min != 42.0 || stats.Max != 42.0 {
		t.Errorf("Single value stats = %+v, want all 42.0", stats)
	}
	if stats.Variance != 0.0 {
		t.Errorf("Single value variance = %v, want 0.0", stats.Variance)
	}
}

// ---------------------------------------------------------------------------
// Key tests
// ---------------------------------------------------------------------------

func TestKey(t *testing.T) {
	w := stream.Window{Start: time.Unix(100, 0), End: time.Unix(200, 0), Type: stream.WindowTumbling}
	k1 := stream.Key(w, 0)
	k2 := stream.Key(w, 1)
	if k1 == k2 {
		t.Error("Keys for different partitions should be different")
	}

	k3 := stream.Key(w, 0)
	if k1 != k3 {
		t.Error("Same window/partition should produce same key")
	}
}

// ---------------------------------------------------------------------------
// Window String tests
// ---------------------------------------------------------------------------

func TestWindowString(t *testing.T) {
	w := stream.Window{
		Start: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		End:   time.Date(2024, 1, 1, 0, 0, 10, 0, time.UTC),
		Type:  stream.WindowTumbling,
	}
	s := w.String()
	if s == "" {
		t.Error("Window.String() should not return empty string")
	}
}
