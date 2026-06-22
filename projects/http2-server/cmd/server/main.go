package main

import (
	"crypto/tls"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"github.com/anthropic/http2-server/internal/connection"
	"github.com/anthropic/http2-server/internal/handler"
)

func main() {
	// Parse command line flags
	addr := flag.String("addr", ":8443", "Listen address")
	certFile := flag.String("cert", "server.crt", "TLS certificate file")
	keyFile := flag.String("key", "server.key", "TLS key file")
	flag.Parse()

	// Create default handler
	defaultHandler := handler.NewDefaultHandler()

	// Load TLS certificate
	cert, err := tls.LoadX509KeyPair(*certFile, *keyFile)
	if err != nil {
		log.Fatalf("Failed to load TLS certificate: %v", err)
	}

	// Create TLS config
	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		NextProtos:   []string{"h2"}, // HTTP/2 only
	}

	// Create listener
	listener, err := tls.Listen("tcp", *addr, tlsConfig)
	if err != nil {
		log.Fatalf("Failed to create listener: %v", err)
	}
	defer listener.Close()

	log.Printf("HTTP/2 server listening on %s", *addr)

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Println("Shutting down server...")
		listener.Close()
		os.Exit(0)
	}()

	// Accept connections
	for {
		conn, err := listener.Accept()
		if err != nil {
			// Check if listener was closed
			if opErr, ok := err.(*net.OpError); ok && opErr.Err.Error() == "use of closed network connection" {
				break
			}
			log.Printf("Failed to accept connection: %v", err)
			continue
		}

		go handleConnection(conn, defaultHandler.Handle)
	}
}

func handleConnection(conn net.Conn, handler connection.RequestHandler) {
	defer conn.Close()

	log.Printf("New connection from %s", conn.RemoteAddr())

	// Create HTTP/2 connection
	http2Conn := connection.NewConnection(conn, handler)

	// Start processing
	if err := http2Conn.Start(); err != nil {
		log.Printf("Connection error from %s: %v", conn.RemoteAddr(), err)
	}

	log.Printf("Connection closed from %s", conn.RemoteAddr())
}

func init() {
	// Configure logging
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.SetOutput(os.Stdout)

	fmt.Println("╔═══════════════════════════════════════════════════════════╗")
	fmt.Println("║                   HTTP/2 Server                           ║")
	fmt.Println("║                                                           ║")
	fmt.Println("║   This server implements HTTP/2 protocol with:            ║")
	fmt.Println("║   • Frame parsing and serialization                       ║")
	fmt.Println("║   • HPACK header compression                              ║")
	fmt.Println("║   • Stream multiplexing                                   ║")
	fmt.Println("║   • Flow control                                          ║")
	fmt.Println("║                                                           ║")
	fmt.Println("║   Usage:                                                  ║")
	fmt.Println("║     ./server -addr :8443 -cert server.crt -key server.key ║")
	fmt.Println("║                                                           ║")
	fmt.Println("║   Endpoints:                                              ║")
	fmt.Println("║     GET  /        - Welcome page                          ║")
	fmt.Println("║     GET  /health  - Health check                          ║")
	fmt.Println("║     GET  /info    - Server information                    ║")
	fmt.Println("║     POST /echo    - Echo request body                     ║")
	fmt.Println("╚═══════════════════════════════════════════════════════════╝")
}
