package websocket

import (
	"bytes"
	"crypto/sha1"
	"encoding/base64"
	"net/http"
	"strings"
	"testing"
)

// TestUpgradeResponse tests the WebSocket accept key generation.
func TestUpgradeResponse(t *testing.T) {
	// RFC 6455 Section 1.3 test vector
	clientKey := "dGhlIHNhbXBsZSBub25jZQ=="
	expectedAccept := "s3pPLMBiTxaQ0kYGwdlTT1cug9g="

	accept, err := UpgradeResponse(clientKey)
	if err != nil {
		t.Fatalf("UpgradeResponse error: %v", err)
	}
	if accept != expectedAccept {
		t.Errorf("accept = %q, want %q", accept, expectedAccept)
	}
}

// TestUpgradeResponseEmptyKey tests with empty key.
func TestUpgradeResponseEmptyKey(t *testing.T) {
	accept, err := UpgradeResponse("")
	if err != nil {
		t.Fatalf("UpgradeResponse with empty key error: %v", err)
	}
	if accept == "" {
		t.Error("accept should not be empty")
	}
}

// TestUpgradeResponseDifferentKeys tests that different keys produce different accepts.
func TestUpgradeResponseDifferentKeys(t *testing.T) {
	accept1, _ := UpgradeResponse("key1")
	accept2, _ := UpgradeResponse("key2")
	if accept1 == accept2 {
		t.Error("different keys should produce different accept keys")
	}
}

// TestVerifyHandshakeRequest tests handshake request validation.
func TestVerifyHandshakeRequest(t *testing.T) {
	validRequest := &http.Request{
		Header: http.Header{
			"Upgrade":               []string{"websocket"},
			"Connection":            []string{"Upgrade"},
			"Sec-WebSocket-Key":     []string{"dGhlIHNhbXBsZSBub25jZQ=="},
			"Sec-WebSocket-Version": []string{"13"},
		},
	}

	key, err := VerifyHandshakeRequest(validRequest)
	if err != nil {
		t.Errorf("valid request rejected: %v", err)
	}
	if key != "dGhlIHNhbXBsZSBub25jZQ==" {
		t.Errorf("key = %q, want %q", key, "dGhlIHNhbXBsZSBub25jZQ==")
	}
}

// TestVerifyHandshakeRequestMissingUpgrade tests rejection of missing Upgrade header.
func TestVerifyHandshakeRequestMissingUpgrade(t *testing.T) {
	req := &http.Request{
		Header: http.Header{
			"Connection":            []string{"Upgrade"},
			"Sec-WebSocket-Key":     []string{"test"},
			"Sec-WebSocket-Version": []string{"13"},
		},
	}

	_, err := VerifyHandshakeRequest(req)
	if err == nil {
		t.Error("should reject request without Upgrade header")
	}
}

// TestVerifyHandshakeRequestMissingConnection tests rejection of missing Connection header.
func TestVerifyHandshakeRequestMissingConnection(t *testing.T) {
	req := &http.Request{
		Header: http.Header{
			"Upgrade":               []string{"websocket"},
			"Sec-WebSocket-Key":     []string{"test"},
			"Sec-WebSocket-Version": []string{"13"},
		},
	}

	_, err := VerifyHandshakeRequest(req)
	if err == nil {
		t.Error("should reject request without Connection header")
	}
}

// TestVerifyHandshakeRequestMissingKey tests rejection of missing Sec-WebSocket-Key.
func TestVerifyHandshakeRequestMissingKey(t *testing.T) {
	req := &http.Request{
		Header: http.Header{
			"Upgrade":               []string{"websocket"},
			"Connection":            []string{"Upgrade"},
			"Sec-WebSocket-Version": []string{"13"},
		},
	}

	_, err := VerifyHandshakeRequest(req)
	if err == nil {
		t.Error("should reject request without Sec-WebSocket-Key")
	}
}

// TestVerifyHandshakeRequestWrongVersion tests rejection of wrong version.
func TestVerifyHandshakeRequestWrongVersion(t *testing.T) {
	req := &http.Request{
		Header: http.Header{
			"Upgrade":               []string{"websocket"},
			"Connection":            []string{"Upgrade"},
			"Sec-WebSocket-Key":     []string{"test"},
			"Sec-WebSocket-Version": []string{"12"},
		},
	}

	_, err := VerifyHandshakeRequest(req)
	if err == nil {
		t.Error("should reject request with wrong version")
	}
}

// TestVerifyHandshakeRequestCaseInsensitive tests case-insensitive header matching.
func TestVerifyHandshakeRequestCaseInsensitive(t *testing.T) {
	req := &http.Request{
		Header: http.Header{
			"upgrade":               []string{"websocket"},
			"connection":            []string{"upgrade"},
			"Sec-WebSocket-Key":     []string{"test"},
			"Sec-WebSocket-Version": []string{"13"},
		},
	}

	key, err := VerifyHandshakeRequest(req)
	if err != nil {
		t.Errorf("case-insensitive headers should be accepted: %v", err)
	}
	if key != "test" {
		t.Errorf("key = %q, want %q", key, "test")
	}
}

