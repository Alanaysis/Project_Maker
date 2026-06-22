package server

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"cdn-service/pkg/cache"
	"cdn-service/pkg/origin"
)

func TestGenerateCacheKey(t *testing.T) {
	tests := []struct {
		method   string
		host     string
		path     string
		expected string
	}{
		{"GET", "example.com", "/", "GET:example.com:/"},
		{"GET", "example.com", "/test", "GET:example.com:/test"},
		{"POST", "example.com", "/api", "POST:example.com:/api"},
		{"GET", "localhost:8080", "/test", "GET:localhost:8080:/test"},
	}

	for _, test := range tests {
		req := httptest.NewRequest(test.method, test.path, nil)
		req.Host = test.host

		key := generateCacheKey(req)
		if key != test.expected {
			t.Errorf("generateCacheKey(%s, %s, %s) = %s, want %s",
				test.method, test.host, test.path, key, test.expected)
		}
	}
}

func TestIsCacheable(t *testing.T) {
	tests := []struct {
		statusCode int
		expected   bool
	}{
		{200, true},
		{203, true},
		{204, true},
		{206, true},
		{300, true},
		{301, true},
		{400, false},
		{404, false},
		{500, false},
		{502, false},
		{503, false},
	}

	for _, test := range tests {
		result := isCacheable(test.statusCode)
		if result != test.expected {
			t.Errorf("isCacheable(%d) = %v, want %v", test.statusCode, result, test.expected)
		}
	}
}

func TestWriteResponse(t *testing.T) {
	// Create a server
	config := DefaultConfig()
	config.OriginURL = "http://localhost:9090"
	srv := NewServer(config)

	// Create a cache item
	item := &cache.CacheItem{
		Key:        "test-key",
		Value:      []byte("<html>Test</html>"),
		Headers:    http.Header{"Content-Type": []string{"text/html"}},
		StatusCode: 200,
	}

	// Create a response recorder
	w := httptest.NewRecorder()

	// Write response
	srv.writeResponse(w, item)

	// Check response
	resp := w.Result()
	if resp.StatusCode != 200 {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	if resp.Header.Get("X-Cache") != "HIT" {
		t.Errorf("Expected X-Cache: HIT, got %s", resp.Header.Get("X-Cache"))
	}

	if resp.Header.Get("Content-Type") != "text/html" {
		t.Errorf("Expected Content-Type: text/html, got %s", resp.Header.Get("Content-Type"))
	}

	body, _ := io.ReadAll(resp.Body)
	if string(body) != "<html>Test</html>" {
		t.Errorf("Unexpected body: %s", string(body))
	}
}

func TestWriteFetchResponse(t *testing.T) {
	// Create a server
	config := DefaultConfig()
	config.OriginURL = "http://localhost:9090"
	srv := NewServer(config)

	// Create a fetch response
	resp := &origin.FetchResponse{
		StatusCode: 200,
		Headers:    http.Header{"Content-Type": []string{"text/plain"}},
		Body:       []byte("Hello World"),
		Size:       11,
	}

	// Create a response recorder
	w := httptest.NewRecorder()

	// Write response
	srv.writeFetchResponse(w, resp)

	// Check response
	result := w.Result()
	if result.StatusCode != 200 {
		t.Errorf("Expected status 200, got %d", result.StatusCode)
	}

	if result.Header.Get("X-Cache") != "MISS" {
		t.Errorf("Expected X-Cache: MISS, got %s", result.Header.Get("X-Cache"))
	}

	body, _ := io.ReadAll(result.Body)
	if string(body) != "Hello World" {
		t.Errorf("Unexpected body: %s", string(body))
	}
}

func TestHandleCacheStats(t *testing.T) {
	// Create a server
	config := DefaultConfig()
	config.OriginURL = "http://localhost:9090"
	srv := NewServer(config)

	// Create a request
	req := httptest.NewRequest("GET", "/admin/cache/stats", nil)
	w := httptest.NewRecorder()

	// Handle request
	srv.handleCacheStats(w, req)

	// Check response
	resp := w.Result()
	if resp.StatusCode != 200 {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	if resp.Header.Get("Content-Type") != "application/json" {
		t.Errorf("Expected Content-Type: application/json, got %s", resp.Header.Get("Content-Type"))
	}

	body, _ := io.ReadAll(resp.Body)
	if len(body) == 0 {
		t.Error("Expected non-empty body")
	}
}

func TestHandleCachePurge(t *testing.T) {
	// Create a server
	config := DefaultConfig()
	config.OriginURL = "http://localhost:9090"
	srv := NewServer(config)

	// Add an item to cache
	srv.cache.Set("test-key", &cache.CacheItem{
		Key:        "test-key",
		Value:      []byte("test-value"),
		StatusCode: 200,
	}, time.Hour)

	// Purge specific key
	req := httptest.NewRequest("POST", "/admin/cache/purge", nil)
	req.Body = io.NopCloser(fmt.Sprintf("/test"))
	w := httptest.NewRecorder()

	srv.handleCachePurge(w, req)

	// Check response
	resp := w.Result()
	if resp.StatusCode != 200 {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// Verify item was purged
	_, ok := srv.cache.Get("test-key")
	if ok {
		t.Error("Expected item to be purged")
	}
}

func TestHandleCachePurgeAll(t *testing.T) {
	// Create a server
	config := DefaultConfig()
	config.OriginURL = "http://localhost:9090"
	srv := NewServer(config)

	// Add items to cache
	srv.cache.Set("key1", &cache.CacheItem{Key: "key1", Value: []byte("value1")}, time.Hour)
	srv.cache.Set("key2", &cache.CacheItem{Key: "key2", Value: []byte("value2")}, time.Hour)

	// Purge all
	req := httptest.NewRequest("POST", "/admin/cache/purge", nil)
	req.Body = io.NopCloser(fmt.Sprintf(""))
	w := httptest.NewRecorder()

	srv.handleCachePurge(w, req)

	// Check response
	resp := w.Result()
	if resp.StatusCode != 200 {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// Verify cache is empty
	if srv.cache.Len() != 0 {
		t.Errorf("Expected cache to be empty, got %d items", srv.cache.Len())
	}
}

func TestHandleCachePurgeMethodNotAllowed(t *testing.T) {
	// Create a server
	config := DefaultConfig()
	config.OriginURL = "http://localhost:9090"
	srv := NewServer(config)

	// Try GET method (should fail)
	req := httptest.NewRequest("GET", "/admin/cache/purge", nil)
	w := httptest.NewRecorder()

	srv.handleCachePurge(w, req)

	// Check response
	resp := w.Result()
	if resp.StatusCode != http.StatusMethodNotAllowed {
		t.Errorf("Expected status 405, got %d", resp.StatusCode)
	}
}

func TestHandleHealth(t *testing.T) {
	// Create a server
	config := DefaultConfig()
	config.OriginURL = "http://localhost:9090"
	srv := NewServer(config)

	// Create a request
	req := httptest.NewRequest("GET", "/admin/health", nil)
	w := httptest.NewRecorder()

	// Handle request
	srv.handleHealth(w, req)

	// Check response
	resp := w.Result()
	if resp.StatusCode != 200 {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	if resp.Header.Get("Content-Type") != "application/json" {
		t.Errorf("Expected Content-Type: application/json, got %s", resp.Header.Get("Content-Type"))
	}

	body, _ := io.ReadAll(resp.Body)
	if len(body) == 0 {
		t.Error("Expected non-empty body")
	}
}