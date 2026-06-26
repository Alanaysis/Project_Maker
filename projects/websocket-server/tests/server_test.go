package websocket

import (
	"sync"
	"testing"
	"time"
)

// TestNewServer tests server creation with default config.
func TestNewServerDefault(t *testing.T) {
	server := NewServer(ServerConfig{})
	if server == nil {
		t.Fatal("NewServer returned nil")
	}
	if server.clients == nil {
		t.Error("clients map should not be nil")
	}
	if server.rooms == nil {
		t.Error("rooms map should not be nil")
	}
	if server.quit == nil {
		t.Error("quit channel should not be nil")
	}
}

// TestNewServerWithConfig tests server creation with custom config.
func TestNewServerWithConfig(t *testing.T) {
	server := NewServer(ServerConfig{
		HeartbeatInterval: 10 * time.Second,
		HeartbeatTimeout:  20 * time.Second,
		MaxMessageSize:    1024,
	})
	if server == nil {
		t.Fatal("NewServer returned nil")
	}
}

// TestServerStartStop tests server start and stop.
func TestServerStartStop(t *testing.T) {
	server := NewServer(ServerConfig{})
	server.Start()

	// Give background goroutines time to start
	time.Sleep(10 * time.Millisecond)

	server.Stop()

	// Stop should be idempotent
	server.Stop()
}

// TestAddAndRemoveClient tests client registration and removal.
func TestAddAndRemoveClient(t *testing.T) {
	server := NewServer(ServerConfig{})

	client := &Client{
		ID:     1,
		Conn:   nil,
		Send:   make(chan []byte, 10),
		closed: 0,
	}

	server.AddClient(client)
	if server.GetClientCount() != 1 {
		t.Errorf("client count = %d, want 1", server.GetClientCount())
	}

	retrieved, ok := server.GetClient(1)
	if !ok {
		t.Error("should find client by ID")
	}
	if retrieved != client {
		t.Error("retrieved client should be the same instance")
	}

	server.RemoveClient(1)
	if server.GetClientCount() != 0 {
		t.Errorf("client count = %d, want 0", server.GetClientCount())
	}

	_, ok = server.GetClient(1)
	if ok {
		t.Error("should not find removed client")
	}
}

// TestBroadcast tests global broadcast.
func TestBroadcast(t *testing.T) {
	server := NewServer(ServerConfig{})

	c1 := &Client{ID: 1, Send: make(chan []byte, 10), closed: 0}
	c2 := &Client{ID: 2, Send: make(chan []byte, 10), closed: 0}

	server.AddClient(c1)
	server.AddClient(c2)

	server.Broadcast("hello")

	// Check both clients received the message
	select {
	case msg := <-c1.Send:
		if string(msg) != "hello" {
			t.Errorf("c1 msg = %q, want %q", string(msg), "hello")
		}
	default:
		t.Error("c1 should have received broadcast")
	}

	select {
	case msg := <-c2.Send:
		if string(msg) != "hello" {
			t.Errorf("c2 msg = %q, want %q", string(msg), "hello")
		}
	default:
		t.Error("c2 should have received broadcast")
	}
}

// TestBroadcastRoom tests room-specific broadcast.
func TestBroadcastRoom(t *testing.T) {
	server := NewServer(ServerConfig{})

	c1 := &Client{ID: 1, Room: "room1", Send: make(chan []byte, 10), closed: 0}
	c2 := &Client{ID: 2, Room: "room1", Send: make(chan []byte, 10), closed: 0}
	c3 := &Client{ID: 3, Room: "room2", Send: make(chan []byte, 10), closed: 0}

	server.AddClient(c1)
	server.AddClient(c2)
	server.AddClient(c3)

	server.BroadcastRoom("room1", "room message")

	// c1 and c2 should receive
	received1 := false
	received2 := false
	for i := 0; i < 2; i++ {
		select {
		case msg := <-c1.Send:
			if string(msg) == "room message" {
				received1 = true
			}
		case msg := <-c2.Send:
			if string(msg) == "room message" {
				received2 = true
			}
		default:
		}
	}

	if !received1 {
		t.Error("c1 should have received room message")
	}
	if !received2 {
		t.Error("c2 should have received room message")
	}

	// c3 should not receive (different room)
	select {
	case <-c3.Send:
		t.Error("c3 should not have received room1 message")
	default:
		// Good, c3 didn't receive
	}
}

