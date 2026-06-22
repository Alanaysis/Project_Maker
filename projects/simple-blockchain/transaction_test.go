package main

import (
	"testing"
)

func TestCoinbaseTransaction(t *testing.T) {
	tx := NewCoinbaseTX("test-address", "Test data")

	if tx.ID == [32]byte{} {
		t.Error("Transaction ID should not be zero")
	}
	if len(tx.Inputs) != 1 {
		t.Errorf("Expected 1 input, got %d", len(tx.Inputs))
	}
	if len(tx.Outputs) != 1 {
		t.Errorf("Expected 1 output, got %d", len(tx.Outputs))
	}

	input := tx.Inputs[0]
	if input.OutIndex != -1 {
		t.Errorf("Expected out index -1, got %d", input.OutIndex)
	}

	output := tx.Outputs[0]
	if output.Value != 10.0 {
		t.Errorf("Expected value 10.0, got %.2f", output.Value)
	}
	if string(output.PubKeyHash) != "test-address" {
		t.Errorf("Expected address 'test-address', got '%s'", string(output.PubKeyHash))
	}
}

func TestTransactionHash(t *testing.T) {
	tx1 := NewCoinbaseTX("address1", "Data 1")
	tx2 := NewCoinbaseTX("address2", "Data 2")

	if tx1.ID == tx2.ID {
		t.Error("Different transactions should have different hashes")
	}

	if tx1.ID == [32]byte{} || tx2.ID == [32]byte{} {
		t.Error("Transaction IDs should not be zero")
	}
}

func TestTransactionSerialization(t *testing.T) {
	tx := NewCoinbaseTX("test-address", "Test data")

	data, err := tx.Serialize()
	if err != nil {
		t.Fatalf("Failed to serialize transaction: %v", err)
	}

	loadedTx, err := DeserializeTransaction(data)
	if err != nil {
		t.Fatalf("Failed to deserialize transaction: %v", err)
	}

	if loadedTx.ID != tx.ID {
		t.Error("Deserialized transaction ID should match original")
	}
	if len(loadedTx.Inputs) != len(tx.Inputs) {
		t.Error("Deserialized transaction inputs count should match")
	}
	if len(loadedTx.Outputs) != len(tx.Outputs) {
		t.Error("Deserialized transaction outputs count should match")
	}
}

func TestTransactionIsCoinbase(t *testing.T) {
	coinbase := NewCoinbaseTX("test", "Test")
	if !coinbase.IsCoinbase() {
		t.Error("Should be identified as coinbase transaction")
	}
}

func TestTransactionSign(t *testing.T) {
	tx := NewCoinbaseTX("test-address", "Test data")

	err := tx.Sign([]byte("test-key"))
	if err != nil {
		t.Fatalf("Failed to sign transaction: %v", err)
	}

	for _, input := range tx.Inputs {
		if input.Signature == nil {
			t.Error("Input should have signature after signing")
		}
	}
}

func TestTransactionVerify(t *testing.T) {
	// Coinbase transactions should pass verification without signing
	cbTx := NewCoinbaseTX("test-address", "Test data")
	err := cbTx.Verify()
	if err != nil {
		t.Errorf("Coinbase transaction should pass verification: %v", err)
	}

	// Sign and verify should still work
	cbTx.Sign([]byte("test-key"))
	err = cbTx.Verify()
	if err != nil {
		t.Errorf("Signed coinbase transaction should pass verification: %v", err)
	}
}

func TestTransactionTimestamp(t *testing.T) {
	tx := NewCoinbaseTX("test-address", "Test data")

	if tx.Timestamp == 0 {
		t.Error("Transaction timestamp should not be zero")
	}
}
