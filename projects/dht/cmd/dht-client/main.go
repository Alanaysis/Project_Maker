package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"

	"github.com/dht-chord/internal"
)

func main() {
	// Command line flags
	serverAddr := flag.String("server", "localhost:8000", "DHT server address")
	filesDir := flag.String("dir", "./shared_files", "Shared files directory")
	action := flag.String("action", "list", "Action: share, download, search, list")
	filePath := flag.String("file", "", "File path for share/download")
	query := flag.String("query", "", "Search query")
	flag.Parse()

	fmt.Println("=== P2P File Sharing Client ===")

	// Create network node for client
	node := internal.NewNetworkNode("localhost:0") // Random port
	if err := node.Start(); err != nil {
		log.Fatalf("Failed to start client node: %v", err)
	}
	defer node.Stop()

	// Connect to server
	if err := node.Ping(*serverAddr); err != nil {
		log.Fatalf("Failed to connect to server: %v", err)
	}
	fmt.Printf("Connected to server: %s\n", *serverAddr)

	// Create P2P network
	p2p, err := internal.NewP2PNetwork(node, *filesDir)
	if err != nil {
		log.Fatalf("Failed to create P2P network: %v", err)
	}

	switch *action {
	case "share":
		if *filePath == "" {
			log.Fatal("File path required for share action")
		}
		absPath, err := filepath.Abs(*filePath)
		if err != nil {
			log.Fatalf("Invalid file path: %v", err)
		}
		info, err := p2p.ShareFile(absPath)
		if err != nil {
			log.Fatalf("Failed to share file: %v", err)
		}
		fmt.Printf("File shared successfully:\n")
		fmt.Printf("  Name: %s\n", info.Name)
		fmt.Printf("  Hash: %s\n", info.Hash)
		fmt.Printf("  Size: %d bytes\n", info.Size)

	case "download":
		if *filePath == "" {
			log.Fatal("File hash required for download action")
		}
		path, err := p2p.DownloadFile(*filePath)
		if err != nil {
			log.Fatalf("Failed to download file: %v", err)
		}
		fmt.Printf("File downloaded to: %s\n", path)

	case "search":
		if *query == "" {
			log.Fatal("Query required for search action")
		}
		results := p2p.SearchFiles(*query)
		if len(results) == 0 {
			fmt.Println("No files found")
		} else {
			fmt.Printf("Found %d files:\n", len(results))
			for _, info := range results {
				fmt.Printf("  %s (hash: %s, size: %d bytes)\n", info.Name, info.Hash, info.Size)
			}
		}

	case "list":
		files := p2p.ListFiles()
		if len(files) == 0 {
			fmt.Println("No files shared")
		} else {
			fmt.Printf("Shared files (%d):\n", len(files))
			for _, info := range files {
				fmt.Printf("  %s (hash: %s, size: %d bytes)\n", info.Name, info.Hash, info.Size)
			}
		}

	default:
		fmt.Printf("Unknown action: %s\n", *action)
		os.Exit(1)
	}
}
