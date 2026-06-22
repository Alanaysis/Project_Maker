package main

import (
	"testing"
)

func TestProofOfWorkCreation(t *testing.T) {
	cbTx := NewCoinbaseTX("test", "Test")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 2)

	pow := NewProofOfWork(block, 2)

	if pow.Block != block {
		t.Error("PoW block should match")
	}
	if pow.Difficulty != 2 {
		t.Errorf("Expected difficulty 2, got %d", pow.Difficulty)
	}
	if pow.Target == nil {
		t.Error("Target should not be nil")
	}
}

func TestProofOfWorkRun(t *testing.T) {
	cbTx := NewCoinbaseTX("test", "Test")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 1)

	pow := NewProofOfWork(block, 1)
	nonce, hash := pow.Run()

	if hash == [32]byte{} {
		t.Error("Hash should not be zero")
	}

	block.Header.Nonce = nonce
	block.Hash = hash

	if !pow.Validate() {
		t.Error("Proof of work should be valid")
	}
}

func TestProofOfWorkValidate(t *testing.T) {
	cbTx := NewCoinbaseTX("test", "Test")
	block := NewBlock([]*Transaction{cbTx}, [32]byte{}, 8)

	pow := NewProofOfWork(block, 8)
	nonce, hash := pow.Run()

	block.Header.Nonce = nonce
	block.Hash = hash

	if !pow.Validate() {
		t.Error("Proof of work should be valid")
	}

	block.Header.Nonce = nonce + 1
	block.Hash = block.CalculateHash()
	if pow.Validate() {
		t.Error("Proof of work with wrong nonce should be invalid")
	}
}

func TestTargetCalculation(t *testing.T) {
	for difficulty := uint32(1); difficulty <= 4; difficulty++ {
		target := GetTarget(difficulty)
		if target == nil {
			t.Errorf("Target for difficulty %d should not be nil", difficulty)
		}

		if difficulty > 1 {
			prevTarget := GetTarget(difficulty - 1)
			if target.Cmp(prevTarget) >= 0 {
				t.Errorf("Target for difficulty %d should be less than for difficulty %d", difficulty, difficulty-1)
			}
		}
	}
}

func TestDifficultyAdjustment(t *testing.T) {
	newDiff := CalculateDifficulty(2, 100, 600)
	if newDiff != 3 {
		t.Errorf("Expected difficulty 3, got %d", newDiff)
	}

	newDiff = CalculateDifficulty(4, 1201, 600)
	if newDiff != 3 {
		t.Errorf("Expected difficulty 3, got %d", newDiff)
	}

	newDiff = CalculateDifficulty(4, 600, 600)
	if newDiff != 4 {
		t.Errorf("Expected difficulty 4, got %d", newDiff)
	}

	newDiff = CalculateDifficulty(1, 1200, 600)
	if newDiff != 1 {
		t.Errorf("Expected difficulty 1, got %d", newDiff)
	}
}

func TestHashDifficulty(t *testing.T) {
	var hash [32]byte
	hash[0] = 0x00
	hash[1] = 0x00
	hash[2] = 0x0F

	difficulty := HashDifficulty(hash)
	if difficulty != 20 {
		t.Errorf("Expected difficulty 20, got %d", difficulty)
	}

	hash[0] = 0xFF
	difficulty = HashDifficulty(hash)
	if difficulty != 0 {
		t.Errorf("Expected difficulty 0, got %d", difficulty)
	}
}
