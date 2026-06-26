// Package main implements a simple MQTT client for connecting to an MQTT broker.
//
// This client demonstrates the MQTT client-side protocol flow:
// 1. Connect (CONNECT → CONNACK)
// 2. Subscribe (SUBSCRIBE → SUBACK)
// 3. Publish (PUBLISH → PUBACK)
// 4. Receive messages via subscription
// 5. Keep-alive (PINGREQ → PINGRESP)
// 6. Disconnect (DISCONNECT)
//
// MQTT Protocol Overview:
// MQTT (Message Queuing Telemetry Transport) is a lightweight publish/subscribe
// messaging protocol designed for constrained devices and low-bandwidth networks.
// It operates over TCP/IP and is commonly used in IoT applications.
package main

import (
	"bufio"
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
)

// MQTT packet types
const (
	CONNECT     byte = 1
	CONNACK     byte = 2
	PUBLISH     byte = 3
	PUBACK      byte = 4
	PUBREC      byte = 5
	PUBREL      byte = 6
	PUBCOMP     byte = 7
	SUBSCRIBE   byte = 8
	SUBACK      byte = 9
	UNSUBSCRIBE byte = 10
	UNSUBACK    byte = 11
	PINGREQ     byte = 12
	PINGRESP    byte = 13
	DISCONNECT  byte = 14
)

// MQTTClient is a simple MQTT client implementation.
type MQTTClient struct {
	conn       net.Conn
	clientID   string
	cleanSession bool
	keepAlive  uint16
	packetID   uint16
	username   string
	willTopic  string
	willMsg    []byte
	willQoS    byte
	willRetain bool
}

// NewClient creates a new MQTT client.
func NewClient(clientID string) *MQTTClient {
	return &MQTTClient{
		clientID:     clientID,
		cleanSession: true,
		keepAlive:    60,
	}
}

// Connect connects to the MQTT broker.
func (c *MQTTClient) Connect(addr string) error {
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		return fmt.Errorf("dial: %w", err)
	}
	c.conn = conn

	// Build CONNECT packet
	packet := c.encodeConnect()
	if _, err := c.conn.Write(packet); err != nil {
		return fmt.Errorf("send CONNECT: %w", err)
	}

	// Read CONNACK
	return c.readConnack()
}

// Close disconnects from the broker.
func (c *MQTTClient) Close() {
	if c.conn != nil {
		// Send DISCONNECT packet
		c.conn.Write([]byte{DISCONNECT << 4, 0})
		c.conn.Close()
	}
}

// Subscribe subscribes to one or more topics with the given QoS levels.
func (c *MQTTClient) Subscribe(topics []string, qos []byte) error {
	packetID := c.nextPacketID()
	subscribePacket := c.encodeSubscribe(packetID, topics, qos)
	if _, err := c.conn.Write(subscribePacket); err != nil {
		return fmt.Errorf("send SUBSCRIBE: %w", err)
	}
	return c.readSuback()
}

// Unsubscribe unsubscribes from topics.
func (c *MQTTClient) Unsubscribe(topics []string) error {
	packetID := c.nextPacketID()
	unsubPacket := c.encodeUnsubscribe(packetID, topics)
	if _, err := c.conn.Write(unsubPacket); err != nil {
		return fmt.Errorf("send UNSUBSCRIBE: %w", err)
	}
	return c.readUnsuback()
}

// Publish publishes a message to a topic with the specified QoS level.
func (c *MQTTClient) Publish(topic string, payload []byte, qos byte, retain bool) error {
	publishPacket := c.encodePublish(topic, payload, qos, retain)
	if _, err := c.conn.Write(publishPacket); err != nil {
		return fmt.Errorf("send PUBLISH: %w", err)
	}

	// If QoS 1, wait for PUBACK
	if qos == 1 {
		return c.readPuback()
	}
	// If QoS 2, wait for PUBREC
	if qos == 2 {
		return c.readPubrec()
	}
	return nil
}

