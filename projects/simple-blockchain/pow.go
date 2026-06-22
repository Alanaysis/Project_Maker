package main

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"math"
	"math/big"
)

const maxNonce = math.MaxInt64

// ProofOfWork represents a proof of work
type ProofOfWork struct {
	Block      *Block
	Target     *big.Int
	Difficulty uint32
}

// NewProofOfWork creates a new proof of work
func NewProofOfWork(block *Block, difficulty uint32) *ProofOfWork {
	target := big.NewInt(1)
	target.Lsh(target, uint(256-int(difficulty)))

	return &ProofOfWork{
		Block:      block,
		Target:     target,
		Difficulty: difficulty,
	}
}

// Run performs the proof of work
func (pow *ProofOfWork) Run() (uint64, [32]byte) {
	var hashInt big.Int
	var hash [32]byte
	nonce := uint64(0)

	fmt.Printf("Mining a new block with difficulty %d\n", pow.Difficulty)

	for nonce < maxNonce {
		// Prepare data
		data := pow.prepareData(nonce)

		// Calculate hash
		hash = sha256.Sum256(data)
		hashInt.SetBytes(hash[:])

		// Check if hash meets target
		if hashInt.Cmp(pow.Target) == -1 {
			fmt.Printf("Found nonce: %d\n", nonce)
			return nonce, hash
		}

		nonce++
	}

	fmt.Println("Mining failed: max nonce reached")
	return 0, hash
}

// Validate validates the proof of work
func (pow *ProofOfWork) Validate() bool {
	var hashInt big.Int

	data := pow.prepareData(pow.Block.Header.Nonce)
	hash := sha256.Sum256(data)
	hashInt.SetBytes(hash[:])

	return hashInt.Cmp(pow.Target) == -1
}

// prepareData prepares the data for hashing
func (pow *ProofOfWork) prepareData(nonce uint64) []byte {
	data := bytes.Join(
		[][]byte{
			IntToHex(int64(pow.Block.Header.Version)),
			pow.Block.Header.PrevBlockHash[:],
			pow.Block.Header.MerkleRoot[:],
			IntToHex(pow.Block.Header.Timestamp),
			IntToHex(int64(pow.Block.Header.Difficulty)),
			IntToHex(int64(nonce)),
		},
		[]byte{},
	)

	return data
}

// GetTarget returns the target for the given difficulty
func GetTarget(difficulty uint32) *big.Int {
	target := big.NewInt(1)
	target.Lsh(target, uint(256-int(difficulty)))
	return target
}

// CalculateDifficulty calculates the new difficulty
func CalculateDifficulty(oldDifficulty uint32, actualTime int64, expectedTime int64) uint32 {
	if actualTime < expectedTime/2 {
		return oldDifficulty + 1
	} else if actualTime > expectedTime*2 {
		if oldDifficulty > 1 {
			return oldDifficulty - 1
		}
		return 1
	}
	return oldDifficulty
}

// HashDifficulty returns the number of leading zeros in a hash
func HashDifficulty(hash [32]byte) int {
	difficulty := 0
	for _, b := range hash {
		if b == 0 {
			difficulty += 8
		} else {
			// Count leading zeros in the byte
			for i := 7; i >= 0; i-- {
				if b&(1<<uint(i)) == 0 {
					difficulty++
				} else {
					return difficulty
				}
			}
		}
	}
	return difficulty
}
