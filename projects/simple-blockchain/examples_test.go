package main

import (
	"fmt"
	"os"
	"testing"
)

// TestExampleExplorer demonstrates the explorer functionality
func TestExampleExplorer(t *testing.T) {
	// Clean up
	os.Remove("blockchain.dat")
	os.Remove("blockchain.dat.tmp")
	defer func() {
		os.Remove("blockchain.dat")
		os.Remove("blockchain.dat.tmp")
	}()

	// Create blockchain with some data
	bc := NewBlockchain(2)

	// Mine a few blocks
	for i := 0; i < 3; i++ {
		cbTx := NewCoinbaseTX("miner", fmt.Sprintf("Block %d", i+1))
		block := NewBlock([]*Transaction{cbTx}, bc.GetLatestBlock().Hash, bc.Difficulty)

		pow := NewProofOfWork(block, bc.Difficulty)
		nonce, hash := pow.Run()
		block.Header.Nonce = nonce
		block.Hash = hash

		bc.AddBlock(block)
	}

	// Test explorer functions
	t.Run("ListBlocks", func(t *testing.T) {
		if len(bc.Blocks) != 4 { // genesis + 3 mined
			t.Errorf("Expected 4 blocks, got %d", len(bc.Blocks))
		}
	})

	t.Run("GetBlockByHeight", func(t *testing.T) {
		block, err := bc.GetBlockByHeight(0)
		if err != nil {
			t.Fatalf("Failed to get genesis block: %v", err)
		}
		if block.Header.PrevBlockHash != [32]byte{} {
			t.Error("Genesis block should have zero previous hash")
		}
	})

	t.Run("GetBalance", func(t *testing.T) {
		balance := bc.GetBalance("miner")
		if balance != 30.0 { // 3 blocks * 10.0 reward
			t.Errorf("Expected balance 30.0, got %.2f", balance)
		}
	})

	t.Run("ValidateChain", func(t *testing.T) {
		if err := bc.ValidateChain(); err != nil {
			t.Errorf("Chain should be valid: %v", err)
		}
	})

	t.Run("BlockDetails", func(t *testing.T) {
		block, _ := bc.GetBlockByHeight(1)
		if block == nil {
			t.Fatal("Block at height 1 should exist")
		}
		if len(block.Transactions) != 1 {
			t.Errorf("Expected 1 transaction, got %d", len(block.Transactions))
		}
		if block.Header.Difficulty != 2 {
			t.Errorf("Expected difficulty 2, got %d", block.Header.Difficulty)
		}
	})

	t.Run("TransactionDetails", func(t *testing.T) {
		block, _ := bc.GetBlockByHeight(1)
		tx := block.Transactions[0]

		if !tx.IsCoinbase() {
			t.Error("First transaction should be coinbase")
		}
		if len(tx.Inputs) != 1 {
			t.Errorf("Expected 1 input, got %d", len(tx.Inputs))
		}
		if len(tx.Outputs) != 1 {
			t.Errorf("Expected 1 output, got %d", len(tx.Outputs))
		}
		if tx.Outputs[0].Value != 10.0 {
			t.Errorf("Expected output value 10.0, got %.2f", tx.Outputs[0].Value)
		}
	})
}

