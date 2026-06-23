package tests

import (
	"bytes"
	"fmt"
	"net"
	"sync"
	"testing"
	"time"

	"github.com/user/mqtt-broker/internal/broker"
	"github.com/user/mqtt-broker/internal/packet"
)

// testClient simulates an MQTT client for testing.
type testClient struct {
	conn     net.Conn
	received []packet.Packet
	mu       sync.Mutex
}

func newTestClient(addr string) (*testClient, error) {
	conn, err := net.DialTimeout("tcp", addr, 5*time.Second)
	if err != nil {
		return nil, err
	}
	tc := &testClient{conn: conn}
	go tc.readLoop()
	return tc, nil
}

func (tc *testClient) readLoop() {
	for {
		pkt, _, err := packet.ReadPacket(tc.conn)
		if err != nil {
			return
		}
		tc.mu.Lock()
		tc.received = append(tc.received, pkt)
		tc.mu.Unlock()
	}
}

func (tc *testClient) send(pkt packet.Packet) error {
	data, err := pkt.Encode()
	if err != nil {
		return err
	}
	_, err = tc.conn.Write(data)
	return err
}

func (tc *testClient) getReceived() []packet.Packet {
	tc.mu.Lock()
	defer tc.mu.Unlock()
	result := make([]packet.Packet, len(tc.received))
	copy(result, tc.received)
	return result
}

func (tc *testClient) waitForPacket(pktType byte, timeout time.Duration) (packet.Packet, error) {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		tc.mu.Lock()
		for _, pkt := range tc.received {
			if pkt.Type() == pktType {
				tc.mu.Unlock()
				return pkt, nil
			}
		}
		tc.mu.Unlock()
		time.Sleep(10 * time.Millisecond)
	}
	return nil, fmt.Errorf("timeout waiting for packet type %d", pktType)
}

func (tc *testClient) clearReceived() {
	tc.mu.Lock()
	tc.received = nil
	tc.mu.Unlock()
}

func (tc *testClient) close() {
	tc.conn.Close()
}

func setupBroker(t *testing.T) (*broker.Broker, string) {
	t.Helper()
	b := broker.New()
	// Use port 0 to get a random available port
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("Failed to listen: %v", err)
	}
	addr := ln.Addr().String()
	ln.Close()

	if err := b.Start(addr); err != nil {
		t.Fatalf("Failed to start broker: %v", err)
	}
	time.Sleep(50 * time.Millisecond)
	return b, addr
}

func connectClient(t *testing.T, addr string, clientID string, cleanSession bool) *testClient {
	t.Helper()
	tc, err := newTestClient(addr)
	if err != nil {
		t.Fatalf("Failed to connect: %v", err)
	}

	connectPkt := &packet.ConnectPacket{
		ProtocolName:  "MQTT",
		ProtocolLevel: 4,
		CleanSession:  cleanSession,
		KeepAlive:     60,
		ClientID:      clientID,
	}
	if err := tc.send(connectPkt); err != nil {
		t.Fatalf("Failed to send CONNECT: %v", err)
	}

	connack, err := tc.waitForPacket(packet.CONNACK, 2*time.Second)
	if err != nil {
		t.Fatalf("Failed to get CONNACK: %v", err)
	}
	ca := connack.(*packet.ConnackPacket)
	if ca.ReturnCode != packet.ConnAccepted {
		t.Fatalf("Connection refused: %d", ca.ReturnCode)
	}

	return tc
}

func TestBrokerConnectDisconnect(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	tc := connectClient(t, addr, "test-1", true)
	time.Sleep(50 * time.Millisecond)

	if b.ClientCount() != 1 {
		t.Errorf("ClientCount = %d, want 1", b.ClientCount())
	}

	tc.close()
	time.Sleep(100 * time.Millisecond)

	if b.ClientCount() != 0 {
		t.Errorf("ClientCount = %d, want 0", b.ClientCount())
	}
}

