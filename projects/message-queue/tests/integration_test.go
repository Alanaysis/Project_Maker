// Package tests provides integration tests for the message queue system.
// These tests exercise the full publish-subscribe pipeline across multiple
// components: API, broker, producer, consumer, and persistence.
package tests

import (
	"encoding/json"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/example/message-queue/internal/consumer"
	"github.com/example/message-queue/internal/persistence"
	"github.com/example/message-queue/internal/producer"
	"github.com/example/message-queue/internal/protocol"
	"github.com/example/message-queue/internal/queue"
	"github.com/example/message-queue/pkg/api"
)

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

func setupMemoryBroker(t *testing.T) (*queue.Broker, func()) {
	t.Helper()
	broker := queue.NewBroker(queue.DefaultConfig(), persistence.NewMemStore())
	return broker, func() { broker.Close() }
}

// ---------------------------------------------------------------------------
// 1. Producer -> Broker -> Consumer pipeline
// ---------------------------------------------------------------------------

func TestIntegration_ProducerToConsumer(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	broker.CreateTopic("orders")

	var received []string
	var mu sync.Mutex

	handler := func(msg *protocol.Message) error {
		mu.Lock()
		received = append(received, string(msg.Payload))
		mu.Unlock()
		return nil
	}

	cons := consumer.New("worker-1", broker, handler)
	defer cons.Close()

	if err := cons.Subscribe("orders"); err != nil {
		t.Fatalf("subscribe: %v", err)
	}

	prod := producer.New(broker)

	// Publish several messages.
	for i := 0; i < 10; i++ {
		payload := fmt.Sprintf("order-%d", i)
		if _, err := prod.PublishString("orders", payload); err != nil {
			t.Fatalf("publish %d: %v", i, err)
		}
	}

	// Give the consumer goroutine time to process.
	time.Sleep(500 * time.Millisecond)

	mu.Lock()
	defer mu.Unlock()

	if len(received) != 10 {
		t.Errorf("expected 10 messages received, got %d", len(received))
	}
	// Verify ordering is preserved.
	for i, r := range received {
		expected := fmt.Sprintf("order-%d", i)
		if r != expected {
			t.Errorf("message[%d] = %q, want %q", i, r, expected)
		}
	}
}

// ---------------------------------------------------------------------------
// 2. Fan-out: multiple consumers on the same topic
// ---------------------------------------------------------------------------

func TestIntegration_FanOut(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	broker.CreateTopic("events")

	var c1Count, c2Count int32

	makeHandler := func(counter *int32) consumer.Handler {
		return func(msg *protocol.Message) error {
			atomic.AddInt32(counter, 1)
			return nil
		}
	}

	cons1 := consumer.New("c1", broker, makeHandler(&c1Count))
	cons2 := consumer.New("c2", broker, makeHandler(&c2Count))
	defer cons1.Close()
	defer cons2.Close()

	cons1.Subscribe("events")
	cons2.Subscribe("events")

	prod := producer.New(broker)
	for i := 0; i < 5; i++ {
		prod.PublishString("events", "event")
	}

	time.Sleep(500 * time.Millisecond)

	if atomic.LoadInt32(&c1Count) != 5 {
		t.Errorf("c1 expected 5, got %d", atomic.LoadInt32(&c1Count))
	}
	if atomic.LoadInt32(&c2Count) != 5 {
		t.Errorf("c2 expected 5, got %d", atomic.LoadInt32(&c2Count))
	}
}

// ---------------------------------------------------------------------------
// 3. Persistence: messages survive broker restart
// ---------------------------------------------------------------------------

