package transport

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"net/http"
	"sync"
)

// HTTPTransport HTTP 传输实现
type HTTPTransport struct {
	mu       sync.RWMutex
	listener net.Listener
	server   *http.Server
	handler  func(*Message) (*Message, error)
	addr     string
}

// NewHTTPTransport 创建 HTTP 传输
func NewHTTPTransport() *HTTPTransport {
	return &HTTPTransport{}
}

// SetHandler 设置消息处理函数
func (t *HTTPTransport) SetHandler(handler func(*Message) (*Message, error)) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.handler = handler
}

func (t *HTTPTransport) Listen(addr string) error {
	t.mu.Lock()
	t.addr = addr
	t.mu.Unlock()

	mux := http.NewServeMux()
	mux.HandleFunc("/rpc", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		// 读取请求体
		body, err := io.ReadAll(r.Body)
		if err != nil {
			http.Error(w, "Failed to read body", http.StatusBadRequest)
			return
		}
		defer r.Body.Close()

		// 解析长度前缀的消息
		msg, err := decodeHTTPMessage(body)
		if err != nil {
			http.Error(w, "Failed to decode message", http.StatusBadRequest)
			return
		}

		// 处理消息
		t.mu.RLock()
		h := t.handler
		t.mu.RUnlock()

		if h == nil {
			http.Error(w, "No handler set", http.StatusInternalServerError)
			return
		}

		resp, err := h(msg)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		// 编码响应
		respData := encodeHTTPMessage(resp)
		w.Header().Set("Content-Type", "application/octet-stream")
		w.Write(respData)
	})

	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return fmt.Errorf("failed to listen on %s: %w", addr, err)
	}

	t.mu.Lock()
	t.listener = ln
	t.server = &http.Server{Handler: mux}
	t.mu.Unlock()

	return nil
}

func (t *HTTPTransport) Accept() (Conn, error) {
	// HTTP 传输不使用 Accept 模式
	return nil, fmt.Errorf("HTTP transport does not support Accept, use Listen with handler")
}

// Start 启动 HTTP 服务器（阻塞）
func (t *HTTPTransport) Start() error {
	t.mu.RLock()
	server := t.server
	ln := t.listener
	t.mu.RUnlock()

	if server == nil || ln == nil {
		return fmt.Errorf("HTTP transport not initialized, call Listen first")
	}

	return server.Serve(ln)
}

func (t *HTTPTransport) Dial(addr string) (Conn, error) {
	return NewHTTPConn(addr), nil
}

func (t *HTTPTransport) Close() error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.server != nil {
		return t.server.Close()
	}
	if t.listener != nil {
		return t.listener.Close()
	}
	return nil
}

func (t *HTTPTransport) Addr() net.Addr {
	t.mu.RLock()
	defer t.mu.RUnlock()

	if t.listener != nil {
		return t.listener.Addr()
	}
	return nil
}

// HTTPConn HTTP 连接实现
type HTTPConn struct {
	addr string
	mu   sync.Mutex
}

// NewHTTPConn 创建 HTTP 连接
func NewHTTPConn(addr string) *HTTPConn {
	return &HTTPConn{addr: addr}
}

func (c *HTTPConn) Send(msg *Message) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	data := encodeHTTPMessage(msg)

	url := fmt.Sprintf("http://%s/rpc", c.addr)
	resp, err := http.Post(url, "application/octet-stream", bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("HTTP send error: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("HTTP error %d: %s", resp.StatusCode, string(body))
	}

	// 读取响应
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("HTTP read response error: %w", err)
	}

	// 解析响应并存储（简化实现：直接丢弃，由 Receive 获取）
	_ = respBody

	return nil
}

func (c *HTTPConn) Receive() (*Message, error) {
	// HTTP 模式下，Send 已经获取了响应
	// 这里返回空消息，实际使用中需要改进
	return &Message{Header: make(map[string]string)}, nil
}

func (c *HTTPConn) Close() error {
	return nil
}

func (c *HTTPConn) RemoteAddr() net.Addr {
	return nil
}