// TestJoinRoom tests room joining.
func TestJoinRoom(t *testing.T) {
	server := NewServer(ServerConfig{})

	client := &Client{ID: 1, Send: make(chan []byte, 10), closed: 0}
	server.AddClient(client)

	server.JoinRoom(1, "lobby")

	members := server.GetRoomMembers("lobby")
	if len(members) != 1 {
		t.Errorf("room members = %d, want 1", len(members))
	}

	if client.Room != "lobby" {
		t.Errorf("client room = %q, want %q", client.Room, "lobby")
	}
}

// TestLeaveRoom tests room leaving.
func TestLeaveRoom(t *testing.T) {
	server := NewServer(ServerConfig{})

	c1 := &Client{ID: 1, Room: "lobby", Send: make(chan []byte, 10), closed: 0}
	c2 := &Client{ID: 2, Room: "lobby", Send: make(chan []byte, 10), closed: 0}

	server.AddClient(c1)
	server.AddClient(c2)
	server.JoinRoom(1, "lobby")
	server.JoinRoom(2, "lobby")

	server.LeaveRoom(1, "lobby")

	members := server.GetRoomMembers("lobby")
	if len(members) != 1 {
		t.Errorf("room members = %d, want 1", len(members))
	}
}

// TestGetRoomMembers tests getting room members.
func TestGetRoomMembers(t *testing.T) {
	server := NewServer(ServerConfig{})

	c1 := &Client{ID: 1, Send: make(chan []byte, 10), closed: 0}
	c2 := &Client{ID: 2, Send: make(chan []byte, 10), closed: 0}

	server.AddClient(c1)
	server.AddClient(c2)
	server.JoinRoom(1, "room")
	server.JoinRoom(2, "room")

	members := server.GetRoomMembers("room")
	if len(members) != 2 {
		t.Errorf("members = %d, want 2", len(members))
	}

	// Check both IDs are present
	found1, found2 := false, false
	for _, id := range members {
		if id == 1 {
			found1 = true
		}
		if id == 2 {
			found2 = true
		}
	}
	if !found1 || !found2 {
		t.Error("both client IDs should be in room members")
	}
}

// TestEmptyRoomMembers tests getting members of non-existent room.
func TestEmptyRoomMembers(t *testing.T) {
	server := NewServer(ServerConfig{})

	members := server.GetRoomMembers("nonexistent")
	if members != nil {
		t.Error("non-existent room should return nil")
	}
}

// TestConcurrentBroadcast tests concurrent broadcast safety.
func TestConcurrentBroadcast(t *testing.T) {
	server := NewServer(ServerConfig{})

	// Create 10 clients
	var clients []*Client
	for i := uint64(1); i <= 10; i++ {
		c := &Client{
			ID:     i,
			Send:   make(chan []byte, 10),
			closed: 0,
		}
		clients = append(clients, c)
		server.AddClient(c)
	}

	var wg sync.WaitGroup
	// Broadcast concurrently from multiple goroutines
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			for j := 0; j < 10; j++ {
				server.Broadcast("msg")
			}
		}(i)
	}

	wg.Wait()
}

// TestConcurrentClientOperations tests concurrent client operations.
func TestConcurrentClientOperations(t *testing.T) {
	server := NewServer(ServerConfig{})

	var wg sync.WaitGroup

	// Concurrent add/remove
	for i := uint64(1); i <= 10; i++ {
		wg.Add(1)
		go func(id uint64) {
			defer wg.Done()
			c := &Client{
				ID:     id,
				Send:   make(chan []byte, 10),
				closed: 0,
			}
			server.AddClient(c)
			time.Sleep(time.Millisecond)
			server.RemoveClient(id)
		}(i)
	}

	// Concurrent broadcast
	wg.Add(1)
	go func() {
		defer wg.Done()
		for j := 0; j < 10; j++ {
			server.Broadcast("test")
		}
	}()

	wg.Wait()
}

// TestClientIsClosed tests the closed state.
func TestClientIsClosed(t *testing.T) {
	client := &Client{
		ID:     1,
		Send:   make(chan []byte, 10),
		closed: 0,
	}

	if client.IsClosed() {
		t.Error("new client should not be closed")
	}

	// Simulate closing
	client.closed = 1
	if !client.IsClosed() {
		t.Error("client should be closed after setting closed flag")
	}
}

// TestClientSendText tests sending text to a client.
func TestClientSendText(t *testing.T) {
	client := &Client{
		ID:     1,
		Send:   make(chan []byte, 10),
		closed: 0,
	}

	client.SendText("hello")

	select {
	case data := <-client.Send:
		if len(data) == 0 {
			t.Error("should have received data")
		}
	default:
		t.Error("should have received data in channel")
	}
}

