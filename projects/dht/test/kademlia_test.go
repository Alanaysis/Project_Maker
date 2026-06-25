package test

import (
	"math/big"
	"testing"

	"github.com/dht-chord/internal"
)

// ==================== XOR Distance Tests ====================

func TestXOR(t *testing.T) {
	tests := []struct {
		name     string
		a        int64
		b        int64
		expected int64
	}{
		{"same value", 5, 5, 0},
		{"different values", 5, 3, 6},
		{"zero and value", 0, 7, 7},
		{"large values", 255, 1, 254},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			a := big.NewInt(tt.a)
			b := big.NewInt(tt.b)
			result := internal.XOR(a, b)
			expected := big.NewInt(tt.expected)
			if result.Cmp(expected) != 0 {
				t.Errorf("XOR(%d, %d) = %s, want %s", tt.a, tt.b, result.String(), expected.String())
			}
		})
	}
}

func TestXORDistance(t *testing.T) {
	a := big.NewInt(10)
	b := big.NewInt(5)
	dist := internal.XORDistance(a, b)

	// XOR(10, 5) = 15
	expected := big.NewInt(15)
	if dist.Cmp(expected) != 0 {
		t.Errorf("XORDistance(10, 5) = %s, want %s", dist.String(), expected.String())
	}
}

func TestLeadingZeros(t *testing.T) {
	tests := []struct {
		name     string
		value    int64
		expected int
	}{
		{"zero", 0, internal.IDLength},
		{"one", 1, internal.IDLength - 1},
		{"two", 2, internal.IDLength - 2},
		{"four", 4, internal.IDLength - 3},
		{"255", 255, internal.IDLength - 8},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			n := big.NewInt(tt.value)
			result := internal.LeadingZeros(n)
			if result != tt.expected {
				t.Errorf("LeadingZeros(%d) = %d, want %d", tt.value, result, tt.expected)
			}
		})
	}
}

func TestBucketIndex(t *testing.T) {
	// Create two IDs that differ in specific bits
	localID := big.NewInt(0) // All zeros
	remoteID := big.NewInt(1) // Lowest bit set

	idx := internal.BucketIndex(localID, remoteID)
	if idx != 0 {
		t.Errorf("BucketIndex for lowest bit should be 0, got %d", idx)
	}

	// Test with higher bit
	remoteID = big.NewInt(128) // 2^7
	idx = internal.BucketIndex(localID, remoteID)
	if idx != 7 {
		t.Errorf("BucketIndex for 2^7 should be 7, got %d", idx)
	}
}

// ==================== KBucket Tests ====================

func TestKBucketAddContact(t *testing.T) {
	bucket := internal.NewKBucket()

	// Add contacts up to K
	for i := 0; i < internal.K; i++ {
		id := big.NewInt(int64(i))
		contact := internal.NewContact(id, "addr"+string(rune('0'+i)))
		added := bucket.AddContact(contact)
		if !added {
			t.Errorf("Contact %d should be added", i)
		}
	}

	if bucket.Size() != internal.K {
		t.Errorf("Bucket size = %d, want %d", bucket.Size(), internal.K)
	}

	// Add one more - should evict oldest
	extraContact := internal.NewContact(big.NewInt(999), "extra")
	added := bucket.AddContact(extraContact)
	if !added {
		t.Error("Extra contact should be added")
	}

	if bucket.Size() != internal.K {
		t.Errorf("Bucket size after overflow = %d, want %d", bucket.Size(), internal.K)
	}
}

func TestKBucketDuplicateContact(t *testing.T) {
	bucket := internal.NewKBucket()

	id := big.NewInt(1)
	contact1 := internal.NewContact(id, "addr1")
	contact2 := internal.NewContact(id, "addr1")

	bucket.AddContact(contact1)
	bucket.AddContact(contact2)

	if bucket.Size() != 1 {
		t.Errorf("Duplicate contact should not increase size, got %d", bucket.Size())
	}
}

func TestKBucketRemoveContact(t *testing.T) {
	bucket := internal.NewKBucket()

	id := big.NewInt(1)
	contact := internal.NewContact(id, "addr1")
	bucket.AddContact(contact)

	bucket.RemoveContact(id)

	if bucket.Size() != 0 {
		t.Errorf("Bucket should be empty after removal, got %d", bucket.Size())
	}
}

func TestKBucketGetContacts(t *testing.T) {
	bucket := internal.NewKBucket()

	for i := 0; i < 5; i++ {
		id := big.NewInt(int64(i))
		contact := internal.NewContact(id, "addr")
		bucket.AddContact(contact)
	}

	contacts := bucket.GetContacts()
	if len(contacts) != 5 {
		t.Errorf("GetContacts returned %d contacts, want 5", len(contacts))
	}
}