func TestBrokerSubscribePublish(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	// Subscriber
	sub := connectClient(t, addr, "subscriber", true)
	defer sub.close()

	// Subscribe
	sub.send(&packet.SubscribePacket{
		PacketID: 1,
		Topics:   []string{"test/topic"},
		QoSs:     []byte{0},
	})

	_, err := sub.waitForPacket(packet.SUBACK, 2*time.Second)
	if err != nil {
		t.Fatalf("Failed to get SUBACK: %v", err)
	}

	// Publisher
	pub := connectClient(t, addr, "publisher", true)
	defer pub.close()

	// Publish
	pub.send(&packet.PublishPacket{
		TopicName: "test/topic",
		Payload:   []byte("hello world"),
		QoS:       0,
	})

	// Wait for message delivery
	time.Sleep(100 * time.Millisecond)

	msg, err := sub.waitForPacket(packet.PUBLISH, 2*time.Second)
	if err != nil {
		t.Fatalf("Subscriber didn't receive message: %v", err)
	}

	pubPkt := msg.(*packet.PublishPacket)
	if pubPkt.TopicName != "test/topic" {
		t.Errorf("Topic = %q, want %q", pubPkt.TopicName, "test/topic")
	}
	if string(pubPkt.Payload) != "hello world" {
		t.Errorf("Payload = %q, want %q", pubPkt.Payload, "hello world")
	}
}

func TestBrokerQoS1(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	sub := connectClient(t, addr, "sub-qos1", true)
	defer sub.close()

	sub.send(&packet.SubscribePacket{
		PacketID: 1,
		Topics:   []string{"qos1/test"},
		QoSs:     []byte{1},
	})
	sub.waitForPacket(packet.SUBACK, 2*time.Second)

	pub := connectClient(t, addr, "pub-qos1", true)
	defer pub.close()

	pub.send(&packet.PublishPacket{
		TopicName: "qos1/test",
		Payload:   []byte("qos1 message"),
		QoS:       1,
		PacketID:  1,
	})

	// Publisher should receive PUBACK
	puback, err := pub.waitForPacket(packet.PUBACK, 2*time.Second)
	if err != nil {
		t.Fatalf("Publisher didn't receive PUBACK: %v", err)
	}
	pa := puback.(*packet.PubackPacket)
	if pa.PacketID != 1 {
		t.Errorf("PUBACK PacketID = %d, want 1", pa.PacketID)
	}

	// Subscriber should receive the message
	msg, err := sub.waitForPacket(packet.PUBLISH, 2*time.Second)
	if err != nil {
		t.Fatalf("Subscriber didn't receive message: %v", err)
	}
	if string(msg.(*packet.PublishPacket).Payload) != "qos1 message" {
		t.Errorf("Wrong payload: %q", msg.(*packet.PublishPacket).Payload)
	}
}

func TestBrokerQoS2(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	sub := connectClient(t, addr, "sub-qos2", true)
	defer sub.close()

	sub.send(&packet.SubscribePacket{
		PacketID: 1,
		Topics:   []string{"qos2/test"},
		QoSs:     []byte{2},
	})
	sub.waitForPacket(packet.SUBACK, 2*time.Second)

	pub := connectClient(t, addr, "pub-qos2", true)
	defer pub.close()

	pub.send(&packet.PublishPacket{
		TopicName: "qos2/test",
		Payload:   []byte("exactly once"),
		QoS:       2,
		PacketID:  1,
	})

	// Publisher: PUBLISH -> PUBREC -> PUBREL -> PUBCOMP
	pubrec, err := pub.waitForPacket(packet.PUBREC, 2*time.Second)
	if err != nil {
		t.Fatalf("Publisher didn't receive PUBREC: %v", err)
	}
	if pubrec.(*packet.PubrecPacket).PacketID != 1 {
		t.Errorf("PUBREC PacketID wrong")
	}

	pub.send(&packet.PubrelPacket{PacketID: 1})

	pubcomp, err := pub.waitForPacket(packet.PUBCOMP, 2*time.Second)
	if err != nil {
		t.Fatalf("Publisher didn't receive PUBCOMP: %v", err)
	}
	if pubcomp.(*packet.PubcompPacket).PacketID != 1 {
		t.Errorf("PUBCOMP PacketID wrong")
	}

	// Subscriber: PUBLISH -> PUBREL -> send PUBREC -> PUBCOMP
	msg, err := sub.waitForPacket(packet.PUBLISH, 2*time.Second)
	if err != nil {
		t.Fatalf("Subscriber didn't receive message: %v", err)
	}
	if string(msg.(*packet.PublishPacket).Payload) != "exactly once" {
		t.Errorf("Wrong payload")
	}

	sub.send(&packet.PubrecPacket{PacketID: msg.(*packet.PublishPacket).PacketID})

	_, err = sub.waitForPacket(packet.PUBREL, 2*time.Second)
	if err != nil {
		t.Fatalf("Subscriber didn't receive PUBREL: %v", err)
	}
}

