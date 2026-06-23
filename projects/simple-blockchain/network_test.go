package main

import (
	"bytes"
	"encoding/gob"
	"os"
	"testing"
)

func TestNewNetwork(t *testing.T) {
	// Clean up blockchain.dat from working dir
	defer func() {
		_ = removeTestFiles()
	}()

	bc := &Blockchain{
		Blocks:     make([]*Block, 0),
		Difficulty: 2,
	}
	cbTx := NewCoinbaseTX("genesis", "Genesis Block")
	genesis := NewGenesisBlock(cbTx, 2)
	bc.Blocks = append(bc.Blocks, genesis)

	n := NewNetwork(":9000", bc)
	if n == nil {
		t.Fatal("NewNetwork should not return nil")
	}
	if n.Address != ":9000" {
		t.Errorf("Address should be ':9000', got '%s'", n.Address)
	}
	if n.Blockchain != bc {
		t.Error("Blockchain should match the one provided")
	}
	if len(n.Nodes) != 0 {
		t.Error("New network should have no nodes")
	}
}

func TestNetworkAddRemoveNode(t *testing.T) {
	bc := &Blockchain{
		Blocks:     make([]*Block, 0),
		Difficulty: 2,
	}
	cbTx := NewCoinbaseTX("genesis", "Genesis Block")
	genesis := NewGenesisBlock(cbTx, 2)
	bc.Blocks = append(bc.Blocks, genesis)

	n := NewNetwork(":9001", bc)

	// Use a pipe to simulate a connection for testing addNode
	// We can't easily test with real net.Conn, so test the map directly
	n.mu.Lock()
	n.Nodes["test:8000"] = &Node{
		Address: "test:8000",
		Version: 1,
		Height:  1,
	}
	n.mu.Unlock()

	if len(n.Nodes) != 1 {
		t.Errorf("Should have 1 node, got %d", len(n.Nodes))
	}

	// Remove node
	n.mu.Lock()
	delete(n.Nodes, "test:8000")
	n.mu.Unlock()

	if len(n.Nodes) != 0 {
		t.Errorf("Should have 0 nodes after removal, got %d", len(n.Nodes))
	}
}

func TestEncodeDecodeMessage(t *testing.T) {
	original := VersionMessage{
		Version:    1,
		BestHeight: 5,
		AddrFrom:   "localhost:3000",
	}

	data := encodeMessage(original)
	if len(data) == 0 {
		t.Fatal("encodeMessage should return non-empty data")
	}

	var decoded VersionMessage
	err := decodeMessage(data, &decoded)
	if err != nil {
		t.Fatalf("decodeMessage failed: %v", err)
	}

	if decoded.Version != original.Version {
		t.Errorf("Version should be %d, got %d", original.Version, decoded.Version)
	}
	if decoded.BestHeight != original.BestHeight {
		t.Errorf("BestHeight should be %d, got %d", original.BestHeight, decoded.BestHeight)
	}
	if decoded.AddrFrom != original.AddrFrom {
		t.Errorf("AddrFrom should be '%s', got '%s'", original.AddrFrom, decoded.AddrFrom)
	}
}

func TestEncodeDecodeInvMessage(t *testing.T) {
	original := InvMessage{
		Type:  "block",
		Items: [][]byte{[]byte("hash1"), []byte("hash2")},
	}

	data := encodeMessage(original)
	if len(data) == 0 {
		t.Fatal("encodeMessage should return non-empty data")
	}

	var decoded InvMessage
	err := decodeMessage(data, &decoded)
	if err != nil {
		t.Fatalf("decodeMessage failed: %v", err)
	}

	if decoded.Type != "block" {
		t.Errorf("Type should be 'block', got '%s'", decoded.Type)
	}
	if len(decoded.Items) != 2 {
		t.Errorf("Items should have 2 entries, got %d", len(decoded.Items))
	}
}

func TestSendMessageReadMessage(t *testing.T) {
	// Create an in-memory pipe to test message serialization
	// Using bytes.Buffer as a stand-in for testing gob encode/decode
	var buf bytes.Buffer

	msg := &Message{
		Command: CmdVersion,
		Data: encodeMessage(VersionMessage{
			Version:    1,
			BestHeight: 10,
			AddrFrom:   "127.0.0.1:3000",
		}),
	}

	// Encode
	encoder := gob.NewEncoder(&buf)
	if err := encoder.Encode(msg); err != nil {
		t.Fatalf("Failed to encode message: %v", err)
	}

	// Decode
	decoded := &Message{}
	decoder := gob.NewDecoder(&buf)
	if err := decoder.Decode(decoded); err != nil {
		t.Fatalf("Failed to decode message: %v", err)
	}

	if decoded.Command != CmdVersion {
		t.Errorf("Command should be '%s', got '%s'", CmdVersion, decoded.Command)
	}
	if len(decoded.Data) == 0 {
		t.Error("Decoded message data should not be empty")
	}

	// Decode the inner data
	var versionMsg VersionMessage
	if err := decodeMessage(decoded.Data, &versionMsg); err != nil {
		t.Fatalf("Failed to decode inner version message: %v", err)
	}
	if versionMsg.Version != 1 {
		t.Errorf("Inner Version should be 1, got %d", versionMsg.Version)
	}
}

func TestMessageCommandConstants(t *testing.T) {
	// Verify command constants are distinct
	commands := []string{CmdVersion, CmdVerack, CmdTx, CmdBlock, CmdGetBlocks, CmdInv}
	seen := make(map[string]bool)
	for _, cmd := range commands {
		if seen[cmd] {
			t.Errorf("Duplicate command constant: %s", cmd)
		}
		seen[cmd] = true
	}

	// Verify lengths
	for _, cmd := range commands {
		if len(cmd) == 0 {
			t.Error("Command constant should not be empty")
		}
	}
}

func TestNodeStruct(t *testing.T) {
	node := &Node{
		Address:    "127.0.0.1:3000",
		Version:    1,
		Height:     5,
		Connection: nil,
	}

	if node.Address != "127.0.0.1:3000" {
		t.Errorf("Address should be '127.0.0.1:3000', got '%s'", node.Address)
	}
	if node.Version != 1 {
		t.Errorf("Version should be 1, got %d", node.Version)
	}
	if node.Height != 5 {
		t.Errorf("Height should be 5, got %d", node.Height)
	}
}

func TestNetworkBroadcastWithNoNodes(t *testing.T) {
	bc := &Blockchain{
		Blocks:     make([]*Block, 0),
		Difficulty: 2,
	}
	cbTx := NewCoinbaseTX("genesis", "Genesis Block")
	genesis := NewGenesisBlock(cbTx, 2)
	bc.Blocks = append(bc.Blocks, genesis)

	n := NewNetwork(":9002", bc)

	// Broadcasting to no nodes should not error
	block := NewBlock([]*Transaction{cbTx}, genesis.Hash, 2)
	err := n.BroadcastBlock(block)
	if err != nil {
		t.Errorf("BroadcastBlock with no nodes should not error: %v", err)
	}

	tx := NewCoinbaseTX("test", "test tx")
	err = n.BroadcastTx(tx)
	if err != nil {
		t.Errorf("BroadcastTx with no nodes should not error: %v", err)
	}
}

func removeTestFiles() error {
	os.Remove("blockchain.dat")
	os.Remove("blockchain.dat.tmp")
	return nil
}
