package registry

import (
	"fmt"
	"sync"
	"time"
)

// ServiceInstance 服务实例
type ServiceInstance struct {
	ServiceName string            `json:"service_name"`
	InstanceID  string            `json:"instance_id"`
	Address     string            `json:"address"`
	Port        int               `json:"port"`
	Metadata    map[string]string `json:"metadata"`
	LastSeen    time.Time         `json:"last_seen"`
	Status      string            `json:"status"` // "healthy", "unhealthy"
}

// Registry 服务注册接口
type Registry interface {
	// Register 注册服务实例
	Register(instance *ServiceInstance) error
	// Deregister 注销服务实例
	Deregister(instanceID string) error
	// GetService 获取服务的所有实例
	GetService(serviceName string) ([]*ServiceInstance, error)
	// GetInstance 获取特定服务实例
	GetInstance(serviceName, instanceID string) (*ServiceInstance, error)
	// ListServices 列出所有服务
	ListServices() ([]string, error)
	// Watch 监听服务变化
	Watch(serviceName string) (<-chan []*ServiceInstance, error)
	// Close 关闭注册中心
	Close() error
}

// MemoryRegistry 内存注册中心实现
type MemoryRegistry struct {
	mu        sync.RWMutex
	services  map[string]map[string]*ServiceInstance
	watchers  map[string][]chan []*ServiceInstance
	stopCh    chan struct{}
}

// NewMemoryRegistry 创建内存注册中心
func NewMemoryRegistry() *MemoryRegistry {
	r := &MemoryRegistry{
		services: make(map[string]map[string]*ServiceInstance),
		watchers: make(map[string][]chan []*ServiceInstance),
		stopCh:   make(chan struct{}),
	}

	// 启动健康检查
	go r.healthCheck()

	return r
}

func (r *MemoryRegistry) Register(instance *ServiceInstance) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if _, ok := r.services[instance.ServiceName]; !ok {
		r.services[instance.ServiceName] = make(map[string]*ServiceInstance)
	}

	instance.LastSeen = time.Now()
	instance.Status = "healthy"
	r.services[instance.ServiceName][instance.InstanceID] = instance

	// 通知 watchers
	r.notifyWatchers(instance.ServiceName)

	return nil
}

func (r *MemoryRegistry) Deregister(instanceID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	for serviceName, instances := range r.services {
		if _, ok := instances[instanceID]; ok {
			delete(instances, instanceID)
			// 通知 watchers
			r.notifyWatchers(serviceName)
			return nil
		}
	}

	return fmt.Errorf("instance not found: %s", instanceID)
}

func (r *MemoryRegistry) GetService(serviceName string) ([]*ServiceInstance, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	instances, ok := r.services[serviceName]
	if !ok {
		return nil, fmt.Errorf("service not found: %s", serviceName)
	}

	result := make([]*ServiceInstance, 0, len(instances))
	for _, inst := range instances {
		if inst.Status == "healthy" {
			result = append(result, inst)
		}
	}

	if len(result) == 0 {
		return nil, fmt.Errorf("no healthy instances for service: %s", serviceName)
	}

	return result, nil
}

func (r *MemoryRegistry) GetInstance(serviceName, instanceID string) (*ServiceInstance, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	instances, ok := r.services[serviceName]
	if !ok {
		return nil, fmt.Errorf("service not found: %s", serviceName)
	}

	instance, ok := instances[instanceID]
	if !ok {
		return nil, fmt.Errorf("instance not found: %s", instanceID)
	}

	return instance, nil
}

func (r *MemoryRegistry) ListServices() ([]string, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	services := make([]string, 0, len(r.services))
	for name := range r.services {
		services = append(services, name)
	}

	return services, nil
}

func (r *MemoryRegistry) Watch(serviceName string) (<-chan []*ServiceInstance, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	ch := make(chan []*ServiceInstance, 10)
	r.watchers[serviceName] = append(r.watchers[serviceName], ch)

	return ch, nil
}

func (r *MemoryRegistry) Close() error {
	close(r.stopCh)
	return nil
}

func (r *MemoryRegistry) notifyWatchers(serviceName string) {
	watchers, ok := r.watchers[serviceName]
	if !ok {
		return
	}

	instances := make([]*ServiceInstance, 0)
	if svcs, ok := r.services[serviceName]; ok {
		for _, inst := range svcs {
			if inst.Status == "healthy" {
				instances = append(instances, inst)
			}
		}
	}

	for _, ch := range watchers {
		select {
		case ch <- instances:
		default:
			// 如果 channel 满了，跳过
		}
	}
}

func (r *MemoryRegistry) healthCheck() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-r.stopCh:
			return
		case <-ticker.C:
			r.mu.Lock()
			for serviceName, instances := range r.services {
				for id, inst := range instances {
					if time.Since(inst.LastSeen) > 30*time.Second {
						inst.Status = "unhealthy"
						r.notifyWatchers(serviceName)
						_ = id
					}
				}
			}
			r.mu.Unlock()
		}
	}
}

// Heartbeat 发送心跳
func (r *MemoryRegistry) Heartbeat(instanceID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	for _, instances := range r.services {
		if inst, ok := instances[instanceID]; ok {
			inst.LastSeen = time.Now()
			inst.Status = "healthy"
			return nil
		}
	}

	return fmt.Errorf("instance not found: %s", instanceID)
}
