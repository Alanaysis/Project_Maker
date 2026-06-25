package main

import (
	"fmt"
	"math"
	"time"

	"github.com/learning/stream-processing/internal/core"
	"github.com/learning/stream-processing/internal/operator"
	"github.com/learning/stream-processing/internal/pipeline"
)

// MetricPoint represents a metric measurement.
type MetricPoint struct {
	Name  string
	Value float64
}

func main() {
	fmt.Println("=== Anomaly Detection Example ===")
	fmt.Println()

	demoThresholdDetection()
	demoMovingAverageDetection()
	demoZScoreDetection()
}

// demoThresholdDetection shows simple threshold-based anomaly detection.
func demoThresholdDetection() {
	fmt.Println("--- Threshold-based Detection ---")
	fmt.Println("  Rule: Alert if CPU > 90% or Memory > 85%")

	// Create pipeline
	p := pipeline.NewPipeline()

	// Filter anomalies
	p.AddOperator(operator.NewFilterOperator(func(e core.Event) bool {
		mp := e.Value.(MetricPoint)
		if mp.Name == "cpu" && mp.Value > 90.0 {
			return true
		}
		if mp.Name == "memory" && mp.Value > 85.0 {
			return true
		}
		return false
	}))

	// Format alert
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		mp := v.(MetricPoint)
		return fmt.Sprintf("ALERT: %s = %.1f%%", mp.Name, mp.Value)
	}))

	// Generate metrics
	input := core.NewStream(100)
	go func() {
		defer input.Close()

		metrics := []MetricPoint{
			{"cpu", 45.0},
			{"cpu", 92.5},    // anomaly
			{"memory", 70.0},
			{"memory", 88.0}, // anomaly
			{"cpu", 60.0},
			{"cpu", 95.0},    // anomaly
			{"memory", 50.0},
		}

		for _, m := range metrics {
			input.Emit(core.NewEvent(m.Name, m))
		}
	}()

	// Process
	output := p.Execute(input)

	count := 0
	for e := range output.Events() {
		fmt.Printf("  %s\n", e.Value.(string))
		count++
	}

	fmt.Printf("  Found %d anomalies\n", count)
	fmt.Println()
}

// demoMovingAverageDetection shows moving average based detection.
func demoMovingAverageDetection() {
	fmt.Println("--- Moving Average Detection ---")
	fmt.Println("  Rule: Alert if value deviates > 2x from moving average")

	type WindowStats struct {
		values []float64
		avg    float64
	}

	// Use windowed reduce to compute statistics
	windowSize := 5 * time.Second
	statsOp := operator.NewWindowedReduceOperator(
		windowSize,
		windowSize,
		func(a, b interface{}) interface{} {
			v1 := a.([]float64)
			v2 := b.([]float64)
			return append(v1, v2...)
		},
	)

	base := time.Now()
	out := core.NewStream(100)

	go func() {
		defer out.Close()

		// Normal values around 100
		values := []float64{98, 102, 99, 101, 100, 97, 103, 99, 101, 100}

		// Add some anomalies
		anomalies := map[int]float64{
			5:  250.0, // spike
			8:  10.0,  // drop
		}

		for i, v := range values {
			if anom, ok := anomalies[i]; ok {
				v = anom
			}

			event := core.NewEventWithTime(
				"metric",
				[]float64{v},
				base.Add(time.Duration(i)*500*time.Millisecond),
			)
			statsOp.Process(event, out)
		}

		statsOp.EmitWindows(out)
	}()

	// Process results
	for e := range out.Events() {
		if values, ok := e.Value.([]float64); ok && len(values) > 0 {
			avg := average(values)
			for _, v := range values {
				deviation := math.Abs(v-avg) / avg
				if deviation > 1.0 { // 100% deviation
					fmt.Printf("  ANOMALY: %.1f (avg=%.1f, deviation=%.1f%%)\n",
						v, avg, deviation*100)
				}
			}
		}
	}

	fmt.Println()
}

// demoZScoreDetection shows Z-score based anomaly detection.
func demoZScoreDetection() {
	fmt.Println("--- Z-Score Detection ---")
	fmt.Println("  Rule: Alert if Z-score > 3.0 (statistical outlier)")

	// Pipeline for Z-score calculation
	type Stats struct {
		values []float64
	}

	p := pipeline.NewPipeline()

	// Collect values in window
	p.AddOperator(operator.NewWindowedReduceOperator(
		10*time.Second,
		10*time.Second,
		func(a, b interface{}) interface{} {
			s1 := a.(Stats)
			s2 := b.(Stats)
			return Stats{values: append(s1.values, s2.values...)}
		},
	))

	// Detect anomalies using Z-score
	p.AddOperator(operator.NewFlatMapOperator(func(e core.Event) []core.Event {
		stats, ok := e.Value.(Stats)
		if !ok || len(stats.values) < 2 {
			return nil
		}

		avg := average(stats.values)
		stddev := standardDeviation(stats.values, avg)

		var anomalies []core.Event
		for _, v := range stats.values {
			zscore := (v - avg) / stddev
			if math.Abs(zscore) > 3.0 {
				anomalies = append(anomalies, core.NewEvent(
					"anomaly",
					fmt.Sprintf("Value=%.1f, Z-score=%.2f", v, zscore),
				))
			}
		}
		return anomalies
	}))

	// Generate data
	input := core.NewStream(100)
	go func() {
		defer input.Close()

		base := time.Now()
		// Normal distribution around 100 with std ~5
		normalValues := []float64{
			98, 102, 99, 101, 100, 97, 103, 99, 101, 100,
			96, 104, 98, 102, 100, 99, 101, 97, 103, 100,
		}

		// Add outliers
		normalValues[5] = 150.0  // Z-score ~10
		normalValues[15] = 50.0  // Z-score ~-10

		for i, v := range normalValues {
			input.Emit(core.NewEventWithTime(
				"metric",
				Stats{values: []float64{v}},
				base.Add(time.Duration(i)*time.Second),
			))
		}
	}()

	output := p.Execute(input)

	count := 0
	for e := range output.Events() {
		fmt.Printf("  DETECTED: %s\n", e.Value.(string))
		count++
	}

	if count == 0 {
		fmt.Println("  No anomalies detected")
	} else {
		fmt.Printf("  Found %d anomalies\n", count)
	}
	fmt.Println()
}

// Helper functions

func average(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

func standardDeviation(values []float64, avg float64) float64 {
	if len(values) < 2 {
		return 0
	}
	sumSquaredDiff := 0.0
	for _, v := range values {
		diff := v - avg
		sumSquaredDiff += diff * diff
	}
	variance := sumSquaredDiff / float64(len(values)-1)
	return math.Sqrt(variance)
}
