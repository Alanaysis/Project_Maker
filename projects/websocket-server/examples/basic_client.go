// Basic WebSocket client example using Go
//
// This example demonstrates how to connect to the WebSocket server
// and send/receive messages programmatically.
//
// Usage:
//   go run examples/basic_client.go

package main

import (
	"bufio"
	"bytes"
	"crypto/sha1"
	"encoding/base64"
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"os"
	"strings"
)

const websocketGUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

func main() {
	serverAddr := "localhost:8080"
	if len(os.Args) > 1 {
		serverAddr = os.Args[1]
	}

	fmt.Printf("Connecting to ws://%s/ws ...\n", serverAddr)

	conn, err := net.Dial("tcp", serverAddr)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to connect: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close()

	// Perform WebSocket handshake
	if err := handshake(conn, serverAddr); err != nil {
		fmt.Fprintf(os.Stderr, "Handshake failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Connected! Type messages and press Enter to send.")
	fmt.Println("Press Ctrl+C to exit.")
	fmt.Println("---")

	// Start reading messages in background
	go readMessages(conn)

	// Read from stdin and send
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		text := scanner.Text()
		if text == "" {
			continue
		}
		if err := sendTextMessage(conn, text); err != nil {
			fmt.Fprintf(os.Stderr, "Send failed: %v\n", err)
			break
		}
	}
}

func handshake(conn net.Conn, host string) error {
	// Generate random key
	key := make([]byte, 16)
	for i := range key {
		key[i] = byte(i + 1) // Simple key for example
	}
	encodedKey := base64.StdEncoding.EncodeToString(key)

	// Send upgrade request
	request := fmt.Sprintf("GET /ws HTTP/1.1\r\n"+
		"Host: %s\r\n"+
		"Upgrade: websocket\r\n"+
		"Connection: Upgrade\r\n"+
		"Sec-WebSocket-Key: %s\r\n"+
		"Sec-WebSocket-Version: 13\r\n"+
		"\r\n",
		host, encodedKey)

	if _, err := conn.Write([]byte(request)); err != nil {
		return fmt.Errorf("send request: %w", err)
	}

	// Read response
	reader := bufio.NewReader(conn)
	line, err := reader.ReadString('\n')
	if err != nil {
		return fmt.Errorf("read status: %w", err)
	}

	if !strings.Contains(line, "101") {
		return fmt.Errorf("unexpected response: %s", line)
	}

	// Skip remaining headers
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			return fmt.Errorf("read header: %w", err)
		}
		if line == "\r\n" || line == "\n" {
			break
		}
	}

	// Verify accept key
	expectedAccept := computeAcceptKey(encodedKey)
	_ = expectedAccept // In production, verify the server's Sec-WebSocket-Accept

	return nil
}

func computeAcceptKey(key string) string {
	h := sha1.New()
	h.Write([]byte(key + websocketGUID))
	return base64.StdEncoding.EncodeToString(h.Sum(nil))
}

func sendTextMessage(conn net.Conn, text string) error {
	payload := []byte(text)
	frame := buildFrame(0x1, payload, false) // 0x1 = text, not masked
	_, err := conn.Write(frame)
	return err
}

func buildFrame(opcode byte, payload []byte, masked bool) []byte {
	var buf bytes.Buffer

	// First byte: FIN + opcode
	b0 := 0x80 | opcode // FIN bit set
	buf.WriteByte(byte(b0))

	// Second byte: MASK + payload length
	if masked {
		buf.WriteByte(byte(0x80 | len(payload)))
	} else {
		buf.WriteByte(byte(len(payload)))
	}

	// Write payload
	buf.Write(payload)

	return buf.Bytes()
}

func readMessages(conn net.Conn) {
	for {
		frame, err := readFrame(conn)
		if err != nil {
			if err == io.EOF {
				fmt.Println("\nConnection closed by server")
			} else {
				fmt.Fprintf(os.Stderr, "\nRead error: %v\n", err)
			}
			os.Exit(0)
		}

		switch frame.Opcode {
		case 0x1: // Text
			fmt.Printf("\r<- %s\n> ", string(frame.Payload))
		case 0x2: // Binary
			fmt.Printf("\r<- [binary: %d bytes]\n> ", len(frame.Payload))
		case 0x8: // Close
			fmt.Println("\nServer sent close frame")
			os.Exit(0)
		case 0x9: // Ping
			// Send pong
			pong := buildFrame(0xA, frame.Payload, false)
			conn.Write(pong)
		case 0xA: // Pong
			// Ignore pong
		}
	}
}

type Frame struct {
	Fin     bool
	Opcode  byte
	Masked  bool
	Payload []byte
}

func readFrame(r io.Reader) (*Frame, error) {
	header := make([]byte, 2)
	if _, err := io.ReadFull(r, header); err != nil {
		return nil, err
	}

	f := &Frame{}
	f.Fin = (header[0] & 0x80) != 0
	f.Opcode = header[0] & 0x0F
	f.Masked = (header[1] & 0x80) != 0
	payloadLen := uint64(header[1] & 0x7F)

	switch payloadLen {
	case 126:
		extLen := make([]byte, 2)
		if _, err := io.ReadFull(r, extLen); err != nil {
			return nil, err
		}
		payloadLen = uint64(binary.BigEndian.Uint16(extLen))
	case 127:
		extLen := make([]byte, 8)
		if _, err := io.ReadFull(r, extLen); err != nil {
			return nil, err
		}
		payloadLen = binary.BigEndian.Uint64(extLen)
	}

	var maskKey [4]byte
	if f.Masked {
		if _, err := io.ReadFull(r, maskKey[:]); err != nil {
			return nil, err
		}
	}

	f.Payload = make([]byte, payloadLen)
	if _, err := io.ReadFull(r, f.Payload); err != nil {
		return nil, err
	}

	if f.Masked {
		for i := range f.Payload {
			f.Payload[i] ^= maskKey[i%4]
		}
	}

	return f, nil
}
