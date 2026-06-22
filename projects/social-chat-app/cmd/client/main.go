package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
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

// AuthResponse 认证响应
type AuthResponse struct {
	Token string `json:"token"`
	User  struct {
		ID       string `json:"id"`
		Username string `json:"username"`
		Nickname string `json:"nickname"`
	} `json:"user"`
}

var serverAddr = "http://localhost:8080"

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(1)
	}

	// 允许通过环境变量覆盖服务器地址
	if addr := os.Getenv("CHAT_SERVER_ADDR"); addr != "" {
		serverAddr = addr
	}

	action := os.Args[1]

	switch action {
	case "register":
		if len(os.Args) < 4 {
			fmt.Println("Usage: client register <username> <password>")
			os.Exit(1)
		}
		register(os.Args[2], os.Args[3])

	case "login":
		if len(os.Args) < 4 {
			fmt.Println("Usage: client login <username> <password>")
			os.Exit(1)
		}
		login(os.Args[2], os.Args[3])

	case "chat":
		if len(os.Args) < 3 {
			fmt.Println("Usage: client chat <token>")
			os.Exit(1)
		}
		chat(os.Args[2])

	default:
		fmt.Println("Unknown command:", action)
		printUsage()
		os.Exit(1)
	}
}

func printUsage() {
	fmt.Println("Social Chat Client")
	fmt.Println("")
	fmt.Println("Usage:")
	fmt.Println("  client register <username> <password>   Register a new user")
	fmt.Println("  client login <username> <password>       Login and get token")
	fmt.Println("  client chat <token>                      Start chatting with token")
	fmt.Println("")
	fmt.Println("Environment Variables:")
	fmt.Println("  CHAT_SERVER_ADDR  Server address (default: http://localhost:8080)")
}

func register(username, password string) {
	body := map[string]string{
		"username": username,
		"password": password,
	}

	jsonBody, _ := json.Marshal(body)
	resp, err := http.Post(serverAddr+"/api/register", "application/json", bytes.NewBuffer(jsonBody))
	if err != nil {
		fmt.Printf("Failed to register: %v\n", err)
		return
	}
	defer resp.Body.Close()

	respBody, _ := io.ReadAll(resp.Body)

	if resp.StatusCode != http.StatusCreated {
		fmt.Printf("Registration failed (status %d): %s\n", resp.StatusCode, string(respBody))
		return
	}

	var authResp AuthResponse
	json.Unmarshal(respBody, &authResp)

	fmt.Println("Registration successful!")
	fmt.Printf("  User ID:  %s\n", authResp.User.ID)
	fmt.Printf("  Username: %s\n", authResp.User.Username)
	fmt.Printf("  Token:    %s\n", authResp.Token)
	fmt.Println()
	fmt.Println("To start chatting:")
	fmt.Printf("  client chat %s\n", authResp.Token)
}

func login(username, password string) {
	body := map[string]string{
		"username": username,
		"password": password,
	}

	jsonBody, _ := json.Marshal(body)
	resp, err := http.Post(serverAddr+"/api/login", "application/json", bytes.NewBuffer(jsonBody))
	if err != nil {
		fmt.Printf("Failed to login: %v\n", err)
		return
	}
	defer resp.Body.Close()

	respBody, _ := io.ReadAll(resp.Body)

	if resp.StatusCode != http.StatusOK {
		fmt.Printf("Login failed (status %d): %s\n", resp.StatusCode, string(respBody))
		return
	}

	var authResp AuthResponse
	json.Unmarshal(respBody, &authResp)

	fmt.Println("Login successful!")
	fmt.Printf("  User ID:  %s\n", authResp.User.ID)
	fmt.Printf("  Username: %s\n", authResp.User.Username)
	fmt.Printf("  Token:    %s\n", authResp.Token)
	fmt.Println()
	fmt.Println("To start chatting:")
	fmt.Printf("  client chat %s\n", authResp.Token)
}

func chat(token string) {
	// 构建 WebSocket URL
	wsURL := strings.Replace(serverAddr, "http://", "ws://", 1)
	wsURL = strings.Replace(wsURL, "https://", "wss://", 1)
	wsURL += "/ws"

	u, err := url.Parse(wsURL)
	if err != nil {
		log.Fatalf("Invalid URL: %v", err)
	}

	q := u.Query()
	q.Set("token", token)
	u.RawQuery = q.Encode()

	fmt.Printf("Connecting to %s...\n", u.String())

	conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer conn.Close()

	fmt.Println("Connected!")
	fmt.Println("Commands:")
	fmt.Println("  /to <user_id> <message>  - Set recipient and send message")
	fmt.Println("  /ping                    - Send heartbeat")
	fmt.Println("  /quit                    - Exit")
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

			case "/ping":
				sendPing(conn)

			case "/quit":
				fmt.Println("Bye!")
				return

			default:
				fmt.Println("Unknown command:", parts[0])
			}
		} else if currentTo != "" {
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

func sendPing(conn *websocket.Conn) {
	req := WSRequest{
		Type: "ping",
		ID:   fmt.Sprintf("ping_%d", time.Now().UnixNano()),
	}

	data, _ := json.Marshal(req)
	if err := conn.WriteMessage(websocket.TextMessage, data); err != nil {
		log.Printf("Failed to send ping: %v", err)
	}
}

func readMessages(conn *websocket.Conn) {
	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			fmt.Printf("\nConnection error: %v\n", err)
			os.Exit(1)
		}

		var resp WSResponse
		if err := json.Unmarshal(message, &resp); err != nil {
			fmt.Printf("Failed to unmarshal: %v\n", err)
			continue
		}

		switch resp.Type {
		case "message":
			handleIncomingMessage(resp)
		case "ack":
			payload, ok := resp.Payload.(map[string]interface{})
			if ok {
				fmt.Printf("[ACK] Message ID: %v\n", payload["message_id"])
			}
		case "error":
			payload, ok := resp.Payload.(map[string]interface{})
			if ok {
				fmt.Printf("[ERROR] %v: %v\n", payload["code"], payload["message"])
			}
		case "typing":
			payload, ok := resp.Payload.(map[string]interface{})
			if ok {
				fmt.Printf("[TYPING] %s is typing...\n", payload["from"])
			}
		case "pong":
			fmt.Println("[PONG] Heartbeat received")
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
