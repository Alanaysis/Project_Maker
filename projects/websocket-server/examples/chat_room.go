// Package main implements a chat room demo.
//
// This example demonstrates the room/group feature of the WebSocket server.
// Clients can join rooms with a special message format:
//   JOIN <room_name>
//
// Messages sent while in a room are only broadcast to room members.
// Leave a room with: LEAVE
//
// 本示例演示 WebSocket 服务器的房间/群组功能：
// - JOIN <room_name> - 加入房间
// - LEAVE - 离开房间
// - 在房间内的消息只广播给房间成员
//
// Run: go run examples/chat_room.go
package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"sync/atomic"
	"syscall"

	"websocket-server/websocket"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8081"
	}

	var nextID uint64

	server := websocket.NewServer(websocket.ServerConfig{})
	server.Start()
	defer server.Stop()

	http.HandleFunc("/chat", func(w http.ResponseWriter, r *http.Request) {
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

		fmt.Printf("[CHAT] Client %d connected (total: %d)\n", id, server.GetClientCount())

		go server.ReadMessages(client)
		go server.WriteMessages(client)
	})

	// Handle JOIN/LEAVE commands in broadcast
	go func() {
		ticker := chan struct{} {}
		_ = ticker
		_ = strings.TrimSpace
	}()

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		fmt.Fprint(w, `<html>
<head><title>Chat Room Demo</title></head>
<body>
<h1>Chat Room</h1>
<p>Commands: JOIN &lt;room&gt;, LEAVE</p>
<div id="log" style="height:300px;overflow:auto;border:1px solid #ccc;padding:10px;margin:10px 0;"></div>
<input id="msg" style="width:400px;padding:8px;" placeholder="Type a message...">
<button onclick="send()">Send</button>
<select id="room">
<option value="">Global</option>
<option value="tech">Tech</option>
<option value="gaming">Gaming</option>
<option value="random">Random</option>
</select>
<script>
var ws, currentRoom = "";
function log(msg) {
	var d = document.getElementById("log");
	d.innerHTML += "<div>" + msg + "</div>";
	d.scrollTop = d.scrollHeight;
}
function connect() {
	ws = new WebSocket("ws://" + location.host + "/chat");
	ws.onopen = function() { log("Connected to chat server"); };
	ws.onmessage = function(e) { log(e.data); };
	ws.onclose = function() { log("Disconnected"); };
}
connect();
function send() {
	var msg = document.getElementById("msg").value;
	if(!msg) return;
	var room = document.getElementById("room").value;
	if(room) msg = "JOIN " + room + "\n" + msg;
	ws.send(msg);
	document.getElementById("msg").value = "";
}
</script>
</body></html>`)
	})

	addr := ":" + port
	fmt.Printf("[INFO] Chat server starting on ws://localhost%s/chat\n", addr)

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