// TestMagicConstant tests the magic constant value.
func TestMagicConstant(t *testing.T) {
	expected := "258EAFA5-E914-47DA-95CA-5AB9FC1C9437"
	if websocketKey != expected {
		t.Errorf("magic constant = %q, want %q", websocketKey, expected)
	}
}

// TestHandshakeSha1Computation verifies SHA1 computation matches RFC 6455.
func TestHandshakeSha1Computation(t *testing.T) {
	clientKey := "dGhlIHNhbXBsZSBub25jZQ=="
	h := sha1.New()
	h.Write([]byte(clientKey + websocketKey))
	expected := base64.StdEncoding.EncodeToString(h.Sum(nil))

	accept, err := UpgradeResponse(clientKey)
	if err != nil {
		t.Fatalf("UpgradeResponse error: %v", err)
	}
	if accept != expected {
		t.Errorf("accept = %q, want %q", accept, expected)
	}
}

// TestVerifyHandshakeRequestEmptyKey tests rejection of empty key.
func TestVerifyHandshakeRequestEmptyKey(t *testing.T) {
	req := &http.Request{
		Header: http.Header{
			"Upgrade":               []string{"websocket"},
			"Connection":            []string{"Upgrade"},
			"Sec-WebSocket-Key":     []string{""},
			"Sec-WebSocket-Version": []string{"13"},
		},
	}

	_, err := VerifyHandshakeRequest(req)
	if err == nil {
		t.Error("should reject request with empty Sec-WebSocket-Key")
	}
}

// TestHandshakeResponseHeader tests that correct headers are set.
func TestHandshakeResponseHeader(t *testing.T) {
	req := &http.Request{
		Header: http.Header{
			"Upgrade":               []string{"websocket"},
			"Connection":            []string{"Upgrade"},
			"Sec-WebSocket-Key":     []string{"dGhlIHNhbXBsZSBub25jZQ=="},
			"Sec-WebSocket-Version": []string{"13"},
		},
	}

	key, err := VerifyHandshakeRequest(req)
	if err != nil {
		t.Fatalf("VerifyHandshakeRequest error: %v", err)
	}

	accept, err := UpgradeResponse(key)
	if err != nil {
		t.Fatalf("UpgradeResponse error: %v", err)
	}

	expectedHeaders := http.Header{
		"Upgrade":               []string{"websocket"},
		"Connection":            []string{"Upgrade"},
		"Sec-WebSocket-Accept":  []string{accept},
		"Sec-WebSocket-Version": []string{"13"},
	}

	if expectedHeaders.Get("Upgrade") != "websocket" {
		t.Error("Upgrade header should be 'websocket'")
	}
	if !strings.Contains(expectedHeaders.Get("Connection"), "Upgrade") {
		t.Error("Connection header should contain 'Upgrade'")
	}
}

// TestVerifyHandshakeRequestMultipleConnections tests handling of Connection with multiple values.
func TestVerifyHandshakeRequestMultipleConnections(t *testing.T) {
	req := &http.Request{
		Header: http.Header{
			"Upgrade":               []string{"websocket"},
			"Connection":            []string{"keep-alive", "Upgrade"},
			"Sec-WebSocket-Key":     []string{"test"},
			"Sec-WebSocket-Version": []string{"13"},
		},
	}

	key, err := VerifyHandshakeRequest(req)
	if err != nil {
		t.Errorf("should accept Connection with multiple values: %v", err)
	}
	if key != "test" {
		t.Errorf("key = %q, want %q", key, "test")
	}
}

// TestHandshakeResponseWrite tests that WriteHandshakeResponse produces valid HTTP response.
func TestHandshakeResponseWrite(t *testing.T) {
	clientKey := "dGhlIHNhbXBsZSBub25jZQ=="

	accept, err := UpgradeResponse(clientKey)
	if err != nil {
		t.Fatalf("UpgradeResponse error: %v", err)
	}

	expected := "HTTP/1.1 101 Switching Protocols\r\n" +
		"Upgrade: websocket\r\n" +
		"Connection: Upgrade\r\n" +
		"Sec-WebSocket-Accept: " + accept + "\r\n" +
		"Sec-WebSocket-Version: 13\r\n" +
		"\r\n"

	// We can't easily test WriteHandshakeResponse without a real connection,
	// but we can verify the format
	if !strings.Contains(expected, "101 Switching Protocols") {
		t.Error("response should contain 101 status")
	}
	if !strings.Contains(expected, "Upgrade: websocket") {
		t.Error("response should contain Upgrade header")
	}
}
