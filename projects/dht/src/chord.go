// Package chord implements the Chord Distributed Hash Table (DHT) protocol.
//
// Chord is a peer-to-peer protocol that provides a distributed key-value store.
// It uses consistent hashing to map both keys and nodes to an ID space [0, 2^m).
// Each node is responsible for keys that fall in the range between its predecessor
// and itself (in clockwise direction on the ring).
//
// Core concepts:
//   - Ring: IDs are integers in [0, 2^m), forming a logical ring
//   - Successor: The first node that matches or follows a given ID clockwise
//   - Finger Table: Each node maintains a routing table for O(log N) lookups
//   - Key-Value Store: Each node stores values for keys it is responsible for
//   - Stabilization: Periodic protocol to maintain ring consistency
package chord
