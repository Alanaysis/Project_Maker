package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
)

const baseURL = "http://localhost:8080"

type AuthResponse struct {
	Token string `json:"token"`
	User  struct {
		ID       string `json:"id"`
		Username string `json:"username"`
		Nickname string `json:"nickname"`
	} `json:"user"`
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage:")
		fmt.Println("  go run register_and_login.go register <username> <password>")
		fmt.Println("  go run register_and_login.go login <username> <password>")
		os.Exit(1)
	}

	action := os.Args[1]

	switch action {
	case "register":
		if len(os.Args) < 4 {
			fmt.Println("Usage: go run register_and_login.go register <username> <password>")
			os.Exit(1)
		}
		username := os.Args[2]
		password := os.Args[3]
		register(username, password)

	case "login":
		if len(os.Args) < 4 {
			fmt.Println("Usage: go run register_and_login.go login <username> <password>")
			os.Exit(1)
		}
		username := os.Args[2]
		password := os.Args[3]
		login(username, password)

	default:
		fmt.Println("Unknown action:", action)
		os.Exit(1)
	}
}

func register(username, password string) {
	url := baseURL + "/api/register"
	body := map[string]string{
		"username": username,
		"password": password,
	}

	jsonBody, _ := json.Marshal(body)
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(jsonBody))
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
	fmt.Printf("User ID: %s\n", authResp.User.ID)
	fmt.Printf("Username: %s\n", authResp.User.Username)
	fmt.Printf("Token: %s\n", authResp.Token)
	fmt.Println("\nUse this token to connect via WebSocket:")
	fmt.Printf("  go run client.go ws://localhost:8080/ws %s\n", authResp.Token)
}

func login(username, password string) {
	url := baseURL + "/api/login"
	body := map[string]string{
		"username": username,
		"password": password,
	}

	jsonBody, _ := json.Marshal(body)
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(jsonBody))
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
	fmt.Printf("User ID: %s\n", authResp.User.ID)
	fmt.Printf("Username: %s\n", authResp.User.Username)
	fmt.Printf("Token: %s\n", authResp.Token)
	fmt.Println("\nUse this token to connect via WebSocket:")
	fmt.Printf("  go run client.go ws://localhost:8080/ws %s\n", authResp.Token)
}