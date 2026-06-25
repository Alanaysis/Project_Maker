package internal

import (
	"crypto/sha1"
	"fmt"
	"math/big"
	"math/rand"
	"sort"
	"sync"
	"time"
)

// Kademlia constants
const (
	K         = 20    // K-bucket size
	Alpha     = 3     // Concurrency parameter
	IDLength  = 160   // ID length in bits (SHA-1)
	NumBuckets = IDLength // Number of k-buckets
)

// XOR calculates the XOR distance between two IDs
func XOR(a, b *big.Int) *big.Int {
	return new(big.Int).Xor(a, b)
}

// XORDistance calculates the XOR distance and returns it as a big.Int
func XORDistance(a, b *big.Int) *big.Int {
	return XOR(a, b)
}

// LeadingZeros returns the number of leading zero bits in a big.Int
// This is used to determine which k-bucket a node belongs to
func LeadingZeros(n *big.Int) int {
	if n.Sign() == 0 {
		return IDLength
	}
	bits := n.BitLen()
	return IDLength - bits
}

// BucketIndex returns the k-bucket index for a node given the local node's ID
// The index is determined by the length of the common prefix (leading zeros in XOR)
func BucketIndex(localID, remoteID *big.Int) int {
	dist := XOR(localID, remoteID)
	leading := LeadingZeros(dist)
	idx := IDLength - 1 - leading
	if idx < 0 {
		idx = 0
	}
	if idx >= NumBuckets {
		idx = NumBuckets - 1
	}
	return idx
}

// Contact represents a node in the Kademlia network
type Contact struct {
	ID       *big.Int
	Addr     string
	LastSeen time.Time
}

// NewContact creates a new contact
func NewContact(id *big.Int, addr string) *Contact {
	return &Contact{
		ID:       id,
		Addr:     addr,
		LastSeen: time.Now(),
	}
}

// KBucket represents a k-bucket that holds up to K contacts
type KBucket struct {
	mu       sync.RWMutex
	contacts []*Contact
}

// NewKBucket creates a new k-bucket
func NewKBucket() *KBucket {
	return &KBucket{
		contacts: make([]*Contact, 0, K),
	}
}

// AddContact adds a contact to the k-bucket
// Returns true if the contact was added, false if the bucket is full
func (kb *KBucket) AddContact(contact *Contact) bool {
	kb.mu.Lock()
	defer kb.mu.Unlock()

	// Check if contact already exists
	for i, c := range kb.contacts {
		if c.ID.Cmp(contact.ID) == 0 {
			// Move to end (most recently seen)
			kb.contacts = append(kb.contacts[:i], kb.contacts[i+1:]...)
			contact.LastSeen = time.Now()
			kb.contacts = append(kb.contacts, contact)
			return true
		}
	}

	// If bucket is full, evict least recently seen (first element)
	if len(kb.contacts) >= K {
		kb.contacts = kb.contacts[1:]
	}

	contact.LastSeen = time.Now()
	kb.contacts = append(kb.contacts, contact)
	return true
}

// RemoveContact removes a contact from the k-bucket
func (kb *KBucket) RemoveContact(id *big.Int) {
	kb.mu.Lock()
	defer kb.mu.Unlock()

	for i, c := range kb.contacts {
		if c.ID.Cmp(id) == 0 {
			kb.contacts = append(kb.contacts[:i], kb.contacts[i+1:]...)
			return
		}
	}
}

// GetContacts returns all contacts in the k-bucket
func (kb *KBucket) GetContacts() []*Contact {
	kb.mu.RLock()
	defer kb.mu.RUnlock()

	result := make([]*Contact, len(kb.contacts))
	copy(result, kb.contacts)
	return result
}

// Size returns the number of contacts in the k-bucket
func (kb *KBucket) Size() int {
	kb.mu.RLock()
	defer kb.mu.RUnlock()
	return len(kb.contacts)
}

