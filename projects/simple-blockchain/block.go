package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/gob"
	"fmt"
	"time"
)

// BlockHeader represents the header of a block
type BlockHeader struct {
	Version       int32    // Version
	PrevBlockHash [32]byte // Previous block hash
	MerkleRoot    [32]byte // Merkle root
	Timestamp     int64    // Timestamp
	Difficulty    uint32   // Difficulty target
	Nonce         uint64   // Nonce
}

// Block represents a block in the blockchain
type Block struct {
	Header       BlockHeader
	Transactions []*Transaction
	Hash         [32]byte
}

// NewBlock creates a new block
func NewBlock(transactions []*Transaction, prevBlockHash [32]byte, difficulty uint32) *Block {
	block := &Block{
		Header: BlockHeader{
			Version:       1,
			PrevBlockHash: prevBlockHash,
			Timestamp:     time.Now().Unix(),
			Difficulty:    difficulty,
			Nonce:         0,
		},
		Transactions: transactions,
	}

	// Calculate merkle root
	block.Header.MerkleRoot = block.CalculateMerkleRoot()

	// Calculate block hash
	block.Hash = block.CalculateHash()

	return block
}

// NewGenesisBlock creates the genesis block
func NewGenesisBlock(coinbase *Transaction, difficulty uint32) *Block {
	return NewBlock([]*Transaction{coinbase}, [32]byte{}, difficulty)
}

// CalculateHash calculates the hash of the block
func (b *Block) CalculateHash() [32]byte {
	var hash [32]byte

	data := bytes.Join(
		[][]byte{
			IntToHex(int64(b.Header.Version)),
			b.Header.PrevBlockHash[:],
			b.Header.MerkleRoot[:],
			IntToHex(b.Header.Timestamp),
			IntToHex(int64(b.Header.Difficulty)),
			IntToHex(int64(b.Header.Nonce)),
		},
		[]byte{},
	)

	hash = sha256.Sum256(data)
	return hash
}

// CalculateMerkleRoot calculates the merkle root of the block's transactions
func (b *Block) CalculateMerkleRoot() [32]byte {
	var transactions [][]byte

	for _, tx := range b.Transactions {
		transactions = append(transactions, tx.ID[:])
	}

	if len(transactions) == 0 {
		return [32]byte{}
	}

	// Build merkle tree
	for len(transactions) > 1 {
		var newLevel [][]byte
		for i := 0; i < len(transactions); i += 2 {
			if i+1 < len(transactions) {
				combined := append(transactions[i], transactions[i+1]...)
				hash := sha256.Sum256(combined)
				newLevel = append(newLevel, hash[:])
			} else {
				combined := append(transactions[i], transactions[i]...)
				hash := sha256.Sum256(combined)
				newLevel = append(newLevel, hash[:])
			}
		}
		transactions = newLevel
	}

	var root [32]byte
	copy(root[:], transactions[0])
	return root
}

// Serialize serializes the block
func (b *Block) Serialize() ([]byte, error) {
	var buf bytes.Buffer
	enc := gob.NewEncoder(&buf)
	err := enc.Encode(b)
	if err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// DeserializeBlock deserializes a block
func DeserializeBlock(data []byte) (*Block, error) {
	var block Block
	buf := bytes.NewBuffer(data)
	dec := gob.NewDecoder(buf)
	err := dec.Decode(&block)
	if err != nil {
		return nil, err
	}
	return &block, nil
}

// Validate validates the block
func (b *Block) Validate() error {
	// Validate hash
	calculatedHash := b.CalculateHash()
	if calculatedHash != b.Hash {
		return fmt.Errorf("invalid block hash")
	}

	// Validate merkle root
	calculatedMerkleRoot := b.CalculateMerkleRoot()
	if calculatedMerkleRoot != b.Header.MerkleRoot {
		return fmt.Errorf("invalid merkle root")
	}

	// Validate transactions
	for _, tx := range b.Transactions {
		if err := tx.Verify(); err != nil {
			return fmt.Errorf("invalid transaction: %v", err)
		}
	}

	return nil
}

// String returns a string representation of the block
func (b *Block) String() string {
	var buf bytes.Buffer
	buf.WriteString(fmt.Sprintf("Block %x\n", b.Hash))
	buf.WriteString(fmt.Sprintf("  Version: %d\n", b.Header.Version))
	buf.WriteString(fmt.Sprintf("  PrevBlockHash: %x\n", b.Header.PrevBlockHash))
	buf.WriteString(fmt.Sprintf("  MerkleRoot: %x\n", b.Header.MerkleRoot))
	buf.WriteString(fmt.Sprintf("  Timestamp: %d\n", b.Header.Timestamp))
	buf.WriteString(fmt.Sprintf("  Difficulty: %d\n", b.Header.Difficulty))
	buf.WriteString(fmt.Sprintf("  Nonce: %d\n", b.Header.Nonce))
	buf.WriteString(fmt.Sprintf("  Transactions: %d\n", len(b.Transactions)))
	for _, tx := range b.Transactions {
		buf.WriteString(fmt.Sprintf("    %x\n", tx.ID))
	}
	return buf.String()
}
