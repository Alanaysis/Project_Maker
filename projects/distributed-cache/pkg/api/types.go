package api

import "time"

// CacheRequest represents a cache request
type CacheRequest struct {
	Key       string        `json:"key"`
	Value     interface{}   `json:"value"`
	TTL       time.Duration `json:"ttl"`
	Operation string        `json:"operation"`
}

// CacheResponse represents a cache response
type CacheResponse struct {
	Success bool        `json:"success"`
	Value   interface{} `json:"value,omitempty"`
	Error   string      `json:"error,omitempty"`
	Stats   *CacheStats `json:"stats,omitempty"`
}

// CacheStats represents cache statistics
type CacheStats struct {
	Hits       int64   `json:"hits"`
	Misses     int64   `json:"misses"`
	HitRate    float64 `json:"hit_rate"`
	Size       int     `json:"size"`
	Capacity   int     `json:"capacity"`
	Evictions  int64   `json:"evictions"`
}

// NodeInfo represents node information
type NodeInfo struct {
	ID      string            `json:"id"`
	Address string            `json:"address"`
	State   string            `json:"state"`
	Stats   *CacheStats       `json:"stats"`
	Meta    map[string]string `json:"meta"`
}

// ClusterInfo represents cluster information
type ClusterInfo struct {
	Nodes       []NodeInfo `json:"nodes"`
	TotalKeys   int        `json:"total_keys"`
	TotalMemory int64      `json:"total_memory"`
}