// encodeHTTPMessage 编码 HTTP 消息
func encodeHTTPMessage(msg *Message) []byte {
	payloadLen := len(msg.Payload)
	headerLen := 0

	// 计算 header 长度
	if len(msg.Header) > 0 {
		headerLen = len(encodeHeader(msg.Header))
	}

	// 格式: [header_len(4)][header][payload_len(4)][payload]
	buf := new(bytes.Buffer)

	// header 长度
	binary.Write(buf, binary.BigEndian, int32(headerLen))

	// header 内容
	if headerLen > 0 {
		buf.Write(encodeHeader(msg.Header))
	}

	// payload 长度
	binary.Write(buf, binary.BigEndian, int32(payloadLen))

	// payload 内容
	buf.Write(msg.Payload)

	return buf.Bytes()
}

// decodeHTTPMessage 解码 HTTP 消息
func decodeHTTPMessage(data []byte) (*Message, error) {
	if len(data) < 4 {
		return nil, fmt.Errorf("message too short")
	}

	buf := bytes.NewReader(data)

	// 读取 header 长度
	var headerLen int32
	if err := binary.Read(buf, binary.BigEndian, &headerLen); err != nil {
		return nil, fmt.Errorf("read header length error: %w", err)
	}

	// 读取 header
	header := make(map[string]string)
	if headerLen > 0 {
		headerBytes := make([]byte, headerLen)
		if _, err := io.ReadFull(buf, headerBytes); err != nil {
			return nil, fmt.Errorf("read header error: %w", err)
		}
		header = decodeHeader(headerBytes)
	}

	// 读取 payload 长度
	var payloadLen int32
	if err := binary.Read(buf, binary.BigEndian, &payloadLen); err != nil {
		return nil, fmt.Errorf("read payload length error: %w", err)
	}

	// 读取 payload
	payload := make([]byte, payloadLen)
	if _, err := io.ReadFull(buf, payload); err != nil {
		return nil, fmt.Errorf("read payload error: %w", err)
	}

	return &Message{
		Header:  header,
		Payload: payload,
	}, nil
}

// encodeHeader 编码 header
func encodeHeader(header map[string]string) []byte {
	buf := new(bytes.Buffer)
	for k, v := range header {
		buf.WriteString(k)
		buf.WriteByte(0)
		buf.WriteString(v)
		buf.WriteByte(0)
	}
	return buf.Bytes()
}

// decodeHeader 解码 header
func decodeHeader(data []byte) map[string]string {
	header := make(map[string]string)
	parts := bytes.Split(data, []byte{0})
	for i := 0; i+1 < len(parts); i += 2 {
		if len(parts[i]) > 0 && len(parts[i+1]) > 0 {
			header[string(parts[i])] = string(parts[i+1])
		}
	}
	return header
}

// HTTPRoundTripper HTTP 连接（支持请求-响应模式）
type HTTPRoundTripper struct {
	addr   string
	mu     sync.Mutex
	respCh chan []byte
}

// NewHTTPRoundTripper 创建支持请求-响应的 HTTP 连接
func NewHTTPRoundTripper(addr string) *HTTPRoundTripper {
	return &HTTPRoundTripper{
		addr:   addr,
		respCh: make(chan []byte, 1),
	}
}

func (c *HTTPRoundTripper) Send(msg *Message) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	data := encodeHTTPMessage(msg)

	url := fmt.Sprintf("http://%s/rpc", c.addr)
	resp, err := http.Post(url, "application/octet-stream", bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("HTTP send error: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("HTTP error %d: %s", resp.StatusCode, string(body))
	}

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("HTTP read response error: %w", err)
	}

	// 将响应放入 channel
	select {
	case c.respCh <- respBody:
	default:
	}

	return nil
}

func (c *HTTPRoundTripper) Receive() (*Message, error) {
	data, ok := <-c.respCh
	if !ok {
		return nil, fmt.Errorf("connection closed")
	}
	return decodeHTTPMessage(data)
}

func (c *HTTPRoundTripper) Close() error {
	close(c.respCh)
	return nil
}

func (c *HTTPRoundTripper) RemoteAddr() net.Addr {
	return nil
}