// RoutingTable represents the Kademlia routing table
type RoutingTable struct {
	mu        sync.RWMutex
	localID   *big.Int
	localAddr string
	buckets   [NumBuckets]*KBucket
}

// NewRoutingTable creates a new routing table
func NewRoutingTable(localID *big.Int, localAddr string) *RoutingTable {
	rt := &RoutingTable{
		localID:   localID,
		localAddr: localAddr,
	}
	for i := 0; i < NumBuckets; i++ {
		rt.buckets[i] = NewKBucket()
	}
	return rt
}

// AddContact adds a contact to the appropriate k-bucket
func (rt *RoutingTable) AddContact(contact *Contact) {
	if contact.ID.Cmp(rt.localID) == 0 {
		return // Don't add ourselves
	}
	idx := BucketIndex(rt.localID, contact.ID)
	rt.buckets[idx].AddContact(contact)
}

// RemoveContact removes a contact from the routing table
func (rt *RoutingTable) RemoveContact(id *big.Int) {
	idx := BucketIndex(rt.localID, id)
	rt.buckets[idx].RemoveContact(id)
}

// FindClosestContacts finds the K closest contacts to a target ID
func (rt *RoutingTable) FindClosestContacts(target *big.Int, count int) []*Contact {
	rt.mu.RLock()
	defer rt.mu.RUnlock()

	// Collect all contacts
	var allContacts []*Contact
	for _, bucket := range rt.buckets {
		allContacts = append(allContacts, bucket.GetContacts()...)
	}

	// Sort by XOR distance to target
	sort.Slice(allContacts, func(i, j int) bool {
		distI := XOR(allContacts[i].ID, target)
		distJ := XOR(allContacts[j].ID, target)
		return distI.Cmp(distJ) < 0
	})

	// Return up to count contacts
	if count > len(allContacts) {
		count = len(allContacts)
	}
	return allContacts[:count]
}

// GetBucketSize returns the size of a specific k-bucket
func (rt *RoutingTable) GetBucketSize(idx int) int {
	if idx < 0 || idx >= NumBuckets {
		return 0
	}
	return rt.buckets[idx].Size()
}

// TotalContacts returns the total number of contacts in the routing table
func (rt *RoutingTable) TotalContacts() int {
	rt.mu.RLock()
	defer rt.mu.RUnlock()

	total := 0
	for _, bucket := range rt.buckets {
		total += bucket.Size()
	}
	return total
}

// KademliaNode represents a Kademlia DHT node
type KademliaNode struct {
	mu          sync.RWMutex
	ID          *big.Int
	Addr        string
	RT          *RoutingTable
	storage     map[string]string
	hashFunc    HashFunc
	alive       bool
	bootstrap   *Contact
}

// NewKademliaNode creates a new Kademlia node
func NewKademliaNode(addr string, hashFunc HashFunc) *KademliaNode {
	if hashFunc == nil {
		hashFunc = DefaultHash
	}

	id := hashFunc(addr)
	return &KademliaNode{
		ID:       id,
		Addr:     addr,
		RT:       NewRoutingTable(id, addr),
		storage:  make(map[string]string),
		hashFunc: hashFunc,
		alive:    true,
	}
}

// IsAlive returns whether the node is alive
func (kn *KademliaNode) IsAlive() bool {
	kn.mu.RLock()
	defer kn.mu.RUnlock()
	return kn.alive
}

// SetAlive sets the node's alive status
func (kn *KademliaNode) SetAlive(alive bool) {
	kn.mu.Lock()
	defer kn.mu.Unlock()
	kn.alive = alive
}

// Store stores a key-value pair
func (kn *KademliaNode) Store(key, value string) {
	kn.mu.Lock()
	defer kn.mu.Unlock()
	kn.storage[key] = value
}

