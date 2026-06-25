package internal

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"math/big"
	"net/http"
	"sync"
	"time"
)

// MessageType represents the type of DHT message
type MessageType string

const (
	MsgPing        MessageType = "PING"
	MsgPong        MessageType = "PONG"
	MsgStore       MessageType = "STORE"
	MsgFindNode    MessageType = "FIND_NODE"
	MsgFindValue   MessageType = "FIND_VALUE"
	MsgFindNodeResp  MessageType = "FIND_NODE_RESP"
	MsgFindValueResp MessageType = "FIND_VALUE_RESP"
)

// Message represents a DHT network message
type Message struct {
	Type      MessageType `json:"type"`
	SenderID  string      `json:"sender_id"`
	SenderAddr string     `json:"sender_addr"`
	TargetID  string      `json:"target_id,omitempty"`
	Key       string      `json:"key,omitempty"`
	Value     string      `json:"value,omitempty"`
	Contacts  []ContactInfo `json:"contacts,omitempty"`
	Found     bool        `json:"found,omitempty"`
}

// ContactInfo is a serializable contact representation
type ContactInfo struct {
	ID   string `json:"id"`
	Addr string `json:"addr"`
}

// NetworkNode represents a network-capable DHT node
type NetworkNode struct {
	node       *KademliaNode
	httpServer *http.Server
	mu         sync.RWMutex
	peers      map[string]*ContactInfo // addr -> contact info
	running    bool
}

// NewNetworkNode creates a new network DHT node
func NewNetworkNode(addr string) *NetworkNode {
	node := NewKademliaNode(addr, nil)
	return &NetworkNode{
		node:  node,
		peers: make(map[string]*ContactInfo),
	}
}

// Start starts the HTTP server for the DHT node
func (nn *NetworkNode) Start() error {
	nn.mu.Lock()
	if nn.running {
		nn.mu.Unlock()
		return fmt.Errorf("node already running")
	}
	nn.running = true
	nn.mu.Unlock()

	mux := http.NewServeMux()
	mux.HandleFunc("/ping", nn.handlePing)
	mux.HandleFunc("/store", nn.handleStore)
	mux.HandleFunc("/find_node", nn.handleFindNode)
	mux.HandleFunc("/find_value", nn.handleFindValue)
	mux.HandleFunc("/info", nn.handleInfo)

	nn.httpServer = &http.Server{
		Addr:    nn.node.Addr,
		Handler: mux,
	}

	go func() {
		log.Printf("[%s] Starting DHT node on %s", FormatID(nn.node.ID), nn.node.Addr)
		if err := nn.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("[%s] Server error: %v", FormatID(nn.node.ID), err)
		}
	}()

	return nil
}

// Stop stops the HTTP server
func (nn *NetworkNode) Stop() error {
	nn.mu.Lock()
	nn.running = false
	nn.mu.Unlock()

	if nn.httpServer != nil {
		return nn.httpServer.Close()
	}
	return nil
}

// IsRunning returns whether the node is running
func (nn *NetworkNode) IsRunning() bool {
	nn.mu.RLock()
	defer nn.mu.RUnlock()
	return nn.running
}

// GetID returns the node's ID
func (nn *NetworkNode) GetID() *big.Int {
	return nn.node.ID
}

// GetAddr returns the node's address
func (nn *NetworkNode) GetAddr() string {
	return nn.node.Addr
}

