package main

import (
	"flag"
	"log"

	"github.com/distributed-game-system/internal/server"
)

func main() {
	addr := flag.String("addr", ":8080", "HTTP service address")
	flag.Parse()

	log.Printf("Starting Distributed Game System on %s", *addr)

	gameServer := server.NewGameServer()
	if err := gameServer.Start(*addr); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
