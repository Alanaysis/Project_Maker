// Package broker implements the MQTT broker (server) that handles client
// connections, message routing, QoS delivery, and session management.
package broker

import (
	"fmt"
	"log"
	"net"
	"sync"
	"time"

	"github.com/user/mqtt-broker/internal/packet"
	"github.com/user/mqtt-broker/internal/topic"
)

// QoS states for QoS 2 protocol flow
const (
	qos2Pending   byte = 0
	qos2Received  byte = 1 // PUBREC sent
	qos2Completed byte = 2 // PUBCOMP sent
)

// Broker is the MQTT broker.
type Broker struct {
	mu       sync.RWMutex
	clients  map[string]*Client // clientID -> Client
	listener net.Listener
	topics   *topic.Manager
	done     chan struct{}
}

// New creates a new MQTT broker.
func New() *Broker {
	return &Broker{
		clients: make(map[string]*Client),
		topics:  topic.NewManager(),
		done:    make(chan struct{}),
	}
}

// Start starts the broker on the given address.
func (b *Broker) Start(addr string) error {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return fmt.Errorf("failed to listen: %w", err)
	}
	b.listener = ln
	log.Printf("MQTT broker listening on %s", addr)

	go b.acceptLoop()
	return nil
}

// Stop gracefully stops the broker.
func (b *Broker) Stop() {
	close(b.done)
	if b.listener != nil {
		b.listener.Close()
	}

	b.mu.Lock()
	defer b.mu.Unlock()
	for _, client := range b.clients {
		client.Close()
	}
}

// ClientCount returns the number of connected clients.
func (b *Broker) ClientCount() int {
	b.mu.RLock()
	defer b.mu.RUnlock()
	return len(b.clients)
}

func (b *Broker) acceptLoop() {
	for {
		conn, err := b.listener.Accept()
		if err != nil {
			select {
			case <-b.done:
				return
			default:
				log.Printf("Accept error: %v", err)
				continue
			}
		}
		go b.handleConnection(conn)
	}
}

func (b *Broker) handleConnection(conn net.Conn) {
	client := NewClient(conn)

	defer func() {
		b.handleDisconnect(client)
		conn.Close()
	}()

	for {
		// Set read deadline based on keepalive
		if client.keepAlive > 0 {
			deadline := time.Duration(client.keepAlive)*3/2 + 5
			conn.SetReadDeadline(time.Now().Add(deadline * time.Second))
		}

		pkt, fh, err := packet.ReadPacket(conn)
		if err != nil {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				log.Printf("Client %s: keepalive timeout", client.ClientID())
			}
			return
		}

		client.UpdateActivity()

		switch p := pkt.(type) {
		case *packet.ConnectPacket:
			b.handleConnect(client, p)
		case *packet.PublishPacket:
			b.handlePublish(client, p)
		case *packet.PubackPacket:
			b.handlePuback(client, p)
		case *packet.PubrecPacket:
			b.handlePubrec(client, p)
		case *packet.PubrelPacket:
			b.handlePubrel(client, p)
		case *packet.PubcompPacket:
			b.handlePubcomp(client, p)
		case *packet.SubscribePacket:
			b.handleSubscribe(client, p)
		case *packet.UnsubscribePacket:
			b.handleUnsubscribe(client, p)
		case *packet.PingreqPacket:
			b.handlePingreq(client)
		case *packet.DisconnectPacket:
			b.handleDisconnectClean(client)
			return
		default:
			log.Printf("Client %s: unhandled packet type %d (header: %+v)",
				client.ClientID(), fh.Type, fh)
		}
	}
}

