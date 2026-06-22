package main

import (
	"testing"
	"time"
)

func TestBlockCreation(t *testing.T) {
	cbTx := NewCoinbaseTX("test", "Test coinbase")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 2)

	if block.Header.Version != 1 {
		t.Errorf("Expected version 1, got %d", block.Header.Version)
	}
	if block.Header.Timestamp == 0 {
		t.Error("Timestamp should not be zero")
	}
	if block.Header.Difficulty != 2 {
		t.Errorf("Expected difficulty 2, got %d", block.Header.Difficulty)
	}
	if len(block.Transactions) != 1 {
		t.Errorf("Expected 1 transaction, got %d", len(block.Transactions))
	}
	if block.Hash == [32]byte{} {
		t.Error("Block hash should not be zero")
	}
}

func TestBlockHash(t *testing.T) {
	cbTx := NewCoinbaseTX("test", "Test coinbase")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 2)
	hash := block.CalculateHash()
	if hash != block.Hash {
		t.Error("Calculated hash should match stored hash")
	}
}

func TestBlockSerialization(t *testing.T) {
	cbTx := NewCoinbaseTX("test", "Test coinbase")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 2)

	data, err := block.Serialize()
	if err != nil {
		t.Fatalf("Failed to serialize block: %v", err)
	}

	loadedBlock, err := DeserializeBlock(data)
	if err != nil {
		t.Fatalf("Failed to deserialize block: %v", err)
	}

	if loadedBlock.Hash != block.Hash {
		t.Error("Deserialized block hash should match original")
	}
	if loadedBlock.Header.Timestamp != block.Header.Timestamp {
		t.Error("Deserialized block timestamp should match original")
	}
	if len(loadedBlock.Transactions) != len(block.Transactions) {
		t.Error("Deserialized block transactions count should match original")
	}
}

func TestGenesisBlock(t *testing.T) {
	cbTx := NewCoinbaseTX("genesis", "Genesis Block")
	genesis := NewGenesisBlock(cbTx, 2)

	if genesis.Header.PrevBlockHash != [32]byte{} {
		t.Error("Genesis block should have zero previous hash")
	}
	if genesis.Hash == [32]byte{} {
		t.Error("Genesis block should have a hash")
	}
	if len(genesis.Transactions) != 1 {
		t.Errorf("Genesis block should have 1 transaction, got %d", len(genesis.Transactions))
	}
}

func TestBlockValidation(t *testing.T) {
	cbTx := NewCoinbaseTX("test", "Test coinbase")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 2)

	err := block.Validate()
	if err != nil {
		t.Errorf("Block should be valid: %v", err)
	}

	block.Hash = [32]byte{1, 2, 3}
	err = block.Validate()
	if err == nil {
		t.Error("Block with corrupted hash should be invalid")
	}
}

func TestMerkleRoot(t *testing.T) {
	txs := []*Transaction{
		NewCoinbaseTX("addr1", "tx1"),
		NewCoinbaseTX("addr2", "tx2"),
		NewCoinbaseTX("addr3", "tx3"),
	}

	block := NewBlock(txs, [32]byte{}, 2)
	merkleRoot := block.CalculateMerkleRoot()

	if merkleRoot == [32]byte{} {
		t.Error("Merkle root should not be zero")
	}
	if merkleRoot != block.Header.MerkleRoot {
		t.Error("Calculated merkle root should match block header")
	}
}

func TestBlockTimestamp(t *testing.T) {
	before := time.Now().Unix()
	cbTx := NewCoinbaseTX("test", "Test coinbase")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 2)
	after := time.Now().Unix()

	if block.Header.Timestamp < before || block.Header.Timestamp > after {
		t.Errorf("Block timestamp %d should be between %d and %d", block.Header.Timestamp, before, after)
	}
}
