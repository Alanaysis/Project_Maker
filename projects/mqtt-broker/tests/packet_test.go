package tests

import (
	"bytes"
	"testing"

	"github.com/user/mqtt-broker/internal/packet"
)

func TestConnectPacketEncodeDecode(t *testing.T) {
	original := &packet.ConnectPacket{
		ProtocolName:  "MQTT",
		ProtocolLevel: 4,
		CleanSession:  true,
		KeepAlive:     60,
		ClientID:      "test-client",
	}

	data, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	connect, ok := decoded.(*packet.ConnectPacket)
	if !ok {
		t.Fatal("Expected ConnectPacket")
	}

	if connect.ProtocolName != "MQTT" {
		t.Errorf("ProtocolName = %q, want %q", connect.ProtocolName, "MQTT")
	}
	if connect.ProtocolLevel != 4 {
		t.Errorf("ProtocolLevel = %d, want %d", connect.ProtocolLevel, 4)
	}
	if !connect.CleanSession {
		t.Error("CleanSession should be true")
	}
	if connect.KeepAlive != 60 {
		t.Errorf("KeepAlive = %d, want %d", connect.KeepAlive, 60)
	}
	if connect.ClientID != "test-client" {
		t.Errorf("ClientID = %q, want %q", connect.ClientID, "test-client")
	}
}

func TestConnectPacketWithWill(t *testing.T) {
	original := &packet.ConnectPacket{
		ProtocolName:  "MQTT",
		ProtocolLevel: 4,
		CleanSession:  true,
		KeepAlive:     30,
		ClientID:      "will-client",
		WillFlag:      true,
		WillTopic:     "test/will",
		WillMessage:   []byte("offline"),
		WillQoS:       1,
		WillRetain:    true,
	}

	data, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	connect := decoded.(*packet.ConnectPacket)

	if !connect.WillFlag {
		t.Error("WillFlag should be true")
	}
	if connect.WillTopic != "test/will" {
		t.Errorf("WillTopic = %q, want %q", connect.WillTopic, "test/will")
	}
	if string(connect.WillMessage) != "offline" {
		t.Errorf("WillMessage = %q, want %q", connect.WillMessage, "offline")
	}
	if connect.WillQoS != 1 {
		t.Errorf("WillQoS = %d, want %d", connect.WillQoS, 1)
	}
	if !connect.WillRetain {
		t.Error("WillRetain should be true")
	}
}

func TestConnackPacketEncodeDecode(t *testing.T) {
	original := &packet.ConnackPacket{
		SessionPresent: true,
		ReturnCode:     packet.ConnAccepted,
	}

	data, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	connack, ok := decoded.(*packet.ConnackPacket)
	if !ok {
		t.Fatal("Expected ConnackPacket")
	}

	if connack.ReturnCode != packet.ConnAccepted {
		t.Errorf("ReturnCode = %d, want %d", connack.ReturnCode, packet.ConnAccepted)
	}
}

func TestPublishPacketQoS0(t *testing.T) {
	original := &packet.PublishPacket{
		TopicName: "test/topic",
		Payload:   []byte("hello"),
		QoS:       0,
	}

	data, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	pub, ok := decoded.(*packet.PublishPacket)
	if !ok {
		t.Fatal("Expected PublishPacket")
	}

	if pub.TopicName != "test/topic" {
		t.Errorf("TopicName = %q, want %q", pub.TopicName, "test/topic")
	}
	if string(pub.Payload) != "hello" {
		t.Errorf("Payload = %q, want %q", pub.Payload, "hello")
	}
	if pub.QoS != 0 {
		t.Errorf("QoS = %d, want %d", pub.QoS, 0)
	}
}

func TestPublishPacketQoS1(t *testing.T) {
	original := &packet.PublishPacket{
		TopicName: "test/topic",
		Payload:   []byte("hello"),
		QoS:       1,
		PacketID:  42,
	}

	data, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	pub := decoded.(*packet.PublishPacket)
	if pub.QoS != 1 {
		t.Errorf("QoS = %d, want %d", pub.QoS, 1)
	}
	if pub.PacketID != 42 {
		t.Errorf("PacketID = %d, want %d", pub.PacketID, 42)
	}
}

func TestPublishPacketQoS2(t *testing.T) {
	original := &packet.PublishPacket{
		TopicName: "test/exactly",
		Payload:   []byte("once"),
		QoS:       2,
		PacketID:  100,
	}

	data, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	pub := decoded.(*packet.PublishPacket)
	if pub.QoS != 2 {
		t.Errorf("QoS = %d, want %d", pub.QoS, 2)
	}
	if pub.PacketID != 100 {
		t.Errorf("PacketID = %d, want %d", pub.PacketID, 100)
	}
}

func TestPubackPacket(t *testing.T) {
	original := &packet.PubackPacket{PacketID: 123}

	data, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	puback, ok := decoded.(*packet.PubackPacket)
	if !ok {
		t.Fatal("Expected PubackPacket")
	}
	if puback.PacketID != 123 {
		t.Errorf("PacketID = %d, want %d", puback.PacketID, 123)
	}
}

func TestSubscribePacket(t *testing.T) {
	original := &packet.SubscribePacket{
		PacketID: 10,
		Topics:   []string{"test/a", "test/b"},
		QoSs:     []byte{0, 1},
	}

	data, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	sub, ok := decoded.(*packet.SubscribePacket)
	if !ok {
		t.Fatal("Expected SubscribePacket")
	}

	if sub.PacketID != 10 {
		t.Errorf("PacketID = %d, want %d", sub.PacketID, 10)
	}
	if len(sub.Topics) != 2 {
		t.Fatalf("Topics count = %d, want 2", len(sub.Topics))
	}
	if sub.Topics[0] != "test/a" || sub.Topics[1] != "test/b" {
		t.Errorf("Topics = %v, want [test/a test/b]", sub.Topics)
	}
}

func TestPingreqPingresp(t *testing.T) {
	pingreq := &packet.PingreqPacket{}
	data, err := pingreq.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	if _, ok := decoded.(*packet.PingreqPacket); !ok {
		t.Fatal("Expected PingreqPacket")
	}

	pingresp := &packet.PingrespPacket{}
	data, err = pingresp.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err = packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	if _, ok := decoded.(*packet.PingrespPacket); !ok {
		t.Fatal("Expected PingrespPacket")
	}
}

func TestDisconnectPacket(t *testing.T) {
	original := &packet.DisconnectPacket{}
	data, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	if _, ok := decoded.(*packet.DisconnectPacket); !ok {
		t.Fatal("Expected DisconnectPacket")
	}
}

func TestPubrelPacket(t *testing.T) {
	original := &packet.PubrelPacket{PacketID: 55}
	data, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	decoded, _, err := packet.ReadPacket(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("ReadPacket failed: %v", err)
	}

	pubrel, ok := decoded.(*packet.PubrelPacket)
	if !ok {
		t.Fatal("Expected PubrelPacket")
	}
	if pubrel.PacketID != 55 {
		t.Errorf("PacketID = %d, want %d", pubrel.PacketID, 55)
	}
}
