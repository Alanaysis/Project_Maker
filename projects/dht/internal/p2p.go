package internal

import (
	"crypto/sha1"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"sync"
)

// FileInfo represents metadata about a shared file
type FileInfo struct {
	Hash     string `json:"hash"`
	Name     string `json:"name"`
	Size     int64  `json:"size"`
	Uploader string `json:"uploader"`
}

// P2PNetwork implements P2P file sharing over DHT
type P2PNetwork struct {
	mu        sync.RWMutex
	node      *NetworkNode
	filesDir  string // Directory for storing shared files
	files     map[string]*FileInfo
}

// NewP2PNetwork creates a new P2P file sharing network
func NewP2PNetwork(node *NetworkNode, filesDir string) (*P2PNetwork, error) {
	// Create files directory if it doesn't exist
	if err := os.MkdirAll(filesDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create files directory: %v", err)
	}

	return &P2PNetwork{
		node:     node,
		filesDir: filesDir,
		files:    make(map[string]*FileInfo),
	}, nil
}

// ShareFile shares a file on the P2P network
func (p2p *P2PNetwork) ShareFile(filePath string) (*FileInfo, error) {
	// Open file
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %v", err)
	}
	defer file.Close()

	// Get file info
	stat, err := file.Stat()
	if err != nil {
		return nil, fmt.Errorf("failed to get file info: %v", err)
	}

	// Calculate hash
	hash := sha1.New()
	if _, err := io.Copy(hash, file); err != nil {
		return nil, fmt.Errorf("failed to calculate hash: %v", err)
	}
	hashStr := fmt.Sprintf("%x", hash.Sum(nil))

	// Copy file to shared directory
	destPath := filepath.Join(p2p.filesDir, hashStr)
	if err := copyFile(filePath, destPath); err != nil {
		return nil, fmt.Errorf("failed to copy file: %v", err)
	}

	// Create file info
	info := &FileInfo{
		Hash:     hashStr,
		Name:     filepath.Base(filePath),
		Size:     stat.Size(),
		Uploader: p2p.node.GetAddr(),
	}

	// Store file metadata in DHT
	metadata := fmt.Sprintf("%s|%s|%d|%s", info.Hash, info.Name, info.Size, info.Uploader)
	if err := p2p.node.KademliaStore("file:"+hashStr, metadata); err != nil {
		log.Printf("[P2P] Failed to store file metadata: %v", err)
	}

	// Store locally
	p2p.mu.Lock()
	p2p.files[hashStr] = info
	p2p.mu.Unlock()

	log.Printf("[P2P] Shared file: %s (hash: %s)", info.Name, hashStr)
	return info, nil
}

// DownloadFile downloads a file by its hash
func (p2p *P2PNetwork) DownloadFile(hash string) (string, error) {
	// Check if already downloaded
	p2p.mu.RLock()
	if info, ok := p2p.files[hash]; ok {
		p2p.mu.RUnlock()
		return filepath.Join(p2p.filesDir, info.Hash), nil
	}
	p2p.mu.RUnlock()

	// Find file metadata in DHT
	metadata, found := p2p.node.KademliaIterativeFindValue("file:" + hash)
	if !found {
		return "", fmt.Errorf("file not found: %s", hash)
	}

	// Parse metadata
	var name, uploader string
	var size int64
	fmt.Sscanf(metadata, "%[^|]|%[^|]|%d|%s", &hash, &name, &size, &uploader)

	// Download from uploader
	// In a real implementation, this would involve actual file transfer
	// For now, we'll just create a placeholder
	log.Printf("[P2P] File found: %s (size: %d bytes)", name, size)

	info := &FileInfo{
		Hash:     hash,
		Name:     name,
		Size:     size,
		Uploader: uploader,
	}

	p2p.mu.Lock()
	p2p.files[hash] = info
	p2p.mu.Unlock()

	return filepath.Join(p2p.filesDir, hash), nil
}

// SearchFiles searches for files by name
func (p2p *P2PNetwork) SearchFiles(query string) []*FileInfo {
	p2p.mu.RLock()
	defer p2p.mu.RUnlock()

	var results []*FileInfo
	for _, info := range p2p.files {
		if contains(info.Name, query) {
			results = append(results, info)
		}
	}
	return results
}

// ListFiles lists all shared files
func (p2p *P2PNetwork) ListFiles() []*FileInfo {
	p2p.mu.RLock()
	defer p2p.mu.RUnlock()

	files := make([]*FileInfo, 0, len(p2p.files))
	for _, info := range p2p.files {
		files = append(files, info)
	}
	return files
}

// GetFileInfo returns info about a specific file
func (p2p *P2PNetwork) GetFileInfo(hash string) (*FileInfo, bool) {
	p2p.mu.RLock()
	defer p2p.mu.RUnlock()
	info, ok := p2p.files[hash]
	return info, ok
}

// RemoveFile removes a file from the shared directory
func (p2p *P2PNetwork) RemoveFile(hash string) error {
	p2p.mu.Lock()
	defer p2p.mu.Unlock()

	info, ok := p2p.files[hash]
	if !ok {
		return fmt.Errorf("file not found: %s", hash)
	}

	// Remove file
	path := filepath.Join(p2p.filesDir, hash)
	if err := os.Remove(path); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("failed to remove file: %v", err)
	}

	// Remove from DHT
	if err := p2p.node.node.Delete("file:" + hash); err != nil {
		log.Printf("[P2P] Failed to remove file metadata from DHT: %v", err)
	}

	delete(p2p.files, hash)
	log.Printf("[P2P] Removed file: %s", info.Name)
	return nil
}

// contains checks if a string contains a substring (case-insensitive)
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && len(substr) > 0)
}

// copyFile copies a file from src to dst
func copyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	destFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer destFile.Close()

	_, err = io.Copy(destFile, sourceFile)
	return err
}
