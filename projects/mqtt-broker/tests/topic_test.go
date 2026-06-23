package tests

import (
	"sync"
	"testing"

	"github.com/user/mqtt-broker/internal/topic"
)

func TestExactMatch(t *testing.T) {
	m := topic.NewManager()
	received := false
	var mu sync.Mutex

	m.Subscribe("test/topic", &topic.Subscriber{
		ClientID: "client1",
		QoS:      0,
		Callback: func(msg *topic.Message) {
			mu.Lock()
			received = true
			mu.Unlock()
		},
	})

	subs := m.GetSubscribers("test/topic")
	if len(subs) != 1 {
		t.Fatalf("Expected 1 subscriber, got %d", len(subs))
	}

	mu.Lock()
	if received {
		t.Error("Callback should not have been called yet")
	}
	mu.Unlock()
}

func TestWildcardPlus(t *testing.T) {
	m := topic.NewManager()

	m.Subscribe("sensor/+/temperature", &topic.Subscriber{
		ClientID: "client1",
		QoS:      0,
	})

	tests := []struct {
		topic    string
		expected int
	}{
		{"sensor/room1/temperature", 1},
		{"sensor/room2/temperature", 1},
		{"sensor/room1/humidity", 0},
		{"sensor/room1/sub/temperature", 0},
	}

	for _, tt := range tests {
		subs := m.GetSubscribers(tt.topic)
		if len(subs) != tt.expected {
			t.Errorf("Topic %q: got %d subscribers, want %d", tt.topic, len(subs), tt.expected)
		}
	}
}

func TestWildcardHash(t *testing.T) {
	m := topic.NewManager()

	m.Subscribe("sensor/#", &topic.Subscriber{
		ClientID: "client1",
		QoS:      0,
	})

	tests := []struct {
		topic    string
		expected int
	}{
		{"sensor/temperature", 1},
		{"sensor/room1/temperature", 1},
		{"sensor/a/b/c/d", 1},
		{"other/topic", 0},
	}

	for _, tt := range tests {
		subs := m.GetSubscribers(tt.topic)
		if len(subs) != tt.expected {
			t.Errorf("Topic %q: got %d subscribers, want %d", tt.topic, len(subs), tt.expected)
		}
	}
}

func TestMultipleSubscribers(t *testing.T) {
	m := topic.NewManager()

	m.Subscribe("test/topic", &topic.Subscriber{ClientID: "client1", QoS: 0})
	m.Subscribe("test/topic", &topic.Subscriber{ClientID: "client2", QoS: 1})
	m.Subscribe("test/#", &topic.Subscriber{ClientID: "client3", QoS: 2})

	subs := m.GetSubscribers("test/topic")
	if len(subs) != 3 {
		t.Fatalf("Expected 3 subscribers, got %d", len(subs))
	}
}

func TestDuplicateSubscription(t *testing.T) {
	m := topic.NewManager()

	m.Subscribe("test/topic", &topic.Subscriber{ClientID: "client1", QoS: 0})
	m.Subscribe("test/topic", &topic.Subscriber{ClientID: "client1", QoS: 2})

	subs := m.GetSubscribers("test/topic")
	if len(subs) != 1 {
		t.Fatalf("Expected 1 subscriber (no duplicate), got %d", len(subs))
	}
	if subs[0].QoS != 2 {
		t.Errorf("QoS = %d, want 2 (updated)", subs[0].QoS)
	}
}

func TestUnsubscribe(t *testing.T) {
	m := topic.NewManager()

	m.Subscribe("test/topic", &topic.Subscriber{ClientID: "client1", QoS: 0})
	m.Subscribe("test/topic", &topic.Subscriber{ClientID: "client2", QoS: 0})

	m.Unsubscribe("test/topic", "client1")

	subs := m.GetSubscribers("test/topic")
	if len(subs) != 1 {
		t.Fatalf("Expected 1 subscriber, got %d", len(subs))
	}
	if subs[0].ClientID != "client2" {
		t.Errorf("ClientID = %q, want %q", subs[0].ClientID, "client2")
	}
}

func TestUnsubscribeAll(t *testing.T) {
	m := topic.NewManager()

	m.Subscribe("topic/a", &topic.Subscriber{ClientID: "client1", QoS: 0})
	m.Subscribe("topic/b", &topic.Subscriber{ClientID: "client1", QoS: 0})
	m.Subscribe("topic/a", &topic.Subscriber{ClientID: "client2", QoS: 0})

	m.UnsubscribeAll("client1")

	if len(m.GetSubscribers("topic/a")) != 1 {
		t.Error("Expected 1 subscriber in topic/a")
	}
	if len(m.GetSubscribers("topic/b")) != 0 {
		t.Error("Expected 0 subscribers in topic/b")
	}
}

func TestRetainedMessage(t *testing.T) {
	m := topic.NewManager()

	// Set retained message
	m.SetRetained("test/retained", &topic.Message{
		Topic:   "test/retained",
		Payload: []byte("retained-data"),
		QoS:     1,
		Retain:  true,
	})

	msg := m.GetRetained("test/retained")
	if msg == nil {
		t.Fatal("Expected retained message")
	}
	if string(msg.Payload) != "retained-data" {
		t.Errorf("Payload = %q, want %q", msg.Payload, "retained-data")
	}

	// Delete retained message by sending empty payload
	m.SetRetained("test/retained", &topic.Message{
		Topic:   "test/retained",
		Payload: []byte{},
	})

	msg = m.GetRetained("test/retained")
	if msg != nil {
		t.Error("Expected no retained message after clear")
	}
}

func TestRetainedMessageWildcard(t *testing.T) {
	m := topic.NewManager()

	m.SetRetained("sensor/temp", &topic.Message{
		Topic:   "sensor/temp",
		Payload: []byte("25"),
	})
	m.SetRetained("sensor/humidity", &topic.Message{
		Topic:   "sensor/humidity",
		Payload: []byte("60"),
	})

	msgs := m.GetRetainedForPattern("sensor/+")
	if len(msgs) != 2 {
		t.Errorf("Expected 2 retained messages, got %d", len(msgs))
	}
}

func TestComplexWildcardPatterns(t *testing.T) {
	m := topic.NewManager()

	m.Subscribe("$SYS/#", &topic.Subscriber{ClientID: "admin", QoS: 0})

	// $SYS topics should match
	subs := m.GetSubscribers("$SYS/broker/clients")
	if len(subs) != 1 {
		t.Errorf("$SYS/# should match $SYS/broker/clients, got %d subs", len(subs))
	}

	// Regular topics should not match $SYS
	subs = m.GetSubscribers("regular/topic")
	if len(subs) != 0 {
		t.Error("$SYS/# should not match regular/topic")
	}
}
