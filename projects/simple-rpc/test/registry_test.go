package test

import (
	"testing"
	"time"

	"github.com/simple-rpc/internal/registry"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestMemoryRegistryRegister(t *testing.T) {
	reg := registry.NewMemoryRegistry()
	defer reg.Close()

	instance := &registry.ServiceInstance{
		ServiceName: "TestService",
		InstanceID:  "instance-1",
		Address:     "localhost",
		Port:        8080,
	}

	err := reg.Register(instance)
	require.NoError(t, err)

	// 验证服务已注册
	services, err := reg.ListServices()
	require.NoError(t, err)
	assert.Contains(t, services, "TestService")

	// 获取服务实例
	instances, err := reg.GetService("TestService")
	require.NoError(t, err)
	assert.Len(t, instances, 1)
	assert.Equal(t, "instance-1", instances[0].InstanceID)
}

func TestMemoryRegistryDeregister(t *testing.T) {
	reg := registry.NewMemoryRegistry()
	defer reg.Close()

	instance := &registry.ServiceInstance{
		ServiceName: "TestService",
		InstanceID:  "instance-1",
		Address:     "localhost",
		Port:        8080,
	}

	err := reg.Register(instance)
	require.NoError(t, err)

	// 注销服务
	err = reg.Deregister("instance-1")
	require.NoError(t, err)

	// 验证服务已注销
	_, err = reg.GetService("TestService")
	assert.Error(t, err)
}

func TestMemoryRegistryMultipleInstances(t *testing.T) {
	reg := registry.NewMemoryRegistry()
	defer reg.Close()

	// 注册多个实例
	for i := 0; i < 3; i++ {
		instance := &registry.ServiceInstance{
			ServiceName: "TestService",
			InstanceID:  "instance-" + string(rune('A'+i)),
			Address:     "localhost",
			Port:        8080 + i,
		}
		err := reg.Register(instance)
		require.NoError(t, err)
	}

	// 获取所有实例
	instances, err := reg.GetService("TestService")
	require.NoError(t, err)
	assert.Len(t, instances, 3)
}

func TestMemoryRegistryGetInstance(t *testing.T) {
	reg := registry.NewMemoryRegistry()
	defer reg.Close()

	instance := &registry.ServiceInstance{
		ServiceName: "TestService",
		InstanceID:  "instance-1",
		Address:     "localhost",
		Port:        8080,
		Metadata:    map[string]string{"version": "1.0"},
	}

	err := reg.Register(instance)
	require.NoError(t, err)

	// 获取特定实例
	inst, err := reg.GetInstance("TestService", "instance-1")
	require.NoError(t, err)
	assert.Equal(t, "instance-1", inst.InstanceID)
	assert.Equal(t, "1.0", inst.Metadata["version"])
}

func TestMemoryRegistryWatch(t *testing.T) {
	reg := registry.NewMemoryRegistry()
	defer reg.Close()

	// 监听服务变化
	ch, err := reg.Watch("TestService")
	require.NoError(t, err)

	// 注册服务
	instance := &registry.ServiceInstance{
		ServiceName: "TestService",
		InstanceID:  "instance-1",
		Address:     "localhost",
		Port:        8080,
	}

	err = reg.Register(instance)
	require.NoError(t, err)

	// 等待通知
	select {
	case instances := <-ch:
		assert.Len(t, instances, 1)
		assert.Equal(t, "instance-1", instances[0].InstanceID)
	case <-time.After(1 * time.Second):
		t.Fatal("timeout waiting for watch notification")
	}
}

func TestMemoryRegistryHeartbeat(t *testing.T) {
	reg := registry.NewMemoryRegistry()
	defer reg.Close()

	instance := &registry.ServiceInstance{
		ServiceName: "TestService",
		InstanceID:  "instance-1",
		Address:     "localhost",
		Port:        8080,
	}

	err := reg.Register(instance)
	require.NoError(t, err)

	// 发送心跳
	err = reg.Heartbeat("instance-1")
	require.NoError(t, err)

	// 验证实例状态
	inst, err := reg.GetInstance("TestService", "instance-1")
	require.NoError(t, err)
	assert.Equal(t, "healthy", inst.Status)
}

func TestMemoryRegistryServiceNotFound(t *testing.T) {
	reg := registry.NewMemoryRegistry()
	defer reg.Close()

	// 获取不存在的服务
	_, err := reg.GetService("NonExistentService")
	assert.Error(t, err)
}

func TestMemoryRegistryInstanceNotFound(t *testing.T) {
	reg := registry.NewMemoryRegistry()
	defer reg.Close()

	// 获取不存在的实例
	_, err := reg.GetInstance("NonExistentService", "instance-1")
	assert.Error(t, err)
}