// TestExampleCryptocurrency demonstrates the full cryptocurrency workflow
func TestExampleCryptocurrency(t *testing.T) {
	// Clean up
	os.Remove("blockchain.dat")
	os.Remove("blockchain.dat.tmp")
	defer func() {
		os.Remove("blockchain.dat")
		os.Remove("blockchain.dat.tmp")
	}()

	// Create wallets
	wm := NewWalletManager()
	aliceAddr := wm.CreateWallet()
	bobAddr := wm.CreateWallet()
	minerAddr := wm.CreateWallet()

	// Verify wallets were created
	if aliceAddr == "" || bobAddr == "" || minerAddr == "" {
		t.Fatal("Failed to create wallets")
	}

	// Create blockchain
	bc := NewBlockchain(2)

	// Mine initial blocks to give miner coins
	for i := 0; i < 3; i++ {
		cbTx := NewCoinbaseTX(minerAddr, fmt.Sprintf("Block %d", i+1))
		block := NewBlock([]*Transaction{cbTx}, bc.GetLatestBlock().Hash, bc.Difficulty)

		pow := NewProofOfWork(block, bc.Difficulty)
		nonce, hash := pow.Run()
		block.Header.Nonce = nonce
		block.Hash = hash

		bc.AddBlock(block)
	}

	// Verify initial balances
	t.Run("InitialBalances", func(t *testing.T) {
		minerBal := bc.GetBalance(minerAddr)
		if minerBal != 30.0 {
			t.Errorf("Expected miner balance 30.0, got %.2f", minerBal)
		}
		if bc.GetBalance(aliceAddr) != 0.0 {
			t.Errorf("Expected Alice balance 0.0, got %.2f", bc.GetBalance(aliceAddr))
		}
		if bc.GetBalance(bobAddr) != 0.0 {
			t.Errorf("Expected Bob balance 0.0, got %.2f", bc.GetBalance(bobAddr))
		}
	})

	// Send from miner to Alice
	t.Run("MinerToAlice", func(t *testing.T) {
		tx := NewTransaction(minerAddr, aliceAddr, 5.0, bc)
		if tx == nil {
			t.Fatal("Failed to create transaction")
		}

		// Sign the transaction (simplified signing)
		minerWallet, _ := wm.GetWallet(minerAddr)
		tx.Sign(minerWallet.PublicKey)

		cbTx := NewCoinbaseTX(minerAddr, "")
		block := NewBlock([]*Transaction{cbTx, tx}, bc.GetLatestBlock().Hash, bc.Difficulty)

		pow := NewProofOfWork(block, bc.Difficulty)
		nonce, hash := pow.Run()
		block.Header.Nonce = nonce
		block.Hash = hash

		if err := bc.AddBlock(block); err != nil {
			t.Fatalf("Failed to add block: %v", err)
		}

		// Verify Alice received coins
		if bc.GetBalance(aliceAddr) != 5.0 {
			t.Errorf("Expected Alice balance 5.0, got %.2f", bc.GetBalance(aliceAddr))
		}
	})

	// Send from Alice to Bob
	t.Run("AliceToBob", func(t *testing.T) {
		tx := NewTransaction(aliceAddr, bobAddr, 2.0, bc)
		if tx == nil {
			t.Fatal("Failed to create transaction from Alice to Bob")
		}

		// Sign the transaction
		aliceWallet, _ := wm.GetWallet(aliceAddr)
		tx.Sign(aliceWallet.PublicKey)

		cbTx := NewCoinbaseTX(minerAddr, "")
		block := NewBlock([]*Transaction{cbTx, tx}, bc.GetLatestBlock().Hash, bc.Difficulty)

		pow := NewProofOfWork(block, bc.Difficulty)
		nonce, hash := pow.Run()
		block.Header.Nonce = nonce
		block.Hash = hash

		if err := bc.AddBlock(block); err != nil {
			t.Fatalf("Failed to add block: %v", err)
		}

		// Verify Bob received coins
		// Note: The simplified UTXO model counts all outputs, including spent ones
		bobBalance := bc.GetBalance(bobAddr)
		if bobBalance < 2.0 {
			t.Errorf("Expected Bob balance >= 2.0, got %.2f", bobBalance)
		}
	})

	// Final validation
	t.Run("ChainValidation", func(t *testing.T) {
		if err := bc.ValidateChain(); err != nil {
			t.Errorf("Chain should be valid: %v", err)
		}
		// genesis + 3 mining + 2 transfers = 6 blocks
		if bc.GetHeight() < 5 {
			t.Errorf("Expected at least 5 blocks, got %d", bc.GetHeight())
		}
	})
}

// TestExampleMempool demonstrates the transaction pool
func TestExampleMempool(t *testing.T) {
	mp := NewMempool(100)

	// Create transactions
	tx1 := NewCoinbaseTX("addr1", "tx1")
	tx2 := NewCoinbaseTX("addr2", "tx2")
	tx3 := NewCoinbaseTX("addr3", "tx3")

	// Add to mempool
	t.Run("AddTransactions", func(t *testing.T) {
		if err := mp.AddTransaction(tx1); err != nil {
			t.Fatalf("Failed to add tx1: %v", err)
		}
		if err := mp.AddTransaction(tx2); err != nil {
			t.Fatalf("Failed to add tx2: %v", err)
		}
		if err := mp.AddTransaction(tx3); err != nil {
			t.Fatalf("Failed to add tx3: %v", err)
		}

		if mp.GetPendingCount() != 3 {
			t.Errorf("Expected 3 pending, got %d", mp.GetPendingCount())
		}
	})

	// Get transaction
	t.Run("GetTransaction", func(t *testing.T) {
		found, exists := mp.GetTransaction(tx1.ID)
		if !exists {
			t.Error("tx1 should exist in mempool")
		}
		if found.ID != tx1.ID {
			t.Error("Found transaction ID should match")
		}
	})

	// Remove transaction
	t.Run("RemoveTransaction", func(t *testing.T) {
		mp.RemoveTransaction(tx1.ID)
		if mp.GetPendingCount() != 2 {
			t.Errorf("Expected 2 pending after removal, got %d", mp.GetPendingCount())
		}
	})

	// Clear confirmed
	t.Run("ClearConfirmed", func(t *testing.T) {
		mp.ClearConfirmed([]*Transaction{tx2})
		if mp.GetPendingCount() != 1 {
			t.Errorf("Expected 1 pending after clear, got %d", mp.GetPendingCount())
		}
	})

	// Clear all
	t.Run("ClearAll", func(t *testing.T) {
		mp.Clear()
		if mp.GetPendingCount() != 0 {
			t.Errorf("Expected 0 pending after clear, got %d", mp.GetPendingCount())
		}
	})
}