func TestIntegration_PersistenceRecovery(t *testing.T) {
	dir := t.TempDir()

	cfg := api.Config{
		TopicCapacity:     1000,
		SubscriberBufSize: 64,
		DataDir:           dir,
	}

	// Phase 1: publish messages and close.
	mq1, err := api.New(cfg)
	if err != nil {
		t.Fatalf("create mq1: %v", err)
	}

	p := mq1.NewProducer()
	msg1, _ := p.PublishString("reliable", "first")
	msg2, _ := p.PublishString("reliable", "second")
	msg3, _ := p.PublishString("reliable", "third")

	// Acknowledge one message before closing.
	topic1, _ := mq1.GetTopic("reliable")
	_ = topic1 // suppress unused warning
	// Ack via broker internals through the api is not directly exposed,
	// so we use the persistence store directly.
	store, _ := persistence.NewFileStore(dir)
	store.UpdateMessage(msg1)
	msg1.MarkAcknowledged()
	store.UpdateMessage(msg1)

	mq1.Close()
	store.Close()

	// Phase 2: reopen and verify recovery.
	mq2, err := api.New(cfg)
	if err != nil {
		t.Fatalf("create mq2: %v", err)
	}
	defer mq2.Close()

	topic2, err := mq2.GetTopic("reliable")
	if err != nil {
		t.Fatalf("get topic: %v", err)
	}

	msgs := topic2.Messages()
	// Only unacknowledged messages should be replayed.
	if len(msgs) != 2 {
		t.Fatalf("expected 2 recovered messages, got %d", len(msgs))
	}

	ids := map[string]bool{}
	for _, m := range msgs {
		ids[m.ID] = true
	}
	if !ids[msg2.ID] {
		t.Error("expected msg2 to be recovered")
	}
	if !ids[msg3.ID] {
		t.Error("expected msg3 to be recovered")
	}
	if ids[msg1.ID] {
		t.Error("msg1 was acknowledged and should not be recovered")
	}
}

// ---------------------------------------------------------------------------
// 4. Auto-acknowledge on successful handler
// ---------------------------------------------------------------------------

func TestIntegration_AutoAcknowledge(t *testing.T) {
	store := persistence.NewMemStore()
	broker := queue.NewBroker(queue.DefaultConfig(), store)
	defer broker.Close()

	broker.CreateTopic("ack-test")

	var processed int32
	handler := func(msg *protocol.Message) error {
		atomic.AddInt32(&processed, 1)
		return nil
	}

	cons := consumer.New("acker", broker, handler)
	defer cons.Close()
	cons.Subscribe("ack-test")

	prod := producer.New(broker)
	prod.PublishString("ack-test", "data")

	time.Sleep(500 * time.Millisecond)

	if atomic.LoadInt32(&processed) != 1 {
		t.Fatalf("expected 1 processed, got %d", atomic.LoadInt32(&processed))
	}

	// Verify the message was acknowledged in the store.
	all, _ := store.LoadAll()
	if len(all) != 1 {
		t.Fatalf("expected 1 stored message, got %d", len(all))
	}
	if all[0].Status != protocol.StatusAcknowledged {
		t.Errorf("expected acknowledged, got %v", all[0].Status)
	}
}

// ---------------------------------------------------------------------------
// 5. Handler failure: message stays unacknowledged
// ---------------------------------------------------------------------------

func TestIntegration_HandlerFailureNoAck(t *testing.T) {
	store := persistence.NewMemStore()
	broker := queue.NewBroker(queue.DefaultConfig(), store)
	defer broker.Close()

	broker.CreateTopic("fail-test")

	// Handler that always fails.
	handler := func(msg *protocol.Message) error {
		return fmt.Errorf("processing error")
	}

	cons := consumer.New("failer", broker, handler)
	defer cons.Close()
	cons.Subscribe("fail-test")

	prod := producer.New(broker)
	prod.PublishString("fail-test", "bad-data")

	// Give time for the handler to run (and fail).
	time.Sleep(500 * time.Millisecond)

	// Message should remain unacknowledged.
	all, _ := store.LoadAll()
	if len(all) != 1 {
		t.Fatalf("expected 1 stored message, got %d", len(all))
	}
	if all[0].Status == protocol.StatusAcknowledged {
		t.Error("failed handler should not cause acknowledgement")
	}
}

