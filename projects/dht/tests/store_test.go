package chord

import (
	"testing"
)

func TestNewKeyValueStore(t *testing.T) {
	store := NewKeyValueStore()
	
	if store == nil {
		t.Fatal("NewKeyValueStore() should not return nil")
	}
	
	if store.Size() != 0 {
		t.Errorf("Empty store size = %d, want 0", store.Size())
	}
}

func TestKeyValueStorePutAndGet(t *testing.T) {
	store := NewKeyValueStore()
	
	store.Put("key1", "value1")
	store.Put("key2", "value2")
	
	val, ok := store.Get("key1")
	if !ok {
		t.Error("Get should find key1")
	}
	if val != "value1" {
		t.Errorf("Get(key1) = %s, want value1", val)
	}
	
	val, ok = store.Get("key2")
	if !ok {
		t.Error("Get should find key2")
	}
	if val != "value2" {
		t.Errorf("Get(key2) = %s, want value2", val)
	}
}

func TestKeyValueStoreGetNotFound(t *testing.T) {
	store := NewKeyValueStore()
	
	val, ok := store.Get("nonexistent")
	if ok {
		t.Error("Get should not find nonexistent key")
	}
	if val != "" {
		t.Errorf("Get(nonexistent) = %s, want empty string", val)
	}
}

func TestKeyValueStoreDelete(t *testing.T) {
	store := NewKeyValueStore()
	
	store.Put("key1", "value1")
	
	ok := store.Delete("key1")
	if !ok {
		t.Error("Delete should return true for existing key")
	}
	
	_, ok = store.Get("key1")
	if ok {
		t.Error("Key should not exist after deletion")
	}
	
	ok = store.Delete("nonexistent")
	if ok {
		t.Error("Delete should return false for nonexistent key")
	}
}

func TestKeyValueStoreKeys(t *testing.T) {
	store := NewKeyValueStore()
	
	store.Put("key1", "value1")
	store.Put("key2", "value2")
	store.Put("key3", "value3")
	
	keys := store.Keys()
	
	if len(keys) != 3 {
		t.Errorf("Keys() length = %d, want 3", len(keys))
	}
	
	// Check all keys are present
	found := make(map[string]bool)
	for _, k := range keys {
		found[k] = true
	}
	
	for _, expected := range []string{"key1", "key2", "key3"} {
		if !found[expected] {
			t.Errorf("Keys() should contain %s", expected)
		}
	}
}

func TestKeyValueStoreSize(t *testing.T) {
	store := NewKeyValueStore()
	
	if store.Size() != 0 {
		t.Errorf("Empty store size = %d, want 0", store.Size())
	}
	
	store.Put("key1", "value1")
	if store.Size() != 1 {
		t.Errorf("Store size after 1 Put = %d, want 1", store.Size())
	}
	
	store.Put("key2", "value2")
	if store.Size() != 2 {
		t.Errorf("Store size after 2 Puts = %d, want 2", store.Size())
	}
}

func TestKeyValueStoreClear(t *testing.T) {
	store := NewKeyValueStore()
	
	store.Put("key1", "value1")
	store.Put("key2", "value2")
	
	store.Clear()
	
	if store.Size() != 0 {
		t.Errorf("Store size after Clear = %d, want 0", store.Size())
	}
	
	_, ok := store.Get("key1")
	if ok {
		t.Error("Key should not exist after Clear")
	}
}

func TestKeyValueStoreHas(t *testing.T) {
	store := NewKeyValueStore()
	
	store.Put("key1", "value1")
	
	if !store.Has("key1") {
		t.Error("Has should return true for existing key")
	}
	
	if store.Has("nonexistent") {
		t.Error("Has should return false for nonexistent key")
	}
}

func TestKeyValueStoreValues(t *testing.T) {
	store := NewKeyValueStore()
	
	store.Put("key1", "value1")
	store.Put("key2", "value2")
	
	values := store.Values()
	
	if len(values) != 2 {
		t.Errorf("Values() length = %d, want 2", len(values))
	}
}

func TestKeyValueStoreForEach(t *testing.T) {
	store := NewKeyValueStore()
	
	store.Put("key1", "value1")
	store.Put("key2", "value2")
	
	count := 0
	store.ForEach(func(key, value string) {
		count++
		if key != "key1" && key != "key2" {
			t.Errorf("ForEach: unexpected key %s", key)
		}
	})
	
	if count != 2 {
		t.Errorf("ForEach count = %d, want 2", count)
	}
}

func TestKeyValueStoreOverwrite(t *testing.T) {
	store := NewKeyValueStore()
	
	store.Put("key1", "value1")
	store.Put("key1", "value2")
	
	val, ok := store.Get("key1")
	if !ok {
		t.Error("Get should find key1 after overwrite")
	}
	if val != "value2" {
		t.Errorf("Get(key1) = %s, want value2", val)
	}
	
	if store.Size() != 1 {
		t.Errorf("Store size after overwrite = %d, want 1", store.Size())
	}
}