// Ping sends a PINGREQ and waits for PINGRESP.
func (c *MQTTClient) Ping() error {
	c.conn.Write([]byte{PINGREQ << 4, 0})
	return c.readPingresp()
}

// ReadMessages reads incoming messages from the broker.
// It handles PUBLISH, PUBACK, PUBREC, PUBREL, PUBCOMP, and PINGRESP packets.
func (c *MQTTClient) ReadMessages(handler func(topic string, payload []byte, qos byte)) error {
	for {
		packet, err := c.readPacket()
		if err != nil {
			return fmt.Errorf("read packet: %w", err)
		}

		switch pkt := packet.(type) {
		case *PublishPacket:
			handler(pkt.TopicName, pkt.Payload, pkt.QoS)
		case *PubackPacket:
			// QoS 1: acknowledge received
		case *PubrecPacket:
			// QoS 2: step 2, send PUBREL
			c.sendPubrel(pkt.PacketID)
		case *PubcompPacket:
			// QoS 2: complete
		case *PingrespPacket:
			// Heartbeat response
		default:
			fmt.Printf("[Client %s] Received packet type: %d\n", c.clientID, getPacketType(packet))
		}
	}
}

// --- Encoding ---

func (c *MQTTClient) encodeConnect() []byte {
	var buf []byte

	// Variable header: Protocol Name
	buf = append(buf, 0, 4, 'M', 'Q', 'T', 'T')
	buf = append(buf, 4) // Protocol Level

	// Connect flags
	var flags byte = 0x02 // Clean Session
	if c.willFlag() {
		flags |= 0x04
		flags |= (c.willQoS & 0x03) << 3
		if c.willRetain {
			flags |= 0x20
		}
	}
	if c.username != "" {
		flags |= 0x80
	}
	buf = append(buf, flags)

	// Keep Alive
	buf = append(buf, byte(c.keepAlive>>8), byte(c.keepAlive&0xFF))

	// Payload: Client ID
	buf = append(buf, byte(len(c.clientID)>>8), byte(len(c.clientID)&0xFF))
	buf = append(buf, c.clientID...)

	if c.willFlag() {
		buf = append(buf, byte(len(c.willTopic)>>8), byte(len(c.willTopic)&0xFF))
		buf = append(buf, c.willTopic...)
		buf = append(buf, byte(len(c.willMsg)>>8), byte(len(c.willMsg)&0xFF))
		buf = append(buf, c.willMsg...)
	}

	if c.username != "" {
		buf = append(buf, byte(len(c.username)>>8), byte(len(c.username)&0xFF))
		buf = append(buf, c.username...)
	}

	// Fixed header
	var fixed []byte
	fixed = append(fixed, CONNECT<<4)
	fixed = append(fixed, encodeLength(len(buf))...)
	fixed = append(fixed, buf...)
	return fixed
}

func (c *MQTTClient) willFlag() bool {
	return c.willTopic != "" && len(c.willMsg) > 0
}

func (c *MQTTClient) encodeSubscribe(packetID uint16, topics []string, qos []byte) []byte {
	var buf []byte
	buf = append(buf, byte(packetID>>8), byte(packetID&0xFF))
	for i, topic := range topics {
		buf = append(buf, byte(len(topic)>>8), byte(len(topic)&0xFF))
		buf = append(buf, topic...)
		buf = append(buf, qos[i])
	}
	var fixed []byte
	fixed = append(fixed, SUBSCRIBE<<4|0x02) // Fixed flags 0010
	fixed = append(fixed, encodeLength(len(buf))...)
	fixed = append(fixed, buf...)
	return fixed
}

func (c *MQTTClient) encodeUnsubscribe(packetID uint16, topics []string) []byte {
	var buf []byte
	buf = append(buf, byte(packetID>>8), byte(packetID&0xFF))
	for _, topic := range topics {
		buf = append(buf, byte(len(topic)>>8), byte(len(topic)&0xFF))
		buf = append(buf, topic...)
	}
	var fixed []byte
	fixed = append(fixed, UNSUBSCRIBE<<4|0x02)
	fixed = append(fixed, encodeLength(len(buf))...)
	fixed = append(fixed, buf...)
	return fixed
}

