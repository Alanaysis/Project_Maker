package websocket

import (
	"crypto/sha1"
	"encoding/base64"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
)

// WebSocket handshake magic constant per RFC 6455 Section 1.3.
// WebSocket 握手使用的魔法字符串
var websocketKey = "258EAFA5-E914-47DA-95CA-5AB9FC1C9437"

// UpgradeResponse generates the HTTP 101 Switching Protocols response.
// 生成 HTTP 101 协议升级响应
//
// WebSocket 握手流程（HTTP 升级）：
// 1. 客户端发送 HTTP 请求，包含特殊的 Upgrade 请求头
// 2. 服务端验证请求头，返回 101 状态码
// 3. 连接从 HTTP 升级为 WebSocket 全双工连接
//
// 关键请求头：
// - Upgrade: websocket - 声明要升级到 WebSocket 协议
// - Connection: Upgrade - 声明连接要升级
// - Sec-WebSocket-Key: <base64 random> - 客户端生成的随机密钥
// - Sec-WebSocket-Version: 13 - WebSocket 协议版本
//
// 关键响应头：
// - HTTP/1.1 101 Switching Protocols - 101 状态码表示协议切换
// - Upgrade: websocket - 确认升级到 WebSocket
// - Connection: Upgrade - 确认连接升级
// - Sec-WebSocket-Accept: <derived key> - 从客户端密钥派生的响应
func UpgradeResponse(clientKey string) (string, error) {
	// Sec-WebSocket-Accept is computed as:
	// SHA1(Client-Key + Magic-String), then base64 encoded
	// 计算响应密钥：SHA1(客户端密钥 + 魔法字符串)，然后 base64 编码
	h := sha1.New()
	h.Write([]byte(clientKey + websocketKey))
	acceptKey := base64.StdEncoding.EncodeToString(h.Sum(nil))
	return acceptKey, nil
}

// BuildHandshakeResponse creates the HTTP 101 response writer.
// 构建 HTTP 101 响应
func BuildHandshakeResponse(acceptKey string) http.ResponseWriter {
	return &handshakeResponse{acceptKey: acceptKey}
}

// handshakeResponse wraps http.ResponseWriter to send 101 response
type handshakeResponse struct {
	acceptKey string
	wrote     bool
}

func (h *handshakeResponse) Header() http.Header {
	return http.Header{
		"Upgrade":               []string{"websocket"},
		"Connection":            []string{"Upgrade"},
		"Sec-WebSocket-Accept":  []string{h.acceptKey},
		"Sec-WebSocket-Version": []string{"13"},
	}
}

func (h *handshakeResponse) Write(data []byte) (int, error) {
	return len(data), nil
}

func (h *handshakeResponse) WriteHeader(statusCode int) {}

// VerifyHandshakeRequest checks if the HTTP request is a valid WebSocket upgrade request.
// 验证 HTTP 请求是否是合法的 WebSocket 升级请求
//
// 验证项：
// 1. Upgrade 请求头包含 "websocket"
// 2. Connection 请求头包含 "Upgrade"
// 3. Sec-WebSocket-Key 存在且非空
// 4. Sec-WebSocket-Version 为 13
func VerifyHandshakeRequest(r *http.Request) (string, error) {
	// Check Upgrade header
	// 检查 Upgrade 头
	upgrade := r.Header.Get("Upgrade")
	if !strings.EqualFold(upgrade, "websocket") {
		return "", fmt.Errorf("invalid Upgrade header: %q", upgrade)
	}

	// Check Connection header
	// 检查 Connection 头
	connection := r.Header.Get("Connection")
	if !strings.Contains(strings.ToLower(connection), "upgrade") {
		return "", fmt.Errorf("missing Connection: Upgrade header")
	}

	// Get Sec-WebSocket-Key
	// 获取 Sec-WebSocket-Key
	key := r.Header.Get("Sec-WebSocket-Key")
	if key == "" {
		return "", fmt.Errorf("missing Sec-WebSocket-Key")
	}

	// Check version
	// 检查版本号
	version := r.Header.Get("Sec-WebSocket-Version")
	if version != "13" {
		return "", fmt.Errorf("unsupported WebSocket version: %q", version)
	}

	return key, nil
}

// HijackConn extracts the underlying net.Conn from an http.Hijacker.
// 从 http.Hijacker 提取底层 net.Conn
//
// Hijack 是 WebSocket 升级的关键步骤：
// - 将 HTTP 连接的控制权从 http.Server 接管到我们的代码
// - 此后我们可以直接读写 TCP 连接，使用 WebSocket 协议
func HijackConn(w http.ResponseWriter, r *http.Request) (net.Conn, error) {
	hijacker, ok := w.(http.Hijacker)
	if !ok {
		return nil, fmt.Errorf("webserver does not support hijacking")
	}

	conn, _, err := hijacker.Hijack()
	if err != nil {
		return nil, fmt.Errorf("hijack failed: %w", err)
	}

	return conn, nil
}

// WriteHandshakeResponse sends the 101 Switching Protocols response over a raw connection.
// 通过原始连接发送 101 协议升级响应
func WriteHandshakeResponse(conn net.Conn, clientKey string) error {
	acceptKey, err := UpgradeResponse(clientKey)
	if err != nil {
		return fmt.Errorf("generate accept key: %w", err)
	}

	response := fmt.Sprintf(
		"HTTP/1.1 101 Switching Protocols\r\n"+
			"Upgrade: websocket\r\n"+
			"Connection: Upgrade\r\n"+
			"Sec-WebSocket-Accept: %s\r\n"+
			"Sec-WebSocket-Version: 13\r\n"+
			"\r\n",
		acceptKey,
	)

	if _, err := io.WriteString(conn, response); err != nil {
		return fmt.Errorf("write handshake response: %w", err)
	}

	return nil
}
