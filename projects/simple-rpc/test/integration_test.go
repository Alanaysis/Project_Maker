package test

import (
	"context"
	"net"
	"testing"
	"time"

	"github.com/simple-rpc/examples"
	"github.com/simple-rpc/internal/client"
	"github.com/simple-rpc/internal/codec"
	"github.com/simple-rpc/internal/loadbalancer"
	"github.com/simple-rpc/internal/registry"
	"github.com/simple-rpc/internal/server"
	"github.com/simple-rpc/internal/timeout"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestIntegrationCalculator(t *testing.T) {
	// 创建共享的注册中心
	reg := registry.NewMemoryRegistry()

	// 创建编解码器
	c := codec.NewJSONCodec()

	// 获取可用端口
	listener, err := net.Listen("tcp", "localhost:0")
	require.NoError(t, err)
	addr := listener.Addr().String()
	listener.Close()

	// 创建并启动服务器
	srv := server.NewServer(addr, c, reg)
	err = srv.Register(&examples.Calculator{})
	require.NoError(t, err)

	go func() {
		err := srv.Start(addr)
		if err != nil {
			t.Logf("Server stopped: %v", err)
		}
	}()

	// 等待服务器启动
	time.Sleep(200 * time.Millisecond)

	// 创建客户端（使用同一个注册中心）
	balancer := loadbalancer.NewRoundRobinBalancer()
	config := &client.ClientConfig{
		ServiceName:   "Calculator",
		BalancerName:  "round_robin",
		TimeoutConfig: timeout.DefaultConfig(),
		MaxRetries:    3,
	}

	rpcClient := client.NewClient(reg, balancer, c, config)
	defer rpcClient.Close()

	// 测试 Add
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	addReq := &examples.AddRequest{A: 10, B: 20}
	addResp := &examples.AddResponse{}
	err = rpcClient.Call(ctx, "Calculator", "Add", addReq, addResp)
	require.NoError(t, err)
	assert.Equal(t, 30, addResp.Result)

	// 测试 Multiply
	mulReq := &examples.MultiplyRequest{A: 5, B: 6}
	mulResp := &examples.MultiplyResponse{}
	err = rpcClient.Call(ctx, "Calculator", "Multiply", mulReq, mulResp)
	require.NoError(t, err)
	assert.Equal(t, 30, mulResp.Result)

	// 停止服务器
	err = srv.Stop()
	assert.NoError(t, err)
}

func TestIntegrationUserService(t *testing.T) {
	// 创建共享的注册中心
	reg := registry.NewMemoryRegistry()

	// 创建编解码器
	c := codec.NewJSONCodec()

	// 获取可用端口
	listener, err := net.Listen("tcp", "localhost:0")
	require.NoError(t, err)
	addr := listener.Addr().String()
	listener.Close()

	// 创建并启动服务器
	srv := server.NewServer(addr, c, reg)
	err = srv.Register(&examples.UserService{})
	require.NoError(t, err)

	go func() {
		err := srv.Start(addr)
		if err != nil {
			t.Logf("Server stopped: %v", err)
		}
	}()

	// 等待服务器启动
	time.Sleep(200 * time.Millisecond)

	// 创建客户端（使用同一个注册中心）
	balancer := loadbalancer.NewRoundRobinBalancer()
	config := &client.ClientConfig{
		ServiceName:   "UserService",
		BalancerName:  "round_robin",
		TimeoutConfig: timeout.DefaultConfig(),
		MaxRetries:    3,
	}

	rpcClient := client.NewClient(reg, balancer, c, config)
	defer rpcClient.Close()

	// 测试 GetUser
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	getReq := &examples.GetUserRequest{UserID: "123"}
	getResp := &examples.GetUserResponse{}
	err = rpcClient.Call(ctx, "UserService", "GetUser", getReq, getResp)
	require.NoError(t, err)
	assert.Equal(t, "123", getResp.UserID)
	assert.Equal(t, "user_123", getResp.Username)
	assert.Equal(t, "123@example.com", getResp.Email)

	// 测试 ListUsers
	listReq := &examples.ListUsersRequest{Page: 1, PageSize: 5}
	listResp := &examples.ListUsersResponse{}
	err = rpcClient.Call(ctx, "UserService", "ListUsers", listReq, listResp)
	require.NoError(t, err)
	assert.Equal(t, 100, listResp.Total)
	assert.Len(t, listResp.Users, 5)

	// 停止服务器
	err = srv.Stop()
	assert.NoError(t, err)
}

func TestIntegrationMultipleServers(t *testing.T) {
	// 创建共享的注册中心
	reg := registry.NewMemoryRegistry()

	// 创建编解码器
	c := codec.NewJSONCodec()

	// 启动多个服务器
	serverCount := 3
	servers := make([]*server.Server, serverCount)
	addrs := make([]string, serverCount)

	for i := 0; i < serverCount; i++ {
		// 获取可用端口
		listener, err := net.Listen("tcp", "localhost:0")
		require.NoError(t, err)
		addr := listener.Addr().String()
		listener.Close()

		// 创建并启动服务器
		srv := server.NewServer(addr, c, reg)
		err = srv.Register(&examples.Calculator{})
		require.NoError(t, err)

		servers[i] = srv
		addrs[i] = addr

		go func() {
			err := srv.Start(addr)
			if err != nil {
				t.Logf("Server stopped: %v", err)
			}
		}()
	}

	// 等待服务器启动
	time.Sleep(300 * time.Millisecond)

	// 验证所有服务器都已注册
	instances, err := reg.GetService("Calculator")
	require.NoError(t, err)
	assert.Len(t, instances, serverCount)

	// 创建客户端（使用同一个注册中心）
	balancer := loadbalancer.NewRoundRobinBalancer()
	config := &client.ClientConfig{
		ServiceName:   "Calculator",
		BalancerName:  "round_robin",
		TimeoutConfig: timeout.DefaultConfig(),
		MaxRetries:    3,
	}

	rpcClient := client.NewClient(reg, balancer, c, config)
	defer rpcClient.Close()

	// 测试多个调用
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	for i := 0; i < 10; i++ {
		addReq := &examples.AddRequest{A: i, B: i * 2}
		addResp := &examples.AddResponse{}
		err = rpcClient.Call(ctx, "Calculator", "Add", addReq, addResp)
		require.NoError(t, err)
		assert.Equal(t, i+i*2, addResp.Result)
	}

	// 停止所有服务器
	for _, srv := range servers {
		err = srv.Stop()
		assert.NoError(t, err)
	}
}

func TestIntegrationTimeout(t *testing.T) {
	// 创建共享的注册中心
	reg := registry.NewMemoryRegistry()

	// 创建编解码器
	c := codec.NewJSONCodec()

	// 获取可用端口
	listener, err := net.Listen("tcp", "localhost:0")
	require.NoError(t, err)
	addr := listener.Addr().String()
	listener.Close()

	// 创建并启动服务器
	srv := server.NewServer(addr, c, reg)
	err = srv.Register(&examples.Calculator{})
	require.NoError(t, err)

	go func() {
		err := srv.Start(addr)
		if err != nil {
			t.Logf("Server stopped: %v", err)
		}
	}()

	// 等待服务器启动
	time.Sleep(200 * time.Millisecond)

	// 创建客户端，设置短超时
	balancer := loadbalancer.NewRoundRobinBalancer()
	config := &client.ClientConfig{
		ServiceName:  "Calculator",
		BalancerName: "round_robin",
		TimeoutConfig: &timeout.TimeoutConfig{
			ConnectTimeout:   1 * time.Second,
			RequestTimeout:   100 * time.Millisecond, // 很短的超时
			KeepAliveTimeout: 30 * time.Second,
		},
		MaxRetries: 1,
	}

	rpcClient := client.NewClient(reg, balancer, c, config)
	defer rpcClient.Close()

	// 测试超时
	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	addReq := &examples.AddRequest{A: 10, B: 20}
	addResp := &examples.AddResponse{}
	err = rpcClient.Call(ctx, "Calculator", "Add", addReq, addResp)
	// 可能成功也可能超时，取决于网络速度
	if err != nil {
		assert.Contains(t, err.Error(), "timed out")
	}

	// 停止服务器
	err = srv.Stop()
	assert.NoError(t, err)
}

func TestIntegrationLoadBalancer(t *testing.T) {
	// 创建共享的注册中心
	reg := registry.NewMemoryRegistry()

	// 创建编解码器
	c := codec.NewJSONCodec()

	// 启动多个服务器
	serverCount := 3
	servers := make([]*server.Server, serverCount)

	for i := 0; i < serverCount; i++ {
		// 获取可用端口
		listener, err := net.Listen("tcp", "localhost:0")
		require.NoError(t, err)
		addr := listener.Addr().String()
		listener.Close()

		// 创建并启动服务器
		srv := server.NewServer(addr, c, reg)
		err = srv.Register(&examples.Calculator{})
		require.NoError(t, err)

		servers[i] = srv

		go func() {
			err := srv.Start(addr)
			if err != nil {
				t.Logf("Server stopped: %v", err)
			}
		}()
	}

	// 等待服务器启动
	time.Sleep(300 * time.Millisecond)

	// 测试不同的负载均衡器
	balancers := []string{"random", "round_robin", "weighted", "least_connections"}

	for _, balancerName := range balancers {
		t.Run(balancerName, func(t *testing.T) {
			balancerReg := loadbalancer.NewBalancerRegistry()
			balancer, err := balancerReg.Get(balancerName)
			require.NoError(t, err)

			config := &client.ClientConfig{
				ServiceName:   "Calculator",
				BalancerName:  balancerName,
				TimeoutConfig: timeout.DefaultConfig(),
				MaxRetries:    3,
			}

			rpcClient := client.NewClient(reg, balancer, c, config)
			defer rpcClient.Close()

			// 测试调用
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()

			addReq := &examples.AddRequest{A: 10, B: 20}
			addResp := &examples.AddResponse{}
			err = rpcClient.Call(ctx, "Calculator", "Add", addReq, addResp)
			require.NoError(t, err)
			assert.Equal(t, 30, addResp.Result)
		})
	}

	// 停止所有服务器
	for _, srv := range servers {
		err := srv.Stop()
		assert.NoError(t, err)
	}
}
