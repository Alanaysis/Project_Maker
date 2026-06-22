package server

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"cdn-service/pkg/cache"
	"cdn-service/pkg/dispatcher"
	"cdn-service/pkg/origin"
)

// ServerConfig holds the configuration for the CDN server.
type ServerConfig struct {
	Addr           string
	ReadTimeout    time.Duration
	WriteTimeout   time.Duration
	MaxHeaderBytes int
	DefaultTTL     time.Duration
	OriginURL      string
	AdminToken     string // Bearer token required for admin endpoints
}

// DefaultConfig returns a default server configuration.
func DefaultConfig() ServerConfig {
	return ServerConfig{
		Addr:           ":8080",
		ReadTimeout:    30 * time.Second,
		WriteTimeout:   30 * time.Second,
		MaxHeaderBytes: 1 << 20, // 1MB
		DefaultTTL:     1 * time.Hour,
		OriginURL:      "http://localhost:9090",
	}
}

// Server is the main CDN server that handles HTTP requests.
// It coordinates between the cache, origin fetcher, and dispatcher.
//
// ⭐ Key Responsibilities:
// 1. Accept HTTP requests
// 2. Check cache for content
// 3. Fetch from origin if cache miss
// 4. Cache the response
// 5. Return the response to the client
//
// 💡 Request Flow:
// Client → Server → Cache Lookup → [HIT] → Return Cached
//                                → [MISS] → Origin Fetch → Cache → Return
type Server struct {
	config     ServerConfig
	cache      *cache.CacheManager
	origin     *origin.Fetcher
	dispatcher *dispatcher.Dispatcher
	httpServer *http.Server
}

// NewServer creates a new CDN server with the given configuration.
//
// Parameters:
//   - config: server configuration
//
// Returns:
//   - *Server: a new server instance
func NewServer(config ServerConfig) *Server {
	// Create cache manager
	cacheManager := cache.NewCacheManager(
		1000,           // capacity
		config.DefaultTTL,
		5*time.Minute,  // cleanup interval
	)

	// Create origin fetcher
	originFetcher := origin.NewFetcher(
		config.OriginURL,
		origin.WithTimeout(10*time.Second),
		origin.WithRetries(3),
	)

	// Create dispatcher with round-robin strategy
	dispatch := dispatcher.NewDispatcher(
		dispatcher.NewRoundRobinStrategy(),
	)

	s := &Server{
		config:     config,
		cache:      cacheManager,
		origin:     originFetcher,
		dispatcher: dispatch,
	}

	// Create HTTP server
	mux := http.NewServeMux()
	mux.HandleFunc("/", s.handleRequest)
	mux.HandleFunc("/admin/cache/stats", s.handleCacheStats)
	mux.HandleFunc("/admin/cache/purge", s.handleCachePurge)
	mux.HandleFunc("/admin/health", s.handleHealth)

	s.httpServer = &http.Server{
		Addr:           config.Addr,
		Handler:        mux,
		ReadTimeout:    config.ReadTimeout,
		WriteTimeout:   config.WriteTimeout,
		MaxHeaderBytes: config.MaxHeaderBytes,
	}

	return s
}

// Start starts the CDN server.
func (s *Server) Start() error {
	log.Printf("CDN server starting on %s", s.config.Addr)
	log.Printf("Origin server: %s", s.config.OriginURL)
	return s.httpServer.ListenAndServe()
}

// Stop stops the CDN server gracefully.
func (s *Server) Stop() error {
	log.Println("CDN server stopping...")
	s.cache.Stop()
	s.dispatcher.Stop()
	return s.httpServer.Close()
}

// handleRequest is the main request handler for the CDN server.
// It implements the core CDN logic: cache lookup → origin fetch → cache update.
//
// ⭐ Algorithm:
// 1. Generate cache key from request
// 2. Look up cache
// 3. If cache hit, return cached content
// 4. If cache miss, fetch from origin
// 5. Cache the response
// 6. Return the response
func (s *Server) handleRequest(w http.ResponseWriter, r *http.Request) {
	start := time.Now()

	// Generate cache key
	cacheKey := generateCacheKey(r)

	// Check cache
	if item, ok := s.cache.Get(cacheKey); ok {
		// Cache HIT
		log.Printf("Cache HIT: %s (%v)", cacheKey, time.Since(start))
		s.writeResponse(w, item)
		return
	}

	// Cache MISS - fetch from origin
	log.Printf("Cache MISS: %s", cacheKey)

	resp, err := s.origin.FetchWithRetry(r.URL.Path, r.Header)
	if err != nil {
		log.Printf("Origin fetch error: %v", err)
		http.Error(w, "Bad Gateway", http.StatusBadGateway)
		return
	}

	// Check if response is cacheable
	if !isCacheable(resp.StatusCode) {
		// Don't cache non-cacheable responses
		log.Printf("Non-cacheable response: %d", resp.StatusCode)
		s.writeFetchResponse(w, resp)
		return
	}

	// Cache the response
	item := &cache.CacheItem{
		Key:        cacheKey,
		Value:      resp.Body,
		Headers:    resp.Headers,
		StatusCode: resp.StatusCode,
		Size:       resp.Size,
	}
	s.cache.Set(cacheKey, item, s.config.DefaultTTL)

	log.Printf("Cached response: %s (%v)", cacheKey, time.Since(start))

	// Return the response
	s.writeResponse(w, item)
}

