package tests

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"cdn-service/pkg/cache"
	"cdn-service/pkg/origin"
)

func BenchmarkCDNServer_CacheHit(b *testing.B) {
	// Create a test origin server
	originServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "<html><body>Hello</body></html>")
	}))
	defer originServer.Close()

	// Create cache manager
	cm := cache.NewCacheManager(1000, time.Hour, time.Minute)

	// Pre-populate cache
	for i := 0; i < 100; i++ {
		key := fmt.Sprintf("GET:localhost:/path%d", i)
		cm.Set(key, &cache.CacheItem{
			Key:        key,
			Value:      []byte("<html><body>Hello</body></html>"),
			Headers:    http.Header{"Content-Type": []string{"text/html"}},
			StatusCode: 200,
		}, time.Hour)
	}

	// Create origin fetcher
	fetcher := origin.NewFetcher(originServer.URL)

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		key := fmt.Sprintf("GET:localhost:/path%d", i%100)
		item, ok := cm.Get(key)
		if ok {
			_ = item
		} else {
			// Cache miss - fetch from origin
			resp, _ := fetcher.Fetch(fmt.Sprintf("/path%d", i%100), nil)
			if resp != nil {
				cm.Set(key, &cache.CacheItem{
					Key:        key,
					Value:      resp.Body,
					Headers:    resp.Headers,
					StatusCode: resp.StatusCode,
				}, time.Hour)
			}
		}
	}
}

func BenchmarkCDNServer_CacheMiss(b *testing.B) {
	// Create a test origin server
	originServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "<html><body>Hello</body></html>")
	}))
	defer originServer.Close()

	// Create cache manager with small capacity
	cm := cache.NewCacheManager(10, time.Hour, time.Minute)

	// Create origin fetcher
	fetcher := origin.NewFetcher(originServer.URL)

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		key := fmt.Sprintf("GET:localhost:/path%d", i)
		_, ok := cm.Get(key)
		if !ok {
			// Cache miss - fetch from origin
			resp, _ := fetcher.Fetch(fmt.Sprintf("/path%d", i), nil)
			if resp != nil {
				cm.Set(key, &cache.CacheItem{
					Key:        key,
					Value:      resp.Body,
					Headers:    resp.Headers,
					StatusCode: resp.StatusCode,
				}, time.Hour)
			}
		}
	}
}

func BenchmarkCacheManager_Get(b *testing.B) {
	cm := cache.NewCacheManager(1000, time.Hour, time.Minute)

	// Pre-populate cache
	for i := 0; i < 1000; i++ {
		key := fmt.Sprintf("key%d", i)
		cm.Set(key, &cache.CacheItem{
			Key:   key,
			Value: []byte("value"),
		}, time.Hour)
	}

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		key := fmt.Sprintf("key%d", i%1000)
		cm.Get(key)
	}
}

func BenchmarkCacheManager_Set(b *testing.B) {
	cm := cache.NewCacheManager(1000, time.Hour, time.Minute)

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		key := fmt.Sprintf("key%d", i)
		cm.Set(key, &cache.CacheItem{
			Key:   key,
			Value: []byte("value"),
		}, time.Hour)
	}
}

func BenchmarkOriginFetcher_Fetch(b *testing.B) {
	// Create a test origin server
	originServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "<html><body>Hello</body></html>")
	}))
	defer originServer.Close()

	// Create fetcher
	fetcher := origin.NewFetcher(originServer.URL)

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		fetcher.Fetch(fmt.Sprintf("/path%d", i%100), nil)
	}
}