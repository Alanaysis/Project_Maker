// Network log forwarding example.
//
// This example demonstrates network-based log collection and forwarding:
// 1. Starting a TCP receiver
// 2. Starting a UDP receiver
// 3. Sending logs over TCP/UDP
// 4. Forwarding logs to destinations
//
// Run: go run examples/network_forwarding.go

package main

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/project/log-collector/internal/collector"
	"github.com/project/log-collector/internal/filter"
	"github.com/project/log-collector/internal/forwarder"
	"github.com/project/log-collector/internal/parser"
	"github.com/project/log-collector/internal/storage"
	"github.com/project/log-collector/internal/transport"
)

func main() {
	fmt.Println("=== Log Collector - Network Forwarding Example ===")
	fmt.Println()

	// Step 1: Demonstrate TCP receiver concepts
	fmt.Println("Step 1: TCP Receiver")
	demoTCPReceiver()
	fmt.Println()

	// Step 2: Demonstrate UDP receiver concepts
	fmt.Println("Step 2: UDP Receiver")
	demoUDPReceiver()
	fmt.Println()

	// Step 3: Demonstrate log forwarding
	fmt.Println("Step 3: Log Forwarding")
	demoForwarding()
	fmt.Println()

	// Step 4: Demonstrate network log sending
	fmt.Println("Step 4: Network Log Sending")
	demoNetworkSending()
	fmt.Println()

	fmt.Println("=== Example Complete ===")
}

// demoTCPReceiver demonstrates TCP log reception concepts.
func demoTCPReceiver() {
	fmt.Println("  TCP Receiver Concepts:")
	fmt.Println("  - Listens on a TCP port for incoming log connections")
	fmt.Println("  - Each connection is handled in a separate goroutine")
	fmt.Println("  - Log lines are sent to an output channel")

	// Show what the TCPReceiver does
	tcpReceiver := transport.NewTCPReceiver(":0", make(chan transport.RawLog, 100))
	fmt.Printf("  - Created TCP receiver on address: %s\n", tcpReceiver.Addr())
	fmt.Println("  - Start(): begins accepting connections")
	fmt.Println("  - Each connection spawns handleConn() goroutine")
	fmt.Println("  - handleConn() reads lines with bufio.Scanner")
	fmt.Println("  - Stop(): closes listener and waits for connections to drain")

	// Demonstrate the RawLog structure
	rawLog := transport.RawLog{
		Line:   `{"level":"info","msg":"test","ts":"2024-01-15T10:00:00Z"}`,
		Source: "tcp:192.168.1.100:54321",
		Addr:   "192.168.1.100:54321",
	}
	fmt.Printf("\n  RawLog example:\n")
	fmt.Printf("    Line:   %s\n", rawLog.Line)
	fmt.Printf("    Source: %s\n", rawLog.Source)
	fmt.Printf("    Addr:   %s\n", rawLog.Addr)
}

// demoUDPReceiver demonstrates UDP log reception concepts.
func demoUDPReceiver() {
	fmt.Println("  UDP Receiver Concepts:")
	fmt.Println("  - Listens on a UDP port for incoming log packets")
	fmt.Println("  - Each packet is treated as one log line")
	fmt.Println("  - No connection state (stateless)")

	udpReceiver := transport.NewUDPReceiver(":0", make(chan transport.RawLog, 100))
	fmt.Printf("  - Created UDP receiver on address: %s\n", udpReceiver.Addr())
	fmt.Println("  - Start(): begins listening for packets")
	fmt.Println("  - receive() goroutine reads 65KB max packets")
	fmt.Println("  - Stop(): closes UDP connection")

	// Demonstrate the RawLog structure
	rawLog := transport.RawLog{
		Line:   `2024-01-15 10:00:00 [INFO] test message`,
		Source: "udp:10.0.0.50:12345",
		Addr:   "10.0.0.50:12345",
	}
	fmt.Printf("\n  RawLog example:\n")
	fmt.Printf("    Line:   %s\n", rawLog.Line)
	fmt.Printf("    Source: %s\n", rawLog.Source)
	fmt.Printf("    Addr:   %s\n", rawLog.Addr)
}

