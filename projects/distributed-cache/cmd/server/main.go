package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/distributed-cache/internal/application"
	"github.com/distributed-cache/internal/cache"
	"github.com/distributed-cache/internal/distributed"
)

func main() {
	// Parse command line arguments
	port := "8080"
	if len(os.Args) > 1 {
		port = os.Args[1]
	}

	nodeID := fmt.Sprintf("node-%s", port)
	address := fmt.Sprintf("localhost:%s", port)

	// Create cache
	cacheConfig := cache.CacheConfig{
		Capacity:     10000,
		EvictionType: "lru",
		DefaultTTL:   10 * time.Minute,
		CleanupTick:  time.Minute,
	}

	// Create node
	node := distributed.NewNode(nodeID, address, cacheConfig)

	// Create application components
	hotCache := application.NewHotCache(
		cache.NewCache(cache.CacheConfig{Capacity: 1000, EvictionType: "lfu"}),
		10, // threshold
		30*time.Minute,
		5*time.Minute,
	)

	sessionStore := application.NewSessionStore(
		cache.NewCache(cache.CacheConfig{Capacity: 5000, EvictionType: "lru"}),
		application.DefaultSessionConfig(),
	)

	rateLimiter := application.NewRateLimiter(
		cache.NewCache(cache.CacheConfig{Capacity: 10000, EvictionType: "lru"}),
		application.RateLimiterConfig{
			RequestsPerWindow: 100,
			WindowSize:        time.Minute,
			BurstSize:         10,
		},
	)

	// Start node
	if err := node.Start(); err != nil {
		log.Fatalf("Failed to start node: %v", err)
	}

	// Setup HTTP handlers
	mux := http.NewServeMux()

	// Cache operations
	mux.HandleFunc("/cache/get", handleCacheGet(node))
	mux.HandleFunc("/cache/set", handleCacheSet(node))
	mux.HandleFunc("/cache/delete", handleCacheDelete(node))

	// Hot cache
	mux.HandleFunc("/hot/get", handleHotGet(hotCache))
	mux.HandleFunc("/hot/set", handleHotSet(hotCache))
	mux.HandleFunc("/hot/keys", handleHotKeys(hotCache))

	// Session operations
	mux.HandleFunc("/session/create", handleSessionCreate(sessionStore))
	mux.HandleFunc("/session/get", handleSessionGet(sessionStore))
	mux.HandleFunc("/session/update", handleSessionUpdate(sessionStore))
	mux.HandleFunc("/session/delete", handleSessionDelete(sessionStore))

	// Rate limiter
	mux.HandleFunc("/ratelimit/check", handleRateLimitCheck(rateLimiter))

	// Cluster operations
	mux.HandleFunc("/cluster/info", handleClusterInfo(node))
	mux.HandleFunc("/cluster/stats", handleClusterStats(node))

	// Health check
	mux.HandleFunc("/health", handleHealth(node))

	// Start HTTP server
	server := &http.Server{
		Addr:    ":" + port,
		Handler: mux,
	}

	go func() {
		log.Printf("Starting distributed cache server on port %s", port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed: %v", err)
		}
	}()

	// Wait for interrupt signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	log.Println("Shutting down...")
	node.Stop()
	hotCache.Stop()
}

// ============ Cache Handlers ============

func handleCacheGet(node *distributed.Node) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		key := r.URL.Query().Get("key")
		if key == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "key required"})
			return
		}

		val, err := node.Get(key)
		if err != nil {
			writeJSON(w, http.StatusNotFound, map[string]string{"error": err.Error()})
			return
		}

		writeJSON(w, http.StatusOK, map[string]interface{}{"value": val})
	}
}

func handleCacheSet(node *distributed.Node) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "POST required"})
			return
		}

		var req struct {
			Key   string      `json:"key"`
			Value interface{} `json:"value"`
			TTL   int         `json:"ttl"` // seconds
		}

		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}

		ttl := time.Duration(req.TTL) * time.Second
		if err := node.Set(req.Key, req.Value, ttl); err != nil {
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
			return
		}

		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	}
}

func handleCacheDelete(node *distributed.Node) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		key := r.URL.Query().Get("key")
		if key == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "key required"})
			return
		}

		if err := node.Delete(key); err != nil {
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
			return
		}

		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	}
}

// ============ Hot Cache Handlers ============

func handleHotGet(hotCache *application.HotCache) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		key := r.URL.Query().Get("key")
		if key == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "key required"})
			return
		}

		val, ok := hotCache.Get(key)
		if !ok {
			writeJSON(w, http.StatusNotFound, map[string]string{"error": "not found"})
			return
		}

		writeJSON(w, http.StatusOK, map[string]interface{}{"value": val})
	}
}

func handleHotSet(hotCache *application.HotCache) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "POST required"})
			return
		}

		var req struct {
			Key   string      `json:"key"`
			Value interface{} `json:"value"`
		}

		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}

		hotCache.Set(req.Key, req.Value)
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	}
}

func handleHotKeys(hotCache *application.HotCache) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		keys := hotCache.GetHotKeys()
		writeJSON(w, http.StatusOK, map[string]interface{}{"hot_keys": keys})
	}
}

// ============ Session Handlers ============

func handleSessionCreate(ss *application.SessionStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "POST required"})
			return
		}

		var req struct {
			UserID string                 `json:"user_id"`
			Data   map[string]interface{} `json:"data"`
		}

		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}

		session, err := ss.Create(req.UserID, req.Data)
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
			return
		}

		writeJSON(w, http.StatusOK, session)
	}
}

func handleSessionGet(ss *application.SessionStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		sessionID := r.URL.Query().Get("id")
		if sessionID == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "id required"})
			return
		}

		session, err := ss.Get(sessionID)
		if err != nil {
			writeJSON(w, http.StatusNotFound, map[string]string{"error": err.Error()})
			return
		}

		writeJSON(w, http.StatusOK, session)
	}
}

func handleSessionUpdate(ss *application.SessionStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "POST required"})
			return
		}

		var req struct {
			ID   string                 `json:"id"`
			Data map[string]interface{} `json:"data"`
		}

		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}

		if err := ss.Update(req.ID, req.Data); err != nil {
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
			return
		}

		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	}
}

func handleSessionDelete(ss *application.SessionStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		sessionID := r.URL.Query().Get("id")
		if sessionID == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "id required"})
			return
		}

		ss.Delete(sessionID)
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	}
}

// ============ Rate Limiter Handler ============

func handleRateLimitCheck(rl *application.RateLimiter) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		key := r.URL.Query().Get("key")
		if key == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "key required"})
			return
		}

		result := rl.Allow(key)
		writeJSON(w, http.StatusOK, result)
	}
}

// ============ Cluster Handlers ============

func handleClusterInfo(node *distributed.Node) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]interface{}{
			"node_id": node.ID,
			"address": node.Address,
			"state":   node.State(),
		})
	}
}

func handleClusterStats(node *distributed.Node) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		stats := node.Stats()
		writeJSON(w, http.StatusOK, stats)
	}
}

// ============ Health Handler ============

func handleHealth(node *distributed.Node) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "healthy"})
	}
}

// ============ Helpers ============

func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}
