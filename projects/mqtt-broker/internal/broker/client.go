package broker

import (
	"net"
	"sync"
	"sync/atomic"
	"time"

	"github.com/user/mqtt-broker/internal/packet"
)

// Client represents a connected MQTT client.
type Client struct {
	conn         net.Conn
	clientID     string
	username     string
	cleanSession bool
	keepAlive    uint16

	// Will message
	willTopic   string
	willMessage []byte
	willQoS     byte
	willRetain  bool
	willFlag    bool

	// Subscriptions
	subscriptions []string

	// QoS 1 & 2 state
	mu          sync.Mutex
	nextPacketID uint16
	inflight    map[uint16]*InflightMessage
	qos2State   map[uint16]byte // packetID -> state for QoS 2

	// Connection state
	connected    int32
	lastActivity time.Time

	// Outbound message channel
	outChan chan []byte

	// Done channel for cleanup
	done chan struct{}
}

// InflightMessage tracks an in-flight QoS 1 or QoS 2 message.
type InflightMessage struct {
	PacketID  uint16
	Packet    *packet.PublishPacket
	State     byte
	Timestamp time.Time
}

// NewClient creates a new client from a connection.
func NewClient(conn net.Conn) *Client {
	return &Client{
		conn:         conn,
		nextPacketID: 1,
		inflight:     make(map[uint16]*InflightMessage),
		qos2State:    make(map[uint16]byte),
		lastActivity: time.Now(),
		outChan:      make(chan []byte, 256),
		done:         make(chan struct{}),
	}
}

// ClientID returns the client identifier.
func (c *Client) ClientID() string {
	return c.clientID
}

// SetClientID sets the client identifier.
func (c *Client) SetClientID(id string) {
	c.clientID = id
}

// Connected returns whether the client is connected.
func (c *Client) Connected() bool {
	return atomic.LoadInt32(&c.connected) == 1
}

// SetConnected sets the connection state.
func (c *Client) SetConnected(v bool) {
	if v {
		atomic.StoreInt32(&c.connected, 1)
	} else {
		atomic.StoreInt32(&c.connected, 0)
	}
}

// NextPacketID returns the next available packet identifier.
func (c *Client) NextPacketID() uint16 {
	c.mu.Lock()
	defer c.mu.Unlock()
	pid := c.nextPacketID
	c.nextPacketID++
	if c.nextPacketID == 0 {
		c.nextPacketID = 1
	}
	return pid
}

// AddInflight adds a message to the inflight store.
func (c *Client) AddInflight(msg *InflightMessage) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.inflight[msg.PacketID] = msg
}

// GetInflight returns an inflight message by packet ID.
func (c *Client) GetInflight(packetID uint16) *InflightMessage {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.inflight[packetID]
}

// RemoveInflight removes a message from the inflight store.
func (c *Client) RemoveInflight(packetID uint16) {
	c.mu.Lock()
	defer c.mu.Unlock()
	delete(c.inflight, packetID)
}

// SetQoS2State sets the QoS 2 state for a packet ID.
func (c *Client) SetQoS2State(packetID uint16, state byte) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.qos2State[packetID] = state
}

// GetQoS2State gets the QoS 2 state for a packet ID.
func (c *Client) GetQoS2State(packetID uint16) byte {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.qos2State[packetID]
}

// RemoveQoS2State removes the QoS 2 state for a packet ID.
func (c *Client) RemoveQoS2State(packetID uint16) {
	c.mu.Lock()
	defer c.mu.Unlock()
	delete(c.qos2State, packetID)
}

// UpdateActivity updates the last activity timestamp.
func (c *Client) UpdateActivity() {
	c.lastActivity = time.Now()
}

// Send sends raw bytes to the client.
func (c *Client) Send(data []byte) error {
	_, err := c.conn.Write(data)
	return err
}

// Close closes the client connection.
func (c *Client) Close() {
	c.SetConnected(false)
	close(c.done)
	c.conn.Close()
}

// Done returns the done channel.
func (c *Client) Done() <-chan struct{} {
	return c.done
}