func (c *MQTTClient) encodePublish(topic string, payload []byte, qos byte, retain bool) []byte {
	var buf []byte
	buf = append(buf, byte(len(topic)>>8), byte(len(topic)&0xFF))
	buf = append(buf, topic...)
	if qos > 0 {
		packetID := c.nextPacketID()
		buf = append(buf, byte(packetID>>8), byte(packetID&0xFF))
	}
	buf = append(buf, payload...)

	var header byte = PUBLISH << 4
	if qos == 1 {
		header |= 0x02
	} else if qos == 2 {
		header |= 0x04
	}
	if retain {
		header |= 0x01
	}

	var fixed []byte
	fixed = append(fixed, header)
	fixed = append(fixed, encodeLength(len(buf))...)
	fixed = append(fixed, buf...)
	return fixed
}

func (c *MQTTClient) sendPubrel(packetID uint16) {
	var buf []byte
	buf = append(buf, byte(packetID>>8), byte(packetID&0xFF))
	var fixed []byte
	fixed = append(fixed, PUBREL<<4|0x02)
	fixed = append(fixed, encodeLength(len(buf))...)
	fixed = append(fixed, buf...)
	c.conn.Write(fixed)
}

// --- Decoding ---

func (c *MQTTClient) readConnack() error {
	buf := make([]byte, 2)
	if _, err := c.conn.Read(buf); err != nil {
		return fmt.Errorf("read CONNACK: %w", err)
	}
	if buf[0] != 0 || buf[1] != 0 {
		return fmt.Errorf("connection rejected with code %d", buf[1])
	}
	fmt.Printf("[Client %s] Connected to broker! Session present: %v\n", c.clientID, buf[0] != 0)
	return nil
}

func (c *MQTTClient) readSuback() error {
	// Read packet type and remaining length
	header := make([]byte, 2)
	if _, err := c.conn.Read(header); err != nil {
		return fmt.Errorf("read SUBACK header: %w", err)
	}
	if (header[0] >> 4) != SUBACK {
		return fmt.Errorf("expected SUBACK, got packet type %d", header[0]>>4)
	}

	// Read packet ID (2 bytes)
	pktIDBuf := make([]byte, 2)
	if _, err := c.conn.Read(pktIDBuf); err != nil {
		return fmt.Errorf("read SUBACK packet ID: %w", err)
	}
	pktID := binary.BigEndian.Uint16(pktIDBuf)

	// Read return codes
	rcLen := header[1]
	rcBuf := make([]byte, rcLen)
	if _, err := c.conn.Read(rcBuf); err != nil {
		return fmt.Errorf("read SUBACK return codes: %w", err)
	}

	fmt.Printf("[Client %s] SUBACK received for packet ID %d, return codes: %v\n", c.clientID, pktID, rcBuf)
	return nil
}

func (c *MQTTClient) readUnsuback() error {
	header := make([]byte, 2)
	if _, err := c.conn.Read(header); err != nil {
		return fmt.Errorf("read UNSUBACK header: %w", err)
	}
	if (header[0] >> 4) != UNSUBACK {
		return fmt.Errorf("expected UNSUBACK, got %d", header[0]>>4)
	}
	return nil
}

func (c *MQTTClient) readPuback() error {
	header := make([]byte, 2)
	if _, err := c.conn.Read(header); err != nil {
		return fmt.Errorf("read PUBACK header: %w", err)
	}
	if (header[0] >> 4) != PUBACK {
		return fmt.Errorf("expected PUBACK, got %d", header[0]>>4)
	}
	return nil
}

func (c *MQTTClient) readPubrec() error {
	header := make([]byte, 2)
	if _, err := c.conn.Read(header); err != nil {
		return fmt.Errorf("read PUBREC header: %w", err)
	}
	if (header[0] >> 4) != PUBREC {
		return fmt.Errorf("expected PUBREC, got %d", header[0]>>4)
	}
	return nil
}

