package main

import (
	"bytes"
	"encoding/gob"
	"fmt"
	"log"
	"net"
	"sync"
)

const (
	protocol      = "tcp"
	nodeVersion   = 1
	commandLength = 12
)

// Message types
const (
	CmdVersion   = "version"
	CmdVerack    = "verack"
	CmdTx        = "tx"
	CmdBlock     = "block"
	CmdGetBlocks = "getblocks"
	CmdInv       = "inv"
)

// Message represents a network message
type Message struct {
	Command string
	Data    []byte
}

// VersionMessage represents a version message
type VersionMessage struct {
	Version    int32
	BestHeight int
	AddrFrom   string
}

// BlockMessage represents a block message
type BlockMessage struct {
	Block *Block
}

// TxMessage represents a transaction message
type TxMessage struct {
	Tx *Transaction
}

// InvMessage represents an inventory message
type InvMessage struct {
	Type  string
	Items [][]byte
}

// Node represents a network node
type Node struct {
	Address    string
	Connection net.Conn
	Version    int32
	Height     int
}

// Network represents the P2P network
type Network struct {
	Nodes      map[string]*Node
	Blockchain *Blockchain
	mu         sync.RWMutex
	Address    string
}

// NewNetwork creates a new network
func NewNetwork(address string, blockchain *Blockchain) *Network {
	return &Network{
		Nodes:      make(map[string]*Node),
		Blockchain: blockchain,
		Address:    address,
	}
}

// Start starts the network node
func (n *Network) Start() error {
	ln, err := net.Listen(protocol, n.Address)
	if err != nil {
		return err
	}
	defer ln.Close()

	fmt.Printf("Node started on %s\n", n.Address)

	for {
		conn, err := ln.Accept()
		if err != nil {
			log.Printf("Error accepting connection: %v", err)
			continue
		}

		go n.handleConnection(conn)
	}
}

// handleConnection handles an incoming connection
func (n *Network) handleConnection(conn net.Conn) {
	defer conn.Close()

	// Read message
	msg, err := readMessage(conn)
	if err != nil {
		log.Printf("Error reading message: %v", err)
		return
	}

	// Handle message
	switch msg.Command {
	case CmdVersion:
		n.handleVersion(conn, msg)
	case CmdVerack:
		n.handleVerack(conn, msg)
	case CmdTx:
		n.handleTx(conn, msg)
	case CmdBlock:
		n.handleBlock(conn, msg)
	case CmdGetBlocks:
		n.handleGetBlocks(conn, msg)
	case CmdInv:
		n.handleInv(conn, msg)
	default:
		log.Printf("Unknown command: %s", msg.Command)
	}
}

// handleVersion handles a version message
func (n *Network) handleVersion(conn net.Conn, msg *Message) {
	var versionMsg VersionMessage
	if err := decodeMessage(msg.Data, &versionMsg); err != nil {
		log.Printf("Error decoding version message: %v", err)
		return
	}

	// Add node
	n.addNode(conn.RemoteAddr().String(), conn, versionMsg.Version, versionMsg.BestHeight)

	// Send version ack
	verackMsg := &Message{
		Command: CmdVerack,
		Data:    []byte{},
	}
	if err := sendMessage(conn, verackMsg); err != nil {
		log.Printf("Error sending verack: %v", err)
	}
}

// handleVerack handles a version ack message
func (n *Network) handleVerack(conn net.Conn, msg *Message) {
	// Version acknowledged
	fmt.Printf("Node %s acknowledged\n", conn.RemoteAddr().String())
}

// handleTx handles a transaction message
func (n *Network) handleTx(conn net.Conn, msg *Message) {
	var txMsg TxMessage
	if err := decodeMessage(msg.Data, &txMsg); err != nil {
		log.Printf("Error decoding transaction message: %v", err)
		return
	}

	// Verify transaction
	if err := txMsg.Tx.Verify(); err != nil {
		log.Printf("Invalid transaction: %v", err)
		return
	}

	// Add to transaction pool (simplified)
	fmt.Printf("Received transaction: %x\n", txMsg.Tx.ID)
}

// handleBlock handles a block message
func (n *Network) handleBlock(conn net.Conn, msg *Message) {
	var blockMsg BlockMessage
	if err := decodeMessage(msg.Data, &blockMsg); err != nil {
		log.Printf("Error decoding block message: %v", err)
		return
	}

	// Add block to blockchain
	if err := n.Blockchain.AddBlock(blockMsg.Block); err != nil {
		log.Printf("Error adding block: %v", err)
		return
	}

	fmt.Printf("Received block: %x\n", blockMsg.Block.Hash)
}

