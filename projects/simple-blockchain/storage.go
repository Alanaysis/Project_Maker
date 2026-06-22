package main

import (
	"fmt"
	"os"
	"path/filepath"
)

// Storage represents the storage engine
type Storage struct {
	DataDir string
}

// NewStorage creates a new storage engine
func NewStorage(dataDir string) *Storage {
	// Create data directory if it doesn't exist
	if _, err := os.Stat(dataDir); os.IsNotExist(err) {
		os.MkdirAll(dataDir, 0755)
	}

	return &Storage{
		DataDir: dataDir,
	}
}

// SaveBlock saves a block to disk
func (s *Storage) SaveBlock(block *Block) error {
	data, err := block.Serialize()
	if err != nil {
		return err
	}

	filename := filepath.Join(s.DataDir, fmt.Sprintf("%x.dat", block.Hash))
	return os.WriteFile(filename, data, 0644)
}

// LoadBlock loads a block from disk
func (s *Storage) LoadBlock(hash [32]byte) (*Block, error) {
	filename := filepath.Join(s.DataDir, fmt.Sprintf("%x.dat", hash))
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	return DeserializeBlock(data)
}

// SaveBlockchain saves the blockchain to disk
func (s *Storage) SaveBlockchain(bc *Blockchain) error {
	data, err := bc.Serialize()
	if err != nil {
		return err
	}

	filename := filepath.Join(s.DataDir, "blockchain.dat")
	return os.WriteFile(filename, data, 0644)
}

// LoadBlockchain loads the blockchain from disk
func (s *Storage) LoadBlockchain(difficulty uint32) (*Blockchain, error) {
	filename := filepath.Join(s.DataDir, "blockchain.dat")
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	bc := &Blockchain{
		Difficulty: difficulty,
	}
	if err := bc.Deserialize(data); err != nil {
		return nil, err
	}

	return bc, nil
}

// SaveTransaction saves a transaction to disk
func (s *Storage) SaveTransaction(tx *Transaction) error {
	data, err := tx.Serialize()
	if err != nil {
		return err
	}

	filename := filepath.Join(s.DataDir, fmt.Sprintf("tx_%x.dat", tx.ID))
	return os.WriteFile(filename, data, 0644)
}

// LoadTransaction loads a transaction from disk
func (s *Storage) LoadTransaction(id [32]byte) (*Transaction, error) {
	filename := filepath.Join(s.DataDir, fmt.Sprintf("tx_%x.dat", id))
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	return DeserializeTransaction(data)
}

// ListBlocks lists all blocks in the data directory
func (s *Storage) ListBlocks() ([][32]byte, error) {
	files, err := os.ReadDir(s.DataDir)
	if err != nil {
		return nil, err
	}

	var blocks [][32]byte
	for _, file := range files {
		if filepath.Ext(file.Name()) == ".dat" && file.Name() != "blockchain.dat" {
			hash, err := StringToHash(file.Name()[:len(file.Name())-4])
			if err != nil {
				continue
			}
			blocks = append(blocks, hash)
		}
	}

	return blocks, nil
}

// DeleteBlock deletes a block from disk
func (s *Storage) DeleteBlock(hash [32]byte) error {
	filename := filepath.Join(s.DataDir, fmt.Sprintf("%x.dat", hash))
	return os.Remove(filename)
}

// Clear clears all data in the data directory
func (s *Storage) Clear() error {
	return os.RemoveAll(s.DataDir)
}
