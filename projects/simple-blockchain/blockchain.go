package main

import (
	"encoding/hex"
	"fmt"
	"os"
	"sync"
)

const (
	dbFile      = "blockchain.dat"
	dbFileTemp  = "blockchain.dat.tmp"
	genesisData = "Genesis Block"
)

// Blockchain represents the blockchain
type Blockchain struct {
	Blocks     []*Block
	Difficulty uint32
	mu         sync.RWMutex
}

// NewBlockchain creates a new blockchain
func NewBlockchain(difficulty uint32) *Blockchain {
	bc := &Blockchain{
		Blocks:     make([]*Block, 0),
		Difficulty: difficulty,
	}

	// Try to load existing blockchain
	if err := bc.Load(); err != nil {
		// Create genesis block
		coinbase := NewCoinbaseTX("genesis", genesisData)
		genesis := NewGenesisBlock(coinbase, difficulty)
		bc.Blocks = append(bc.Blocks, genesis)
		fmt.Println("Created new blockchain with genesis block")
	} else {
		fmt.Println("Loaded existing blockchain")
	}

	return bc
}

// AddBlock adds a new block to the blockchain
func (bc *Blockchain) AddBlock(block *Block) error {
	bc.mu.Lock()
	defer bc.mu.Unlock()

	// Validate block
	if err := block.Validate(); err != nil {
		return fmt.Errorf("invalid block: %v", err)
	}

	// Check if block references the latest block (use internal access to avoid deadlock)
	if len(bc.Blocks) == 0 {
		return fmt.Errorf("blockchain has no blocks")
	}
	latestBlock := bc.Blocks[len(bc.Blocks)-1]
	if block.Header.PrevBlockHash != latestBlock.Hash {
		return fmt.Errorf("block does not reference the latest block")
	}

	// Add block
	bc.Blocks = append(bc.Blocks, block)

	// Save blockchain
	if err := bc.Save(); err != nil {
		return fmt.Errorf("failed to save blockchain: %v", err)
	}

	return nil
}

// GetLatestBlock returns the latest block
func (bc *Blockchain) GetLatestBlock() *Block {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	if len(bc.Blocks) == 0 {
		return nil
	}
	return bc.Blocks[len(bc.Blocks)-1]
}

// GetBlock returns a block by hash
func (bc *Blockchain) GetBlock(hash [32]byte) (*Block, error) {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	for _, block := range bc.Blocks {
		if block.Hash == hash {
			return block, nil
		}
	}
	return nil, fmt.Errorf("block not found")
}

// GetBlockByHeight returns a block by height
func (bc *Blockchain) GetBlockByHeight(height int) (*Block, error) {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	if height < 0 || height >= len(bc.Blocks) {
		return nil, fmt.Errorf("invalid block height")
	}
	return bc.Blocks[height], nil
}

// GetHeight returns the height of the blockchain
func (bc *Blockchain) GetHeight() int {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	return len(bc.Blocks)
}

// ValidateChain validates the entire blockchain
func (bc *Blockchain) ValidateChain() error {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	for i := 1; i < len(bc.Blocks); i++ {
		block := bc.Blocks[i]
		prevBlock := bc.Blocks[i-1]

		// Validate block
		if err := block.Validate(); err != nil {
			return fmt.Errorf("invalid block at height %d: %v", i, err)
		}

		// Check if block references the previous block
		if block.Header.PrevBlockHash != prevBlock.Hash {
			return fmt.Errorf("block at height %d does not reference the previous block", i)
		}
	}

	return nil
}

// FindSpendableOutputs finds spendable outputs for an address
func (bc *Blockchain) FindSpendableOutputs(address string, amount float64) (float64, map[string][]int) {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	unspentOutputs := make(map[string][]int)
	accumulated := 0.0

	for _, block := range bc.Blocks {
		for _, tx := range block.Transactions {
			txID := hex.EncodeToString(tx.ID[:])

			for outIdx, output := range tx.Outputs {
				if string(output.PubKeyHash) == address {
					accumulated += output.Value
					unspentOutputs[txID] = append(unspentOutputs[txID], outIdx)
				}
			}
		}
	}

	return accumulated, unspentOutputs
}

// FindUTXO finds all unspent transaction outputs for an address
func (bc *Blockchain) FindUTXO(address string) []*TxOutput {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	var utxos []*TxOutput

	for _, block := range bc.Blocks {
		for _, tx := range block.Transactions {
			for _, output := range tx.Outputs {
				if string(output.PubKeyHash) == address {
					utxos = append(utxos, output)
				}
			}
		}
	}

	return utxos
}

// GetBalance returns the balance of an address
func (bc *Blockchain) GetBalance(address string) float64 {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	balance := 0.0
	utxos := bc.FindUTXO(address)

	for _, utxo := range utxos {
		balance += utxo.Value
	}

	return balance
}

// Save saves the blockchain to disk
func (bc *Blockchain) Save() error {
	data, err := bc.Serialize()
	if err != nil {
		return err
	}

	// Write to temp file first
	if err := os.WriteFile(dbFileTemp, data, 0644); err != nil {
		return err
	}

	// Rename temp file to actual file
	return os.Rename(dbFileTemp, dbFile)
}

// Load loads the blockchain from disk
func (bc *Blockchain) Load() error {
	data, err := os.ReadFile(dbFile)
	if err != nil {
		return err
	}

	return bc.Deserialize(data)
}

// Serialize serializes the blockchain
func (bc *Blockchain) Serialize() ([]byte, error) {
	var result []byte

	// Serialize difficulty
	result = append(result, IntToHex(int64(bc.Difficulty))...)

	// Serialize number of blocks
	result = append(result, IntToHex(int64(len(bc.Blocks)))...)

	// Serialize each block
	for _, block := range bc.Blocks {
		blockData, err := block.Serialize()
		if err != nil {
			return nil, err
		}
		// Add block length
		result = append(result, IntToHex(int64(len(blockData)))...)
		result = append(result, blockData...)
	}

	return result, nil
}

// Deserialize deserializes the blockchain
func (bc *Blockchain) Deserialize(data []byte) error {
	if len(data) < 16 {
		return fmt.Errorf("invalid blockchain data")
	}

	// Read difficulty
	bc.Difficulty = uint32(BytesToInt(data[:8]))

	// Read number of blocks
	numBlocks := int(BytesToInt(data[8:16]))
	offset := 16

	bc.Blocks = make([]*Block, 0, numBlocks)

	// Read each block
	for i := 0; i < numBlocks; i++ {
		if offset+8 > len(data) {
			return fmt.Errorf("invalid blockchain data")
		}

		blockLen := int(BytesToInt(data[offset : offset+8]))
		offset += 8

		if offset+blockLen > len(data) {
			return fmt.Errorf("invalid blockchain data")
		}

		block, err := DeserializeBlock(data[offset : offset+blockLen])
		if err != nil {
			return err
		}

		bc.Blocks = append(bc.Blocks, block)
		offset += blockLen
	}

	return nil
}

// Print prints the blockchain
func (bc *Blockchain) Print() {
	bc.mu.RLock()
	defer bc.mu.RUnlock()

	for i, block := range bc.Blocks {
		fmt.Printf("Block %d:\n", i)
		fmt.Println(block)
	}
}