func (b *Broker) handleConnect(client *Client, p *packet.ConnectPacket) {
	if p.ProtocolName != "MQTT" || p.ProtocolLevel != 4 {
		connack := &packet.ConnackPacket{ReturnCode: packet.ConnRefusedProtocol}
		data, _ := connack.Encode()
		client.Send(data)
		return
	}

	// Set client properties
	client.SetClientID(p.ClientID)
	client.cleanSession = p.CleanSession
	client.keepAlive = p.KeepAlive
	client.username = p.Username
	client.willFlag = p.WillFlag
	client.willTopic = p.WillTopic
	client.willMessage = p.WillMessage
	client.willQoS = p.WillQoS
	client.willRetain = p.WillRetain

	// Handle existing session
	sessionPresent := false
	b.mu.Lock()
	if existing, ok := b.clients[p.ClientID]; ok {
		if p.CleanSession {
			// Disconnect existing client
			existing.Close()
			b.topics.UnsubscribeAll(p.ClientID)
		} else {
			// Take over existing session
			existing.Close()
			sessionPresent = true
		}
	}
	b.clients[p.ClientID] = client
	b.mu.Unlock()

	client.SetConnected(true)

	connack := &packet.ConnackPacket{
		SessionPresent: sessionPresent,
		ReturnCode:     packet.ConnAccepted,
	}
	data, _ := connack.Encode()
	client.Send(data)

	log.Printf("Client %s connected (clean=%v)", p.ClientID, p.CleanSession)
}

func (b *Broker) handlePublish(client *Client, p *packet.PublishPacket) {
	switch p.QoS {
	case 0:
		// QoS 0: fire and forget
		b.routeMessage(p)

	case 1:
		// QoS 1: deliver and acknowledge
		b.routeMessage(p)
		puback := &packet.PubackPacket{PacketID: p.PacketID}
		data, _ := puback.Encode()
		client.Send(data)

	case 2:
		// QoS 2: exactly once delivery
		state := client.GetQoS2State(p.PacketID)
		if state == qos2Pending {
			client.SetQoS2State(p.PacketID, qos2Received)
			b.routeMessage(p)
		}
		pubrec := &packet.PubrecPacket{PacketID: p.PacketID}
		data, _ := pubrec.Encode()
		client.Send(data)
	}

	// Handle retained messages
	if p.Retain {
		b.topics.SetRetained(p.TopicName, &topic.Message{
			Topic:   p.TopicName,
			Payload: p.Payload,
			QoS:     p.QoS,
			Retain:  true,
		})
	}
}

func (b *Broker) handlePuback(client *Client, p *packet.PubackPacket) {
	client.RemoveInflight(p.PacketID)
}

func (b *Broker) handlePubrec(client *Client, p *packet.PubrecPacket) {
	// QoS 2 step 2: send PUBREL
	pubrel := &packet.PubrelPacket{PacketID: p.PacketID}
	data, _ := pubrel.Encode()
	client.Send(data)
}

func (b *Broker) handlePubrel(client *Client, p *packet.PubrelPacket) {
	// QoS 2 step 3: send PUBCOMP
	client.RemoveQoS2State(p.PacketID)
	pubcomp := &packet.PubcompPacket{PacketID: p.PacketID}
	data, _ := pubcomp.Encode()
	client.Send(data)
}

func (b *Broker) handlePubcomp(client *Client, p *packet.PubcompPacket) {
	// QoS 2 complete
	client.RemoveInflight(p.PacketID)
}

func (b *Broker) handleSubscribe(client *Client, p *packet.SubscribePacket) {
	returnCodes := make([]byte, len(p.Topics))

	for i, t := range p.Topics {
		qos := p.QoSs[i]
		if qos > 2 {
			qos = 2
		}

		b.topics.Subscribe(t, &topic.Subscriber{
			ClientID: client.ClientID(),
			QoS:      qos,
			Callback: func(msg *topic.Message) {
				b.deliverToClient(client, msg)
			},
		})

		client.subscriptions = append(client.subscriptions, t)
		returnCodes[i] = qos

		// Send retained messages
		retained := b.topics.GetRetainedForPattern(t)
		for _, msg := range retained {
			b.deliverToClient(client, msg)
		}

		log.Printf("Client %s subscribed to %s (QoS %d)", client.ClientID(), t, qos)
	}

	suback := &packet.SubackPacket{
		PacketID:    p.PacketID,
		ReturnCodes: returnCodes,
	}
	data, _ := suback.Encode()
	client.Send(data)
}

