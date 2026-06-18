package main

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/social-chat-app/internal/client"
	"github.com/social-chat-app/pkg/config"
)

func main() {
	cfg := config.DefaultConfig()
	serverURL := fmt.Sprintf("ws://localhost:%s/ws", cfg.ServerPort)

	// Allow override
	if url := os.Getenv("CHAT_SERVER_URL"); url != "" {
		serverURL = url
	}

	fmt.Println("=== Social Chat Client ===")
	fmt.Println("Commands: /login <user> <pass>, /register <user> <pass>, /msg <user> <text>, /room <name>, /join <room>, /leave <room>, /rooms, /users, /quit")
	fmt.Println()

	c := client.NewClient(serverURL)

	reader := bufio.NewReader(os.Stdin)
	fmt.Print("Username: ")
	username, _ := reader.ReadString('\n')
	username = strings.TrimSpace(username)

	fmt.Print("Password: ")
	password, _ := reader.ReadString('\n')
	password = strings.TrimSpace(password)

	if err := c.Connect(); err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer c.Disconnect()

	// Register or login
	if err := c.Register(username, password); err != nil {
		log.Printf("Register failed (may already exist): %v", err)
	}

	if err := c.Login(username, password); err != nil {
		log.Fatalf("Login failed: %v", err)
	}

	fmt.Printf("Logged in as %s. Start chatting!\n", username)

	// Listen for incoming messages
	go c.ListenMessages()

	// Read input
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		input := strings.TrimSpace(scanner.Text())
		if input == "" {
			continue
		}

		if strings.HasPrefix(input, "/quit") {
			fmt.Println("Goodbye!")
			return
		}

		c.HandleCommand(input)
	}
}
