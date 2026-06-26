package tsdb

import (
	"fmt"
	"math"
	"math/rand"
	"time"
)

// GenerateMockData creates realistic mock time series data for testing.
// It simulates sensor-like data with trends, noise, and periodic patterns.
func GenerateMockData(seriesID, name string, count int, interval time.Duration, baseValue float64, variance float64) *Series {
	s := &Series{
		ID:     seriesID,
		Name:   name,
		Points: make([]Point, count),
	}

	startTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	rng := rand.New(rand.NewSource(42))

	for i := 0; i < count; i++ {
		ts := startTime.Add(time.Duration(i) * interval).UnixNano()
		// Add sinusoidal pattern + noise
		sine := math.Sin(float64(i)*0.1) * variance * 0.5
		noise := (rng.Float64() - 0.5) * variance
		value := baseValue + sine + noise

		s.Points[i] = Point{
			Timestamp: ts,
			Value:     math.Round(value*100) / 100,
			Tags: map[string]string{
				"host":    "server-" + fmt.Sprintf("%03d", i%10),
				"region":  "us-east",
				"sensor":  "temp",
				"unit":    "celsius",
			},
		}
	}

	s.Points[0].Timestamp = startTime.UnixNano()
	s.MinTime = s.Points[0].Timestamp
	s.MaxTime = s.Points[count-1].Timestamp

	return s
}

// GenerateConstantData creates data with constant values (good for RLE testing).
func GenerateConstantData(seriesID, name string, count int, interval time.Duration, constantVal float64) *Series {
	s := &Series{
		ID:     seriesID,
		Name:   name,
		Points: make([]Point, count),
	}

	startTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	for i := 0; i < count; i++ {
		ts := startTime.Add(time.Duration(i) * interval).UnixNano()
		s.Points[i] = Point{
			Timestamp: ts,
			Value:     constantVal,
			Tags: map[string]string{
				"type": "constant",
			},
		}
	}

	s.MinTime = s.Points[0].Timestamp
	s.MaxTime = s.Points[count-1].Timestamp
	return s
}

// GenerateRandomData creates random walk data.
func GenerateRandomData(seriesID, name string, count int, interval time.Duration, startVal float64) *Series {
	s := &Series{
		ID:     seriesID,
		Name:   name,
		Points: make([]Point, count),
	}

	startTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	rng := rand.New(rand.NewSource(123))
	currentVal := startVal

	for i := 0; i < count; i++ {
		ts := startTime.Add(time.Duration(i) * interval).UnixNano()
		currentVal += (rng.Float64() - 0.5) * 2
		s.Points[i] = Point{
			Timestamp: ts,
			Value:     math.Round(currentVal*100) / 100,
			Tags: map[string]string{
				"type": "random-walk",
			},
		}
	}

	s.MinTime = s.Points[0].Timestamp
	s.MaxTime = s.Points[count-1].Timestamp
	return s
}
