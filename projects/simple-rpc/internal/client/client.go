package client

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/simple-rpc/internal/codec"
	"github.com/simple-rpc/internal/loadbalancer"
	"github.com/simple-rpc/internal/registry"
	"github.com/simple-rpc/internal/timeout"
	"github.com/simple-rpc/internal/transport"
)

// Client RPC 客户端
type Client struct {
	mu          sync.RWMutex
	codec       codec.Codec
	registry    registry.Registry
	balancer    loadbalancer.Balancer
	connections map[string]transport.Conn
	config      *ClientConfig
}

// ClientConfig 客户端配置
type ClientConfig struct {
	// ServiceName 服务名称
	ServiceName string
	// BalancerName 负载均衡器名称
	BalancerName string
	// TimeoutConfig 超时配置
	TimeoutConfig *timeout.TimeoutConfig
	// MaxRetries 最大重试次数
	MaxRetries int
	// UseCircuitBreaker 是否使用熔断器
	UseCircuitBreaker bool
}

// DefaultClientConfig 默认客户端配置
func DefaultClientConfig() *ClientConfig {
	return &ClientConfig{
		BalancerName:  "round_robin",
		TimeoutConfig: timeout.DefaultConfig(),
		MaxRetries:    3,
	}
}

// NewClient 创建 RPC 客户端
func NewClient(reg registry.Registry, balancer loadbalancer.Balancer, codec codec.Codec, config *ClientConfig) *Client {
	if config == nil {
		config = DefaultClientConfig()
	}

	return &Client{
		codec:       codec,
		registry:    reg,
		balancer:    balancer,
		connections: make(map[string]transport.Conn),
		config:      config,
	}
}

// Call 调用 RPC 方法
func (c *Client) Call(ctx context.Context, serviceName, methodName string, args interface{}, reply interface{}) error {
	// 获取服务实例
	instances, err := c.registry.GetService(serviceName)
	if err != nil {
		return fmt.Errorf("failed to get service: %w", err)
	}

	// 使用负载均衡选择实例
	instance, err := c.balancer.Select(instances)
	if err != nil {
		return fmt.Errorf("failed to select instance: %w", err)
	}

	// 带超时和重试的调用
	return timeout.RetryWithTimeout(ctx, c.config.TimeoutConfig.RequestTimeout, c.config.MaxRetries, func(ctx context.Context) error {
		return c.callInstance(ctx, instance, serviceName, methodName, args, reply)
	})
}

func (c *Client) callInstance(ctx context.Context, instance *registry.ServiceInstance, serviceName, methodName string, args interface{}, reply interface{}) error {
	// 获取或创建连接
	conn, err := c.getConnection(instance)
	if err != nil {
		return fmt.Errorf("failed to get connection: %w", err)
	}

	// 序列化参数
	argsBytes, err := json.Marshal(args)
	if err != nil {
		return fmt.Errorf("failed to marshal args: %w", err)
	}

	// 创建请求
	request := &RpcRequest{
		ServiceName: serviceName,
		MethodName:  methodName,
		Args:        argsBytes,
		RequestID:   generateRequestID(),
	}

	// 序列化请求
	requestBytes, err := json.Marshal(request)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	// 发送请求
	msg := &transport.Message{
		Payload: requestBytes,
	}

	if err := conn.Send(msg); err != nil {
		// 连接失败，移除连接
		c.removeConnection(instance.InstanceID)
		return fmt.Errorf("failed to send request: %w", err)
	}

	// 接收响应
	respMsg, err := conn.Receive()
	if err != nil {
		c.removeConnection(instance.InstanceID)
		return fmt.Errorf("failed to receive response: %w", err)
	}

	// 解析响应
	var response RpcResponse
	if err := json.Unmarshal(respMsg.Payload, &response); err != nil {
		return fmt.Errorf("failed to unmarshal response: %w", err)
	}

	// 检查错误
	if response.Error != "" {
		return fmt.Errorf("rpc error: %s", response.Error)
	}

	// 反序列化结果
	if reply != nil {
		if err := json.Unmarshal(response.Result, reply); err != nil {
			return fmt.Errorf("failed to unmarshal result: %w", err)
		}
	}

	return nil
}

func (c *Client) getConnection(instance *registry.ServiceInstance) (transport.Conn, error) {
	c.mu.RLock()
	conn, ok := c.connections[instance.InstanceID]
	c.mu.RUnlock()

	if ok {
		return conn, nil
	}

	// 创建新连接
	c.mu.Lock()
	defer c.mu.Unlock()

	// 双重检查
	if conn, ok := c.connections[instance.InstanceID]; ok {
		return conn, nil
	}

	// 构建地址（如果 Address 已经包含端口，则不再添加）
	addr := instance.Address
	if instance.Port > 0 && !containsPort(addr) {
		addr = fmt.Sprintf("%s:%d", addr, instance.Port)
	}

	t := transport.NewTCPTransport()
	conn, err := t.Dial(addr)
	if err != nil {
		return nil, fmt.Errorf("failed to dial %s: %w", addr, err)
	}

	c.connections[instance.InstanceID] = conn
	return conn, nil
}

// containsPort 检查地址是否已经包含端口
func containsPort(addr string) bool {
	// 检查是否包含冒号（可能是 host:port 格式）
	for i := len(addr) - 1; i >= 0; i-- {
		if addr[i] == ':' {
			return true
		}
		if addr[i] == ']' {
			// IPv6 地址
			return false
		}
	}
	return false
}

func (c *Client) removeConnection(instanceID string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if conn, ok := c.connections[instanceID]; ok {
		conn.Close()
		delete(c.connections, instanceID)
	}
}

// Close 关闭客户端
func (c *Client) Close() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	for id, conn := range c.connections {
		if err := conn.Close(); err != nil {
			log.Printf("Failed to close connection %s: %v", id, err)
		}
	}

	c.connections = make(map[string]transport.Conn)
	return nil
}

// RpcRequest RPC 请求
type RpcRequest struct {
	ServiceName string          `json:"service_name"`
	MethodName  string          `json:"method_name"`
	Args        json.RawMessage `json:"args"`
	RequestID   string          `json:"request_id"`
}

// RpcResponse RPC 响应
type RpcResponse struct {
	RequestID string          `json:"request_id"`
	Result    json.RawMessage `json:"result"`
	Error     string          `json:"error"`
}

func generateRequestID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}
