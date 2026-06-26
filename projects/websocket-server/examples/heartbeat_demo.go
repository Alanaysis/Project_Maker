// Package main implements a heartbeat demo.
//
// This example demonstrates the WebSocket heartbeat (ping/pong) mechanism.
// The server sends Ping frames at regular intervals. Clients must respond
// with Pong frames. If a client fails to respond within the timeout,
// the connection is closed.
//
// 本示例演示 WebSocket 心跳检测（Ping/Pong）机制：
// - 服务器定期发送 Ping 帧
// - 客户端必须回复 Pong 帧
// - 超时未响应则关闭连接
// - 用于检测死连接，保持连接活跃
//
// Run: go run examples/heartbeat_demo.go
package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync/atomic"
	"syscall"
	"time"

	"websocket-server/websocket"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8083"
	}

	var nextID uint64

	// Use shorter heartbeat intervals for demo purposes
	server := websocket.NewServer(websocket.ServerConfig{
		HeartbeatInterval: 5 * time.Second, // Send ping every 5s
		HeartbeatTimeout:  15 * time.Second, // Timeout after 15s
		MaxMessageSize:    64 * 1024,
	})
	server.Start()
	defer server.Stop()

	http.HandleFunc("/heartbeat", func(w http.ResponseWriter, r *http.Request) {
		key, err := websocket.VerifyHandshakeRequest(r)
		if err != nil {
			http.Error(w, "invalid handshake", http.StatusBadRequest)
			return
		}

		conn, err := websocket.HijackConn(w, r)
		if err != nil {
			http.Error(w, "hijack failed", http.StatusInternalServerError)
			return
		}

		if err := websocket.WriteHandshakeResponse(conn, key); err != nil {
			conn.Close()
			return
		}

		id := atomic.AddUint64(&nextID, 1)
		client := websocket.NewClient(id, conn)
		server.AddClient(client)

		fmt.Printf("[HEARTBEAT] Client %d connected (total: %d)\n", id, server.GetClientCount())

		go server.ReadMessages(client)
		go server.WriteMessages(client)
	})

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		fmt.Fprint(w, `<html>
<head><title>Heartbeat Demo</title></head>
<body>
<h1>Heartbeat Demo</h1>
<p>Server sends ping every 5s, timeout after 15s.</p>
<div id="log" style="height:300px;overflow:auto;border:1px solid #ccc;padding:10px;margin:10px 0;"></div>
<div id="status" style="padding:10px;font-weight:bold;"></div>
<script>
var ws;
function log(msg) {
	var d = document.getElementById("log");
	d.innerHTML += "<div>" + msg + "</div>";
	d.scrollTop = d.scrollHeight;
}
function setStatus(text, color) {
	document.getElementById("status").innerHTML = text;
	document.getElementById("status").style.color = color;
}
function connect() {
	ws = new WebSocket("ws://" + location.host + "/heartbeat");
	ws.onopen = function() { log("Connected!"); setStatus("Connected", "green"); };
	ws.onmessage = function(e) { log("Received: " + e.data); };
	ws.onclose = function() { log("Disconnected"); setStatus("Disconnected", "red"); };
}
connect();
</script>
</body></html>`)
	})

	addr := ":" + port
	fmt.Printf("[INFO] Heartbeat server starting on ws://localhost%s/heartbeat\n", addr)
	fmt.Println("[INFO] Ping interval: 5s, Timeout: 15s")

	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		<-sigCh
		fmt.Println("\n[INFO] Shutting down...")
		server.Stop()
		os.Exit(0)
	}()

	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("[ERROR] Server failed: %v", err)
	}
}