// ---------------------------------------------------------------------------
// 6. Topic capacity enforcement via broker
// ---------------------------------------------------------------------------

func TestIntegration_TopicCapacity(t *testing.T) {
	cfg := queue.BrokerConfig{
		TopicCapacity:     3,
		SubscriberBufSize: 16,
	}
	broker := queue.NewBroker(cfg, persistence.NewMemStore())
	defer broker.Close()

	prod := producer.New(broker)

	for i := 0; i < 3; i++ {
		if _, err := prod.PublishString("limited", fmt.Sprintf("msg-%d", i)); err != nil {
			t.Fatalf("publish %d: %v", i, err)
		}
	}

	// 4th message should fail.
	_, err := prod.PublishString("limited", "overflow")
	if err == nil {
		t.Error("expected error when exceeding topic capacity")
	}
}

// ---------------------------------------------------------------------------
// 7. Multiple topics isolation
// ---------------------------------------------------------------------------

func TestIntegration_MultipleTopicsIsolation(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	broker.CreateTopic("topic-a")
	broker.CreateTopic("topic-b")

	var aCount, bCount int32

	handlerA := func(msg *protocol.Message) error {
		atomic.AddInt32(&aCount, 1)
		return nil
	}
	handlerB := func(msg *protocol.Message) error {
		atomic.AddInt32(&bCount, 1)
		return nil
	}

	consA := consumer.New("ca", broker, handlerA)
	consB := consumer.New("cb", broker, handlerB)
	defer consA.Close()
	defer consB.Close()

	consA.Subscribe("topic-a")
	consB.Subscribe("topic-b")

	prod := producer.New(broker)

	// Publish only to topic-a.
	for i := 0; i < 3; i++ {
		prod.PublishString("topic-a", "a-msg")
	}

	// Publish only to topic-b.
	for i := 0; i < 5; i++ {
		prod.PublishString("topic-b", "b-msg")
	}

	time.Sleep(500 * time.Millisecond)

	if atomic.LoadInt32(&aCount) != 3 {
		t.Errorf("topic-a: expected 3, got %d", atomic.LoadInt32(&aCount))
	}
	if atomic.LoadInt32(&bCount) != 5 {
		t.Errorf("topic-b: expected 5, got %d", atomic.LoadInt32(&bCount))
	}
}

// ---------------------------------------------------------------------------
// 8. Concurrent publishing safety
// ---------------------------------------------------------------------------

func TestIntegration_ConcurrentPublish(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	broker.CreateTopic("concurrent")

	prod := producer.New(broker)

	var wg sync.WaitGroup
	numGoroutines := 20
	messagesPerGoroutine := 50

	wg.Add(numGoroutines)
	for g := 0; g < numGoroutines; g++ {
		go func(id int) {
			defer wg.Done()
			for i := 0; i < messagesPerGoroutine; i++ {
				payload := fmt.Sprintf("g%d-m%d", id, i)
				if _, err := prod.PublishString("concurrent", payload); err != nil {
					t.Errorf("goroutine %d msg %d: %v", id, i, err)
				}
			}
		}(g)
	}
	wg.Wait()

	topic, _ := broker.GetTopic("concurrent")
	msgs := topic.Messages()

	expected := numGoroutines * messagesPerGoroutine
	if len(msgs) != expected {
		t.Errorf("expected %d messages, got %d", expected, len(msgs))
	}
}

// ---------------------------------------------------------------------------
// 9. Message JSON serialization round-trip
// ---------------------------------------------------------------------------