func TestBrokerWillMessage(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	// Subscriber for will topic
	sub := connectClient(t, addr, "will-sub", true)
	defer sub.close()

	sub.send(&packet.SubscribePacket{
		PacketID: 1,
		Topics:   []string{"test/will"},
		QoSs:     []byte{0},
	})
	sub.waitForPacket(packet.SUBACK, 2*time.Second)

	// Client with will message
	willClient, err := newTestClient(addr)
	if err != nil {
		t.Fatalf("Failed to connect: %v", err)
	}

	willClient.send(&packet.ConnectPacket{
		ProtocolName:  "MQTT",
		ProtocolLevel: 4,
		CleanSession:  true,
		KeepAlive:     60,
		ClientID:      "will-client",
		WillFlag:      true,
		WillTopic:     "test/will",
		WillMessage:   []byte("I'm offline"),
		WillQoS:       0,
	})

	willClient.waitForPacket(packet.CONNACK, 2*time.Second)

	// Abruptly close (simulate network failure)
	willClient.conn.Close()
	time.Sleep(200 * time.Millisecond)

	// Subscriber should receive will message
	msg, err := sub.waitForPacket(packet.PUBLISH, 3*time.Second)
	if err != nil {
		t.Fatalf("Subscriber didn't receive will message: %v", err)
	}

	pubPkt := msg.(*packet.PublishPacket)
	if string(pubPkt.Payload) != "I'm offline" {
		t.Errorf("Will payload = %q, want %q", pubPkt.Payload, "I'm offline")
	}
}

func TestBrokerNoWillOnCleanDisconnect(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	sub := connectClient(t, addr, "will-sub2", true)
	defer sub.close()

	sub.send(&packet.SubscribePacket{
		PacketID: 1,
		Topics:   []string{"test/will2"},
		QoSs:     []byte{0},
	})
	sub.waitForPacket(packet.SUBACK, 2*time.Second)

	willClient := connectClient(t, addr, "will-client2", true)

	// Set will, then disconnect cleanly
	willClient.send(&packet.ConnectPacket{
		ProtocolName:  "MQTT",
		ProtocolLevel: 4,
		CleanSession:  true,
		KeepAlive:     60,
		ClientID:      "will-client2",
		WillFlag:      true,
		WillTopic:     "test/will2",
		WillMessage:   []byte("should not appear"),
		WillQoS:       0,
	})

	// Wait for will-client to be fully connected
	time.Sleep(100 * time.Millisecond)

	// Clean disconnect
	willClient.send(&packet.DisconnectPacket{})
	time.Sleep(200 * time.Millisecond)

	// Should NOT receive will message
	_, err := sub.waitForPacket(packet.PUBLISH, 500*time.Millisecond)
	if err == nil {
		t.Error("Should not have received will message on clean disconnect")
	}
}

func TestBrokerRetainedMessage(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	pub := connectClient(t, addr, "retained-pub", true)
	defer pub.close()

	// Publish retained message
	pub.send(&packet.PublishPacket{
		TopicName: "test/retained",
		Payload:   []byte("retained-data"),
		QoS:       0,
		Retain:    true,
	})
	time.Sleep(100 * time.Millisecond)

	// New subscriber should receive retained message
	sub := connectClient(t, addr, "retained-sub", true)
	defer sub.close()

	sub.send(&packet.SubscribePacket{
		PacketID: 1,
		Topics:   []string{"test/retained"},
		QoSs:     []byte{0},
	})
	sub.waitForPacket(packet.SUBACK, 2*time.Second)

	msg, err := sub.waitForPacket(packet.PUBLISH, 2*time.Second)
	if err != nil {
		t.Fatalf("Subscriber didn't receive retained message: %v", err)
	}

	pubPkt := msg.(*packet.PublishPacket)
	if string(pubPkt.Payload) != "retained-data" {
		t.Errorf("Retained payload = %q, want %q", pubPkt.Payload, "retained-data")
	}
}

func TestBrokerPingPong(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	tc := connectClient(t, addr, "ping-client", true)
	defer tc.close()

	tc.send(&packet.PingreqPacket{})

	resp, err := tc.waitForPacket(packet.PINGRESP, 2*time.Second)
	if err != nil {
		t.Fatalf("Didn't receive PINGRESP: %v", err)
	}
	if resp.Type() != packet.PINGRESP {
		t.Errorf("Expected PINGRESP, got %d", resp.Type())
	}
}

