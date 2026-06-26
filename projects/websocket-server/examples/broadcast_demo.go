// Package main implements a broadcast demo.
//
// This example demonstrates global broadcast functionality.
// Any message sent by a client is broadcast to ALL connected clients.
// This is useful for:
// - Real-time notifications
// - Live score updates
// - Multiplayer game state sync
//
// 本示例演示全局广播功能：
// 任何客户端发送的消息都会广播给所有连接的客户端
// 适用场景：
// - 实时通知
// - 实时比分更新
// - 多人游戏状态同步
//
// Run: go run examples/broadcast_demo.go
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
		port = "8082"
	}

	var nextID uint64

	server := websocket.NewServer(websocket.ServerConfig{})
	server.Start()
	defer server.Stop()

	http.HandleFunc("/broadcast", func(w http.ResponseWriter, r *http.Request) {
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

		fmt.Printf("[BROADCAST] Client %d connected (total: %d)\n", id, server.GetClientCount())

		go server.ReadMessages(client)
		go server.WriteMessages(client)
	})

	// Broadcast server status every 5 seconds
	go func() {
		ticker := time.NewTicker(5 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				msg := fmt.Sprintf("[SYSTEM] Active clients: %d", server.GetClientCount())
				server.Broadcast(msg)
			case <-time.After(time.Hour):
				// Keep running
			}
		}
	}()

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		fmt.Fprint(w, `<html>
<head><title>Broadcast Demo</title></head>
<body>
<h1>Broadcast Demo</h1>
<p>Messages are broadcast to ALL connected clients.</p>
<div id="log" style="height:300px;overflow:auto;border:1px solid #ccc;padding:10px;margin:10px 0;"></div>
<input id="msg" style="width:400px;padding:8px;" placeholder="Broadcast a message...">
<button onclick="send()">Broadcast</button>
<script>
var ws;
function log(msg) {
	var d = document.getElementById("log");
	d.innerHTML += "<div>" + msg + "</div>";
	d.scrollTop = d.scrollHeight;
}
function connect() {
	ws = new WebSocket("ws://" + location.host + "/broadcast");
	ws.onopen = function() { log("Connected!"); };
	ws.onmessage = function(e) { log(e.data); };
	ws.onclose = function() { log("Disconnected"); };
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
	fmt.Printf("[INFO] Broadcast server starting on ws://localhost%s/broadcast\n", addr)

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
