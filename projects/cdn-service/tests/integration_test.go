package tests

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"cdn-service/pkg/cache"
	"cdn-service/pkg/origin"
	"cdn-service/pkg/server"
)

func TestCDNServer_CacheMiss(t *testing.T) {
	// Create a test origin server
	originServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		w.Header().Set("X-Origin", "true")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "<html><body>Hello from Origin</body></html>")
	}))
	defer originServer.Close()

	// Create CDN server
	config := server.ServerConfig{
		Addr:           ":0", // Use random port
		ReadTimeout:    30 * time.Second,
		WriteTimeout:   30 * time.Second,
		MaxHeaderBytes: 1 << 20,
		DefaultTTL:     time.Hour,
		OriginURL:      originServer.URL,
	}

	cdnServer := server.NewServer(config)

	// Create a test request
	req := httptest.NewRequest("GET", "/test", nil)
	req.Host = "localhost"
	w := httptest.NewRecorder()

	// Handle the request
	cdnServer.handleRequest(w, req)

	// Check response
	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// Check cache header
	if resp.Header.Get("X-Cache") != "MISS" {
		t.Errorf("Expected X-Cache: MISS, got %s", resp.Header.Get("X-Cache"))
	}

	// Check body
	body, _ := io.ReadAll(resp.Body)
	if string(body) != "<html><body>Hello from Origin</body></html>" {
		t.Errorf("Unexpected body: %s", string(body))
	}
}

func TestCDNServer_CacheHit(t *testing.T) {
	// Create a test origin server that counts requests
	requestCount := 0
	originServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestCount++
		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "<html><body>Hello from Origin</body></html>")
	}))
	defer originServer.Close()

	// Create CDN server
	config := server.ServerConfig{
		Addr:           ":0",
		ReadTimeout:    30 * time.Second,
		WriteTimeout:   30 * time.Second,
		MaxHeaderBytes: 1 << 20,
		DefaultTTL:     time.Hour,
		OriginURL:      originServer.URL,
	}

	cdnServer := server.NewServer(config)

	// First request (cache miss)
	req1 := httptest.NewRequest("GET", "/test", nil)
	req1.Host = "localhost"
	w1 := httptest.NewRecorder()
	cdnServer.handleRequest(w1, req1)

	// Second request (cache hit)
	req2 := httptest.NewRequest("GET", "/test", nil)
	req2.Host = "localhost"
	w2 := httptest.NewRecorder()
	cdnServer.handleRequest(w2, req2)

	// Check that origin was only called once
	if requestCount != 1 {
		t.Errorf("Expected origin called once, got %d", requestCount)
	}

	// Check cache header for second request
	resp2 := w2.Result()
	if resp2.Header.Get("X-Cache") != "HIT" {
		t.Errorf("Expected X-Cache: HIT, got %s", resp2.Header.Get("X-Cache"))
	}
}

func TestCDNServer_CacheExpiration(t *testing.T) {
	// Create a test origin server
	requestCount := 0
	originServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestCount++
		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, "<html><body>Request %d</body></html>", requestCount)
	}))
	defer originServer.Close()

	// Create CDN server with short TTL
	config := server.ServerConfig{
		Addr:           ":0",
		ReadTimeout:    30 * time.Second,
		WriteTimeout:   30 * time.Second,
		MaxHeaderBytes: 1 << 20,
		DefaultTTL:     100 * time.Millisecond, // Short TTL
		OriginURL:      originServer.URL,
	}

	cdnServer := server.NewServer(config)

	// First request
	req1 := httptest.NewRequest("GET", "/test", nil)
	req1.Host = "localhost"
	w1 := httptest.NewRecorder()
	cdnServer.handleRequest(w1, req1)

	// Wait for cache to expire
	time.Sleep(150 * time.Millisecond)

	// Second request (should be cache miss)
	req2 := httptest.NewRequest("GET", "/test", nil)
	req2.Host = "localhost"
	w2 := httptest.NewRecorder()
	cdnServer.handleRequest(w2, req2)

	// Check that origin was called twice
	if requestCount != 2 {
		t.Errorf("Expected origin called twice, got %d", requestCount)
	}

	// Check cache header for second request
	resp2 := w2.Result()
	if resp2.Header.Get("X-Cache") != "MISS" {
		t.Errorf("Expected X-Cache: MISS, got %s", resp2.Header.Get("X-Cache"))
	}
}

