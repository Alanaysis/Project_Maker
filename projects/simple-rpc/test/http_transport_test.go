package test

import (
	"testing"
	"time"

	"github.com/simple-rpc/internal/transport"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestHTTPTransportListen(t *testing.T) {
	httpTransport := transport.NewHTTPTransport()

	// 设置处理函数
	httpTransport.SetHandler(func(msg *transport.Message) (*transport.Message, error) {
		return &transport.Message{
			Header:  map[string]string{"status": "ok"},
			Payload: msg.Payload,
		}, nil
	})

	// 获取可用端口
	err := httpTransport.Listen("localhost:0")
	require.NoError(t, err)
	defer httpTransport.Close()

	addr := httpTransport.Addr()
	assert.NotNil(t, addr)
}

func TestHTTPTransportRoundTrip(t *testing.T) {
	httpTransport := transport.NewHTTPTransport()

	// 设置处理函数（echo）
	httpTransport.SetHandler(func(msg *transport.Message) (*transport.Message, error) {
		return &transport.Message{
			Header:  msg.Header,
			Payload: msg.Payload,
		}, nil
	})

	// 监听
	err := httpTransport.Listen("localhost:0")
	require.NoError(t, err)
	defer httpTransport.Close()

	// 启动 HTTP 服务器
	go httpTransport.Start()

	// 等待服务器启动
	time.Sleep(100 * time.Millisecond)

	addr := httpTransport.Addr().String()

	// 创建客户端连接
	clientConn := transport.NewHTTPRoundTripper(addr)

	// 发送消息
	msg := &transport.Message{
		Header:  map[string]string{"test": "value"},
		Payload: []byte("hello world"),
	}

	err = clientConn.Send(msg)
	require.NoError(t, err)

	// 接收响应
	resp, err := clientConn.Receive()
	require.NoError(t, err)

	assert.Equal(t, "hello world", string(resp.Payload))

	clientConn.Close()
}

func TestHTTPTransportMultipleRequests(t *testing.T) {
	httpTransport := transport.NewHTTPTransport()

	// 设置处理函数
	httpTransport.SetHandler(func(msg *transport.Message) (*transport.Message, error) {
		return &transport.Message{
			Payload: msg.Payload,
		}, nil
	})

	// 监听
	err := httpTransport.Listen("localhost:0")
	require.NoError(t, err)
	defer httpTransport.Close()

	// 启动 HTTP 服务器
	go httpTransport.Start()
	time.Sleep(100 * time.Millisecond)

	addr := httpTransport.Addr().String()

	// 发送多个请求
	for i := 0; i < 10; i++ {
		clientConn := transport.NewHTTPRoundTripper(addr)

		msg := &transport.Message{
			Payload: []byte("test"),
		}

		err := clientConn.Send(msg)
		require.NoError(t, err)

		_, err = clientConn.Receive()
		require.NoError(t, err)

		clientConn.Close()
	}
}

func TestHTTPTransportNoHandler(t *testing.T) {
	httpTransport := transport.NewHTTPTransport()

	// 不设置处理函数
	err := httpTransport.Listen("localhost:0")
	require.NoError(t, err)
	defer httpTransport.Close()

	go httpTransport.Start()
	time.Sleep(100 * time.Millisecond)

	addr := httpTransport.Addr().String()

	// 创建客户端连接
	clientConn := transport.NewHTTPRoundTripper(addr)
	defer clientConn.Close()

	msg := &transport.Message{
		Payload: []byte("test"),
	}

	// 发送应该失败（没有处理函数）
	err = clientConn.Send(msg)
	assert.Error(t, err)
}

func TestHTTPTransportClose(t *testing.T) {
	httpTransport := transport.NewHTTPTransport()

	httpTransport.SetHandler(func(msg *transport.Message) (*transport.Message, error) {
		return msg, nil
	})

	err := httpTransport.Listen("localhost:0")
	require.NoError(t, err)

	go httpTransport.Start()
	time.Sleep(100 * time.Millisecond)

	// 关闭传输
	err = httpTransport.Close()
	assert.NoError(t, err)
}

func TestHTTPTransportAccept(t *testing.T) {
	httpTransport := transport.NewHTTPTransport()

	// HTTP 传输不支持 Accept
	_, err := httpTransport.Accept()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "does not support Accept")
}

func TestHTTPMessageEncoding(t *testing.T) {
	// 测试消息编码/解码通过实际传输
	httpTransport := transport.NewHTTPTransport()

	httpTransport.SetHandler(func(msg *transport.Message) (*transport.Message, error) {
		// 返回相同的消息
		return &transport.Message{
			Header:  msg.Header,
			Payload: msg.Payload,
		}, nil
	})

	err := httpTransport.Listen("localhost:0")
	require.NoError(t, err)
	defer httpTransport.Close()

	go httpTransport.Start()
	time.Sleep(100 * time.Millisecond)

	addr := httpTransport.Addr().String()

	// 测试带 header 的消息
	clientConn := transport.NewHTTPRoundTripper(addr)
	defer clientConn.Close()

	msg := &transport.Message{
		Header: map[string]string{
			"content-type": "application/json",
			"request-id":   "12345",
		},
		Payload: []byte(`{"key":"value"}`),
	}

	err = clientConn.Send(msg)
	require.NoError(t, err)

	resp, err := clientConn.Receive()
	require.NoError(t, err)

	assert.Equal(t, `{"key":"value"}`, string(resp.Payload))
}