func TestIntegration_MessageJSONRoundTrip(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	broker.CreateTopic("json-test")

	prod := producer.New(broker)
	msg, _ := prod.PublishString("json-test", `{"action":"buy","qty":10}`)

	// Marshal the message.
	data, err := json.Marshal(msg)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	// Unmarshal into a fresh message.
	var parsed protocol.Message
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if parsed.ID != msg.ID {
		t.Errorf("ID mismatch: %s vs %s", parsed.ID, msg.ID)
	}
	if parsed.Topic != msg.Topic {
		t.Errorf("Topic mismatch: %s vs %s", parsed.Topic, msg.Topic)
	}
	if string(parsed.Payload) != string(msg.Payload) {
		t.Errorf("Payload mismatch")
	}
	if parsed.Status != msg.Status {
		t.Errorf("Status mismatch: %v vs %v", parsed.Status, msg.Status)
	}
}

// ---------------------------------------------------------------------------
// 10. FileStore full lifecycle
// ---------------------------------------------------------------------------

func TestIntegration_FileStoreLifecycle(t *testing.T) {
	dir := t.TempDir()

	store, err := persistence.NewFileStore(dir)
	if err != nil {
		t.Fatalf("new file store: %v", err)
	}

	// Save several messages across topics.
	msgs := []*protocol.Message{
		protocol.NewMessage("logs", []byte("log-1")),
		protocol.NewMessage("logs", []byte("log-2")),
		protocol.NewMessage("metrics", []byte("cpu-90")),
	}

	for _, m := range msgs {
		if err := store.SaveMessage(m); err != nil {
			t.Fatalf("save: %v", err)
		}
	}

	// LoadAll.
	all, err := store.LoadAll()
	if err != nil {
		t.Fatalf("load all: %v", err)
	}
	if len(all) != 3 {
		t.Errorf("expected 3, got %d", len(all))
	}

	// LoadMessage by ID.
	loaded, err := store.LoadMessage(msgs[0].ID)
	if err != nil {
		t.Fatalf("load by id: %v", err)
	}
	if string(loaded.Payload) != "log-1" {
		t.Errorf("expected 'log-1', got %q", string(loaded.Payload))
	}

	// Update (ack).
	msgs[0].MarkAcknowledged()
	if err := store.UpdateMessage(msgs[0]); err != nil {
		t.Fatalf("update: %v", err)
	}

	loaded, _ = store.LoadMessage(msgs[0].ID)
	if loaded.Status != protocol.StatusAcknowledged {
		t.Errorf("expected acknowledged, got %v", loaded.Status)
	}

	// Delete.
	if err := store.DeleteMessage(msgs[2].ID); err != nil {
		t.Fatalf("delete: %v", err)
	}

	if _, err := store.LoadMessage(msgs[2].ID); err != protocol.ErrMessageNotFound {
		t.Errorf("expected ErrMessageNotFound, got %v", err)
	}

	// Close.
	if err := store.Close(); err != nil {
		t.Fatalf("close: %v", err)
	}
}

// ---------------------------------------------------------------------------
// 11. Broker auto-creates topic on publish
// ---------------------------------------------------------------------------

func TestIntegration_AutoCreateTopic(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	prod := producer.New(broker)

	// Publish without creating topic first.
	msg, err := prod.PublishString("auto-created", "hello")
	if err != nil {
		t.Fatalf("publish: %v", err)
	}
	if msg.Topic != "auto-created" {
		t.Errorf("expected topic 'auto-created', got %q", msg.Topic)
	}

	// Verify topic exists.
	topics := broker.Topics()
	found := false
	for _, name := range topics {
		if name == "auto-created" {
			found = true
		}
	}
	if !found {
		t.Error("expected 'auto-created' to appear in topics list")
	}
}

// ---------------------------------------------------------------------------
// 12. Consumer unsubscribe stops message delivery
// ---------------------------------------------------------------------------

