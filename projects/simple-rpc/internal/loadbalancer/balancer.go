package loadbalancer

import (
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"

	"github.com/simple-rpc/internal/registry"
)

// Balancer 负载均衡器接口
type Balancer interface {
	// Select 选择一个服务实例
	Select(instances []*registry.ServiceInstance) (*registry.ServiceInstance, error)
	// Name 返回负载均衡器名称
	Name() string
}

// RandomBalancer 随机负载均衡
type RandomBalancer struct{}

// NewRandomBalancer 创建随机负载均衡器
func NewRandomBalancer() *RandomBalancer {
	return &RandomBalancer{}
}

func (b *RandomBalancer) Select(instances []*registry.ServiceInstance) (*registry.ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}
	return instances[rand.Intn(len(instances))], nil
}

func (b *RandomBalancer) Name() string {
	return "random"
}

// RoundRobinBalancer 轮询负载均衡
type RoundRobinBalancer struct {
	counter uint64
}

// NewRoundRobinBalancer 创建轮询负载均衡器
func NewRoundRobinBalancer() *RoundRobinBalancer {
	return &RoundRobinBalancer{}
}

func (b *RoundRobinBalancer) Select(instances []*registry.ServiceInstance) (*registry.ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}

	idx := atomic.AddUint64(&b.counter, 1)
	return instances[idx%uint64(len(instances))], nil
}

func (b *RoundRobinBalancer) Name() string {
	return "round_robin"
}

// WeightedBalancer 加权负载均衡
type WeightedBalancer struct {
	mu       sync.Mutex
	weights  map[string]int
}

// NewWeightedBalancer 创建加权负载均衡器
func NewWeightedBalancer() *WeightedBalancer {
	return &WeightedBalancer{
		weights: make(map[string]int),
	}
}

// SetWeight 设置实例权重
func (b *WeightedBalancer) SetWeight(instanceID string, weight int) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.weights[instanceID] = weight
}

func (b *WeightedBalancer) Select(instances []*registry.ServiceInstance) (*registry.ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}

	b.mu.Lock()
	defer b.mu.Unlock()

	// 计算总权重
	totalWeight := 0
	weights := make([]int, len(instances))
	for i, inst := range instances {
		w, ok := b.weights[inst.InstanceID]
		if !ok {
			w = 1 // 默认权重
		}
		weights[i] = w
		totalWeight += w
	}

	if totalWeight == 0 {
		return instances[0], nil
	}

	// 按权重选择
	r := rand.Intn(totalWeight)
	for i, w := range weights {
		r -= w
		if r < 0 {
			return instances[i], nil
		}
	}

	return instances[0], nil
}

func (b *WeightedBalancer) Name() string {
	return "weighted"
}

// LeastConnectionsBalancer 最少连接负载均衡
type LeastConnectionsBalancer struct {
	mu          sync.Mutex
	connections map[string]int
}

// NewLeastConnectionsBalancer 创建最少连接负载均衡器
func NewLeastConnectionsBalancer() *LeastConnectionsBalancer {
	return &LeastConnectionsBalancer{
		connections: make(map[string]int),
	}
}

// IncrementConnections 增加连接数
func (b *LeastConnectionsBalancer) IncrementConnections(instanceID string) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.connections[instanceID]++
}

// DecrementConnections 减少连接数
func (b *LeastConnectionsBalancer) DecrementConnections(instanceID string) {
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.connections[instanceID] > 0 {
		b.connections[instanceID]--
	}
}

func (b *LeastConnectionsBalancer) Select(instances []*registry.ServiceInstance) (*registry.ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}

	b.mu.Lock()
	defer b.mu.Unlock()

	var selected *registry.ServiceInstance
	minConns := -1

	for _, inst := range instances {
		conns := b.connections[inst.InstanceID]
		if minConns == -1 || conns < minConns {
			minConns = conns
			selected = inst
		}
	}

	return selected, nil
}

func (b *LeastConnectionsBalancer) Name() string {
	return "least_connections"
}

// BalancerRegistry 负载均衡器注册表
type BalancerRegistry struct {
	balancers map[string]Balancer
}

// NewBalancerRegistry 创建负载均衡器注册表
func NewBalancerRegistry() *BalancerRegistry {
	r := &BalancerRegistry{
		balancers: make(map[string]Balancer),
	}

	// 注册默认负载均衡器
	r.Register(NewRandomBalancer())
	r.Register(NewRoundRobinBalancer())
	r.Register(NewWeightedBalancer())
	r.Register(NewLeastConnectionsBalancer())

	return r
}

// Register 注册负载均衡器
func (r *BalancerRegistry) Register(balancer Balancer) {
	r.balancers[balancer.Name()] = balancer
}

// Get 获取负载均衡器
func (r *BalancerRegistry) Get(name string) (Balancer, error) {
	balancer, ok := r.balancers[name]
	if !ok {
		return nil, fmt.Errorf("balancer not found: %s", name)
	}
	return balancer, nil
}