func TestBrokerWildcardSubscription(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	sub := connectClient(t, addr, "wildcard-sub", true)
	defer sub.close()

	sub.send(&packet.SubscribePacket{
		PacketID: 1,
		Topics:   []string{"sensor/+/temperature"},
		QoSs:     []byte{0},
	})
	sub.waitForPacket(packet.SUBACK, 2*time.Second)

	pub := connectClient(t, addr, "wildcard-pub", true)
	defer pub.close()

	// Should match
	pub.send(&packet.PublishPacket{
		TopicName: "sensor/room1/temperature",
		Payload:   []byte("25"),
		QoS:       0,
	})

	msg, err := sub.waitForPacket(packet.PUBLISH, 2*time.Second)
	if err != nil {
		t.Fatalf("Didn't receive message: %v", err)
	}
	if string(msg.(*packet.PublishPacket).Payload) != "25" {
		t.Errorf("Wrong payload")
	}
}

func TestBrokerUnsubscribe(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	sub := connectClient(t, addr, "unsub-client", true)
	defer sub.close()

	sub.send(&packet.SubscribePacket{
		PacketID: 1,
		Topics:   []string{"test/unsub"},
		QoSs:     []byte{0},
	})
	sub.waitForPacket(packet.SUBACK, 2*time.Second)

	sub.send(&packet.UnsubscribePacket{
		PacketID: 2,
		Topics:   []string{"test/unsub"},
	})
	sub.waitForPacket(packet.UNSUBACK, 2*time.Second)

	// Publish after unsubscribe - should not receive
	pub := connectClient(t, addr, "unsub-pub", true)
	defer pub.close()

	pub.send(&packet.PublishPacket{
		TopicName: "test/unsub",
		Payload:   []byte("should not receive"),
		QoS:       0,
	})
	time.Sleep(200 * time.Millisecond)

	_, err := sub.waitForPacket(packet.PUBLISH, 500*time.Millisecond)
	if err == nil {
		t.Error("Should not receive message after unsubscribe")
	}
}

func TestBrokerMultipleSubscribers(t *testing.T) {
	b, addr := setupBroker(t)
	defer b.Stop()

	// Create 3 subscribers
	subs := make([]*testClient, 3)
	for i := 0; i < 3; i++ {
		subs[i] = connectClient(t, addr, fmt.Sprintf("multi-sub-%d", i), true)
		defer subs[i].close()

		subs[i].send(&packet.SubscribePacket{
			PacketID: 1,
			Topics:   []string{"broadcast"},
			QoSs:     []byte{0},
		})
		subs[i].waitForPacket(packet.SUBACK, 2*time.Second)
	}

	pub := connectClient(t, addr, "multi-pub", true)
	defer pub.close()

	pub.send(&packet.PublishPacket{
		TopicName: "broadcast",
		Payload:   []byte("hello all"),
		QoS:       0,
	})

	// All subscribers should receive
	for i, sub := range subs {
		msg, err := sub.waitForPacket(packet.PUBLISH, 2*time.Second)
		if err != nil {
			t.Fatalf("Subscriber %d didn't receive: %v", i, err)
		}
		if string(msg.(*packet.PublishPacket).Payload) != "hello all" {
			t.Errorf("Subscriber %d: wrong payload", i)
		}
	}
}

// TestConnackPacketEncodeSpecific tests ConnackPacket encoding directly.
func TestConnackPacketEncodeSpecific(t *testing.T) {
	tests := []struct {
		name     string
		packet   *packet.ConnackPacket
		wantCode byte
	}{
		{"accepted", &packet.ConnackPacket{ReturnCode: packet.ConnAccepted}, 0},
		{"refused_protocol", &packet.ConnackPacket{ReturnCode: packet.ConnRefusedProtocol}, 1},
		{"refused_identifier", &packet.ConnackPacket{ReturnCode: packet.ConnRefusedIdentifier}, 2},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			data, err := tt.packet.Encode()
			if err != nil {
				t.Fatalf("Encode failed: %v", err)
			}

			decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
			if err != nil {
				t.Fatalf("ReadPacket failed: %v", err)
			}

			connack := decoded.(*packet.ConnackPacket)
			if connack.ReturnCode != tt.wantCode {
				t.Errorf("ReturnCode = %d, want %d", connack.ReturnCode, tt.wantCode)
			}
		})
	}
}
