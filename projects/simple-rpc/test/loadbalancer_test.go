package test

import (
	"testing"

	"github.com/simple-rpc/internal/loadbalancer"
	"github.com/simple-rpc/internal/registry"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func createTestInstances(count int) []*registry.ServiceInstance {
	instances := make([]*registry.ServiceInstance, count)
	for i := 0; i < count; i++ {
		instances[i] = &registry.ServiceInstance{
			ServiceName: "TestService",
			InstanceID:  "instance-" + string(rune('A'+i)),
			Address:     "localhost",
			Port:        8080 + i,
			Status:      "healthy",
		}
	}
	return instances
}

func TestRandomBalancer(t *testing.T) {
	balancer := loadbalancer.NewRandomBalancer()
	instances := createTestInstances(3)

	// 测试选择
	instance, err := balancer.Select(instances)
	require.NoError(t, err)
	assert.NotNil(t, instance)
	assert.Contains(t, []string{"instance-A", "instance-B", "instance-C"}, instance.InstanceID)
}

func TestRandomBalancerEmpty(t *testing.T) {
	balancer := loadbalancer.NewRandomBalancer()

	// 测试空实例列表
	_, err := balancer.Select([]*registry.ServiceInstance{})
	assert.Error(t, err)
}

func TestRoundRobinBalancer(t *testing.T) {
	balancer := loadbalancer.NewRoundRobinBalancer()
	instances := createTestInstances(3)

	// 测试轮询选择
	selected := make([]string, 6)
	for i := 0; i < 6; i++ {
		instance, err := balancer.Select(instances)
		require.NoError(t, err)
		selected[i] = instance.InstanceID
	}

	// 验证轮询顺序
	assert.Equal(t, "instance-B", selected[0]) // 第一次选择
	assert.Equal(t, "instance-C", selected[1]) // 第二次选择
	assert.Equal(t, "instance-A", selected[2]) // 第三次选择
	assert.Equal(t, "instance-B", selected[3]) // 第四次选择
	assert.Equal(t, "instance-C", selected[4]) // 第五次选择
	assert.Equal(t, "instance-A", selected[5]) // 第六次选择
}

func TestRoundRobinBalancerEmpty(t *testing.T) {
	balancer := loadbalancer.NewRoundRobinBalancer()

	// 测试空实例列表
	_, err := balancer.Select([]*registry.ServiceInstance{})
	assert.Error(t, err)
}

func TestWeightedBalancer(t *testing.T) {
	balancer := loadbalancer.NewWeightedBalancer()
	instances := createTestInstances(3)

	// 设置权重
	balancer.SetWeight("instance-A", 3)
	balancer.SetWeight("instance-B", 2)
	balancer.SetWeight("instance-C", 1)

	// 测试选择
	counts := make(map[string]int)
	for i := 0; i < 1000; i++ {
		instance, err := balancer.Select(instances)
		require.NoError(t, err)
		counts[instance.InstanceID]++
	}

	// 验证权重分布大致正确
	// A 应该被选择最多，C 最少
	assert.True(t, counts["instance-A"] > counts["instance-B"])
	assert.True(t, counts["instance-B"] > counts["instance-C"])
}

func TestWeightedBalancerEmpty(t *testing.T) {
	balancer := loadbalancer.NewWeightedBalancer()

	// 测试空实例列表
	_, err := balancer.Select([]*registry.ServiceInstance{})
	assert.Error(t, err)
}

func TestLeastConnectionsBalancer(t *testing.T) {
	balancer := loadbalancer.NewLeastConnectionsBalancer()
	instances := createTestInstances(3)

	// 初始选择应该是任意一个（连接数都是 0）
	instance, err := balancer.Select(instances)
	require.NoError(t, err)
	assert.NotNil(t, instance)

	// 增加连接数
	balancer.IncrementConnections("instance-A")
	balancer.IncrementConnections("instance-A")
	balancer.IncrementConnections("instance-B")

	// 现在应该选择 C（连接数最少）
	instance, err = balancer.Select(instances)
	require.NoError(t, err)
	assert.Equal(t, "instance-C", instance.InstanceID)

	// 增加 C 的连接数
	balancer.IncrementConnections("instance-C")
	balancer.IncrementConnections("instance-C")
	balancer.IncrementConnections("instance-C")

	// 现在应该选择 B（连接数最少）
	instance, err = balancer.Select(instances)
	require.NoError(t, err)
	assert.Equal(t, "instance-B", instance.InstanceID)
}

func TestLeastConnectionsBalancerDecrement(t *testing.T) {
	balancer := loadbalancer.NewLeastConnectionsBalancer()
	instances := createTestInstances(2)

	// 增加连接数
	balancer.IncrementConnections("instance-A")
	balancer.IncrementConnections("instance-A")
	balancer.IncrementConnections("instance-B")

	// A 有 2 个连接，B 有 1 个，应该选择 B
	instance, err := balancer.Select(instances)
	require.NoError(t, err)
	assert.Equal(t, "instance-B", instance.InstanceID)

	// 减少 A 的连接数
	balancer.DecrementConnections("instance-A")
	balancer.DecrementConnections("instance-A")

	// 现在 A 有 0 个连接，B 有 1 个，应该选择 A
	instance, err = balancer.Select(instances)
	require.NoError(t, err)
	assert.Equal(t, "instance-A", instance.InstanceID)
}

func TestLeastConnectionsBalancerEmpty(t *testing.T) {
	balancer := loadbalancer.NewLeastConnectionsBalancer()

	// 测试空实例列表
	_, err := balancer.Select([]*registry.ServiceInstance{})
	assert.Error(t, err)
}

func TestBalancerRegistry(t *testing.T) {
	reg := loadbalancer.NewBalancerRegistry()

	// 测试获取默认负载均衡器
	balancer, err := reg.Get("random")
	require.NoError(t, err)
	assert.Equal(t, "random", balancer.Name())

	balancer, err = reg.Get("round_robin")
	require.NoError(t, err)
	assert.Equal(t, "round_robin", balancer.Name())

	balancer, err = reg.Get("weighted")
	require.NoError(t, err)
	assert.Equal(t, "weighted", balancer.Name())

	balancer, err = reg.Get("least_connections")
	require.NoError(t, err)
	assert.Equal(t, "least_connections", balancer.Name())
}

func TestBalancerRegistryNotFound(t *testing.T) {
	reg := loadbalancer.NewBalancerRegistry()

	// 测试获取不存在的负载均衡器
	_, err := reg.Get("nonexistent")
	assert.Error(t, err)
}

func TestBalancerRegistryCustom(t *testing.T) {
	reg := loadbalancer.NewBalancerRegistry()

	// 注册自定义负载均衡器
	custom := &CustomBalancer{name: "custom"}
	reg.Register(custom)

	// 获取自定义负载均衡器
	balancer, err := reg.Get("custom")
	require.NoError(t, err)
	assert.Equal(t, "custom", balancer.Name())
}

// CustomBalancer 自定义负载均衡器
type CustomBalancer struct {
	name string
}

func (b *CustomBalancer) Select(instances []*registry.ServiceInstance) (*registry.ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, assert.AnError
	}
	return instances[0], nil
}

func (b *CustomBalancer) Name() string {
	return b.name
}
