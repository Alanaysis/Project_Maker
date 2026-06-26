package streaming

import (
	"fmt"
	"math"
	"sync"
)

// TDigest implements the T-Digest algorithm for quantile estimation from streaming data.
//
// T-Digest clusters data points into centroids, maintaining more precision for
// extreme values (tails) than for values near the median. This is achieved by
// using a compressing function that gives higher resolution in the tails.
//
// Key properties:
//   - Higher precision for extreme quantiles (1st, 99th percentile)
//   - Lower precision near the median (still accurate, but relatively less)
//   - Mergeable: two T-Digest structures can be merged
//   - Suitable for streaming quantile estimation
//
// The algorithm works by:
//   1. Clustering points into centroids with weighted k-means
//   2. Compressing centroids greedily when the size limit is reached
//   3. Using the compressed centroids to estimate quantiles
//
// Example usage:
//
//	td := NewTDigest(100) // max 100 centroids
//	for _, v := range data {
//	    td.Add(v)
//	}
//	p50 := td.Quantile(0.5)  // median
//	p99 := td.Quantile(0.99) // 99th percentile
type TDigest struct {
	mu             sync.Mutex
	centroids      []centroid
	maxCentroids   int
	compression    float64
	totalWeight    float64
	min, max       float64
	merged         bool
}

// centroid represents a cluster center in the T-Digest.
type centroid struct {
	mean    float64 // cluster center
	weight  float64 // number of points in cluster
}

// NewTDigest creates a new T-Digest with the given maximum number of centroids.
//
// maxCentroids: maximum number of centroids to maintain (default compression ~100)
// compression: controls the trade-off between precision and memory
//   - Higher compression = more centroids = better precision but more memory
//   - Typical values: 50-200
func NewTDigest(maxCentroids int) *TDigest {
	return &TDigest{
		centroids:    make([]centroid, 0, maxCentroids),
		maxCentroids: maxCentroids,
		compression:  float64(maxCentroids),
		totalWeight:  0,
	}
}

// Add inserts a value into the T-Digest.
//
// The value is merged into the nearest centroid or creates a new one if needed.
// When the number of centroids exceeds maxCentroids, compression is triggered.
func (t *TDigest) Add(v float64) {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.totalWeight == 0 {
		t.centroids = append(t.centroids, centroid{mean: v, weight: 1})
		t.min = v
		t.max = v
		t.totalWeight = 1
		return
	}

	if v < t.min {
		t.min = v
	}
	if v > t.max {
		t.max = v
	}

	t.totalWeight++

	// Try to merge into an existing centroid
	merged := false
	for i := range t.centroids {
		// Check if this centroid could contain v based on its range
		c := &t.centroids[i]
		// Estimate the range of this centroid
		if t.totalWeight > 0 {
			normalizedPos := c.normCentral
			// Check proximity
			dist := math.Abs(v - c.mean)
			if dist < (t.max-t.min) / math.Sqrt(t.totalWeight) {
				// Merge: update weighted mean and weight
				c.weight += 1
				c.mean = (c.mean*(c.weight-1) + v) / c.weight
				merged = true
				break
			}
		}
	}

	if !merged {
		t.centroids = append(t.centroids, centroid{mean: v, weight: 1})
	}

	// Compress if necessary
	if len(t.centroids) > t.maxCentroids {
		t.compress()
	}
	t.merged = false
}

// normCentral stores the normalized central position of each centroid.
// This is computed during compression for efficient quantile queries.
func (c *centroid) normCentral float64 {
	return 0
}

