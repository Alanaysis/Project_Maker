package main

import (
	"os"
	"testing"
)

func TestBlockchainCreation(t *testing.T) {
	os.Remove("blockchain.dat")
	defer os.Remove("blockchain.dat")

	bc := NewBlockchain(2)

	if bc.GetHeight() != 1 {
		t.Errorf("Expected height 1, got %d", bc.GetHeight())
	}

	genesis := bc.GetLatestBlock()
	if genesis == nil {
		t.Fatal("Genesis block should exist")
	}

	if genesis.Header.PrevBlockHash != [32]byte{} {
		t.Error("Genesis block should have zero previous hash")
	}
}

func TestBlockchainAddBlock(t *testing.T) {
	os.Remove("blockchain.dat")
	defer os.Remove("blockchain.dat")

	bc := NewBlockchain(2)

	cbTx := NewCoinbaseTX("test", "Test coinbase")
	newBlock := NewBlock([]*Transaction{cbTx}, bc.GetLatestBlock().Hash, 2)

	err := bc.AddBlock(newBlock)
	if err != nil {
		t.Fatalf("Failed to add block: %v", err)
	}

	if bc.GetHeight() != 2 {
		t.Errorf("Expected height 2, got %d", bc.GetHeight())
	}

	latest := bc.GetLatestBlock()
	if latest.Hash != newBlock.Hash {
		t.Error("Latest block should be the new block")
	}
}

func TestBlockchainValidation(t *testing.T) {
	os.Remove("blockchain.dat")
	defer os.Remove("blockchain.dat")

	bc := NewBlockchain(2)

	for i := 0; i < 3; i++ {
		cbTx := NewCoinbaseTX("test", "Test coinbase")
		newBlock := NewBlock([]*Transaction{cbTx}, bc.GetLatestBlock().Hash, 2)
		err := bc.AddBlock(newBlock)
		if err != nil {
			t.Fatalf("Failed to add block %d: %v", i, err)
		}
	}

	err := bc.ValidateChain()
	if err != nil {
		t.Errorf("Blockchain should be valid: %v", err)
	}
}

func TestBlockchainPersistence(t *testing.T) {
	os.Remove("blockchain.dat")
	defer os.Remove("blockchain.dat")

	bc1 := NewBlockchain(2)
	for i := 0; i < 3; i++ {
		cbTx := NewCoinbaseTX("test", "Test coinbase")
		newBlock := NewBlock([]*Transaction{cbTx}, bc1.GetLatestBlock().Hash, 2)
		bc1.AddBlock(newBlock)
	}

	err := bc1.Save()
	if err != nil {
		t.Fatalf("Failed to save blockchain: %v", err)
	}

	bc2 := NewBlockchain(2)
	if bc2.GetHeight() != bc1.GetHeight() {
		t.Errorf("Loaded blockchain height %d should match saved height %d", bc2.GetHeight(), bc1.GetHeight())
	}

	if bc2.GetLatestBlock().Hash != bc1.GetLatestBlock().Hash {
		t.Error("Loaded blockchain latest block hash should match saved hash")
	}
}

func TestBlockchainGetBlock(t *testing.T) {
	os.Remove("blockchain.dat")
	defer os.Remove("blockchain.dat")

	bc := NewBlockchain(2)

	cbTx := NewCoinbaseTX("test", "Test coinbase")
	newBlock := NewBlock([]*Transaction{cbTx}, bc.GetLatestBlock().Hash, 2)
	bc.AddBlock(newBlock)

	block, err := bc.GetBlock(newBlock.Hash)
	if err != nil {
		t.Fatalf("Failed to get block: %v", err)
	}

	if block.Hash != newBlock.Hash {
		t.Error("Retrieved block hash should match")
	}

	block, err = bc.GetBlockByHeight(1)
	if err != nil {
		t.Fatalf("Failed to get block by height: %v", err)
	}

	if block.Hash != newBlock.Hash {
		t.Error("Block at height 1 should match")
	}
}

func TestBlockchainGetBalance(t *testing.T) {
	os.Remove("blockchain.dat")
	defer os.Remove("blockchain.dat")

	bc := NewBlockchain(2)

	cbTx := NewCoinbaseTX("miner", "Mining reward")
	newBlock := NewBlock([]*Transaction{cbTx}, bc.GetLatestBlock().Hash, 2)
	bc.AddBlock(newBlock)

	balance := bc.GetBalance("miner")
	if balance != 10.0 {
		t.Errorf("Expected balance 10.0, got %.2f", balance)
	}

	balance = bc.GetBalance("unknown")
	if balance != 0.0 {
		t.Errorf("Expected balance 0.0, got %.2f", balance)
	}
}

func TestBlockchainFindUTXO(t *testing.T) {
	os.Remove("blockchain.dat")
	defer os.Remove("blockchain.dat")

	bc := NewBlockchain(2)

	cbTx := NewCoinbaseTX("miner", "Mining reward")
	newBlock := NewBlock([]*Transaction{cbTx}, bc.GetLatestBlock().Hash, 2)
	bc.AddBlock(newBlock)

	utxos := bc.FindUTXO("miner")
	if len(utxos) != 1 {
		t.Errorf("Expected 1 UTXO, got %d", len(utxos))
	}

	if utxos[0].Value != 10.0 {
		t.Errorf("Expected UTXO value 10.0, got %.2f", utxos[0].Value)
	}
}
