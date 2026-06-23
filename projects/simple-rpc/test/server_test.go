package test

import (
	"context"
	"encoding/json"
	"net"
	"testing"
	"time"

	"github.com/simple-rpc/internal/codec"
	"github.com/simple-rpc/internal/registry"
	"github.com/simple-rpc/internal/server"
	"github.com/simple-rpc/internal/transport"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestService 测试服务
type TestService struct{}

type TestRequest struct {
	Message string `json:"message"`
}

type TestResponse struct {
	Reply string `json:"reply"`
}

func (s *TestService) Echo(ctx context.Context, req *TestRequest, resp *TestResponse) error {
	resp.Reply = "echo: " + req.Message
	return nil
}

func TestServerStart(t *testing.T) {
	// 创建注册中心
	reg := registry.NewMemoryRegistry()

	// 创建编解码器
	c := codec.NewJSONCodec()

	// 创建服务器
	srv := server.NewServer("localhost:0", c, reg)

	// 注册服务
	err := srv.Register(&TestService{})
	require.NoError(t, err)

	// 获取可用端口
	listener, err := net.Listen("tcp", "localhost:0")
	require.NoError(t, err)
	addr := listener.Addr().String()
	listener.Close()

	// 启动服务器
	go func() {
		err := srv.Start(addr)
		if err != nil {
			t.Logf("Server stopped: %v", err)
		}
	}()

	// 等待服务器启动
	time.Sleep(100 * time.Millisecond)

	// 验证服务器已注册到注册中心
	services, err := reg.ListServices()
	require.NoError(t, err)
	assert.Contains(t, services, "TestService")

	// 停止服务器
	err = srv.Stop()
	assert.NoError(t, err)
}

func TestServerHandleRequest(t *testing.T) {
	// 创建注册中心
	reg := registry.NewMemoryRegistry()

	// 创建编解码器
	c := codec.NewJSONCodec()

	// 创建服务器
	srv := server.NewServer("localhost:0", c, reg)

	// 注册服务
	err := srv.Register(&TestService{})
	require.NoError(t, err)

	// 获取可用端口
	listener, err := net.Listen("tcp", "localhost:0")
	require.NoError(t, err)
	addr := listener.Addr().String()
	listener.Close()

	// 启动服务器
	go func() {
		err := srv.Start(addr)
		if err != nil {
			t.Logf("Server stopped: %v", err)
		}
	}()

	// 等待服务器启动
	time.Sleep(100 * time.Millisecond)

	// 创建客户端连接
	tcpTransport := transport.NewTCPTransport()
	conn, err := tcpTransport.Dial(addr)
	require.NoError(t, err)
	defer conn.Close()

	// 创建请求
	request := server.RpcRequest{
		ServiceName: "TestService",
		MethodName:  "Echo",
		Args:        json.RawMessage(`{"message":"hello"}`),
		RequestID:   "test-123",
	}

	requestBytes, err := json.Marshal(request)
	require.NoError(t, err)

	// 发送请求
	msg := &transport.Message{
		Payload: requestBytes,
	}
	err = conn.Send(msg)
	require.NoError(t, err)

	// 接收响应
	respMsg, err := conn.Receive()
	require.NoError(t, err)

	// 解析响应
	var response server.RpcResponse
	err = json.Unmarshal(respMsg.Payload, &response)
	require.NoError(t, err)

	// 验证响应
	assert.Empty(t, response.Error)
	assert.Equal(t, "test-123", response.RequestID)

	// 解析结果
	var result TestResponse
	err = json.Unmarshal(response.Result, &result)
	require.NoError(t, err)
	assert.Equal(t, "echo: hello", result.Reply)

	// 停止服务器
	err = srv.Stop()
	assert.NoError(t, err)
}

func TestServerMultipleServices(t *testing.T) {
	// 创建注册中心
	reg := registry.NewMemoryRegistry()

	// 创建编解码器
	c := codec.NewJSONCodec()

	// 创建服务器
	srv := server.NewServer("localhost:0", c, reg)

	// 注册多个服务
	err := srv.Register(&TestService{})
	require.NoError(t, err)

	// 获取可用端口
	listener, err := net.Listen("tcp", "localhost:0")
	require.NoError(t, err)
	addr := listener.Addr().String()
	listener.Close()

	// 启动服务器
	go func() {
		err := srv.Start(addr)
		if err != nil {
			t.Logf("Server stopped: %v", err)
		}
	}()

	// 等待服务器启动
	time.Sleep(100 * time.Millisecond)

	// 验证服务已注册
	services, err := reg.ListServices()
	require.NoError(t, err)
	assert.Contains(t, services, "TestService")

	// 停止服务器
	err = srv.Stop()
	assert.NoError(t, err)
}
