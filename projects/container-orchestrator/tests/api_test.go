package tests

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/container-orchestrator/pkg/api"
	"github.com/container-orchestrator/pkg/container"
	"github.com/container-orchestrator/pkg/manager"
	"github.com/stretchr/testify/assert"
)

func setupTestServer() (*api.Server, *manager.Manager) {
	mgr := manager.NewManager()
	server := api.NewServer(mgr)
	return server, mgr
}

func TestCreateNode(t *testing.T) {
	server, _ := setupTestServer()

	body := api.CreateNodeRequest{
		Name:    "node-1",
		Address: "192.168.1.1",
		CPU:     4.0,
		Memory:  8 * 1024 * 1024 * 1024,
		Disk:    100 * 1024 * 1024 * 1024,
	}

	jsonBody, _ := json.Marshal(body)
	req := httptest.NewRequest(http.MethodPost, "/api/nodes", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "node-1", response["name"])
}

func TestGetNodes(t *testing.T) {
	server, mgr := setupTestServer()

	// Add a node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	req := httptest.NewRequest(http.MethodGet, "/api/nodes", nil)
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response []map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Len(t, response, 1)
}

func TestGetNode(t *testing.T) {
	server, mgr := setupTestServer()

	// Add a node
	node := mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	req := httptest.NewRequest(http.MethodGet, "/api/nodes/"+node.ID, nil)
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "node-1", response["name"])
}

func TestDeleteNode(t *testing.T) {
	server, mgr := setupTestServer()

	// Add a node
	node := mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	req := httptest.NewRequest(http.MethodDelete, "/api/nodes/"+node.ID, nil)
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}

func TestCreateService(t *testing.T) {
	server, mgr := setupTestServer()

	// Add a node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	body := api.CreateServiceRequest{
		Name:     "web-service",
		Image:    "nginx:latest",
		Replicas: 2,
		CPU:      0.5,
		Memory:   512 * 1024 * 1024,
		Disk:     5 * 1024 * 1024 * 1024,
	}

	jsonBody, _ := json.Marshal(body)
	req := httptest.NewRequest(http.MethodPost, "/api/services", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "web-service", response["name"])
}

func TestGetServices(t *testing.T) {
	server, mgr := setupTestServer()

	// Add a node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	// Create a service
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}
	mgr.CreateService("web-service", 2, template)

	req := httptest.NewRequest(http.MethodGet, "/api/services", nil)
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}

func TestGetService(t *testing.T) {
	server, mgr := setupTestServer()

	// Add a node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	// Create a service
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}
	service, _ := mgr.CreateService("web-service", 2, template)

	req := httptest.NewRequest(http.MethodGet, "/api/services/"+service.ID, nil)
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "web-service", response["name"])
}

func TestDeleteService(t *testing.T) {
	server, mgr := setupTestServer()

	// Add a node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	// Create a service
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}
	service, _ := mgr.CreateService("web-service", 2, template)

	req := httptest.NewRequest(http.MethodDelete, "/api/services/"+service.ID, nil)
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}

func TestScaleService(t *testing.T) {
	server, mgr := setupTestServer()

	// Add a node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	// Create a service
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}
	service, _ := mgr.CreateService("web-service", 2, template)

	body := api.ScaleServiceRequest{
		Replicas: 5,
	}

	jsonBody, _ := json.Marshal(body)
	req := httptest.NewRequest(http.MethodPut, "/api/services/"+service.ID, bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}

func TestGetStats(t *testing.T) {
	server, mgr := setupTestServer()

	// Add a node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	req := httptest.NewRequest(http.MethodGet, "/api/stats", nil)
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, float64(1), response["total_nodes"])
}

func TestGetHealth(t *testing.T) {
	server, mgr := setupTestServer()

	// Add a node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	// Create a service
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}
	mgr.CreateService("web-service", 2, template)

	req := httptest.NewRequest(http.MethodGet, "/api/health", nil)
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}

func TestMethodNotAllowed(t *testing.T) {
	server, _ := setupTestServer()

	req := httptest.NewRequest(http.MethodPut, "/api/nodes", nil)
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	assert.Equal(t, http.StatusMethodNotAllowed, w.Code)
}