func TestCDNServer_OriginError(t *testing.T) {
	// Create a test origin server that returns errors
	originServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer originServer.Close()

	// Create CDN server
	config := server.ServerConfig{
		Addr:           ":0",
		ReadTimeout:    30 * time.Second,
		WriteTimeout:   30 * time.Second,
		MaxHeaderBytes: 1 << 20,
		DefaultTTL:     time.Hour,
		OriginURL:      originServer.URL,
	}

	cdnServer := server.NewServer(config)

	// Make a request
	req := httptest.NewRequest("GET", "/test", nil)
	req.Host = "localhost"
	w := httptest.NewRecorder()
	cdnServer.handleRequest(w, req)

	// Check response
	resp := w.Result()
	if resp.StatusCode != http.StatusBadGateway {
		t.Errorf("Expected status 502, got %d", resp.StatusCode)
	}
}

func TestCDNServer_NonCacheableResponse(t *testing.T) {
	// Create a test origin server that returns 404
	requestCount := 0
	originServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestCount++
		w.WriteHeader(http.StatusNotFound)
		fmt.Fprint(w, "Not Found")
	}))
	defer originServer.Close()

	// Create CDN server
	config := server.ServerConfig{
		Addr:           ":0",
		ReadTimeout:    30 * time.Second,
		WriteTimeout:   30 * time.Second,
		MaxHeaderBytes: 1 << 20,
		DefaultTTL:     time.Hour,
		OriginURL:      originServer.URL,
	}

	cdnServer := server.NewServer(config)

	// First request
	req1 := httptest.NewRequest("GET", "/not-found", nil)
	req1.Host = "localhost"
	w1 := httptest.NewRecorder()
	cdnServer.handleRequest(w1, req1)

	// Second request (should not be cached)
	req2 := httptest.NewRequest("GET", "/not-found", nil)
	req2.Host = "localhost"
	w2 := httptest.NewRecorder()
	cdnServer.handleRequest(w2, req2)

	// Check that origin was called twice (not cached)
	if requestCount != 2 {
		t.Errorf("Expected origin called twice, got %d", requestCount)
	}
}

func TestCacheManager_Integration(t *testing.T) {
	// Create cache manager
	cm := cache.NewCacheManager(10, time.Hour, time.Minute)

	// Add items
	for i := 0; i < 10; i++ {
		key := fmt.Sprintf("key%d", i)
		cm.Set(key, &cache.CacheItem{
			Key:        key,
			Value:      []byte(fmt.Sprintf("value%d", i)),
			StatusCode: 200,
		}, time.Hour)
	}

	// Check all items exist
	for i := 0; i < 10; i++ {
		key := fmt.Sprintf("key%d", i)
		item, ok := cm.Get(key)
		if !ok {
			t.Errorf("Expected to find %s", key)
		}
		if string(item.Value) != fmt.Sprintf("value%d", i) {
			t.Errorf("Expected value%d, got %s", i, string(item.Value))
		}
	}

	// Check stats
	stats := cm.Stats()
	if stats.Hits != 10 {
		t.Errorf("Expected 10 hits, got %d", stats.Hits)
	}
	if stats.Misses != 0 {
		t.Errorf("Expected 0 misses, got %d", stats.Misses)
	}
}

func TestOriginFetcher_Integration(t *testing.T) {
	// Create a test origin server
	originServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "Hello World")
	}))
	defer originServer.Close()

	// Create fetcher
	fetcher := origin.NewFetcher(originServer.URL)

	// Fetch content
	resp, err := fetcher.Fetch("/test", nil)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	if string(resp.Body) != "Hello World" {
		t.Errorf("Expected 'Hello World', got '%s'", string(resp.Body))
	}
}

func TestOriginFetcher_WithRetry_Integration(t *testing.T) {
	attempts := 0

	// Create a test origin server that fails twice
	originServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		if attempts < 3 {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "Success")
	}))
	defer originServer.Close()

	// Create fetcher with retries
	fetcher := origin.NewFetcher(originServer.URL,
		origin.WithRetries(3),
		origin.WithRetryDelay(10*time.Millisecond),
	)

	// Fetch content
	resp, err := fetcher.FetchWithRetry("/test", nil)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	if attempts != 3 {
		t.Errorf("Expected 3 attempts, got %d", attempts)
	}
}