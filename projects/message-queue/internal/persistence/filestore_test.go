package persistence

import (
	"os"
	"testing"

	"github.com/example/message-queue/internal/protocol"
)

func TestFileStoreSaveAndLoad(t *testing.T) {
	dir, err := os.MkdirTemp("", "mq-test-*")
	if err != nil {
		t.Fatalf("temp dir: %v", err)
	}
	defer os.RemoveAll(dir)

	store, err := NewFileStore(dir)
	if err != nil {
		t.Fatalf("new store: %v", err)
	}

	msg := protocol.NewMessage("topic1", []byte("hello world"))
	if err := store.SaveMessage(msg); err != nil {
		t.Fatalf("save: %v", err)
	}

	loaded, err := store.LoadMessage(msg.ID)
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if loaded.ID != msg.ID {
		t.Errorf("ID mismatch: %s vs %s", loaded.ID, msg.ID)
	}
	if string(loaded.Payload) != "hello world" {
		t.Errorf("payload mismatch: %q", string(loaded.Payload))
	}
}

func TestFileStoreLoadAll(t *testing.T) {
	dir, err := os.MkdirTemp("", "mq-test-*")
	if err != nil {
		t.Fatalf("temp dir: %v", err)
	}
	defer os.RemoveAll(dir)

	store, _ := NewFileStore(dir)

	store.SaveMessage(protocol.NewMessage("a", []byte("1")))
	store.SaveMessage(protocol.NewMessage("b", []byte("2")))
	store.SaveMessage(protocol.NewMessage("a", []byte("3")))

	all, err := store.LoadAll()
	if err != nil {
		t.Fatalf("load all: %v", err)
	}
	if len(all) != 3 {
		t.Errorf("expected 3 messages, got %d", len(all))
	}
}

func TestFileStoreUpdate(t *testing.T) {
	dir, err := os.MkdirTemp("", "mq-test-*")
	if err != nil {
		t.Fatalf("temp dir: %v", err)
	}
	defer os.RemoveAll(dir)

	store, _ := NewFileStore(dir)

	msg := protocol.NewMessage("t", []byte("original"))
	store.SaveMessage(msg)

	msg.MarkAcknowledged()
	store.UpdateMessage(msg)

	loaded, _ := store.LoadMessage(msg.ID)
	if loaded.Status != protocol.StatusAcknowledged {
		t.Errorf("expected acknowledged, got %v", loaded.Status)
	}
}

func TestFileStoreDelete(t *testing.T) {
	dir, err := os.MkdirTemp("", "mq-test-*")
	if err != nil {
		t.Fatalf("temp dir: %v", err)
	}
	defer os.RemoveAll(dir)

	store, _ := NewFileStore(dir)

	msg := protocol.NewMessage("t", []byte("delete me"))
	store.SaveMessage(msg)

	if err := store.DeleteMessage(msg.ID); err != nil {
		t.Fatalf("delete: %v", err)
	}

	if _, err := store.LoadMessage(msg.ID); err != protocol.ErrMessageNotFound {
		t.Errorf("expected ErrMessageNotFound after delete, got %v", err)
	}
}

func TestFileStoreDeleteNotFound(t *testing.T) {
	dir, err := os.MkdirTemp("", "mq-test-*")
	if err != nil {
		t.Fatalf("temp dir: %v", err)
	}
	defer os.RemoveAll(dir)

	store, _ := NewFileStore(dir)

	if err := store.DeleteMessage("nonexistent"); err != protocol.ErrMessageNotFound {
		t.Errorf("expected ErrMessageNotFound, got %v", err)
	}
}