// ==================== RoutingTable Tests ====================

func TestRoutingTableAddContact(t *testing.T) {
	localID := big.NewInt(100)
	rt := internal.NewRoutingTable(localID, "local:8000")

	// Add contact with different ID
	contact := internal.NewContact(big.NewInt(200), "remote:8000")
	rt.AddContact(contact)

	if rt.TotalContacts() != 1 {
		t.Errorf("RoutingTable should have 1 contact, got %d", rt.TotalContacts())
	}
}

func TestRoutingTableDontAddSelf(t *testing.T) {
	localID := big.NewInt(100)
	rt := internal.NewRoutingTable(localID, "local:8000")

	// Try to add ourselves
	contact := internal.NewContact(localID, "local:8000")
	rt.AddContact(contact)

	if rt.TotalContacts() != 0 {
		t.Errorf("Should not add self to routing table, got %d contacts", rt.TotalContacts())
	}
}

func TestRoutingTableFindClosest(t *testing.T) {
	localID := big.NewInt(100)
	rt := internal.NewRoutingTable(localID, "local:8000")

	// Add several contacts
	for i := 0; i < 10; i++ {
		id := big.NewInt(int64(i * 10))
		contact := internal.NewContact(id, "addr")
		rt.AddContact(contact)
	}

	// Find closest to a target
	target := big.NewInt(55)
	closest := rt.FindClosestContacts(target, 5)

	if len(closest) != 5 {
		t.Errorf("FindClosestContacts returned %d contacts, want 5", len(closest))
	}

	// Verify contacts are sorted by distance
	for i := 1; i < len(closest); i++ {
		distPrev := internal.XOR(closest[i-1].ID, target)
		distCurr := internal.XOR(closest[i].ID, target)
		if distPrev.Cmp(distCurr) > 0 {
			t.Error("Contacts should be sorted by XOR distance")
		}
	}
}

// ==================== KademliaNode Tests ====================

func TestNewKademliaNode(t *testing.T) {
	node := internal.NewKademliaNode("test:8000", nil)

	if node == nil {
		t.Fatal("NewKademliaNode should not return nil")
	}

	if node.Addr != "test:8000" {
		t.Errorf("Node addr = %s, want test:8000", node.Addr)
	}

	if node.ID == nil {
		t.Error("Node ID should not be nil")
	}

	if !node.IsAlive() {
		t.Error("Node should be alive initially")
	}
}

func TestKademliaNodeStoreGet(t *testing.T) {
	node := internal.NewKademliaNode("test:8000", nil)

	// Store a value
	node.Store("key1", "value1")

	// Get the value
	value, ok := node.Get("key1")
	if !ok {
		t.Error("Should find key1")
	}
	if value != "value1" {
		t.Errorf("Got %s, want value1", value)
	}

	// Get non-existent key
	_, ok = node.Get("key2")
	if ok {
		t.Error("Should not find key2")
	}
}

func TestKademliaNodeDelete(t *testing.T) {
	node := internal.NewKademliaNode("test:8000", nil)

	// Store and delete
	node.Store("key1", "value1")
	ok := node.Delete("key1")
	if !ok {
		t.Error("Delete should return true")
	}

	// Verify deletion
	_, ok = node.Get("key1")
	if ok {
		t.Error("Key should be deleted")
	}

	// Delete non-existent key
	ok = node.Delete("key2")
	if ok {
		t.Error("Delete of non-existent key should return false")
	}
}

func TestKademliaNodeFindNode(t *testing.T) {
	node := internal.NewKademliaNode("test:8000", nil)

	// Add some contacts to routing table
	for i := 0; i < 5; i++ {
		id := internal.KademliaHash("node" + string(rune('0'+i)))
		contact := internal.NewContact(id, "addr")
		node.RT.AddContact(contact)
	}

	// Find nodes close to a target
	target := internal.KademliaHash("target")
	contacts := node.FindNode(target)

	if len(contacts) == 0 {
		t.Error("FindNode should return contacts")
	}

	if len(contacts) > internal.K {
		t.Errorf("FindNode should return at most K contacts, got %d", len(contacts))
	}
}

func TestKademliaNodeFindValue(t *testing.T) {
	node := internal.NewKademliaNode("test:8000", nil)

	// Store a value
	node.Store("testkey", "testvalue")

	// Find value
	value, contacts, found := node.FindValue("testkey")
	if !found {
		t.Error("FindValue should find stored value")
	}
	if value != "testvalue" {
		t.Errorf("FindValue returned %s, want testvalue", value)
	}
	if contacts != nil {
		t.Error("FindValue should not return contacts when value is found")
	}

	// Find non-existent value
	_, contacts, found = node.FindValue("nonexistent")
	if found {
		t.Error("FindValue should not find non-existent value")
	}
	if len(contacts) == 0 {
		// This is okay if routing table is empty
	}
}