func (b *Broker) handleUnsubscribe(client *Client, p *packet.UnsubscribePacket) {
	for _, t := range p.Topics {
		b.topics.Unsubscribe(t, client.ClientID())
		log.Printf("Client %s unsubscribed from %s", client.ClientID(), t)
	}

	unsuback := &packet.UnsubackPacket{PacketID: p.PacketID}
	data, _ := unsuback.Encode()
	client.Send(data)
}

func (b *Broker) handlePingreq(client *Client) {
	resp := &packet.PingrespPacket{}
	data, _ := resp.Encode()
	client.Send(data)
}

func (b *Broker) handleDisconnect(client *Client) {
	if !client.Connected() {
		return
	}

	client.SetConnected(false)

	// Send will message if configured and not clean disconnect
	if client.willFlag {
		b.publishWill(client)
	}

	// Clean session
	if client.cleanSession {
		b.topics.UnsubscribeAll(client.ClientID())
	}

	b.mu.Lock()
	if c, ok := b.clients[client.ClientID()]; ok && c == client {
		delete(b.clients, client.ClientID())
	}
	b.mu.Unlock()

	log.Printf("Client %s disconnected", client.ClientID())
}

func (b *Broker) handleDisconnectClean(client *Client) {
	// Clean disconnect: do not send will message
	client.willFlag = false
}

func (b *Broker) publishWill(client *Client) {
	pub := &packet.PublishPacket{
		TopicName: client.willTopic,
		Payload:   client.willMessage,
		QoS:       client.willQoS,
		Retain:    client.willRetain,
	}
	b.routeMessage(pub)

	if client.willRetain {
		b.topics.SetRetained(client.willTopic, &topic.Message{
			Topic:   client.willTopic,
			Payload: client.willMessage,
			QoS:     client.willQoS,
			Retain:  true,
		})
	}

	log.Printf("Client %s: published will message to %s", client.ClientID(), client.willTopic)
}

func (b *Broker) routeMessage(pub *packet.PublishPacket) {
	subscribers := b.topics.GetSubscribers(pub.TopicName)
	for _, sub := range subscribers {
		b.mu.RLock()
		client, ok := b.clients[sub.ClientID]
		b.mu.RUnlock()

		if !ok || !client.Connected() {
			continue
		}

		// Use the lower QoS of publish and subscription
		qos := pub.QoS
		if sub.QoS < qos {
			qos = sub.QoS
		}

		msg := &topic.Message{
			Topic:   pub.TopicName,
			Payload: pub.Payload,
			QoS:     qos,
		}
		b.deliverToClient(client, msg)
	}
}

func (b *Broker) deliverToClient(client *Client, msg *topic.Message) {
	switch msg.QoS {
	case 0:
		pub := &packet.PublishPacket{
			TopicName: msg.Topic,
			Payload:   msg.Payload,
			QoS:       0,
		}
		data, _ := pub.Encode()
		client.Send(data)

	case 1:
		pid := client.NextPacketID()
		pub := &packet.PublishPacket{
			TopicName: msg.Topic,
			Payload:   msg.Payload,
			QoS:       1,
			PacketID:  pid,
		}
		data, _ := pub.Encode()
		client.Send(data)

		// Track for retransmission
		client.AddInflight(&InflightMessage{
			PacketID:  pid,
			Packet:    pub,
			State:     0,
			Timestamp: time.Now(),
		})

	case 2:
		pid := client.NextPacketID()
		pub := &packet.PublishPacket{
			TopicName: msg.Topic,
			Payload:   msg.Payload,
			QoS:       2,
			PacketID:  pid,
		}
		data, _ := pub.Encode()
		client.Send(data)

		client.AddInflight(&InflightMessage{
			PacketID:  pid,
			Packet:    pub,
			State:     0,
			Timestamp: time.Now(),
		})
	}
}
