package main

import (
	"fmt"
	"time"

	dnsserver "dns-server/src"
)

// This demo shows how DNS caching works.
//
// DNS caching is essential for performance:
//   - Reduces latency: cached responses are returned instantly
//   - Reduces server load: fewer queries reach authoritative servers
//   - Reduces network traffic: less data on the wire
//
// Cache entries expire based on TTL (Time To Live):
//   - TTL is set by the authoritative server
//   - Clients must respect the TTL
//   - When TTL expires, the entry is removed from cache
//
// This demo shows:
//   1. Adding entries to cache
//   2. Retrieving cached entries
//   3. TTL-based expiration
//   4. Cache eviction when full
func main() {
	fmt.Println("=== DNS Caching Demo ===\n")

	// Create a cache with 1000 entry limit
	cache := dnsserver.NewDNSCache(1024)
	fmt.Printf("Cache created with max size: %d\n", cache.Size())

	// Create a mock response message
	response := dnsserver.NewResponse(0)
	response.Header.ANCount = 1
	response.Answers = []dnsserver.ResourceRecord{
		{
			Name:  "www.example.com",
			Type:  dnsserver.TypeA,
			Class: dnsserver.ClassIN,
			TTL:   300, // 5 minutes
			Data:  []byte{93, 184, 216, 34},
			RawData: &dnsserver.IPv4Address{IP: []byte{93, 184, 216, 34}},
		},
	}

	fmt.Printf("\nCached entry for: %s\n", key)
	fmt.Printf("Cache size: %d\n", cache.Size())

	// Retrieve from cache
	if cached, ok := cache.Get(key); ok {
		fmt.Printf("\nCache HIT for: %s\n", key)
		fmt.Printf("  IP: %s\n", cached.Answers[0].RawData.(*dnsserver.IPv4Address).String())
		fmt.Printf("  TTL: %d seconds\n", cached.Answers[0].TTL)
	} else {
		fmt.Printf("\nCache MISS for: %s\n", key)
	}

	// Add to cache
	key := dnsserver.CacheKey("www.example.com", dnsserver.TypeA, dnsserver.ClassIN)
	cache.Put(key, response, 300)
	fmt.Printf("\nCached entry for: %s\n", key)
	fmt.Printf("Cache size: %d\n", cache.Size())

	// Retrieve from cache
	if cached, ok := cache.Get(key); ok {
		fmt.Printf("\nCache HIT for: %s\n", key)
		fmt.Printf("  IP: %s\n", cached.Answers[0].RawData.(*dns.IPv4Address).String())
		fmt.Printf("  TTL: %d seconds\n", cached.Answers[0].TTL)
	} else {
		fmt.Printf("\nCache MISS for: %s\n", key)
	}

	// Demonstrate TTL expiration
	fmt.Println("\n--- TTL Expiration Demo ---")
	expiringKey := dnsserver.CacheKey("temp.example.com", dnsserver.TypeA, dnsserver.ClassIN)

	expiringResp := dnsserver.NewResponse(0)
	expiringResp.Header.ANCount = 1
	expiringResp.Answers = []dnsserver.ResourceRecord{
		{
			Name:  "temp.example.com",
			Type:  dnsserver.TypeA,
			Class: dnsserver.ClassIN,
			TTL:   1, // Only 1 second TTL
			Data:  []byte{1, 2, 3, 4},
			RawData: &dnsserver.IPv4Address{IP: []byte{1, 2, 3, 4}},
		},
	}
	cache.Put(expiringKey, expiringResp, 1)

	fmt.Printf("  Cached temp.example.com with TTL=1s\n")
	fmt.Printf("  Checking before expiration... ")
	if _, ok := cache.Get(expiringKey); ok {
		fmt.Println("HIT (not yet expired)")
	} else {
		fmt.Println("MISS (unexpected)")
	}

	// Wait for TTL to expire
	fmt.Println("  Waiting 2 seconds for TTL to expire...")
	time.Sleep(2 * time.Second)

	fmt.Printf("  Checking after expiration... ")
	if _, ok := cache.Get(expiringKey); ok {
		fmt.Println("HIT (unexpected)")
	} else {
		fmt.Println("MISS (expired correctly)")
	}

	// Demonstrate cache eviction when full
	fmt.Println("\n--- Cache Eviction Demo ---")
	largeCache := dnsserver.NewDNSCache(5) // Only 5 entries
	fmt.Printf("Cache with max size: %d\n", 5)

	for i := 0; i < 10; i++ {
		name := fmt.Sprintf("host%d.example.com", i)
		key := dnsserver.CacheKey(name, dnsserver.TypeA, dnsserver.ClassIN)
		resp := dnsserver.NewResponse(0)
		resp.Header.ANCount = 1
		resp.Answers = []dnsserver.ResourceRecord{
			{
				Name:  name,
				Type:  dnsserver.TypeA,
				Class: dnsserver.ClassIN,
				TTL:   3600,
				Data:  []byte{10 + byte(i), 0, 0, 1},
				RawData: &dnsserver.IPv4Address{IP: []byte{10 + byte(i), 0, 0, 1}},
			},
		}
		cache.Put(key, resp, 3600)
	}

	fmt.Printf("  Added 10 entries to cache of size 5\n")
	fmt.Printf("  Cache size: %d\n", largeCache.Size())

	// Try to retrieve old entries (they should be evicted)
	fmt.Println("  Checking if old entries are still cached:")
	for i := 0; i < 10; i++ {
		name := fmt.Sprintf("host%d.example.com", i)
		key := dnsserver.CacheKey(name, dnsserver.TypeA, dnsserver.ClassIN)
		if _, ok := largeCache.Get(key); ok {
			fmt.Printf("    %s: HIT\n", name)
		} else {
			fmt.Printf("    %s: MISS (evicted)\n", name)
		}
	}

	// Demonstrate cache statistics
	fmt.Println("\n--- Cache Statistics ---")
	fmt.Printf("  Total entries: %d\n", cache.Size())
	fmt.Printf("  Cache hit for www.example.com: ")
	if _, ok := cache.Get(key); ok {
		fmt.Println("YES")
	} else {
		fmt.Println("NO")
	}

	// Clear cache
	cache.Clear()
	fmt.Printf("  After clear, size: %d\n", cache.Size())
}
