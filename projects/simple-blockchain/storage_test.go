package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestNewStorage(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test_storage_new")
	defer os.RemoveAll(dir)

	s := NewStorage(dir)
	if s == nil {
		t.Fatal("NewStorage should not return nil")
	}
	if s.DataDir != dir {
		t.Errorf("DataDir should be %s, got %s", dir, s.DataDir)
	}

	// Directory should be created
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		t.Error("NewStorage should create the data directory")
	}
}

func TestSaveAndLoadBlock(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test_storage_block")
	defer os.RemoveAll(dir)

	s := NewStorage(dir)

	cbTx := NewCoinbaseTX("test", "Test coinbase")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 2)

	// Save block
	err := s.SaveBlock(block)
	if err != nil {
		t.Fatalf("SaveBlock failed: %v", err)
	}

	// Load block
	loaded, err := s.LoadBlock(block.Hash)
	if err != nil {
		t.Fatalf("LoadBlock failed: %v", err)
	}

	if loaded.Hash != block.Hash {
		t.Error("Loaded block hash should match saved block")
	}
	if len(loaded.Transactions) != len(block.Transactions) {
		t.Error("Loaded block transactions count should match")
	}
}

func TestLoadBlockNotFound(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test_storage_notfound")
	defer os.RemoveAll(dir)

	s := NewStorage(dir)

	var fakeHash [32]byte
	fakeHash[0] = 0xFF

	_, err := s.LoadBlock(fakeHash)
	if err == nil {
		t.Error("LoadBlock should return error for non-existent block")
	}
}

func TestDeleteBlock(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test_storage_delete")
	defer os.RemoveAll(dir)

	s := NewStorage(dir)

	cbTx := NewCoinbaseTX("test", "Test coinbase")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 2)

	// Save then delete
	if err := s.SaveBlock(block); err != nil {
		t.Fatalf("SaveBlock failed: %v", err)
	}

	if err := s.DeleteBlock(block.Hash); err != nil {
		t.Fatalf("DeleteBlock failed: %v", err)
	}

	// Should fail to load after deletion
	_, err := s.LoadBlock(block.Hash)
	if err == nil {
		t.Error("LoadBlock should fail after block is deleted")
	}
}

func TestListBlocks(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test_storage_list")
	defer os.RemoveAll(dir)

	s := NewStorage(dir)

	// Save multiple blocks with distinct content to ensure different hashes
	blocks := make([]*Block, 3)
	prevHash := [32]byte{}
	for i := range blocks {
		cbTx := NewCoinbaseTX("test", "Test coinbase "+string(rune('A'+i)))
		blocks[i] = NewBlock([]*Transaction{cbTx}, prevHash, 2)
		prevHash = blocks[i].Hash
		if err := s.SaveBlock(blocks[i]); err != nil {
			t.Fatalf("SaveBlock %d failed: %v", i, err)
		}
	}

	// List blocks
	hashes, err := s.ListBlocks()
	if err != nil {
		t.Fatalf("ListBlocks failed: %v", err)
	}

	if len(hashes) != 3 {
		t.Errorf("ListBlocks should return 3 hashes, got %d", len(hashes))
	}
}

func TestSaveAndLoadTransaction(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test_storage_tx")
	defer os.RemoveAll(dir)

	s := NewStorage(dir)

	tx := NewCoinbaseTX("test", "Test coinbase")

	// Save transaction
	err := s.SaveTransaction(tx)
	if err != nil {
		t.Fatalf("SaveTransaction failed: %v", err)
	}

	// Load transaction
	loaded, err := s.LoadTransaction(tx.ID)
	if err != nil {
		t.Fatalf("LoadTransaction failed: %v", err)
	}

	if loaded.ID != tx.ID {
		t.Error("Loaded transaction ID should match saved transaction")
	}
	if len(loaded.Outputs) != len(tx.Outputs) {
		t.Error("Loaded transaction outputs count should match")
	}
}

func TestLoadTransactionNotFound(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test_storage_tx_notfound")
	defer os.RemoveAll(dir)

	s := NewStorage(dir)

	var fakeID [32]byte
	fakeID[0] = 0xFF

	_, err := s.LoadTransaction(fakeID)
	if err == nil {
		t.Error("LoadTransaction should return error for non-existent transaction")
	}
}

func TestSaveAndLoadBlockchain(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test_storage_bc")
	defer os.RemoveAll(dir)
	// Clean blockchain.dat from working dir
	defer os.Remove("blockchain.dat")
	defer os.Remove("blockchain.dat.tmp")

	s := NewStorage(dir)

	// Create a blockchain with genesis block
	bc := &Blockchain{
		Difficulty: 2,
	}
	cbTx := NewCoinbaseTX("genesis", "Genesis Block")
	genesis := NewGenesisBlock(cbTx, 2)
	bc.Blocks = append(bc.Blocks, genesis)

	// Save blockchain
	err := s.SaveBlockchain(bc)
	if err != nil {
		t.Fatalf("SaveBlockchain failed: %v", err)
	}

	// Load blockchain
	loaded, err := s.LoadBlockchain(2)
	if err != nil {
		t.Fatalf("LoadBlockchain failed: %v", err)
	}

	if len(loaded.Blocks) != 1 {
		t.Errorf("Loaded blockchain should have 1 block, got %d", len(loaded.Blocks))
	}
	if loaded.Blocks[0].Hash != genesis.Hash {
		t.Error("Loaded genesis block hash should match")
	}
}

func TestClear(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test_storage_clear")
	defer os.RemoveAll(dir)

	s := NewStorage(dir)

	// Save a block
	cbTx := NewCoinbaseTX("test", "Test coinbase")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 2)
	if err := s.SaveBlock(block); err != nil {
		t.Fatalf("SaveBlock failed: %v", err)
	}

	// Clear
	if err := s.Clear(); err != nil {
		t.Fatalf("Clear failed: %v", err)
	}

	// Directory should be gone
	if _, err := os.Stat(dir); !os.IsNotExist(err) {
		t.Error("Clear should remove the data directory")
	}
}