// TestClientSendPing tests sending ping to a client.
func TestClientSendPing(t *testing.T) {
	client := &Client{
		ID:       1,
		Send:     make(chan []byte, 10),
		closed:   0,
		LastPing: time.Time{},
	}

	client.SendPing()

	// Check LastPing was updated
	if client.LastPing.IsZero() {
		t.Error("LastPing should be updated after SendPing")
	}

	select {
	case data := <-client.Send:
		if len(data) == 0 {
			t.Error("should have received ping data")
		}
	default:
		t.Error("should have received ping data in channel")
	}
}

// TestServerGetNonExistentClient tests getting a non-existent client.
func TestServerGetNonExistentClient(t *testing.T) {
	server := NewServer(ServerConfig{})

	_, ok := server.GetClient(999)
	if ok {
		t.Error("should not find non-existent client")
	}
}

// TestServerRemoveNonExistentClient tests removing a non-existent client.
func TestServerRemoveNonExistentClient(t *testing.T) {
	server := NewServer(ServerConfig{})

	// Should not panic
	server.RemoveClient(999)
}

// TestServerBroadcastEmpty tests broadcast with no clients.
func TestServerBroadcastEmpty(t *testing.T) {
	server := NewServer(ServerConfig{})

	// Should not panic
	server.Broadcast("hello")
}

// TestServerBroadcastRoomEmpty tests room broadcast with no members.
func TestServerBroadcastRoomEmpty(t *testing.T) {
	server := NewServer(ServerConfig{})

	// Should not panic
	server.BroadcastRoom("empty-room", "hello")
}

// TestNewClient tests client creation.
func TestNewClient(t *testing.T) {
	client := NewClient(42, nil)
	if client == nil {
		t.Fatal("NewClient returned nil")
	}
	if client.ID != 42 {
		t.Errorf("client ID = %d, want 42", client.ID)
	}
	if client.Send == nil {
		t.Error("Send channel should not be nil")
	}
	if len(client.Send) != 0 {
		t.Error("Send channel should be empty")
	}
}

// TestServerStopIdempotent tests that Stop can be called multiple times.
func TestServerStopIdempotent(t *testing.T) {
	server := NewServer(ServerConfig{})
	server.Start()

	server.Stop()
	server.Stop()
	server.Stop() // Multiple stops should not panic
}

// TestServerStartTwice tests that Start can be called multiple times.
func TestServerStartTwice(t *testing.T) {
	server := NewServer(ServerConfig{})
	server.Start()
	server.Start() // Multiple starts should not panic
	server.Stop()
}

// TestServerGetClientCount tests accurate client count.
func TestServerGetClientCount(t *testing.T) {
	server := NewServer(ServerConfig{})

	if server.GetClientCount() != 0 {
		t.Errorf("initial count = %d, want 0", server.GetClientCount())
	}

	c := &Client{ID: 1, Send: make(chan []byte, 10), closed: 0}
	server.AddClient(c)
	if server.GetClientCount() != 1 {
		t.Errorf("count after add = %d, want 1", server.GetClientCount())
	}

	server.RemoveClient(1)
	if server.GetClientCount() != 0 {
		t.Errorf("count after remove = %d, want 0", server.GetClientCount())
	}
}

// TestServerJoinRoomCreatesRoom tests that JoinRoom creates a new room.
func TestServerJoinRoomCreatesRoom(t *testing.T) {
	server := NewServer(ServerConfig{})

	client := &Client{ID: 1, Send: make(chan []byte, 10), closed: 0}
	server.AddClient(client)

	server.JoinRoom(1, "new-room")

	members := server.GetRoomMembers("new-room")
	if len(members) != 1 {
		t.Errorf("room members = %d, want 1", len(members))
	}
}

// TestServerLeaveRoomRemovesEmptyRoom tests that leaving an empty room removes it.
func TestServerLeaveRoomRemovesEmptyRoom(t *testing.T) {
	server := NewServer(ServerConfig{})

	client := &Client{ID: 1, Room: "temp", Send: make(chan []byte, 10), closed: 0}
	server.AddClient(client)
	server.JoinRoom(1, "temp")

	server.LeaveRoom(1, "temp")

	members := server.GetRoomMembers("temp")
	if members != nil {
		t.Error("empty room should be removed")
	}
}
