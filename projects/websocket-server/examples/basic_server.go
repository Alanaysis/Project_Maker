// Package main implements a basic WebSocket server.
//
// This example demonstrates the core WebSocket server lifecycle:
// 1. HTTP server listens on a port
// 2. WebSocket upgrade request arrives
// 3. Handshake (HTTP 101) completes
// 4. Bidirectional message exchange begins
//
// WebSocket 协议核心流程：
// 1. 客户端发送 HTTP 请求，包含 Upgrade 头
// 2. 服务端返回 101 Switching Protocols
// 3. TCP 连接升级为 WebSocket 全双工连接
// 4. 双方通过帧（Frame）交换数据
//
// Run: go run examples/basic_server.go
package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync/atomic"
	"syscall"

	"websocket-server/websocket"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	var nextID uint64

	server := websocket.NewServer(websocket.ServerConfig{})
	server.Start()
	defer server.Stop()

	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
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

		fmt.Printf("[INFO] Client %d connected (total: %d)\n", id, server.GetClientCount())

		go server.ReadMessages(client)
		go server.WriteMessages(client)
	})

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		fmt.Fprint(w, `<html>
<head><title>WebSocket Server Demo</title></head>
<body>
<h1>WebSocket Server Demo</h1>
<p>Connect via: ws://localhost:8080/ws</p>
<div id="log" style="height:300px;overflow:auto;border:1px solid #ccc;padding:10px;margin:10px 0;"></div>
<input id="msg" style="width:400px;padding:8px;" placeholder="Type a message...">
<button onclick="send()">Send</button>
<script>
var ws;
function log(msg) {
	var d = document.getElementById("log");
	d.innerHTML += "<div>" + msg + "</div>";
	d.scrollTop = d.scrollHeight;
}
function connect() {
	ws = new WebSocket("ws://" + location.host + "/ws");
	ws.onopen = function() { log("Connected!"); };
	ws.onmessage = function(e) { log("Received: " + e.data); };
	ws.onclose = function() { log("Disconnected."); };
}
connect();
function send() {
	if(ws && ws.readyState === 1) {
		ws.send(document.getElementById("msg").value);
		document.getElementById("msg").value = "";
	}
}
</script>
</body></html>`)
	})

	addr := ":" + port
	fmt.Printf("[INFO] WebSocket server starting on ws://localhost%s/ws\n", addr)
	fmt.Println("[INFO] Open http://localhost" + port + " in your browser")

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
