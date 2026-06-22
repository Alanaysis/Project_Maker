package persistence

import (
	"testing"

	"github.com/example/message-queue/internal/protocol"
)

func TestMemStoreSaveAndLoad(t *testing.T) {
	store := NewMemStore()

	msg := protocol.NewMessage("t", []byte("data"))
	store.SaveMessage(msg)

	loaded, err := store.LoadMessage(msg.ID)
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if loaded.ID != msg.ID {
		t.Errorf("ID mismatch")
	}
}

func TestMemStoreLoadAll(t *testing.T) {
	store := NewMemStore()

	store.SaveMessage(protocol.NewMessage("a", []byte("1")))
	store.SaveMessage(protocol.NewMessage("b", []byte("2")))

	all, _ := store.LoadAll()
	if len(all) != 2 {
		t.Errorf("expected 2, got %d", len(all))
	}
}

func TestMemStoreDelete(t *testing.T) {
	store := NewMemStore()

	msg := protocol.NewMessage("t", []byte("x"))
	store.SaveMessage(msg)
	store.DeleteMessage(msg.ID)

	if _, err := store.LoadMessage(msg.ID); err != protocol.ErrMessageNotFound {
		t.Errorf("expected ErrMessageNotFound, got %v", err)
	}
}

func TestMemStoreUpdate(t *testing.T) {
	store := NewMemStore()

	msg := protocol.NewMessage("t", []byte("v1"))
	store.SaveMessage(msg)

	msg.Payload = []byte("v2")
	store.UpdateMessage(msg)

	loaded, _ := store.LoadMessage(msg.ID)
	if string(loaded.Payload) != "v2" {
		t.Errorf("expected 'v2', got %q", string(loaded.Payload))
	}
}