func (c *MQTTClient) readPingresp() error {
	header := make([]byte, 2)
	if _, err := c.conn.Read(header); err != nil {
		return fmt.Errorf("read PINGRESP header: %w", err)
	}
	if (header[0] >> 4) != PINGRESP {
		return fmt.Errorf("expected PINGRESP, got %d", header[0]>>4)
	}
	return nil
}

func (c *MQTTClient) readPacket() (interface{}, error) {
	// Read fixed header
	headerBuf := make([]byte, 2)
	if _, err := c.conn.Read(headerBuf); err != nil {
		return nil, err
	}
	pktType := (headerBuf[0] >> 4) & 0x0F
	remainingLen := headerBuf[1]

	if remainingLen == 0 {
		return getPacketByType(pktType), nil
	}

	body := make([]byte, remainingLen)
	if _, err := c.conn.Read(body); err != nil {
		return nil, err
	}

	bodyReader := newBufferReader(body)

	switch pktType {
	case PUBLISH:
		return decodePublish(bodyReader)
	case PUBACK:
		return decodePuback(bodyReader)
	case PUBREC:
		return decodePubrec(bodyReader)
	case PUBREL:
		return decodePubrel(bodyReader)
	case PUBCOMP:
		return decodePubcomp(bodyReader)
	default:
		return getPacketByType(pktType), nil
	}
}

// --- Helpers ---

func (c *MQTTClient) nextPacketID() uint16 {
	c.packetID++
	if c.packetID == 0 {
		c.packetID = 1
	}
	return c.packetID
}

func encodeLength(length int) []byte {
	var encoded []byte
	for {
		digit := byte(length % 128)
		length /= 128
		if length > 0 {
			digit |= 0x80
		}
		encoded = append(encoded, digit)
		if length == 0 {
			break
		}
	}
	return encoded
}

func getPacketType(pkt interface{}) byte {
	switch pkt.(type) {
	case *PublishPacket:
		return PUBLISH
	case *PubackPacket:
		return PUBACK
	case *PubrecPacket:
		return PUBREC
	case *PubcompPacket:
		return PUBCOMP
	case *PingrespPacket:
		return PINGRESP
	default:
		return 0
	}
}

func getPacketByType(t byte) interface{} {
	switch t {
	case PINGRESP:
		return &PingrespPacket{}
	default:
		return nil
	}
}

// --- Simple buffer reader ---

type bufferReader struct {
	data []byte
	pos  int
}

func newBufferReader(data []byte) *bufferReader {
	return &bufferReader{data: data, pos: 0}
}

func (r *bufferReader) Read(p []byte) (int, error) {
	if r.pos >= len(r.data) {
		return 0, fmt.Errorf("EOF")
	}
	n := copy(p, r.data[r.pos:])
	r.pos += n
	return n, nil
}

// --- Packet types for client ---

type PublishPacket struct {
	TopicName string
	Payload   []byte
	QoS       byte
}

type PubackPacket struct {
	PacketID uint16
}

type PubrecPacket struct {
	PacketID uint16
}

type PubrelPacket struct {
	PacketID uint16
}

type PubcompPacket struct {
	PacketID uint16
}

type PingrespPacket struct{}

func decodePublish(r *bufferReader) (*PublishPacket, error) {
	p := &PublishPacket{}
	// Read topic name (length prefixed)
	topicLenBuf := make([]byte, 2)
	if _, err := r.Read(topicLenBuf); err != nil {
		return nil, err
	}
	topicLen := int(topicLenBuf[0])<<8 | int(topicLenBuf[1])
	topic := make([]byte, topicLen)
	if _, err := r.Read(topic); err != nil {
		return nil, err
	}
	p.TopicName = string(topic)

	// Read packet ID (for QoS > 0)
	pidBuf := make([]byte, 2)
	if _, err := r.Read(pidBuf); err != nil {
		return nil, err
	}
	p.PacketID = uint16(pidBuf[0])<<8 | uint16(pidBuf[1])

	// Read payload
	p.Payload = make([]byte, len(r.data)-r.pos)
	r.Read(p.Payload)
	return p, nil
}