// demoForwarding demonstrates log forwarding concepts.
func demoForwarding() {
	fmt.Println("  Forwarder Concepts:")

	// Show batch size configuration
	bs := forwarder.DefaultBatchSize()
	fmt.Printf("  - Default batch size: %d entries or %d bytes, flush every %v\n",
		bs.MaxEntries, bs.MaxBytes, bs.FlushInterval)

	// Show retry configuration
	rc := forwarder.DefaultRetryConfig()
	fmt.Printf("  - Retry config: %d retries, interval %v -> %v (x%.1f)\n",
		rc.MaxRetries, rc.InitialInterval, rc.MaxInterval, rc.BackoffMultiplier)

	// Demonstrate backpressure
	bm := forwarder.NewBackpressureMonitor(1000)
	fmt.Println("\n  - Backpressure thresholds:")
	for _, load := range []int{100, 300, 500, 700, 800, 850, 900, 950} {
		bm.Check(load)
		ratio := bm.GetBackpressureRatio()
		status := "OK"
		if ratio > 0.8 {
			status = "PRESSURE"
		}
		fmt.Printf("    Load: %4d/1000 (%5.1f%%) -> ratio: %.2f [%s]\n",
			load, float64(load)/1000*100, ratio, status)
	}

	// Demonstrate exponential backoff
	fmt.Println("\n  - Exponential backoff schedule:")
	eb := forwarder.NewExponentialBackoff(100*time.Millisecond, 10*time.Second, 2.0)
	for i := 0; i <= 5; i++ {
		fmt.Printf("    Attempt %d: wait %v\n", i, eb.NextInterval(i))
	}

	// Demonstrate forwarder stats
	stats := forwarder.ForwarderStats{
		TotalReceived:  1000,
		TotalForwarded: 950,
		TotalFailed:    50,
		TotalRetried:   100,
		BatchCount:     10,
	}
	fmt.Printf("\n  - Forwarder stats:\n")
	fmt.Printf("    Received:   %d\n", stats.TotalReceived)
	fmt.Printf("    Forwarded:  %d\n", stats.TotalForwarded)
	fmt.Printf("    Failed:     %d\n", stats.TotalFailed)
	fmt.Printf("    Retried:    %d\n", stats.TotalRetried)
	fmt.Printf("    Success:    %.1f%%\n", float64(stats.TotalForwarded)/float64(stats.TotalReceived)*100)
}

// demoNetworkSending demonstrates sending logs over the network.
func demoNetworkSending() {
	fmt.Println("  Network Log Sending:")

	// Create sample entries
	entries := []forwarder.Entry{
		{
			Timestamp: time.Now(),
			Level:     "INFO",
			Message:   "Application started successfully",
			Source:    "app-server-01",
			Fields:    map[string]string{"version": "1.2.3", "env": "production"},
			Raw:       `{"level":"info","msg":"Application started successfully","version":"1.2.3","env":"production"}`,
		},
		{
			Timestamp: time.Now(),
			Level:     "WARN",
			Message:   "High memory usage detected",
			Source:    "app-server-01",
			Fields:    map[string]string{"memory_pct": "85", "heap_bytes": "1073741824"},
			Raw:       `{"level":"warn","msg":"High memory usage detected","memory_pct":"85","heap_bytes":"1073741824"}`,
		},
		{
			Timestamp: time.Now(),
			Level:     "ERROR",
			Message:   "Connection timeout to database",
			Source:    "app-server-02",
			Fields:    map[string]string{"host": "db-primary", "timeout_ms": "30000"},
			Raw:       `{"level":"error","msg":"Connection timeout to database","host":"db-primary","timeout_ms":"30000"}`,
		},
	}

	// Show formatted output
	fmt.Println("  Formatted log lines for network transmission:")
	for _, e := range entries {
		line := fmt.Sprintf("%s %-5s [%s] %s",
			e.Timestamp.Format("2006-01-02 15:04:05"),
			e.Level, e.Source, e.Message)
		fmt.Printf("    %s\n", line)
	}

	// Demonstrate TCP sender
	fmt.Println("\n  TCP Sender Usage:")
	tcpSender := forwarder.NewTCPSender("localhost:5514")
	fmt.Printf("    Address: %s\n", tcpSender.Addr())
	fmt.Printf("    Name: %s\n", tcpSender.Name())
	fmt.Printf("    IsHealthy: %v\n", tcpSender.IsHealthy())

	// Demonstrate UDP sender
	fmt.Println("\n  UDP Sender Usage:")
	udpSender := &transport.UDPSender{}
	_ = udpSender
	fmt.Println("    Address: localhost:5515")
	fmt.Println("    Name: udp:localhost:5515")
	fmt.Println("    Each packet = one log line")

	// Demonstrate the full pipeline
	fmt.Println("\n  Full Network Pipeline:")
	fmt.Println("  ┌──────────┐     ┌────────────┐     ┌──────────┐     ┌─────────────┐")
	fmt.Println("  │ Log File │────▶│ TCP/UDP    │────▶│ Forwarder│────▶│ Central     │")
	fmt.Println("  │ / App    │     │ Receiver   │     │ (batch,  │     │ Log Server  │")
	fmt.Println("  │          │     │ :5514/:5515│     │ retry)   │     │ :5514       │")
	fmt.Println("  └──────────┘     └────────────┘     └──────────┘     └─────────────┘")
}