func TestIntegration_UnsubscribeStopsDelivery(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	broker.CreateTopic("stop-test")

	var count int32
	handler := func(msg *protocol.Message) error {
		atomic.AddInt32(&count, 1)
		return nil
	}

	cons := consumer.New("c1", broker, handler)
	cons.Subscribe("stop-test")

	prod := producer.New(broker)
	prod.PublishString("stop-test", "before")

	time.Sleep(300 * time.Millisecond)

	// Unsubscribe.
	cons.Unsubscribe("stop-test")

	// Publish more messages -- these should not be delivered.
	prod.PublishString("stop-test", "after1")
	prod.PublishString("stop-test", "after2")

	time.Sleep(300 * time.Millisecond)

	// Count should be 1 (only "before" was delivered).
	if atomic.LoadInt32(&count) != 1 {
		t.Errorf("expected 1 message received, got %d", atomic.LoadInt32(&count))
	}

	cons.Close()
}

// ---------------------------------------------------------------------------
// 13. API facade: create queue with memory store
// ---------------------------------------------------------------------------

func TestIntegration_APIFacadeMemory(t *testing.T) {
	cfg := api.Config{
		TopicCapacity:     100,
		SubscriberBufSize: 32,
	}

	mq, err := api.New(cfg)
	if err != nil {
		t.Fatalf("create mq: %v", err)
	}
	defer mq.Close()

	mq.CreateTopic("facade-test")

	p := mq.NewProducer()
	p.PublishString("facade-test", "via-api")

	topic, _ := mq.GetTopic("facade-test")
	msgs := topic.Messages()
	if len(msgs) != 1 {
		t.Errorf("expected 1, got %d", len(msgs))
	}
}

// ---------------------------------------------------------------------------
// 14. API facade: create queue with file store
// ---------------------------------------------------------------------------

func TestIntegration_APIFacadeFile(t *testing.T) {
	dir := t.TempDir()

	cfg := api.Config{
		TopicCapacity:     100,
		SubscriberBufSize: 32,
		DataDir:           dir,
	}

	mq, err := api.New(cfg)
	if err != nil {
		t.Fatalf("create mq: %v", err)
	}
	defer mq.Close()

	mq.CreateTopic("file-test")

	p := mq.NewProducer()
	p.PublishString("file-test", "persisted")

	mq.Close()

	// Reopen.
	mq2, err := api.New(cfg)
	if err != nil {
		t.Fatalf("reopen: %v", err)
	}
	defer mq2.Close()

	topic, err := mq2.GetTopic("file-test")
	if err != nil {
		t.Fatalf("get topic: %v", err)
	}
	msgs := topic.Messages()
	if len(msgs) != 1 {
		t.Errorf("expected 1 recovered, got %d", len(msgs))
	}
	if string(msgs[0].Payload) != "persisted" {
		t.Errorf("expected 'persisted', got %q", string(msgs[0].Payload))
	}
}

// ---------------------------------------------------------------------------
// 15. Concurrent subscribe/unsubscribe safety
// ---------------------------------------------------------------------------

func TestIntegration_ConcurrentSubscribeUnsubscribe(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	broker.CreateTopic("race-test")

	prod := producer.New(broker)

	var wg sync.WaitGroup
	numConsumers := 10

	wg.Add(numConsumers)
	for i := 0; i < numConsumers; i++ {
		go func(id int) {
			defer wg.Done()
			cons := consumer.New(fmt.Sprintf("c%d", id), broker, func(msg *protocol.Message) error {
				return nil
			})
			topicName := fmt.Sprintf("race-topic-%d", id)
			broker.CreateTopic(topicName)
			cons.Subscribe(topicName)
			prod.PublishString(topicName, "data")
			time.Sleep(50 * time.Millisecond)
			cons.Unsubscribe(topicName)
			cons.Close()
		}(i)
	}
	wg.Wait()

	// No panics or deadlocks means success.
}

// ---------------------------------------------------------------------------
// 16. MemStore delete nonexistent message
// ---------------------------------------------------------------------------

