package transport

import (
	"fmt"
	"io"
	"net"
	"sync"
)

// Message 传输消息
type Message struct {
	Header  map[string]string
	Payload []byte
}

// Transport 定义传输接口
type Transport interface {
	// Listen 监听连接
	Listen(addr string) error
	// Accept 接受连接
	Accept() (Conn, error)
	// Dial 建立连接
	Dial(addr string) (Conn, error)
	// Close 关闭传输
	Close() error
	// Addr 返回监听地址
	Addr() net.Addr
}

// Conn 定义连接接口
type Conn interface {
	// Send 发送消息
	Send(msg *Message) error
	// Receive 接收消息
	Receive() (*Message, error)
	// Close 关闭连接
	Close() error
	// RemoteAddr 返回远程地址
	RemoteAddr() net.Addr
}

// TCPTransport TCP 传输实现
type TCPTransport struct {
	listener net.Listener
	mu       sync.RWMutex
}

// NewTCPTransport 创建 TCP 传输
func NewTCPTransport() *TCPTransport {
	return &TCPTransport{}
}

func (t *TCPTransport) Listen(addr string) error {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return fmt.Errorf("failed to listen on %s: %w", addr, err)
	}
	t.mu.Lock()
	t.listener = ln
	t.mu.Unlock()
	return nil
}

func (t *TCPTransport) Accept() (Conn, error) {
	t.mu.RLock()
	ln := t.listener
	t.mu.RUnlock()

	if ln == nil {
		return nil, fmt.Errorf("transport not listening")
	}

	conn, err := ln.Accept()
	if err != nil {
		return nil, fmt.Errorf("failed to accept connection: %w", err)
	}

	return NewTCPConn(conn), nil
}

func (t *TCPTransport) Dial(addr string) (Conn, error) {
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		return nil, fmt.Errorf("failed to dial %s: %w", addr, err)
	}
	return NewTCPConn(conn), nil
}

func (t *TCPTransport) Close() error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.listener != nil {
		return t.listener.Close()
	}
	return nil
}

func (t *TCPTransport) Addr() net.Addr {
	t.mu.RLock()
	defer t.mu.RUnlock()

	if t.listener != nil {
		return t.listener.Addr()
	}
	return nil
}

// TCPConn TCP 连接实现
type TCPConn struct {
	conn net.Conn
}

// NewTCPConn 创建 TCP 连接
func NewTCPConn(conn net.Conn) *TCPConn {
	return &TCPConn{conn: conn}
}

func (c *TCPConn) Send(msg *Message) error {
	// 简单的消息格式: [header_len(4 bytes)][header_json][payload_len(4 bytes)][payload]
	// 简化实现: 直接写入 payload 长度和内容
	payloadLen := len(msg.Payload)
	header := make([]byte, 4)
	header[0] = byte(payloadLen >> 24)
	header[1] = byte(payloadLen >> 16)
	header[2] = byte(payloadLen >> 8)
	header[3] = byte(payloadLen)

	if _, err := c.conn.Write(header); err != nil {
		return fmt.Errorf("failed to write header: %w", err)
	}

	if _, err := c.conn.Write(msg.Payload); err != nil {
		return fmt.Errorf("failed to write payload: %w", err)
	}

	return nil
}

func (c *TCPConn) Receive() (*Message, error) {
	// 读取长度头
	header := make([]byte, 4)
	if _, err := io.ReadFull(c.conn, header); err != nil {
		return nil, fmt.Errorf("failed to read header: %w", err)
	}

	payloadLen := int(header[0])<<24 | int(header[1])<<16 | int(header[2])<<8 | int(header[3])

	// 读取 payload
	payload := make([]byte, payloadLen)
	if _, err := io.ReadFull(c.conn, payload); err != nil {
		return nil, fmt.Errorf("failed to read payload: %w", err)
	}

	return &Message{
		Header:  make(map[string]string),
		Payload: payload,
	}, nil
}

func (c *TCPConn) Close() error {
	return c.conn.Close()
}

func (c *TCPConn) RemoteAddr() net.Addr {
	return c.conn.RemoteAddr()
}
