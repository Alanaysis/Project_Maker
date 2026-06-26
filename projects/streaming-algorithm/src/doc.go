// Package streaming implements streaming data processing algorithms.
//
// Streaming algorithms are designed to process data elements one at a time
// (in a "stream") with limited memory, making them suitable for:
// - Real-time analytics on high-volume data
// - Approximate query processing with bounded memory
// - Continuous monitoring and alerting systems
//
// Core data flow:
//
//	data enters → window updates → aggregation → result output
//
// Implemented algorithms:
//   - SlidingWindow: Fixed-size and time-based window aggregations
//   - ReservoirSample: Random sampling from a stream of unknown size
//   - CountMinSketch: Frequency estimation with controlled false positives
//   - HyperLogLog: Cardinality estimation using probabilistic counting
//   - TDigest: Quantile estimation using centroid clustering
//   - BloomFilter: Probabilistic set membership testing
//   - StreamAgg: General-purpose stream aggregation (sum, avg, min, max, count)
package streaming