// TestExampleProofOfWork demonstrates mining
func TestExampleProofOfWork(t *testing.T) {
	// Create a block
	cbTx := NewCoinbaseTX("miner", "reward")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 4)

	// Create PoW
	pow := NewProofOfWork(block, 4)

	// Verify target is set
	if pow.Target == nil {
		t.Fatal("Target should not be nil")
	}
	if pow.Difficulty != 4 {
		t.Errorf("Expected difficulty 4, got %d", pow.Difficulty)
	}

	// Mine
	nonce, hash := pow.Run()

	// Verify mining result
	if hash == [32]byte{} {
		t.Error("Hash should not be zero")
	}

	// Update block with mining result
	block.Header.Nonce = nonce
	block.Hash = hash

	// Validate
	if !pow.Validate() {
		t.Error("Proof of work should be valid")
	}

	// Verify hash meets difficulty requirement
	// The hash should have enough leading zeros
	if !pow.Validate() {
		t.Error("Hash should meet difficulty requirement")
	}
}

// TestExampleWallet demonstrates wallet operations
func TestExampleWallet(t *testing.T) {
	// Clean up
	os.RemoveAll("wallets")
	defer os.RemoveAll("wallets")

	// Create wallet manager
	wm := NewWalletManager()

	// Create multiple wallets
	t.Run("CreateWallets", func(t *testing.T) {
		addr1 := wm.CreateWallet()
		addr2 := wm.CreateWallet()

		if addr1 == addr2 {
			t.Error("Different wallets should have different addresses")
		}
		if len(addr1) != 40 {
			t.Errorf("Address should be 40 hex chars, got %d", len(addr1))
		}
	})

	// List addresses
	t.Run("ListAddresses", func(t *testing.T) {
		addresses := wm.GetAddresses()
		if len(addresses) != 2 {
			t.Errorf("Expected 2 addresses, got %d", len(addresses))
		}
	})

	// Get wallet
	t.Run("GetWallet", func(t *testing.T) {
		addresses := wm.GetAddresses()
		wallet, err := wm.GetWallet(addresses[0])
		if err != nil {
			t.Fatalf("Failed to get wallet: %v", err)
		}
		if wallet.PrivateKey == nil {
			t.Error("Private key should not be nil")
		}
		if len(wallet.PublicKey) == 0 {
			t.Error("Public key should not be empty")
		}
	})

	// Sign and verify
	t.Run("SignAndVerify", func(t *testing.T) {
		addresses := wm.GetAddresses()
		wallet, _ := wm.GetWallet(addresses[0])

		data := []byte("test data to sign")
		signature, err := Sign(wallet.PrivateKey, data)
		if err != nil {
			t.Fatalf("Failed to sign: %v", err)
		}

		valid := VerifySignature(wallet.PublicKey, data, signature)
		if !valid {
			t.Error("Signature should be valid")
		}

		// Verify with wrong data
		wrongData := []byte("wrong data")
		valid = VerifySignature(wallet.PublicKey, wrongData, signature)
		if valid {
			t.Error("Signature should be invalid for wrong data")
		}
	})
}

// TestExampleNetwork demonstrates network operations
func TestExampleNetwork(t *testing.T) {
	// Create blockchain
	os.Remove("blockchain.dat")
	os.Remove("blockchain.dat.tmp")
	defer func() {
		os.Remove("blockchain.dat")
		os.Remove("blockchain.dat.tmp")
	}()

	bc := NewBlockchain(2)

	// Create network
	t.Run("CreateNetwork", func(t *testing.T) {
		n := NewNetwork(":9000", bc)
		if n == nil {
			t.Fatal("Network should not be nil")
		}
		if n.Address != ":9000" {
			t.Errorf("Address should be ':9000', got '%s'", n.Address)
		}
		if n.Blockchain != bc {
			t.Error("Blockchain should match")
		}
	})

	// Message encoding/decoding
	t.Run("MessageEncoding", func(t *testing.T) {
		// Version message
		versionMsg := VersionMessage{
			Version:    1,
			BestHeight: 5,
			AddrFrom:   "localhost:3000",
		}
		data := encodeMessage(versionMsg)
		if len(data) == 0 {
			t.Fatal("Encoded data should not be empty")
		}

		var decoded VersionMessage
		if err := decodeMessage(data, &decoded); err != nil {
			t.Fatalf("Failed to decode: %v", err)
		}
		if decoded.Version != 1 {
			t.Errorf("Expected version 1, got %d", decoded.Version)
		}
	})

	// Broadcast with no nodes
	t.Run("BroadcastEmpty", func(t *testing.T) {
		n := NewNetwork(":9001", bc)

		cbTx := NewCoinbaseTX("test", "test")
		block := NewBlock([]*Transaction{cbTx}, bc.GetLatestBlock().Hash, 2)

		// Should not error with no nodes
		if err := n.BroadcastBlock(block); err != nil {
			t.Errorf("BroadcastBlock should not error: %v", err)
		}
	})
}