func decodePuback(r *bufferReader) (*PubackPacket, error) {
	buf := make([]byte, 2)
	if _, err := r.Read(buf); err != nil {
		return nil, err
	}
	return &PubackPacket{PacketID: uint16(buf[0])<<8 | uint16(buf[1])}, nil
}

func decodePubrec(r *bufferReader) (*PubrecPacket, error) {
	buf := make([]byte, 2)
	if _, err := r.Read(buf); err != nil {
		return nil, err
	}
	return &PubrecPacket{PacketID: uint16(buf[0])<<8 | uint16(buf[1])}, nil
}

func decodePubrel(r *bufferReader) (*PubrelPacket, error) {
	buf := make([]byte, 2)
	if _, err := r.Read(buf); err != nil {
		return nil, err
	}
	return &PubrelPacket{PacketID: uint16(buf[0])<<8 | uint16(buf[1])}, nil
}

func decodePubcomp(r *bufferReader) (*PubcompPacket, error) {
	buf := make([]byte, 2)
	if _, err := r.Read(buf); err != nil {
		return nil, err
	}
	return &PubcompPacket{PacketID: uint16(buf[0])<<8 | uint16(buf[1])}, nil
}

// --- Main ---

func main() {
	addr := "127.0.0.1:1883"
	if len(os.Args) > 1 {
		addr = os.Args[1]
	}

	clientID := "mqtt-client-demo"
	if len(os.Args) > 2 {
		clientID = os.Args[2]
	}

	client := NewClient(clientID)

	// Connect to broker
	if err := client.Connect(addr); err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer client.Close()

	// Set up signal handling
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Subscribe to a topic
	topics := []string{"demo/topic"}
	qos := []byte{1}
	if err := client.Subscribe(topics, qos); err != nil {
		log.Fatalf("Failed to subscribe: %v", err)
	}

	// Start message reader in a goroutine
	msgReceived := make(chan struct{})
	go func() {
		client.ReadMessages(func(topic string, payload []byte, qos byte) {
			fmt.Printf("[Received] Topic: %s, Payload: %s, QoS: %d\n", topic, string(payload), qos)
			select {
			case msgReceived <- struct{}{}:
			default:
			}
		})
	}()

	// Publish a few messages
	for i := 0; i < 3; i++ {
		msg := fmt.Sprintf("Hello from %s! Message %d", clientID, i+1)
		if err := client.Publish("demo/topic", []byte(msg), 1, false); err != nil {
			log.Printf("Failed to publish: %v", err)
		}
		fmt.Printf("[Published] %s\n", msg)
		<-msgReceived // Wait for each message to be received
	}

	// Publish a QoS 2 message
	if err := client.Publish("demo/topic/qos2", []byte("Guaranteed delivery message"), 2, false); err != nil {
		log.Printf("Failed to publish QoS 2: %v", err)
	}
	fmt.Println("[Published] QoS 2 message (guaranteed delivery)")

	// Publish a QoS 0 message (fire and forget)
	if err := client.Publish("demo/topic/qos0", []byte("Fire and forget"), 0, false); err != nil {
		log.Printf("Failed to publish QoS 0: %v", err)
	}
	fmt.Println("[Published] QoS 0 message (fire and forget)")

	// Publish a retained message
	if err := client.Publish("demo/topic/status", []byte("online"), 1, true); err != nil {
		log.Printf("Failed to publish retained: %v", err)
	}
	fmt.Println("[Published] Retained message")

	// Ping the broker
	if err := client.Ping(); err != nil {
		log.Printf("Ping failed: %v", err)
	}
	fmt.Println("[Ping] Broker responded")

	// Wait for shutdown signal
	fmt.Println("Press Ctrl+C to disconnect")
	<-sigChan

	fmt.Println("[Client] Disconnecting...")
}
