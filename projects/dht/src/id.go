package chord

import (
	"crypto/sha1"
	"fmt"
	"math"
	"hash/crc32"
)

// NodeID represents a node's position on the Chord ring.
// Chord uses m-bit IDs, defaulting to 2^16 = 65536 for simplicity.
type NodeID uint64

const (
	// RingSize is the size of the ID space (2^16).
	RingSize = 1 << 16
	// RingBits is the number of bits used for node IDs.
	RingBits = 16
)

// NextID returns the next ID on the ring (wrapping around).
func NextID(id NodeID) NodeID {
	return (id + 1) % RingSize
}

// PrevID returns the previous ID on the ring (wrapping around).
func PrevID(id NodeID) NodeID {
	if id == 0 {
		return RingSize - 1
	}
	return id - 1
}

// String returns a string representation of the node ID.
func (id NodeID) String() string {
	return fmt.Sprintf("%d", id)
}

// IDFromString parses a node ID from a string.
func IDFromString(s string) (NodeID, error) {
	var val uint64
	_, err := fmt.Sscanf(s, "%d", &val)
	if err != nil {
		return 0, err
	}
	return NodeID(val % RingSize), nil
}

// GenerateNodeID creates a node ID from a string identifier (e.g., IP address).
// It uses SHA-1 hashing to distribute IDs uniformly across the ring.
func GenerateNodeID(identifier string) NodeID {
	hash := sha1.Sum([]byte(identifier))
	// Use first 16 bits of the hash for the node ID
	return NodeID(uint64(hash[0])<<8 | uint64(hash[1]))
}

// GenerateKeyID creates a key ID from a string key.
// It uses CRC32 for faster hashing since keys are looked up frequently.
func GenerateKeyID(key string) NodeID {
	sum := crc32.ChecksumIEEE([]byte(key))
	// Map to ring size (2^16)
	return NodeID(uint64(sum) % RingSize)
}

// Distance computes the clockwise distance from id1 to id2 on the ring.
// In Chord, distance is always positive and wraps around the ring.
func Distance(id1, id2 NodeID) NodeID {
	if id2 >= id1 {
		return id2 - id1
	}
	return RingSize - id1 + id2
}

// ClosestPrecedingNode finds the closest preceding node to nodeID in the finger table.
// This is used during the finger table maintenance and key lookup.
func ClosestPrecedingNode(nodeID NodeID, fingerTable []NodeID) NodeID {
	// Traverse the finger table from highest index to lowest
	for i := len(fingerTable) - 1; i >= 0; i-- {
		if fingerTable[i] == 0 {
			continue
		}
		// Check if fingerTable[i] is in the range (nodeID, nodeID]
		if Distance(nodeID, fingerTable[i]) < Distance(nodeID, nodeID) {
			// Actually we want the closest node that precedes nodeID on the ring
			// i.e., the node that is closest to nodeID but comes before it clockwise
			distToNode := Distance(fingerTable[i], nodeID)
			// If fingerTable[i] is closer to nodeID than nodeID itself, use it
			if distToNode < RingSize && distToNode != 0 {
				return fingerTable[i]
			}
		}
	}
	return nodeID
}

// ClosestPrecedingNodeOptimized finds the closest preceding node to nodeID in the finger table.
// A node f in finger table precedes nodeID if f is in the interval (nodeID, nodeID] (clockwise).
func ClosestPrecedingNodeOptimized(nodeID, target NodeID, fingerTable []NodeID) NodeID {
	for i := len(fingerTable) - 1; i >= 0; i-- {
		if fingerTable[i] == 0 {
			continue
		}
		// Check if fingerTable[i] is strictly between nodeID and target (clockwise)
		if Distance(nodeID, fingerTable[i]) < Distance(nodeID, target) {
			return fingerTable[i]
		}
	}
	return nodeID
}

// HashToID hashes a string to a NodeID using SHA-1.
func HashToID(s string) NodeID {
	return GenerateNodeID(s)
}

// ComputeFingerTableSize computes the finger table size (log2 of ring size).
func ComputeFingerTableSize() int {
	return int(math.Log2(RingSize))
}

// FingerIndex computes the finger table index for a given distance.
// Finger table entry i covers the range [id + 2^(i-1), id + 2^i).
func FingerIndex(id NodeID, i int) NodeID {
	step := uint64(1) << (i - 1)
	return NodeID((uint64(id) + step) % RingSize)
}