// handlePing handles PING requests
func (nn *NetworkNode) handlePing(w http.ResponseWriter, r *http.Request) {
	var msg Message
	if err := json.NewDecoder(r.Body).Decode(&msg); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	// Add sender to routing table
	if msg.SenderID != "" && msg.SenderAddr != "" {
		senderID, ok := new(big.Int).SetString(msg.SenderID, 16)
		if ok {
			contact := NewContact(senderID, msg.SenderAddr)
			nn.node.RT.AddContact(contact)
		}
	}

	resp := Message{
		Type:       MsgPong,
		SenderID:   nn.node.ID.Text(16),
		SenderAddr: nn.node.Addr,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// handleStore handles STORE requests
func (nn *NetworkNode) handleStore(w http.ResponseWriter, r *http.Request) {
	var msg Message
	if err := json.NewDecoder(r.Body).Decode(&msg); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	// Add sender to routing table
	if msg.SenderID != "" && msg.SenderAddr != "" {
		senderID, ok := new(big.Int).SetString(msg.SenderID, 16)
		if ok {
			contact := NewContact(senderID, msg.SenderAddr)
			nn.node.RT.AddContact(contact)
		}
	}

	nn.node.Store(msg.Key, msg.Value)

	resp := Message{
		Type:       MsgPong,
		SenderID:   nn.node.ID.Text(16),
		SenderAddr: nn.node.Addr,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// handleFindNode handles FIND_NODE requests
func (nn *NetworkNode) handleFindNode(w http.ResponseWriter, r *http.Request) {
	var msg Message
	if err := json.NewDecoder(r.Body).Decode(&msg); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	// Add sender to routing table
	if msg.SenderID != "" && msg.SenderAddr != "" {
		senderID, ok := new(big.Int).SetString(msg.SenderID, 16)
		if ok {
			contact := NewContact(senderID, msg.SenderAddr)
			nn.node.RT.AddContact(contact)
		}
	}

	targetID, ok := new(big.Int).SetString(msg.TargetID, 16)
	if !ok {
		http.Error(w, "Invalid target ID", http.StatusBadRequest)
		return
	}

	contacts := nn.node.FindNode(targetID)
	contactInfos := make([]ContactInfo, len(contacts))
	for i, c := range contacts {
		contactInfos[i] = ContactInfo{
			ID:   c.ID.Text(16),
			Addr: c.Addr,
		}
	}

	resp := Message{
		Type:      MsgFindNodeResp,
		SenderID:  nn.node.ID.Text(16),
		SenderAddr: nn.node.Addr,
		Contacts:  contactInfos,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// handleFindValue handles FIND_VALUE requests
func (nn *NetworkNode) handleFindValue(w http.ResponseWriter, r *http.Request) {
	var msg Message
	if err := json.NewDecoder(r.Body).Decode(&msg); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	// Add sender to routing table
	if msg.SenderID != "" && msg.SenderAddr != "" {
		senderID, ok := new(big.Int).SetString(msg.SenderID, 16)
		if ok {
			contact := NewContact(senderID, msg.SenderAddr)
			nn.node.RT.AddContact(contact)
		}
	}

	value, contacts, found := nn.node.FindValue(msg.Key)
	contactInfos := make([]ContactInfo, len(contacts))
	for i, c := range contacts {
		contactInfos[i] = ContactInfo{
			ID:   c.ID.Text(16),
			Addr: c.Addr,
		}
	}

	resp := Message{
		Type:      MsgFindValueResp,
		SenderID:  nn.node.ID.Text(16),
		SenderAddr: nn.node.Addr,
		Key:       msg.Key,
		Value:     value,
		Found:     found,
		Contacts:  contactInfos,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// handleInfo returns node information
func (nn *NetworkNode) handleInfo(w http.ResponseWriter, r *http.Request) {
	info := map[string]interface{}{
		"id":             nn.node.ID.Text(16),
		"addr":           nn.node.Addr,
		"alive":          nn.node.IsAlive(),
		"total_contacts": nn.node.RT.TotalContacts(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
}

// Ping sends a PING message to a remote node
func (nn *NetworkNode) Ping(addr string) error {
	msg := Message{
		Type:       MsgPing,
		SenderID:   nn.node.ID.Text(16),
		SenderAddr: nn.node.Addr,
	}

	resp, err := nn.sendMessage(addr, msg)
	if err != nil {
		return fmt.Errorf("ping failed: %v", err)
	}

	// Add responder to routing table
	if resp.SenderID != "" && resp.SenderAddr != "" {
		senderID, ok := new(big.Int).SetString(resp.SenderID, 16)
		if ok {
			contact := NewContact(senderID, resp.SenderAddr)
			nn.node.RT.AddContact(contact)
		}
	}

	return nil
}

// RemoteStore sends a STORE message to a remote node
func (nn *NetworkNode) RemoteStore(addr, key, value string) error {
	msg := Message{
		Type:       MsgStore,
		SenderID:   nn.node.ID.Text(16),
		SenderAddr: nn.node.Addr,
		Key:        key,
		Value:      value,
	}

	_, err := nn.sendMessage(addr, msg)
	return err
}

// RemoteFindNode sends a FIND_NODE message to a remote node
func (nn *NetworkNode) RemoteFindNode(addr string, targetID *big.Int) ([]*Contact, error) {
	msg := Message{
		Type:       MsgFindNode,
		SenderID:   nn.node.ID.Text(16),
		SenderAddr: nn.node.Addr,
		TargetID:   targetID.Text(16),
	}

	resp, err := nn.sendMessage(addr, msg)
	if err != nil {
		return nil, err
	}

	contacts := make([]*Contact, len(resp.Contacts))
	for i, ci := range resp.Contacts {
		id, _ := new(big.Int).SetString(ci.ID, 16)
		contacts[i] = NewContact(id, ci.Addr)
	}

	return contacts, nil
}

// RemoteFindValue sends a FIND_VALUE message to a remote node
func (nn *NetworkNode) RemoteFindValue(addr, key string) (string, []*Contact, bool, error) {
	msg := Message{
		Type:       MsgFindValue,
		SenderID:   nn.node.ID.Text(16),
		SenderAddr: nn.node.Addr,
		Key:        key,
	}

	resp, err := nn.sendMessage(addr, msg)
	if err != nil {
		return "", nil, false, err
	}

	if resp.Found {
		return resp.Value, nil, true, nil
	}

	contacts := make([]*Contact, len(resp.Contacts))
	for i, ci := range resp.Contacts {
		id, _ := new(big.Int).SetString(ci.ID, 16)
		contacts[i] = NewContact(id, ci.Addr)
	}

	return "", contacts, false, nil
}

// sendMessage sends a message to a remote node via HTTP
func (nn *NetworkNode) sendMessage(addr string, msg Message) (*Message, error) {
	url := fmt.Sprintf("http://%s/%s", addr, msg.Type)

	jsonData, err := json.Marshal(msg)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal message: %v", err)
	}

	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Post(url, "application/json", bytesReader(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to send message: %v", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %v", err)
	}

	var response Message
	if err := json.Unmarshal(body, &response); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %v", err)
	}

	return &response, nil
}

// bytesReader creates a reader from bytes (helper function)
func bytesReader(b []byte) io.Reader {
	return &simpleReader{data: b}
}

type simpleReader struct {
	data []byte
	pos  int
}

func (r *simpleReader) Read(p []byte) (n int, err error) {
	if r.pos >= len(r.data) {
		return 0, io.EOF
	}
	n = copy(p, r.data[r.pos:])
	r.pos += n
	return n, nil
}

// KademliaIterativeFindNode performs iterative FIND_NODE to find K closest nodes
func (nn *NetworkNode) KademliaIterativeFindNode(targetID *big.Int) []*Contact {
	// Start with closest contacts from local routing table
	closest := nn.node.FindNode(targetID)
	queried := make(map[string]bool)
	queried[nn.node.Addr] = true

	// Iteratively query closer nodes
	for i := 0; i < Alpha; i++ {
		var newClosest []*Contact
		for _, c := range closest {
			if queried[c.Addr] {
				continue
			}
			queried[c.Addr] = true

			contacts, err := nn.RemoteFindNode(c.Addr, targetID)
			if err != nil {
				continue
			}

			// Add new contacts to routing table
			for _, nc := range contacts {
				nn.node.RT.AddContact(nc)
			}

			newClosest = append(newClosest, contacts...)
		}

		// Merge and sort by distance
		closest = append(closest, newClosest...)
		sort.Slice(closest, func(i, j int) bool {
			distI := XOR(closest[i].ID, targetID)
			distJ := XOR(closest[j].ID, targetID)
			return distI.Cmp(distJ) < 0
		})

		// Keep only K closest
		if len(closest) > K {
			closest = closest[:K]
		}
	}

	return closest
}

// KademliaIterativeFindValue performs iterative FIND_VALUE
func (nn *NetworkNode) KademliaIterativeFindValue(key string) (string, bool) {
	keyID := nn.node.hashFunc(key)

	// First check local storage
	if val, ok := nn.node.Get(key); ok {
		return val, true
	}

	// Start with closest contacts
	closest := nn.node.FindNode(keyID)
	queried := make(map[string]bool)
	queried[nn.node.Addr] = true

	for i := 0; i < Alpha; i++ {
		var newClosest []*Contact
		for _, c := range closest {
			if queried[c.Addr] {
				continue
			}
			queried[c.Addr] = true

			value, contacts, found, err := nn.RemoteFindValue(c.Addr, key)
			if err != nil {
				continue
			}

			if found {
				// Store locally for caching
				nn.node.Store(key, value)
				return value, true
			}

			// Add new contacts
			for _, nc := range contacts {
				nn.node.RT.AddContact(nc)
			}

			newClosest = append(newClosest, contacts...)
		}

		// Merge and sort
		closest = append(closest, newClosest...)
		sort.Slice(closest, func(i, j int) bool {
			distI := XOR(closest[i].ID, keyID)
			distJ := XOR(closest[j].ID, keyID)
			return distI.Cmp(distJ) < 0
		})

		if len(closest) > K {
			closest = closest[:K]
		}
	}

	return "", false
}

// KademliaStore performs iterative STORE to store a key-value pair
func (nn *NetworkNode) KademliaStore(key, value string) error {
	keyID := nn.node.hashFunc(key)

	// Store locally
	nn.node.Store(key, value)

	// Find K closest nodes
	closest := nn.node.FindNode(keyID)

	// Store on K closest nodes
	var wg sync.WaitGroup
	for _, c := range closest {
		if c.Addr == nn.node.Addr {
			continue
		}
		wg.Add(1)
		go func(addr string) {
			defer wg.Done()
			nn.RemoteStore(addr, key, value)
		}(c.Addr)
	}
	wg.Wait()

	return nil
}