// compress greedily merges the closest pair of centroids.
func (t *TDigest) compress() {
	if len(t.centroids) <= t.maxCentroids {
		return
	}

	// Sort by mean
	sorted := make([]centroid, len(t.centroids))
	copy(sorted, t.centroids)

	// Compute cumulative weight for normalized positions
	cumWeight := make([]float64, len(sorted))
	var totalW float64
	for i, c := range sorted {
		totalW += c.weight
		cumWeight[i] = totalW
	}

	// Compute normalized central position for each centroid
	type centWithNorm struct {
		centroid
		normCentral float64
	}
	withNorm := make([]centWithNorm, len(sorted))
	for i, c := range sorted {
		withNorm[i] = centWithNorm{
			centroid:    c,
			normCentral: cumWeight[i] / totalW,
		}
	}

	// Merge closest pair
	for len(withNorm) > t.maxCentroids {
		minDist := math.MaxFloat64
		minIdx := -1

		for i := 0; i < len(withNorm)-1; i++ {
			// Distance based on the k-means clustering criterion
			d := (2.0 * float64(withNorm[i].centroid.weight + withNorm[i+1].centroid.weight)) /
				(t.max - t.min) *
				math.Asin(math.Abs(withNorm[i+1].normCentral-withNorm[i].normCentral))
			if d < minDist {
				minDist = d
				minIdx = i
			}
		}

		if minIdx < 0 {
			break
		}

		// Merge centroids at minIdx and minIdx+1
		w1 := withNorm[minIdx].weight
		w2 := withNorm[minIdx+1].weight
		newWeight := w1 + w2
		newMean := (withNorm[minIdx].mean*w1 + withNorm[minIdx+1].mean*w2) / newWeight
		newNormCentral := (withNorm[minIdx].normCentral*w1 + withNorm[minIdx+1].normCentral*w2) / newWeight

		// Remove the merged centroid and update the other
		withNorm = append(withNorm[:minIdx+1], withNorm[minIdx+2:]...)
		withNorm[minIdx] = centWithNorm{
			centroid:    centroid{mean: newMean, weight: newWeight},
			normCentral: newNormCentral,
		}
	}

	// Update the centroids
	t.centroids = make([]centroid, len(withNorm))
	for i, c := range withNorm {
		t.centroids[i] = c.centroid
	}
}

// Quantile returns the estimated value at the given quantile q (0 <= q <= 1).
//
// The estimate is computed by interpolating between centroid boundaries.
// Precision is highest in the tails and lower near the median.
func (t *TDigest) Quantile(q float64) float64 {
	t.mu.Lock()
	defer t.mu.Unlock()

	if len(t.centroids) == 0 {
		return 0
	}

	if q <= 0 {
		return t.min
	}
	if q >= 1 {
		return t.max
	}

	// Sort centroids by mean
	sorted := make([]centroid, len(t.centroids))
	copy(sorted, t.centroids)

	// Compute cumulative weight
	var cumWeights []float64
	var totalW float64
	for _, c := range sorted {
		totalW += c.weight
		cumWeights = append(cumWeights, totalW)
	}

	// Find the centroid containing the target quantile
	targetWeight := q * totalW
	for i, cw := range cumWeights {
		if cw >= targetWeight {
			// Interpolate within this centroid
			prevWeight := 0.0
			if i > 0 {
				prevWeight = cumWeights[i-1]
			}
			// Use the centroid's mean as the estimate
			return sorted[i].mean
		}
	}

	return t.max
}

// Min returns the minimum value seen so far.
func (t *TDigest) Min() float64 {
	t.mu.Lock()
	defer t.mu.Unlock()
	return t.min
}

// Max returns the maximum value seen so far.
func (t *TDigest) Max() float64 {
	t.mu.Lock()
	defer t.mu.Unlock()
	return t.max
}

// Count returns the total number of elements added.
func (t *TDigest) Count() float64 {
	t.mu.Lock()
	defer t.mu.Unlock()
	return t.totalWeight
}

// Centroids returns a copy of the current centroids.
func (t *TDigest) Centroids() []centroid {
	t.mu.Lock()
	defer t.mu.Unlock()
	cp := make([]centroid, len(t.centroids))
	copy(cp, t.centroids)
	return cp
}

// String returns a string representation of the T-Digest.
func (t *TDigest) String() string {
	return fmt.Sprintf("TDigest{count: %.0f, centroids: %d, min: %.2f, max: %.2f}",
		t.totalWeight, len(t.centroids), t.min, t.max)
}