// IsInRange checks if target is in the interval (start, end] on the ring.
// In Chord, intervals are half-open: (start, end] meaning start < x <= end (clockwise).
func IsInRange(start, end, target NodeID) bool {
	if start == end {
		return target == end
	}
	distToTarget := Distance(start, target)
	distToEnd := Distance(start, end)
	return distToTarget > 0 && distToTarget <= distToEnd
}

// ComputeKeyID computes the key ID for a given key string.
func ComputeKeyID(key string) NodeID {
	return GenerateKeyID(key)
}

// MinDistance finds the minimum distance between two nodes.
func MinDistance(a, b NodeID) NodeID {
	if a <= b {
		return b - a
	}
	return RingSize - a + b
}

// VerifyRing checks if the ring is consistent (no gaps larger than expected).
func VerifyRing(nodes []NodeID) bool {
	if len(nodes) < 2 {
		return true
	}
	// Sort nodes
	sorted := make([]NodeID, len(nodes))
	copy(sorted, nodes)
	for i := 0; i < len(sorted); i++ {
		for j := i + 1; j < len(sorted); j++ {
			if sorted[i] > sorted[j] {
				sorted[i], sorted[j] = sorted[j], sorted[i]
			}
		}
	}
	// Check gaps
	for i := 0; i < len(sorted)-1; i++ {
		gap := Distance(sorted[i], sorted[i+1])
		if gap == 0 {
			return false
		}
	}
	// Check wrap-around gap
	lastGap := Distance(sorted[len(sorted)-1], sorted[0])
	if lastGap == 0 {
		return false
	}
	return true
}

// AverageDistance computes the average distance between consecutive nodes on the ring.
func AverageDistance(nodes []NodeID) float64 {
	if len(nodes) < 2 {
		return 0
	}
	// Sort nodes
	sorted := make([]NodeID, len(nodes))
	copy(sorted, nodes)
	for i := 0; i < len(sorted); i++ {
		for j := i + 1; j < len(sorted); j++ {
			if sorted[i] > sorted[j] {
				sorted[i], sorted[j] = sorted[j], sorted[i]
			}
		}
	}
	totalDist := uint64(0)
	for i := 0; i < len(sorted)-1; i++ {
		totalDist += uint64(Distance(sorted[i], sorted[i+1]))
	}
	// Add wrap-around distance
	totalDist += uint64(Distance(sorted[len(sorted)-1], sorted[0]))
	return float64(totalDist) / float64(len(sorted))
}

// CountKeysPerNode computes the expected number of keys per node for uniform key distribution.
func CountKeysPerNode(totalKeys, numNodes int) int {
	if numNodes == 0 {
		return 0
	}
	return totalKeys / numNodes
}

// SimulationStats holds statistics for a Chord ring simulation.
type SimulationStats struct {
	TotalNodes     int
	TotalKeys      int
	AvgFingerTable int
	AvgKeysPerNode float64
	MaxKeysPerNode int
	MinKeysPerNode int
}

// ComputeStats computes simulation statistics.
func ComputeStats(nodes []NodeID, keys []NodeID) SimulationStats {
	stats := SimulationStats{
		TotalNodes: len(nodes),
		TotalKeys:  len(keys),
	}
	if len(nodes) == 0 {
		return stats
	}

	// Count keys per node
	keyCounts := make(map[NodeID]int)
	for _, key := range keys {
		// Find the successor for this key
		successor := findSuccessor(key, nodes)
		keyCounts[successor]++
	}

	// Compute min/max/avg
	minKeys := math.MaxInt64
	maxKeys := 0
	totalKeys := 0
	for _, count := range keyCounts {
		totalKeys += count
		if count < minKeys {
			minKeys = count
		}
		if count > maxKeys {
			maxKeys = count
		}
	}
	if len(keyCounts) > 0 {
		stats.MinKeysPerNode = minKeys
		stats.MaxKeysPerNode = maxKeys
		stats.AvgKeysPerNode = float64(totalKeys) / float64(len(keyCounts))
	}

	// Average finger table size
	stats.AvgFingerTable = ComputeFingerTableSize()

	return stats
}

// findSuccessor finds the successor of a key in a list of nodes.
func findSuccessor(key NodeID, nodes []NodeID) NodeID {
	if len(nodes) == 0 {
		return 0
	}
	for _, node := range nodes {
		if Distance(PrevID(key), node) == 0 || Distance(key, node) == 0 {
			return node
		}
		if Distance(PrevID(key), node) < Distance(PrevID(key), key) {
			return node
		}
	}
	// Wrap around: return the first node
	return nodes[0]
}
