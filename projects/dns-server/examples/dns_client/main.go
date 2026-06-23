// DNS Client Example
//
// Demonstrates how to build and send DNS queries programmatically using
// the protocol package. This is useful for testing and understanding the
// DNS wire format.
//
// Usage:
//
//	# Start the DNS server first:
//	go run cmd/server/main.go
//
//	# Then run this client:
//	go run examples/dns_client/main.go
package main

import (
	"fmt"
	"log"
	"net"
	"time"

	"github.com/anthropic/dns-server/internal/protocol"
)

func main() {
	serverAddr := "127.0.0.1:5353"

	fmt.Println("=== DNS Client Example ===")
	fmt.Printf("Querying server at %s\n\n", serverAddr)

	// Query 1: A record
	queryDNS(serverAddr, "localhost.dns", protocol.TypeA)

	// Query 2: A record for another domain
	queryDNS(serverAddr, "test.local", protocol.TypeA)

	// Query 3: Non-existent domain (will forward to upstream)
	queryDNS(serverAddr, "example.com", protocol.TypeA)
}

func queryDNS(serverAddr, domain string, qtype uint16) {
	// Build a DNS query message
	query := &protocol.Message{
		Header: protocol.Header{
			ID:      uint16(time.Now().UnixNano() & 0xFFFF),
			QR:      protocol.QRQuery,
			Opcode:  protocol.OpcodeQuery,
			RD:      true, // Request recursive resolution
			QDCount: 1,
		},
		Question: []protocol.Question{
			{
				Name:  domain,
				Type:  qtype,
				Class: protocol.ClassIN,
			},
		},
	}

	// Serialize the query
	queryData, err := query.Pack()
	if err != nil {
		log.Printf("Failed to pack query for %s: %v", domain, err)
		return
	}

	fmt.Printf("Query: %s %s (ID: 0x%04x, %d bytes)\n",
		domain, protocol.TypeName(qtype), query.Header.ID, len(queryData))

	// Send via UDP
	conn, err := net.DialTimeout("udp", serverAddr, 5*time.Second)
	if err != nil {
		log.Printf("Failed to connect: %v", err)
		return
	}
	defer conn.Close()

	conn.SetDeadline(time.Now().Add(5 * time.Second))

	_, err = conn.Write(queryData)
	if err != nil {
		log.Printf("Failed to send query: %v", err)
		return
	}

	// Read response
	buf := make([]byte, protocol.MaxUDPPayloadSize)
	n, err := conn.Read(buf)
	if err != nil {
		log.Printf("Failed to read response: %v", err)
		return
	}

	// Parse response
	resp, err := protocol.Unpack(buf[:n])
	if err != nil {
		log.Printf("Failed to parse response: %v", err)
		return
	}

	// Display results
	fmt.Printf("Response: %s (ID: 0x%04x, RCODE: %s)\n",
		domain, resp.Header.ID, protocol.RcodeName(resp.Header.RCODE))

	if len(resp.Answer) == 0 {
		fmt.Println("  (no answers)")
	} else {
		for _, rr := range resp.Answer {
			switch rr.Type {
			case protocol.TypeA:
				fmt.Printf("  A    %s (TTL=%d)\n", protocol.FormatRecordA(rr.RData), rr.TTL)
			case protocol.TypeAAAA:
				fmt.Printf("  AAAA %s (TTL=%d)\n", protocol.FormatRecordAAAA(rr.RData), rr.TTL)
			case protocol.TypeCNAME:
				fmt.Printf("  CNAME %s (TTL=%d)\n", string(rr.RData), rr.TTL)
			default:
				fmt.Printf("  %s (TTL=%d, len=%d)\n", protocol.TypeName(rr.Type), rr.TTL, rr.RDLen)
			}
		}
	}
	fmt.Println()
}