// Helper function to get TCP listener address (for documentation).
func getListenerAddr(ln net.Listener) string {
	if ln != nil {
		return ln.Addr().String()
	}
	return "not started"
}

// startNetworkDemo starts a simple TCP/UDP demo server and client.
func startNetworkDemo() {
	fmt.Println("\n=== Network Demo (interactive) ===")
	fmt.Println("Starting TCP receiver on :5514...")
	fmt.Println("Starting UDP receiver on :5515...")
	fmt.Println("Type messages to send to TCP receiver:")
	fmt.Println("Press Ctrl+C to exit")

	// Create a TCP listener
	ln, err := net.Listen("tcp", ":5514")
	if err != nil {
		fmt.Printf("Failed to start TCP listener: %v\n", err)
		return
	}
	defer ln.Close()

	// Create a UDP listener
	udpAddr, _ := net.ResolveUDPAddr("udp", ":5515")
	udpConn, err := net.ListenUDP("udp", udpAddr)
	if err != nil {
		fmt.Printf("Failed to start UDP listener: %v\n", err)
		return
	}
	defer udpConn.Close()

	// Accept TCP connections in background
	go func() {
		for {
			conn, err := ln.Accept()
			if err != nil {
				return
			}
			go handleTCP(conn)
		}
	}()

	// Read UDP packets in background
	go func() {
		buf := make([]byte, 65535)
		for {
			n, addr, err := udpConn.ReadFromUDP(buf)
			if err != nil {
				return
			}
			fmt.Printf("\n[UDP from %s] %s\n", addr.String(), string(buf[:n]))
		}
	}()

	fmt.Printf("TCP listening on %s\n", getListenerAddr(ln))
	fmt.Println("UDP listening on :5515")

	// Interactive input
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	scanner := bufio.NewScanner(os.Stdin)
	for {
		select {
		case <-sigChan:
			fmt.Println("\nShutting down...")
			return
		default:
			fmt.Print("> ")
			if scanner.Scan() {
				line := scanner.Text()
				if line == "quit" || line == "exit" {
					return
				}
				// Send to TCP
				conn, err := net.Dial("tcp", "localhost:5514")
				if err == nil {
					conn.Write([]byte(line + "\n"))
					conn.Close()
				}
				// Send to UDP
				udpConn.WriteToUDP([]byte(line+"\n"), udpAddr)
			}
		}
	}
}

// handleTCP handles a single TCP connection.
func handleTCP(conn net.Conn) {
	defer conn.Close()
	scanner := bufio.NewScanner(conn)
	for scanner.Scan() {
		line := scanner.Text()
		fmt.Printf("\n[TCP from %s] %s\n", conn.RemoteAddr().String(), line)
	}
}
