package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/gorilla/websocket"
)

// WSRequest WebSocket 请求
type WSRequest struct {
	Type    string      `json:"type"`
	ID      string      `json:"id"`
	Payload interface{} `json:"payload"`
}

// WSResponse WebSocket 响应
type WSResponse struct {
	Type      string      `json:"type"`
	ID        string      `json:"id"`
	Payload   interface{} `json:"payload"`
	Timestamp int64       `json:"timestamp"`
}

// MessagePayload 消息 Payload
type MessagePayload struct {
	To      string `json:"to"`
	Content string `json:"content"`
	MsgType string `json:"msg_type"`
}

func main() {
	if len(os.Args) < 3 {
		fmt.Println("Usage: go run client.go <server_url> <token>")
		fmt.Println("Example: go run client.go ws://localhost:8080/ws eyJhbGciOiJIUzI1NiIs...")
		os.Exit(1)
	}

	serverURL := os.Args[1]
	token := os.Args[2]

	// 连接 WebSocket
	u, err := url.Parse(serverURL)
	if err != nil {
		log.Fatal("Invalid URL:", err)
	}

	q := u.Query()
	q.Set("token", token)
	u.RawQuery = q.Encode()

	fmt.Printf("Connecting to %s...\n", u.String())

	conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		log.Fatal("Failed to connect:", err)
	}
	defer conn.Close()

	fmt.Println("Connected! Type messages and press Enter to send.")
	fmt.Println("Commands:")
	fmt.Println("  /to <user_id> <message> - Send message to user")
	fmt.Println("  /quit - Exit")
	fmt.Println()

	// 启动读取 goroutine
	go readMessages(conn)

	// 读取用户输入
	scanner := bufio.NewScanner(os.Stdin)
	var currentTo string

	for {
		fmt.Print("> ")
		if !scanner.Scan() {
			break
		}

		input := strings.TrimSpace(scanner.Text())
		if input == "" {
			continue
		}

		// 处理命令
		if strings.HasPrefix(input, "/") {
			parts := strings.SplitN(input, " ", 3)
			switch parts[0] {
			case "/to":
				if len(parts) < 3 {
					fmt.Println("Usage: /to <user_id> <message>")
					continue
				}
				currentTo = parts[1]
				sendMessage(conn, currentTo, parts[2])

			case "/quit":
				fmt.Println("Bye!")
				return

			default:
				fmt.Println("Unknown command:", parts[0])
			}
		} else if currentTo != "" {
			// 发送消息给当前目标用户
			sendMessage(conn, currentTo, input)
		} else {
			fmt.Println("Use /to <user_id> <message> to set recipient first")
		}
	}
}

func sendMessage(conn *websocket.Conn, to, content string) {
	req := WSRequest{
		Type: "message",
		ID:   fmt.Sprintf("msg_%d", time.Now().UnixNano()),
		Payload: MessagePayload{
			To:      to,
			Content: content,
			MsgType: "text",
		},
	}

	data, err := json.Marshal(req)
	if err != nil {
		log.Printf("Failed to marshal message: %v", err)
		return
	}

	if err := conn.WriteMessage(websocket.TextMessage, data); err != nil {
		log.Printf("Failed to send message: %v", err)
	}
}

func readMessages(conn *websocket.Conn) {
	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			log.Printf("Connection error: %v", err)
			os.Exit(1)
		}

		var resp WSResponse
		if err := json.Unmarshal(message, &resp); err != nil {
			log.Printf("Failed to unmarshal message: %v", err)
			continue
		}

		switch resp.Type {
		case "message":
			handleIncomingMessage(resp)
		case "ack":
			fmt.Printf("[ACK] Message sent: %v\n", resp.Payload)
		case "error":
			fmt.Printf("[ERROR] %v\n", resp.Payload)
		case "typing":
			payload, ok := resp.Payload.(map[string]interface{})
			if ok {
				fmt.Printf("[TYPING] %s is typing...\n", payload["from"])
			}
		case "pong":
			// 心跳响应，忽略
		default:
			fmt.Printf("[%s] %v\n", resp.Type, resp.Payload)
		}
	}
}

func handleIncomingMessage(resp WSResponse) {
	payload, ok := resp.Payload.(map[string]interface{})
	if !ok {
		fmt.Printf("[MESSAGE] %v\n", resp.Payload)
		return
	}

	from, _ := payload["from"].(string)
	content, _ := payload["content"].(string)
	msgType, _ := payload["type"].(string)

	switch msgType {
	case "text":
		fmt.Printf("\n[%s]: %s\n> ", from, content)
	case "image":
		fmt.Printf("\n[%s] sent an image: %s\n> ", from, content)
	case "file":
		fmt.Printf("\n[%s] sent a file: %s\n> ", from, content)
	default:
		fmt.Printf("\n[%s] (%s): %s\n> ", from, msgType, content)
	}
}