// handleGetBlocks handles a getblocks message
func (n *Network) handleGetBlocks(conn net.Conn, msg *Message) {
	// Send inventory of blocks
	blocks := make([][]byte, 0)
	for _, block := range n.Blockchain.Blocks {
		blocks = append(blocks, block.Hash[:])
	}

	invMsg := &Message{
		Command: CmdInv,
		Data:    encodeMessage(InvMessage{Type: "block", Items: blocks}),
	}
	if err := sendMessage(conn, invMsg); err != nil {
		log.Printf("Error sending inventory: %v", err)
	}
}

// handleInv handles an inventory message
func (n *Network) handleInv(conn net.Conn, msg *Message) {
	var invMsg InvMessage
	if err := decodeMessage(msg.Data, &invMsg); err != nil {
		log.Printf("Error decoding inventory message: %v", err)
		return
	}

	fmt.Printf("Received inventory: %d items\n", len(invMsg.Items))
}

// Connect connects to a remote node
func (n *Network) Connect(address string) error {
	conn, err := net.Dial(protocol, address)
	if err != nil {
		return err
	}

	// Send version message
	versionMsg := VersionMessage{
		Version:    nodeVersion,
		BestHeight: n.Blockchain.GetHeight(),
		AddrFrom:   n.Address,
	}

	msg := &Message{
		Command: CmdVersion,
		Data:    encodeMessage(versionMsg),
	}

	if err := sendMessage(conn, msg); err != nil {
		conn.Close()
		return err
	}

	// Add node
	n.addNode(address, conn, nodeVersion, 0)

	return nil
}

// BroadcastBlock broadcasts a block to all connected nodes
func (n *Network) BroadcastBlock(block *Block) error {
	blockMsg := BlockMessage{Block: block}
	msg := &Message{
		Command: CmdBlock,
		Data:    encodeMessage(blockMsg),
	}

	return n.broadcast(msg)
}

// BroadcastTx broadcasts a transaction to all connected nodes
func (n *Network) BroadcastTx(tx *Transaction) error {
	txMsg := TxMessage{Tx: tx}
	msg := &Message{
		Command: CmdTx,
		Data:    encodeMessage(txMsg),
	}

	return n.broadcast(msg)
}

// broadcast broadcasts a message to all connected nodes
func (n *Network) broadcast(msg *Message) error {
	n.mu.RLock()
	defer n.mu.RUnlock()

	for _, node := range n.Nodes {
		if err := sendMessage(node.Connection, msg); err != nil {
			log.Printf("Error broadcasting to %s: %v", node.Address, err)
		}
	}

	return nil
}

// addNode adds a node to the network
func (n *Network) addNode(address string, conn net.Conn, version int32, height int) {
	n.mu.Lock()
	defer n.mu.Unlock()

	n.Nodes[address] = &Node{
		Address:    address,
		Connection: conn,
		Version:    version,
		Height:     height,
	}
}

// removeNode removes a node from the network
func (n *Network) removeNode(address string) {
	n.mu.Lock()
	defer n.mu.Unlock()

	if node, exists := n.Nodes[address]; exists {
		node.Connection.Close()
		delete(n.Nodes, address)
	}
}

// sendMessage sends a message to a connection
func sendMessage(conn net.Conn, msg *Message) error {
	encoder := gob.NewEncoder(conn)
	return encoder.Encode(msg)
}

// readMessage reads a message from a connection
func readMessage(conn net.Conn) (*Message, error) {
	msg := &Message{}
	decoder := gob.NewDecoder(conn)
	if err := decoder.Decode(msg); err != nil {
		return nil, err
	}
	return msg, nil
}

// encodeMessage encodes a message to bytes
func encodeMessage(data interface{}) []byte {
	var buf bytes.Buffer
	enc := gob.NewEncoder(&buf)
	if err := enc.Encode(data); err != nil {
		log.Printf("Error encoding message: %v", err)
		return nil
	}
	return buf.Bytes()
}

// decodeMessage decodes a message from bytes
func decodeMessage(data []byte, target interface{}) error {
	buf := bytes.NewBuffer(data)
	dec := gob.NewDecoder(buf)
	return dec.Decode(target)
}
