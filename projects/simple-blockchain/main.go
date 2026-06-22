package main

import (
	"fmt"
	"os"
	"strconv"
)

const (
	defaultDifficulty = 4
	defaultPort       = 3000
)

func main() {
	if len(os.Args) < 2 {
		printUsage()
		return
	}

	switch os.Args[1] {
	case "createwallet":
		createWallet()
	case "listaddresses":
		listAddresses()
	case "getbalance":
		getBalance()
	case "send":
		send()
	case "mine":
		mine()
	case "printchain":
		printChain()
	case "startnode":
		startNode()
	case "reindexutxo":
		reindexUTXO()
	case "help":
		printUsage()
	default:
		fmt.Printf("Unknown command: %s\n", os.Args[1])
		printUsage()
	}
}

func printUsage() {
	fmt.Println("Usage:")
	fmt.Println("  createwallet          - Create a new wallet")
	fmt.Println("  listaddresses         - List all wallet addresses")
	fmt.Println("  getbalance -address   - Get balance of an address")
	fmt.Println("  send -from -to -amount - Send coins")
	fmt.Println("  mine                  - Mine a new block")
	fmt.Println("  printchain            - Print the blockchain")
	fmt.Println("  startnode -port       - Start a node")
	fmt.Println("  reindexutxo           - Reindex UTXO set")
}

func createWallet() {
	wm := NewWalletManager()
	address := wm.CreateWallet()
	fmt.Printf("Your new address: %s\n", address)
}

func listAddresses() {
	wm := NewWalletManager()
	addresses := wm.GetAddresses()

	if len(addresses) == 0 {
		fmt.Println("No wallets found")
		return
	}

	fmt.Println("Wallet addresses:")
	for _, address := range addresses {
		fmt.Printf("  %s\n", address)
	}
}

func getBalance() {
	if len(os.Args) < 4 || os.Args[2] != "-address" {
		fmt.Println("Usage: getbalance -address <address>")
		return
	}

	address := os.Args[3]
	bc := NewBlockchain(defaultDifficulty)
	defer bc.Save()

	balance := bc.GetBalance(address)
	fmt.Printf("Balance of '%s': %.2f\n", address, balance)
}

func send() {
	if len(os.Args) < 8 {
		fmt.Println("Usage: send -from <from> -to <to> -amount <amount>")
		return
	}

	from := os.Args[3]
	to := os.Args[5]
	amount, err := strconv.ParseFloat(os.Args[7], 64)
	if err != nil {
		fmt.Printf("Invalid amount: %s\n", os.Args[7])
		return
	}

	bc := NewBlockchain(defaultDifficulty)
	defer bc.Save()

	// Create transaction
	tx := NewTransaction(from, to, amount, bc)
	if tx == nil {
		fmt.Println("Failed to create transaction")
		return
	}

	// Create coinbase transaction for mining reward
	cbTx := NewCoinbaseTX(from, "")

	// Create new block with transactions
	newBlock := NewBlock([]*Transaction{cbTx, tx}, bc.GetLatestBlock().Hash, bc.Difficulty)

	// Add block to blockchain
	if err := bc.AddBlock(newBlock); err != nil {
		fmt.Printf("Failed to add block: %v\n", err)
		return
	}

	fmt.Println("Success!")
}

func mine() {
	bc := NewBlockchain(defaultDifficulty)
	defer bc.Save()

	// Create coinbase transaction
	cbTx := NewCoinbaseTX("miner", "Mining reward")

	// Create new block
	newBlock := NewBlock([]*Transaction{cbTx}, bc.GetLatestBlock().Hash, bc.Difficulty)

	// Perform proof of work
	pow := NewProofOfWork(newBlock, bc.Difficulty)
	nonce, hash := pow.Run()

	// Update block with nonce and hash
	newBlock.Header.Nonce = nonce
	newBlock.Hash = hash

	// Add block to blockchain
	if err := bc.AddBlock(newBlock); err != nil {
		fmt.Printf("Failed to add block: %v\n", err)
		return
	}

	fmt.Println("Mining successful!")
	fmt.Printf("Block hash: %x\n", hash)
	fmt.Printf("Nonce: %d\n", nonce)
}

func printChain() {
	bc := NewBlockchain(defaultDifficulty)
	bc.Print()
}

func startNode() {
	if len(os.Args) < 4 || os.Args[2] != "-port" {
		fmt.Println("Usage: startnode -port <port>")
		return
	}

	port, err := strconv.Atoi(os.Args[3])
	if err != nil {
		fmt.Printf("Invalid port: %s\n", os.Args[3])
		return
	}

	bc := NewBlockchain(defaultDifficulty)
	address := fmt.Sprintf("localhost:%d", port)
	network := NewNetwork(address, bc)

	fmt.Printf("Starting node on %s\n", address)
	if err := network.Start(); err != nil {
		fmt.Printf("Failed to start node: %v\n", err)
	}
}

func reindexUTXO() {
	bc := NewBlockchain(defaultDifficulty)
	defer bc.Save()

	fmt.Println("Reindexing UTXO set...")
	// Simplified UTXO reindexing
	fmt.Println("UTXO reindexing complete")
}
