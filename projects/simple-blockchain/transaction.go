package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/gob"
	"fmt"
	"time"
)

// TxInput represents a transaction input
type TxInput struct {
	TxID      [32]byte // Transaction ID
	OutIndex  int      // Output index
	Signature []byte   // Signature
	PubKey    []byte   // Public key
}

// TxOutput represents a transaction output
type TxOutput struct {
	Value      float64 // Amount
	PubKeyHash []byte  // Public key hash
}

// Transaction represents a blockchain transaction
type Transaction struct {
	ID        [32]byte    // Transaction ID
	Inputs    []*TxInput  // Transaction inputs
	Outputs   []*TxOutput // Transaction outputs
	Timestamp int64       // Timestamp
}

// NewCoinbaseTX creates a new coinbase transaction
func NewCoinbaseTX(to, data string) *Transaction {
	if data == "" {
		data = fmt.Sprintf("Reward to '%s'", to)
	}

	txIn := &TxInput{
		TxID:      [32]byte{},
		OutIndex:  -1,
		Signature: nil,
		PubKey:    []byte(data),
	}

	txOut := &TxOutput{
		Value:      10.0, // Mining reward
		PubKeyHash: []byte(to),
	}

	tx := &Transaction{
		ID:        [32]byte{},
		Inputs:    []*TxInput{txIn},
		Outputs:   []*TxOutput{txOut},
		Timestamp: time.Now().Unix(),
	}
	tx.ID = tx.Hash()

	return tx
}

// NewTransaction creates a new transaction
func NewTransaction(from, to string, amount float64, blockchain *Blockchain) *Transaction {
	var inputs []*TxInput
	var outputs []*TxOutput

	acc, validOutputs := blockchain.FindSpendableOutputs(from, amount)

	if acc < amount {
		fmt.Println("ERROR: Not enough funds")
		return nil
	}

	for txid, outs := range validOutputs {
		txID, _ := StringToHash(txid)
		for _, out := range outs {
			input := &TxInput{
				TxID:      txID,
				OutIndex:  out,
				Signature: nil,
				PubKey:    []byte(from),
			}
			inputs = append(inputs, input)
		}
	}

	outputs = append(outputs, &TxOutput{
		Value:      amount,
		PubKeyHash: []byte(to),
	})

	if acc > amount {
		outputs = append(outputs, &TxOutput{
			Value:      acc - amount,
			PubKeyHash: []byte(from),
		})
	}

	tx := &Transaction{
		ID:        [32]byte{},
		Inputs:    inputs,
		Outputs:   outputs,
		Timestamp: time.Now().Unix(),
	}
	tx.ID = tx.Hash()

	return tx
}

// Hash returns the hash of the transaction
func (tx *Transaction) Hash() [32]byte {
	var hash [32]byte

	var buf bytes.Buffer
	enc := gob.NewEncoder(&buf)
	err := enc.Encode(tx)
	if err != nil {
		return hash
	}

	hash = sha256.Sum256(buf.Bytes())
	return hash
}

// Serialize serializes the transaction
func (tx *Transaction) Serialize() ([]byte, error) {
	var buf bytes.Buffer
	enc := gob.NewEncoder(&buf)
	err := enc.Encode(tx)
	if err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// Deserialize deserializes a transaction
func DeserializeTransaction(data []byte) (*Transaction, error) {
	var tx Transaction
	buf := bytes.NewBuffer(data)
	dec := gob.NewDecoder(buf)
	err := dec.Decode(&tx)
	if err != nil {
		return nil, err
	}
	return &tx, nil
}

// IsCoinbase checks if the transaction is a coinbase transaction
func (tx *Transaction) IsCoinbase() bool {
	return len(tx.Inputs) == 1 && tx.Inputs[0].TxID == [32]byte{} && tx.Inputs[0].OutIndex == -1
}

// Sign signs the transaction
func (tx *Transaction) Sign(privKey []byte) error {
	// Simplified signing - in real implementation, this would use ECDSA
	// For now, we'll just store the public key hash as signature
	for _, input := range tx.Inputs {
		input.Signature = privKey
	}
	return nil
}

// Verify verifies the transaction signature
func (tx *Transaction) Verify() error {
	// Coinbase transactions don't need signature verification
	if tx.IsCoinbase() {
		return nil
	}
	// Simplified verification
	for _, input := range tx.Inputs {
		if input.Signature == nil {
			return fmt.Errorf("transaction is not signed")
		}
	}
	return nil
}

// String returns a string representation of the transaction
func (tx *Transaction) String() string {
	var buf bytes.Buffer
	buf.WriteString(fmt.Sprintf("Transaction %x\n", tx.ID))
	buf.WriteString(fmt.Sprintf("  Timestamp: %d\n", tx.Timestamp))
	buf.WriteString("  Inputs:\n")
	for _, input := range tx.Inputs {
		buf.WriteString(fmt.Sprintf("    TxID: %x, OutIndex: %d\n", input.TxID, input.OutIndex))
	}
	buf.WriteString("  Outputs:\n")
	for _, output := range tx.Outputs {
		buf.WriteString(fmt.Sprintf("    Value: %.2f, PubKeyHash: %x\n", output.Value, output.PubKeyHash))
	}
	return buf.String()
}