func TestIntegration_MemStoreDeleteNonexistent(t *testing.T) {
	store := persistence.NewMemStore()
	err := store.DeleteMessage("no-such-id")
	if err != protocol.ErrMessageNotFound {
		t.Errorf("expected ErrMessageNotFound, got %v", err)
	}
}

// ---------------------------------------------------------------------------
// 17. FileStore delete nonexistent message
// ---------------------------------------------------------------------------

func TestIntegration_FileStoreDeleteNonexistent(t *testing.T) {
	dir := t.TempDir()
	store, _ := persistence.NewFileStore(dir)
	err := store.DeleteMessage("no-such-id")
	if err != protocol.ErrMessageNotFound {
		t.Errorf("expected ErrMessageNotFound, got %v", err)
	}
}

// ---------------------------------------------------------------------------
// 18. Broker: publish to nonexistent topic without auto-create should work
//     (broker.Publish always auto-creates)
// ---------------------------------------------------------------------------

func TestIntegration_BrokerPublishAutoCreates(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	// Publish directly without CreateTopic -- broker auto-creates.
	msg, err := broker.Publish("implicit", []byte("auto"))
	if err != nil {
		t.Fatalf("publish: %v", err)
	}
	if msg.Topic != "implicit" {
		t.Errorf("expected 'implicit', got %q", msg.Topic)
	}

	topic, err := broker.GetTopic("implicit")
	if err != nil {
		t.Fatalf("get topic: %v", err)
	}
	if len(topic.Messages()) != 1 {
		t.Errorf("expected 1 message, got %d", len(topic.Messages()))
	}
}

// ---------------------------------------------------------------------------
// 19. Acknowledge nonexistent message
// ---------------------------------------------------------------------------

func TestIntegration_AcknowledgeNonexistent(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	broker.CreateTopic("ack-miss")

	err := broker.Acknowledge("ack-miss", "no-such-id")
	if err != protocol.ErrMessageNotFound {
		t.Errorf("expected ErrMessageNotFound, got %v", err)
	}
}

// ---------------------------------------------------------------------------
// 20. Subscribe to nonexistent topic
// ---------------------------------------------------------------------------

func TestIntegration_SubscribeNonexistentTopic(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	_, err := broker.Subscribe("ghost", "c1")
	if err != protocol.ErrTopicNotFound {
		t.Errorf("expected ErrTopicNotFound, got %v", err)
	}
}

// ---------------------------------------------------------------------------
// 21. Large payload handling
// ---------------------------------------------------------------------------

func TestIntegration_LargePayload(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	broker.CreateTopic("large")

	// 1 MB payload.
	payload := make([]byte, 1024*1024)
	for i := range payload {
		payload[i] = byte(i % 256)
	}

	msg, err := broker.Publish("large", payload)
	if err != nil {
		t.Fatalf("publish large payload: %v", err)
	}
	if len(msg.Payload) != len(payload) {
		t.Errorf("payload length mismatch: %d vs %d", len(msg.Payload), len(payload))
	}

	topic, _ := broker.GetTopic("large")
	msgs := topic.Messages()
	if len(msgs) != 1 {
		t.Fatalf("expected 1 message, got %d", len(msgs))
	}
	if len(msgs[0].Payload) != len(payload) {
		t.Errorf("stored payload length mismatch")
	}
}

// ---------------------------------------------------------------------------
// 22. API TopicInfo accuracy
// ---------------------------------------------------------------------------