// Get retrieves a value by key
func (kn *KademliaNode) Get(key string) (string, bool) {
	kn.mu.RLock()
	defer kn.mu.RUnlock()
	val, ok := kn.storage[key]
	return val, ok
}

// Delete removes a key-value pair
func (kn *KademliaNode) Delete(key string) bool {
	kn.mu.Lock()
	defer kn.mu.Unlock()
	_, ok := kn.storage[key]
	if ok {
		delete(kn.storage, key)
	}
	return ok
}

// FindNode finds the K closest nodes to a target ID
// This is the Kademlia FIND_NODE operation
func (kn *KademliaNode) FindNode(target *big.Int) []*Contact {
	return kn.RT.FindClosestContacts(target, K)
}

// FindValue finds a value by key, or returns the K closest nodes
// This is the Kademlia FIND_VALUE operation
func (kn *KademliaNode) FindValue(key string) (string, []*Contact, bool) {
	kn.mu.RLock()
	val, ok := kn.storage[key]
	kn.mu.RUnlock()

	if ok {
		return val, nil, true
	}

	// Return closest contacts
	keyID := kn.hashFunc(key)
	contacts := kn.RT.FindClosestContacts(keyID, K)
	return "", contacts, false
}

// Bootstrap connects to a bootstrap node and populates the routing table
func (kn *KademliaNode) Bootstrap(bootstrapAddr string, bootstrapID *big.Int) error {
	kn.mu.Lock()
	kn.bootstrap = NewContact(bootstrapID, bootstrapAddr)
	kn.mu.Unlock()

	// Add bootstrap node to routing table
	contact := NewContact(bootstrapID, bootstrapAddr)
	kn.RT.AddContact(contact)

	// Perform FIND_NODE on ourselves to populate routing table
	closest := kn.RT.FindClosestContacts(kn.ID, K)
	for _, c := range closest {
		kn.RT.AddContact(c)
	}

	return nil
}

// RefreshBuckets refreshes k-buckets by performing FIND_NODE on random IDs
// This is the periodic refresh mechanism
func (kn *KademliaNode) RefreshBuckets() {
	rng := rand.New(rand.NewSource(time.Now().UnixNano()))

	for i := 0; i < NumBuckets; i++ {
		// Generate a random ID in the bucket's range
		bucketStart := new(big.Int).Lsh(big.NewInt(1), uint(i))
		bucketEnd := new(big.Int).Lsh(big.NewInt(1), uint(i+1))

		// Random ID in [bucketStart, bucketEnd)
		diff := new(big.Int).Sub(bucketEnd, bucketStart)
		randomOffset := new(big.Int).Rand(rng, diff)
		randomID := new(big.Int).Add(bucketStart, randomOffset)

		// Perform FIND_NODE to refresh this bucket
		kn.FindNode(randomID)
	}
}

// String returns a string representation of the node
func (kn *KademliaNode) String() string {
	return fmt.Sprintf("KademliaNode{ID: %s, Addr: %s}", FormatID(kn.ID), kn.Addr)
}

// PrintRoutingTable prints the routing table for debugging
func (kn *KademliaNode) PrintRoutingTable() {
	fmt.Printf("Routing Table for %s:\n", FormatID(kn.ID))
	for i := 0; i < NumBuckets; i++ {
		size := kn.RT.GetBucketSize(i)
		if size > 0 {
			fmt.Printf("  Bucket[%d]: %d contacts\n", i, size)
		}
	}
}

// RandomKademliaID generates a random Kademlia ID
func RandomKademliaID() *big.Int {
	b := make([]byte, 20) // 160 bits = 20 bytes
	for i := range b {
		b[i] = byte(rand.Intn(256))
	}
	return new(big.Int).SetBytes(b)
}

// KademliaHash uses SHA-1 for Kademlia ID generation
func KademliaHash(key string) *big.Int {
	hash := sha1.New()
	hash.Write([]byte(key))
	return new(big.Int).SetBytes(hash.Sum(nil))
}
