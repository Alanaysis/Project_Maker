package cache

import (
	"fmt"
	"sync"
	"testing"
	"time"
)

func TestLRUCache_Get(t *testing.T) {
	cache := NewLRUCache(10)

	// Test cache miss
	item, ok := cache.Get("key1")
	if ok {
		t.Error("Expected cache miss, got hit")
	}
	if item != nil {
		t.Error("Expected nil item on cache miss")
	}

	// Test cache hit
	cache.Put("key1", &CacheItem{
		Key:   "key1",
		Value: []byte("value1"),
	})

	item, ok = cache.Get("key1")
	if !ok {
		t.Error("Expected cache hit, got miss")
	}
	if string(item.Value) != "value1" {
		t.Errorf("Expected 'value1', got '%s'", string(item.Value))
	}
}

func TestLRUCache_Put(t *testing.T) {
	cache := NewLRUCache(2)

	// Add first item
	cache.Put("key1", &CacheItem{Key: "key1", Value: []byte("value1")})
	if cache.Len() != 1 {
		t.Errorf("Expected length 1, got %d", cache.Len())
	}

	// Add second item
	cache.Put("key2", &CacheItem{Key: "key2", Value: []byte("value2")})
	if cache.Len() != 2 {
		t.Errorf("Expected length 2, got %d", cache.Len())
	}

	// Add third item (should evict key1)
	cache.Put("key3", &CacheItem{Key: "key3", Value: []byte("value3")})
	if cache.Len() != 2 {
		t.Errorf("Expected length 2, got %d", cache.Len())
	}

	// key1 should be evicted
	_, ok := cache.Get("key1")
	if ok {
		t.Error("Expected key1 to be evicted")
	}

	// key2 and key3 should exist
	_, ok = cache.Get("key2")
	if !ok {
		t.Error("Expected key2 to exist")
	}
	_, ok = cache.Get("key3")
	if !ok {
		t.Error("Expected key3 to exist")
	}
}

func TestLRUCache_Update(t *testing.T) {
	cache := NewLRUCache(10)

	// Add item
	cache.Put("key1", &CacheItem{Key: "key1", Value: []byte("value1")})

	// Update item
	cache.Put("key1", &CacheItem{Key: "key1", Value: []byte("value2")})

	// Get updated item
	item, ok := cache.Get("key1")
	if !ok {
		t.Error("Expected cache hit")
	}
	if string(item.Value) != "value2" {
		t.Errorf("Expected 'value2', got '%s'", string(item.Value))
	}
}

func TestLRUCache_Delete(t *testing.T) {
	cache := NewLRUCache(10)

	// Add item
	cache.Put("key1", &CacheItem{Key: "key1", Value: []byte("value1")})

	// Delete item
	cache.Delete("key1")

	// Should be cache miss
	_, ok := cache.Get("key1")
	if ok {
		t.Error("Expected cache miss after delete")
	}
}

func TestLRUCache_Clear(t *testing.T) {
	cache := NewLRUCache(10)

	// Add items
	cache.Put("key1", &CacheItem{Key: "key1", Value: []byte("value1")})
	cache.Put("key2", &CacheItem{Key: "key2", Value: []byte("value2")})

	// Clear cache
	cache.Clear()

	if cache.Len() != 0 {
		t.Errorf("Expected length 0, got %d", cache.Len())
	}
}

func TestLRUCache_Concurrent(t *testing.T) {
	cache := NewLRUCache(100)
	var wg sync.WaitGroup

	// Concurrent writes
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			key := fmt.Sprintf("key%d", i)
			cache.Put(key, &CacheItem{
				Key:   key,
				Value: []byte(fmt.Sprintf("value%d", i)),
			})
		}(i)
	}
	wg.Wait()

	// Concurrent reads
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			key := fmt.Sprintf("key%d", i)
			_, ok := cache.Get(key)
			if !ok {
				t.Errorf("Expected to find key %s", key)
			}
		}(i)
	}
	wg.Wait()
}

func TestCacheManager_Get(t *testing.T) {
	cm := NewCacheManager(10, time.Hour, time.Minute)

	// Test cache miss
	item, ok := cm.Get("key1")
	if ok {
		t.Error("Expected cache miss")
	}

	// Test cache hit
	cm.Set("key1", &CacheItem{
		Key:        "key1",
		Value:      []byte("value1"),
		StatusCode: 200,
	}, time.Hour)

	item, ok = cm.Get("key1")
	if !ok {
		t.Error("Expected cache hit")
	}
	if string(item.Value) != "value1" {
		t.Errorf("Expected 'value1', got '%s'", string(item.Value))
	}
}

func TestCacheManager_Expiration(t *testing.T) {
	cm := NewCacheManager(10, time.Millisecond*100, time.Minute)

	// Add item with short TTL
	cm.Set("key1", &CacheItem{
		Key:        "key1",
		Value:      []byte("value1"),
		StatusCode: 200,
	}, time.Millisecond*50)

	// Should be cache hit immediately
	_, ok := cm.Get("key1")
	if !ok {
		t.Error("Expected cache hit")
	}

	// Wait for expiration
	time.Sleep(time.Millisecond * 100)

	// Should be cache miss after expiration
	_, ok = cm.Get("key1")
	if ok {
		t.Error("Expected cache miss after expiration")
	}
}

func TestCacheManager_Stats(t *testing.T) {
	cm := NewCacheManager(10, time.Hour, time.Minute)

	// Generate some hits and misses
	cm.Get("key1") // miss
	cm.Set("key1", &CacheItem{
		Key:        "key1",
		Value:      []byte("value1"),
		StatusCode: 200,
	}, time.Hour)
	cm.Get("key1") // hit
	cm.Get("key2") // miss

	stats := cm.Stats()
	if stats.Hits != 1 {
		t.Errorf("Expected 1 hit, got %d", stats.Hits)
	}
	if stats.Misses != 2 {
		t.Errorf("Expected 2 misses, got %d", stats.Misses)
	}
}

func TestCacheManager_HitRate(t *testing.T) {
	stats := &CacheStats{
		Hits:   3,
		Misses: 1,
	}

	rate := stats.HitRate()
	if rate != 0.75 {
		t.Errorf("Expected hit rate 0.75, got %f", rate)
	}
}

func TestCacheManager_ZeroHitRate(t *testing.T) {
	stats := &CacheStats{}

	rate := stats.HitRate()
	if rate != 0 {
		t.Errorf("Expected hit rate 0, got %f", rate)
	}
}

func BenchmarkLRUCache_Get(b *testing.B) {
	cache := NewLRUCache(1000)
	for i := 0; i < 1000; i++ {
		key := fmt.Sprintf("key%d", i)
		cache.Put(key, &CacheItem{Key: key, Value: []byte("value")})
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		key := fmt.Sprintf("key%d", i%1000)
		cache.Get(key)
	}
}

func BenchmarkLRUCache_Put(b *testing.B) {
	cache := NewLRUCache(1000)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		key := fmt.Sprintf("key%d", i)
		cache.Put(key, &CacheItem{Key: key, Value: []byte("value")})
	}
}