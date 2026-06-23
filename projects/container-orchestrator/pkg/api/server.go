package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"

	"github.com/container-orchestrator/pkg/container"
	"github.com/container-orchestrator/pkg/manager"
)

// Server represents the API server
type Server struct {
	manager *manager.Manager
	mux     *http.ServeMux
}

// NewServer creates a new API server
func NewServer(mgr *manager.Manager) *Server {
	s := &Server{
		manager: mgr,
		mux:     http.NewServeMux(),
	}

	s.routes()

	return s
}

// routes sets up API routes
func (s *Server) routes() {
	// Node endpoints
	s.mux.HandleFunc("/api/nodes", s.handleNodes)
	s.mux.HandleFunc("/api/nodes/", s.handleNode)

	// Service endpoints
	s.mux.HandleFunc("/api/services", s.handleServices)
	s.mux.HandleFunc("/api/services/", s.handleService)

	// Discovery endpoints
	s.mux.HandleFunc("/api/resolve/", s.handleResolve)

	// Stats endpoints
	s.mux.HandleFunc("/api/stats", s.handleStats)
	s.mux.HandleFunc("/api/health", s.handleHealth)
}

// ServeHTTP implements http.Handler
func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	s.mux.ServeHTTP(w, r)
}

// handleNodes handles /api/nodes
func (s *Server) handleNodes(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		nodes := s.manager.GetNodes()
		writeJSON(w, http.StatusOK, nodes)
	case http.MethodPost:
		var req CreateNodeRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeError(w, http.StatusBadRequest, "invalid request body")
			return
		}

		node := s.manager.AddNode(req.Name, req.Address, container.Resources{
			CPU:    req.CPU,
			Memory: req.Memory,
			Disk:   req.Disk,
		})

		writeJSON(w, http.StatusCreated, node)
	default:
		writeError(w, http.StatusMethodNotAllowed, "method not allowed")
	}
}

// handleNode handles /api/nodes/{id}
func (s *Server) handleNode(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimPrefix(r.URL.Path, "/api/nodes/")
	if id == "" {
		writeError(w, http.StatusBadRequest, "node ID required")
		return
	}

	switch r.Method {
	case http.MethodGet:
		node, err := s.manager.GetNode(id)
		if err != nil {
			writeError(w, http.StatusNotFound, "node not found")
			return
		}
		writeJSON(w, http.StatusOK, node)
	case http.MethodDelete:
		if err := s.manager.RemoveNode(id); err != nil {
			writeError(w, http.StatusNotFound, "node not found")
			return
		}
		writeJSON(w, http.StatusOK, map[string]string{"status": "deleted"})
	default:
		writeError(w, http.StatusMethodNotAllowed, "method not allowed")
	}
}

// handleServices handles /api/services
func (s *Server) handleServices(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		services := s.manager.GetServices()
		writeJSON(w, http.StatusOK, services)
	case http.MethodPost:
		var req CreateServiceRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeError(w, http.StatusBadRequest, "invalid request body")
			return
		}

		template := container.ContainerTemplate{
			Image:  req.Image,
			Labels: req.Labels,
			Resources: container.Resources{
				CPU:    req.CPU,
				Memory: req.Memory,
				Disk:   req.Disk,
			},
		}

		service, err := s.manager.CreateService(req.Name, req.Replicas, template)
		if err != nil {
			writeError(w, http.StatusInternalServerError, err.Error())
			return
		}

		writeJSON(w, http.StatusCreated, service)
	default:
		writeError(w, http.StatusMethodNotAllowed, "method not allowed")
	}
}

// handleService handles /api/services/{id}
func (s *Server) handleService(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimPrefix(r.URL.Path, "/api/services/")
	if id == "" {
		writeError(w, http.StatusBadRequest, "service ID required")
		return
	}

	switch r.Method {
	case http.MethodGet:
		service, err := s.manager.GetService(id)
		if err != nil {
			writeError(w, http.StatusNotFound, "service not found")
			return
		}
		writeJSON(w, http.StatusOK, service)
	case http.MethodDelete:
		if err := s.manager.DeleteService(id); err != nil {
			writeError(w, http.StatusNotFound, "service not found")
			return
		}
		writeJSON(w, http.StatusOK, map[string]string{"status": "deleted"})
	case http.MethodPut:
		var req ScaleServiceRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeError(w, http.StatusBadRequest, "invalid request body")
			return
		}

		if err := s.manager.ScaleService(id, req.Replicas); err != nil {
			writeError(w, http.StatusInternalServerError, err.Error())
			return
		}

		writeJSON(w, http.StatusOK, map[string]string{"status": "scaled"})
	default:
		writeError(w, http.StatusMethodNotAllowed, "method not allowed")
	}
}

// handleResolve handles /api/resolve/{serviceName}
func (s *Server) handleResolve(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}

	serviceName := strings.TrimPrefix(r.URL.Path, "/api/resolve/")
	if serviceName == "" {
		writeError(w, http.StatusBadRequest, "service name required")
		return
	}

	endpoint, err := s.manager.ResolveService(serviceName)
	if err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}

	writeJSON(w, http.StatusOK, endpoint)
}

// handleStats handles /api/stats
func (s *Server) handleStats(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}

	stats := s.manager.GetClusterStats()
	writeJSON(w, http.StatusOK, stats)
}

// handleHealth handles /api/health
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}

	summary := s.manager.GetHealthSummary()
	writeJSON(w, http.StatusOK, summary)
}

// writeJSON writes a JSON response
func writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// writeError writes an error response
func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}

// CreateNodeRequest represents a request to create a node
type CreateNodeRequest struct {
	Name    string  `json:"name"`
	Address string  `json:"address"`
	CPU     float64 `json:"cpu"`
	Memory  int64   `json:"memory"`
	Disk    int64   `json:"disk"`
}

// CreateServiceRequest represents a request to create a service
type CreateServiceRequest struct {
	Name     string            `json:"name"`
	Image    string            `json:"image"`
	Replicas int               `json:"replicas"`
	CPU      float64           `json:"cpu"`
	Memory   int64             `json:"memory"`
	Disk     int64             `json:"disk"`
	Labels   map[string]string `json:"labels,omitempty"`
}

// ScaleServiceRequest represents a request to scale a service
type ScaleServiceRequest struct {
	Replicas int `json:"replicas"`
}

// Start starts the API server
func (s *Server) Start(addr string) error {
	fmt.Printf("API server starting on %s\n", addr)
	return http.ListenAndServe(addr, s)
}