// requireAdminAuth checks the Authorization header for a valid bearer token.
// Returns true if the request is authorized, false otherwise (response already written).
func (s *Server) requireAdminAuth(w http.ResponseWriter, r *http.Request) bool {
	if s.config.AdminToken == "" {
		// No token configured — deny by default to avoid open admin endpoints
		http.Error(w, "Admin access disabled", http.StatusForbidden)
		return false
	}

	auth := r.Header.Get("Authorization")
	const prefix = "Bearer "
	if len(auth) > len(prefix) && auth[:len(prefix)] == prefix {
		if auth[len(prefix):] == s.config.AdminToken {
			return true
		}
	}

	http.Error(w, "Unauthorized", http.StatusUnauthorized)
	return false
}

// handleCacheStats returns cache statistics as JSON.
func (s *Server) handleCacheStats(w http.ResponseWriter, r *http.Request) {
	if !s.requireAdminAuth(w, r) {
		return
	}
	stats := s.cache.Stats()

	w.Header().Set("Content-Type", "application/json")
	fmt.Fprintf(w, `{
  "hits": %d,
  "misses": %d,
  "hit_rate": %.3f,
  "evictions": %d,
  "size": %d,
  "items": %d
}`, stats.Hits, stats.Misses, stats.HitRate(), stats.Evictions, stats.Size, s.cache.Len())
}

// handleCachePurge clears the cache or purges a specific key.
func (s *Server) handleCachePurge(w http.ResponseWriter, r *http.Request) {
	if !s.requireAdminAuth(w, r) {
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Read request body
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}

	path := strings.TrimSpace(string(body))
	if path == "" {
		// Clear all cache
		s.cache.Clear()
		log.Println("Cache cleared")
		fmt.Fprintf(w, `{"message": "Cache cleared"}`)
	} else {
		// Purge specific key
		cacheKey := "GET:" + r.Host + ":" + path
		s.cache.Delete(cacheKey)
		log.Printf("Cache purged: %s", cacheKey)
		fmt.Fprintf(w, `{"message": "Cache purged: %s"}`, path)
	}
}

// handleHealth returns the health status of the server.
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	fmt.Fprintf(w, `{"status": "healthy", "timestamp": "%s"}`, time.Now().Format(time.RFC3339))
}

// writeResponse writes a cached item to the HTTP response.
func (s *Server) writeResponse(w http.ResponseWriter, item *cache.CacheItem) {
	// Set headers
	for key, values := range item.Headers {
		for _, value := range values {
			w.Header().Add(key, value)
		}
	}

	// Set cache headers
	w.Header().Set("X-Cache", "HIT")
	w.Header().Set("X-Cache-Key", item.Key)

	// Set status code and write body
	w.WriteHeader(item.StatusCode)
	w.Write(item.Value)
}

// writeFetchResponse writes an origin fetch response to the HTTP response.
func (s *Server) writeFetchResponse(w http.ResponseWriter, resp *origin.FetchResponse) {
	// Set headers
	for key, values := range resp.Headers {
		for _, value := range values {
			w.Header().Add(key, value)
		}
	}

	// Set cache header
	w.Header().Set("X-Cache", "MISS")

	// Set status code and write body
	w.WriteHeader(resp.StatusCode)
	w.Write(resp.Body)
}

// generateCacheKey generates a cache key from the HTTP request.
//
// ⭐ Cache Key Format:
// method:host:path
//
// 💡 Why this format?
// - Includes method to distinguish GET/POST
// - Includes host for virtual hosting
// - Includes path for the specific resource
func generateCacheKey(r *http.Request) string {
	return fmt.Sprintf("%s:%s:%s", r.Method, r.Host, r.URL.Path)
}

// isCacheable checks if a response status code is cacheable.
//
// 💡 Cacheable Status Codes:
// - 200 OK
// - 203 Non-Authoritative Information
// - 204 No Content
// - 206 Partial Content
// - 300 Multiple Choices
// - 301 Moved Permanently
//
// Non-cacheable:
// - 4xx errors (client errors)
// - 5xx errors (server errors)
func isCacheable(statusCode int) bool {
	switch statusCode {
	case 200, 203, 204, 206, 300, 301:
		return true
	default:
		return false
	}
}