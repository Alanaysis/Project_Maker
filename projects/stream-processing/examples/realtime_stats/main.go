package main

import (
	"fmt"
	"math/rand"
	"time"

	"github.com/learning/stream-processing/internal/core"
	"github.com/learning/stream-processing/internal/operator"
	"github.com/learning/stream-processing/internal/state"
)

func main() {
	fmt.Println("=== Real-time Statistics Example ===")
	fmt.Println()

	demoSensorAggregation()
	demoSlidingWindowAverage()
	demoKeyedStateTracking()
}

// demoSensorAggregation shows real-time sensor data aggregation.
func demoSensorAggregation() {
	fmt.Println("--- Sensor Aggregation (10-second tumbling window) ---")

	// Create windowed reduce operator for sum
	sumOp := operator.NewWindowedReduceOperator(
		10*time.Second,
		10*time.Second,
		func(a, b interface{}) interface{} {
			return a.(float64) + b.(float64)
		},
	)

	// Create count operator
	countOp := operator.NewWindowedReduceOperator(
		10*time.Second,
		10*time.Second,
		func(a, b interface{}) interface{} {
			return a.(int) + b.(int)
		},
	)

	base := time.Now()
	sensors := []string{"temp-01", "temp-02", "humidity-01"}

	// Generate simulated sensor data
	out := core.NewStream(100)
	go func() {
		defer out.Close()

		for i := 0; i < 30; i++ {
			sensor := sensors[rand.Intn(len(sensors))]
			value := 20.0 + rand.Float64()*10.0 // 20-30 degrees

			event := core.NewEventWithTime(
				sensor,
				value,
				base.Add(time.Duration(i)*time.Second),
			)

			sumOp.Process(event, out)
			countOp.Process(core.NewEventWithTime(sensor, 1, event.Timestamp), out)
		}

		sumOp.EmitWindows(out)
		countOp.EmitWindows(out)
	}()

	// Collect and display results
	totalSum := 0.0
	totalCount := 0

	for e := range out.Events() {
		if e.Key == "window_result" {
			if v, ok := e.Value.(float64); ok {
				totalSum += v
			} else if v, ok := e.Value.(int); ok {
				totalCount += v
			}
		}
	}

	fmt.Printf("  Processed %d events\n", 30)
	fmt.Printf("  Total sum: %.2f, Total count: %d\n", totalSum, totalCount)
	if totalCount > 0 {
		fmt.Printf("  Average: %.2f\n", totalSum/float64(totalCount))
	}
	fmt.Println()
}

// demoSlidingWindowAverage shows sliding window average calculation.
func demoSlidingWindowAverage() {
	fmt.Println("--- Sliding Window Average (window=10s, slide=5s) ---")

	// For average, we need sum and count, then divide
	type sumCount struct {
		sum   float64
		count int
	}

	avgOp := operator.NewWindowedReduceOperator(
		10*time.Second,
		5*time.Second,
		func(a, b interface{}) interface{} {
			sc1 := a.(sumCount)
			sc2 := b.(sumCount)
			return sumCount{
				sum:   sc1.sum + sc2.sum,
				count: sc1.count + sc2.count,
			}
		},
	)

	base := time.Now()
	out := core.NewStream(100)

	go func() {
		defer out.Close()

		// Generate data across 15 seconds
		for i := 0; i < 15; i++ {
			value := 100.0 + float64(i)*2.5
			event := core.NewEventWithTime(
				"metric",
				sumCount{sum: value, count: 1},
				base.Add(time.Duration(i)*time.Second),
			)
			avgOp.Process(event, out)
		}

		avgOp.EmitWindows(out)
	}()

	// Collect results
	var averages []float64
	for e := range out.Events() {
		if sc, ok := e.Value.(sumCount); ok {
			if sc.count > 0 {
				avg := sc.sum / float64(sc.count)
				averages = append(averages, avg)
			}
		}
	}

	fmt.Printf("  Computed %d window averages\n", len(averages))
	for i, avg := range averages {
		fmt.Printf("    Window %d: %.2f\n", i+1, avg)
	}
	fmt.Println()
}

// demoKeyedStateTracking shows per-key state management.
func demoKeyedStateTracking() {
	fmt.Println("--- Keyed State Tracking ---")

	ks := state.NewKeyedState()

	// Simulate user activity tracking
	activities := []struct {
		user     string
		action   string
		duration int
	}{
		{"alice", "login", 0},
		{"alice", "browse", 5},
		{"alice", "purchase", 120},
		{"bob", "login", 0},
		{"bob", "browse", 15},
		{"alice", "logout", 300},
		{"bob", "logout", 180},
	}

	for _, a := range activities {
		// Update user state
		ks.Put(a.user, "last_action", a.action)
		ks.Put(a.user, "last_duration", a.duration)

		// Increment action count
		userState := ks.GetState(a.user)
		countKey := fmt.Sprintf("count_%s", a.action)
		current, _ := userState.Get(countKey)
		if current == nil {
			userState.Put(countKey, 1)
		} else {
			userState.Put(countKey, current.(int)+1)
		}
	}

	// Display user states
	fmt.Println("  User Activity Summary:")
	for _, user := range ks.Keys() {
		userState := ks.GetState(user)
		lastAction, _ := userState.Get("last_action")
		lastDuration, _ := userState.Get("last_duration")
		fmt.Printf("    %s: last=%s, duration=%ds\n", user, lastAction, lastDuration)
	}

	// Create checkpoint
	snapshot, _ := ks.Snapshot()
	fmt.Printf("\n  Checkpoint created with %d user states\n", len(snapshot.States))
	fmt.Println()
}

// helper function for demo
func init() {
	rand.Seed(time.Now().UnixNano())
}