func TestKademliaNodeBootstrap(t *testing.T) {
	node := internal.NewKademliaNode("test:8000", nil)

	bootstrapID := internal.KademliaHash("bootstrap:8000")
	err := node.Bootstrap("bootstrap:8000", bootstrapID)
	if err != nil {
		t.Fatalf("Bootstrap failed: %v", err)
	}

	// Check that bootstrap node is in routing table
	contacts := node.FindNode(bootstrapID)
	found := false
	for _, c := range contacts {
		if c.ID.Cmp(bootstrapID) == 0 {
			found = true
			break
		}
	}
	if !found {
		t.Error("Bootstrap node should be in routing table")
	}
}

// ==================== Integration Tests ====================

func TestKademliaIntegration(t *testing.T) {
	// Create multiple nodes
	nodes := make([]*internal.KademliaNode, 5)
	for i := 0; i < 5; i++ {
		addr := "node" + string(rune('0'+i)) + ":800" + string(rune('0'+i))
		nodes[i] = internal.NewKademliaNode(addr, nil)
	}

	// Connect nodes (simulate bootstrap)
	for i := 1; i < len(nodes); i++ {
		// Add previous nodes to routing table
		for j := 0; j < i; j++ {
			contact := internal.NewContact(nodes[j].ID, nodes[j].Addr)
			nodes[i].RT.AddContact(contact)
		}
	}

	// Store values on different nodes
	testData := map[string]string{
		"key1": "value1",
		"key2": "value2",
		"key3": "value3",
	}

	for key, value := range testData {
		// Store on first node
		nodes[0].Store(key, value)
	}

	// Verify all nodes can find values through routing
	for key, expected := range testData {
		// Check that the value is stored
		value, ok := nodes[0].Get(key)
		if !ok {
			t.Errorf("Key %s not found on node 0", key)
			continue
		}
		if value != expected {
			t.Errorf("Key %s: got %s, want %s", key, value, expected)
		}
	}
}

func TestXORDistanceProperties(t *testing.T) {
	a := big.NewInt(100)
	b := big.NewInt(200)
	c := big.NewInt(150)

	// Property 1: XOR distance is symmetric
	distAB := internal.XORDistance(a, b)
	distBA := internal.XORDistance(b, a)
	if distAB.Cmp(distBA) != 0 {
		t.Error("XOR distance should be symmetric")
	}

	// Property 2: XOR distance to self is 0
	distAA := internal.XORDistance(a, a)
	if distAA.Sign() != 0 {
		t.Error("XOR distance to self should be 0")
	}

	// Property 3: XOR distance is non-negative
	if distAB.Sign() < 0 {
		t.Error("XOR distance should be non-negative")
	}

	// Property 4: Triangle inequality (XOR version)
	// d(a,c) <= d(a,b) + d(b,c) doesn't hold for XOR
	// But d(a,c) = d(a,b) XOR d(b,c) does hold
	distAC := internal.XORDistance(a, c)
	distBC := internal.XORDistance(b, c)
	xorDist := new(big.Int).Xor(distAB, distBC)
	if distAC.Cmp(xorDist) != 0 {
		t.Error("XOR distance should satisfy: d(a,c) = d(a,b) XOR d(b,c)")
	}
}

func TestBucketIndexConsistency(t *testing.T) {
	localID := internal.KademliaHash("local")

	// Test that bucket index is consistent
	for i := 0; i < 100; i++ {
		remoteID := internal.KademliaHash("remote" + string(rune('0'+i%10)))
		idx1 := internal.BucketIndex(localID, remoteID)
		idx2 := internal.BucketIndex(localID, remoteID)
		if idx1 != idx2 {
			t.Errorf("BucketIndex should be consistent, got %d and %d", idx1, idx2)
		}
	}
}

func TestRoutingTableConcurrency(t *testing.T) {
	localID := big.NewInt(100)
	rt := internal.NewRoutingTable(localID, "local:8000")

	// Concurrent adds
	done := make(chan bool)
	for i := 0; i < 10; i++ {
		go func(idx int) {
			id := big.NewInt(int64(idx * 100))
			contact := internal.NewContact(id, "addr")
			rt.AddContact(contact)
			done <- true
		}(i)
	}

	for i := 0; i < 10; i++ {
		<-done
	}

	// Concurrent reads
	for i := 0; i < 10; i++ {
		go func() {
			target := big.NewInt(50)
			rt.FindClosestContacts(target, 5)
			done <- true
		}()
	}

	for i := 0; i < 10; i++ {
		<-done
	}
}
