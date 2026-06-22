package persistence

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"

	"github.com/example/message-queue/internal/protocol"
)

// FileStore implements Store using the local filesystem.
// Each message is stored as a separate JSON file organized by topic.
type FileStore struct {
	baseDir string
	mu      sync.RWMutex
}

// NewFileStore creates a file-based store rooted at the given directory.
func NewFileStore(baseDir string) (*FileStore, error) {
	if err := os.MkdirAll(baseDir, 0755); err != nil {
		return nil, fmt.Errorf("create store dir: %w", err)
	}
	return &FileStore{baseDir: baseDir}, nil
}

// topicDir returns the directory for a given topic.
func (fs *FileStore) topicDir(topic string) string {
	return filepath.Join(fs.baseDir, topic)
}

// msgPath returns the file path for a specific message.
func (fs *FileStore) msgPath(topic, id string) string {
	return filepath.Join(fs.topicDir(topic), id+".json")
}

// SaveMessage writes a message to disk.
func (fs *FileStore) SaveMessage(msg *protocol.Message) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	dir := fs.topicDir(msg.Topic)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("create topic dir: %w", err)
	}

	data, err := json.MarshalIndent(msg, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal message: %w", err)
	}

	path := fs.msgPath(msg.Topic, msg.ID)
	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("write message file: %w", err)
	}
	return nil
}

// UpdateMessage overwrites an existing message file.
func (fs *FileStore) UpdateMessage(msg *protocol.Message) error {
	return fs.SaveMessage(msg) // same operation for file-based store
}

// LoadMessage reads a single message from disk.
func (fs *FileStore) LoadMessage(id string) (*protocol.Message, error) {
	fs.mu.RLock()
	defer fs.mu.RUnlock()

	// Search across all topic directories.
	entries, err := os.ReadDir(fs.baseDir)
	if err != nil {
		return nil, fmt.Errorf("read store dir: %w", err)
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		path := fs.msgPath(entry.Name(), id)
		if _, err := os.Stat(path); err == nil {
			return fs.readMessageFile(path)
		}
	}
	return nil, protocol.ErrMessageNotFound
}

// LoadAll reads every persisted message.
func (fs *FileStore) LoadAll() ([]*protocol.Message, error) {
	fs.mu.RLock()
	defer fs.mu.RUnlock()

	var messages []*protocol.Message

	entries, err := os.ReadDir(fs.baseDir)
	if err != nil {
		return nil, fmt.Errorf("read store dir: %w", err)
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		topicDir := filepath.Join(fs.baseDir, entry.Name())
		files, err := os.ReadDir(topicDir)
		if err != nil {
			continue
		}

		for _, f := range files {
			if filepath.Ext(f.Name()) != ".json" {
				continue
			}
			path := filepath.Join(topicDir, f.Name())
			msg, err := fs.readMessageFile(path)
			if err != nil {
				continue
			}
			messages = append(messages, msg)
		}
	}
	return messages, nil
}

// DeleteMessage removes a message file from disk.
func (fs *FileStore) DeleteMessage(id string) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	entries, err := os.ReadDir(fs.baseDir)
	if err != nil {
		return fmt.Errorf("read store dir: %w", err)
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		path := fs.msgPath(entry.Name(), id)
		if _, err := os.Stat(path); err == nil {
			return os.Remove(path)
		}
	}
	return protocol.ErrMessageNotFound
}

// Close is a no-op for the file store.
func (fs *FileStore) Close() error {
	return nil
}

// readMessageFile parses a JSON message file.
func (fs *FileStore) readMessageFile(path string) (*protocol.Message, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read file: %w", err)
	}

	var msg protocol.Message
	if err := json.Unmarshal(data, &msg); err != nil {
		return nil, fmt.Errorf("unmarshal message: %w", err)
	}
	return &msg, nil
}
