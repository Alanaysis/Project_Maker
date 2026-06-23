// Package topic implements MQTT topic subscription matching with wildcard support.
// MQTT wildcards:
//   - '+' matches one topic level
//   - '#' matches any number of topic levels (must be last)
package topic

import (
	"strings"
	"sync"
)

// Message represents a message published to a topic.
type Message struct {
	Topic   string
	Payload []byte
	QoS     byte
	Retain  bool
}

// Subscriber represents a subscribed client.
type Subscriber struct {
	ClientID string
	QoS      byte
	Callback func(msg *Message)
}

// Manager manages topic subscriptions and message routing.
type Manager struct {
	mu          sync.RWMutex
	subscribers map[string][]*Subscriber // topic -> subscribers
	retained    map[string]*Message      // topic -> retained message
}

// NewManager creates a new topic manager.
func NewManager() *Manager {
	return &Manager{
		subscribers: make(map[string][]*Subscriber),
		retained:    make(map[string]*Message),
	}
}

// Subscribe adds a subscriber to a topic pattern.
func (m *Manager) Subscribe(topic string, sub *Subscriber) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Avoid duplicate subscriptions
	subs := m.subscribers[topic]
	for _, existing := range subs {
		if existing.ClientID == sub.ClientID {
			existing.QoS = sub.QoS
			existing.Callback = sub.Callback
			return
		}
	}
	m.subscribers[topic] = append(subs, sub)
}

// Unsubscribe removes a subscriber from a topic.
func (m *Manager) Unsubscribe(topic string, clientID string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	subs := m.subscribers[topic]
	for i, sub := range subs {
		if sub.ClientID == clientID {
			m.subscribers[topic] = append(subs[:i], subs[i+1:]...)
			return
		}
	}
}

// UnsubscribeAll removes a subscriber from all topics.
func (m *Manager) UnsubscribeAll(clientID string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	for topic, subs := range m.subscribers {
		for i, sub := range subs {
			if sub.ClientID == clientID {
				m.subscribers[topic] = append(subs[:i], subs[i+1:]...)
				break
			}
		}
	}
}

// GetSubscribers returns all subscribers matching a topic.
// Supports '+' and '#' wildcards.
func (m *Manager) GetSubscribers(topic string) []*Subscriber {
	m.mu.RLock()
	defer m.mu.RUnlock()

	var matched []*Subscriber
	seen := make(map[string]bool)

	for pattern, subs := range m.subscribers {
		if matchTopic(pattern, topic) {
			for _, sub := range subs {
				if !seen[sub.ClientID] {
					matched = append(matched, sub)
					seen[sub.ClientID] = true
				}
			}
		}
	}

	return matched
}

// SetRetained stores a retained message for a topic.
// If payload is empty, the retained message is removed.
func (m *Manager) SetRetained(topic string, msg *Message) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if len(msg.Payload) == 0 {
		delete(m.retained, topic)
	} else {
		m.retained[topic] = msg
	}
}

// GetRetained returns the retained message for a topic, or nil if none exists.
func (m *Manager) GetRetained(topic string) *Message {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.retained[topic]
}

// GetRetainedForPattern returns retained messages matching a subscription pattern.
func (m *Manager) GetRetainedForPattern(pattern string) []*Message {
	m.mu.RLock()
	defer m.mu.RUnlock()

	var messages []*Message
	for topic, msg := range m.retained {
		if matchTopic(pattern, topic) {
			messages = append(messages, msg)
		}
	}
	return messages
}

// matchTopic checks if a subscription pattern matches a publish topic.
// MQTT topic matching rules:
//   - Exact match: "a/b/c" matches "a/b/c"
//   - '+': "a/+/c" matches "a/b/c", "a/x/c"
//   - '#': "a/#" matches "a/b", "a/b/c", "a"
func matchTopic(pattern, topic string) bool {
	// Fast path: exact match
	if pattern == topic {
		return true
	}

	patternParts := strings.Split(pattern, "/")
	topicParts := strings.Split(topic, "/")

	for i, part := range patternParts {
		if part == "#" {
			return true // '#' matches everything from here on
		}
		if i >= len(topicParts) {
			return false
		}
		if part != "+" && part != topicParts[i] {
			return false
		}
	}

	return len(patternParts) == len(topicParts)
}