func TestIntegration_TopicInfoAccuracy(t *testing.T) {
	cfg := api.DefaultConfig()
	mq, _ := api.New(cfg)
	defer mq.Close()

	mq.CreateTopic("info-check")

	p := mq.NewProducer()
	p.PublishString("info-check", "a")
	p.PublishString("info-check", "b")
	p.PublishString("info-check", "c")

	msgs, subs, err := mq.TopicInfo("info-check")
	if err != nil {
		t.Fatalf("topic info: %v", err)
	}
	if msgs != 3 {
		t.Errorf("expected 3 messages, got %d", msgs)
	}
	if subs != 0 {
		t.Errorf("expected 0 subscribers, got %d", subs)
	}

	// Add a consumer and re-check.
	cons := mq.NewConsumer("info-c", func(msg *protocol.Message) error { return nil })
	cons.Subscribe("info-check")
	defer cons.Close()

	_, subs, _ = mq.TopicInfo("info-check")
	if subs != 1 {
		t.Errorf("expected 1 subscriber, got %d", subs)
	}
}

// ---------------------------------------------------------------------------
// 23. Message status string representation
// ---------------------------------------------------------------------------

func TestIntegration_MessageStatusString(t *testing.T) {
	tests := []struct {
		status protocol.MessageStatus
		want   string
	}{
		{protocol.StatusPending, "pending"},
		{protocol.StatusDelivered, "delivered"},
		{protocol.StatusAcknowledged, "acknowledged"},
		{protocol.MessageStatus(999), "unknown"},
	}

	for _, tc := range tests {
		if got := tc.status.String(); got != tc.want {
			t.Errorf("Status(%d).String() = %q, want %q", tc.status, got, tc.want)
		}
	}
}

// ---------------------------------------------------------------------------
// 24. Multiple topics, same producer
// ---------------------------------------------------------------------------

func TestIntegration_SameProducerMultipleTopics(t *testing.T) {
	broker, cleanup := setupMemoryBroker(t)
	defer cleanup()

	prod := producer.New(broker)

	prod.PublishString("topic-x", "x1")
	prod.PublishString("topic-y", "y1")
	prod.PublishString("topic-z", "z1")

	topics := broker.Topics()
	if len(topics) != 3 {
		t.Errorf("expected 3 topics, got %d", len(topics))
	}

	for _, name := range []string{"topic-x", "topic-y", "topic-z"} {
		topic, err := broker.GetTopic(name)
		if err != nil {
			t.Fatalf("get %s: %v", name, err)
		}
		if len(topic.Messages()) != 1 {
			t.Errorf("%s: expected 1 message, got %d", name, len(topic.Messages()))
		}
	}
}

// ---------------------------------------------------------------------------
// 25. Full API lifecycle: create, produce, consume, close
// ---------------------------------------------------------------------------

func TestIntegration_FullAPILifecycle(t *testing.T) {
	cfg := api.Config{
		TopicCapacity:     500,
		SubscriberBufSize: 64,
	}

	mq, err := api.New(cfg)
	if err != nil {
		t.Fatalf("new: %v", err)
	}

	// Create topic.
	mq.CreateTopic("lifecycle")

	// Set up consumer.
	var received int32
	handler := func(msg *protocol.Message) error {
		atomic.AddInt32(&received, 1)
		return nil
	}
	cons := mq.NewConsumer("lc-consumer", handler)
	cons.Subscribe("lifecycle")

	// Produce messages.
	p := mq.NewProducer()
	for i := 0; i < 20; i++ {
		_, err := p.PublishString("lifecycle", fmt.Sprintf("msg-%d", i))
		if err != nil {
			t.Fatalf("publish %d: %v", i, err)
		}
	}

	// Wait for processing.
	time.Sleep(500 * time.Millisecond)

	if atomic.LoadInt32(&received) != 20 {
		t.Errorf("expected 20 received, got %d", atomic.LoadInt32(&received))
	}

	// Check topic info.
	msgs, subs, _ := mq.TopicInfo("lifecycle")
	if msgs != 20 {
		t.Errorf("expected 20 stored messages, got %d", msgs)
	}
	if subs != 1 {
		t.Errorf("expected 1 subscriber, got %d", subs)
	}

	// Clean shutdown.
	cons.Close()
	if err := mq.Close(); err != nil {
		t.Fatalf("close: %v", err)
	}
}

