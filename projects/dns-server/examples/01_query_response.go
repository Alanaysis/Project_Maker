package main

import (
	"fmt"
	"strings"

	dnsserver "dns-server/src"
)

// This demo shows DNS packet encoding and decoding.
// It demonstrates the core DNS wire format defined in RFC 1035.
//
// DNS wire format structure:
//   Header (12 bytes) + Questions + Answers + Authority + Additional
//
// Each domain name in the wire format uses label compression:
//   - Each label is prefixed with its length byte
//   - Labels are separated by dots in the name, but length-prefixed in wire format
//   - A zero byte terminates the name
//   - Compression pointers (0xC0 prefix) can reference earlier occurrences
func main() {
	fmt.Println("=== DNS Query and Response Demo ===\n")

	// Create a DNS query message
	// The ID (0x1234) is used to match responses to their queries
	query := dnsserver.NewMessage(0x1234)
	query.Header.QDCount = 1
	query.Questions = []dnsserver.Question{
		{
			Name:  "www.example.com",
			Type:  dnsserver.TypeA,
			Class: dnsserver.ClassIN,
		},
	}
	query.SetRD(true) // Set Recursion Desired flag

	// Display the query
	fmt.Println("DNS Query:")
	fmt.Printf("  %s\n", query)

	// Encode the query to wire format
	queryBytes, err := query.Encode()
	if err != nil {
		fmt.Printf("Error encoding query: %v\n", err)
		return
	}
	fmt.Printf("  Encoded size: %d bytes\n", len(queryBytes))
	fmt.Printf("  Hex dump:\n")
	for i := 0; i < len(queryBytes); i += 16 {
		end := i + 16
		if end > len(queryBytes) {
			end = len(queryBytes)
		}
		fmt.Printf("    ")
		for j := i; j < end; j++ {
			fmt.Printf("%02x ", queryBytes[j])
		}
		fmt.Print(" ")
		for j := i; j < end; j++ {
			c := queryBytes[j]
			if c >= 0x20 && c < 0x7f {
				fmt.Printf("%c", c)
			} else {
				fmt.Print(".")
			}
		}
		fmt.Println()
	}

	// Create a DNS response message
	// This simulates what a real DNS server would return
	response := dnsserver.NewResponse(0x1234)
	response.Header.ANCount = 2
	response.Answers = []dnsserver.ResourceRecord{
		{
			Name:  "www.example.com",
			Type:  dnsserver.TypeCNAME,
			Class: dnsserver.ClassIN,
			TTL:   300, // 5 minutes
			Data:  []byte{},
			RawData: &dnsserver.DomainNameRecord{Name: "example.com"},
		},
		{
			Name:  "example.com",
			Type:  dnsserver.TypeA,
			Class: dnsserver.ClassIN,
			TTL:   3600,
			Data:  []byte{93, 184, 216, 34}, // 93.184.216.34
			RawData: &dnsserver.IPv4Address{IP: []byte{93, 184, 216, 34}},
		},
	}

	fmt.Println("\nDNS Response:")
	fmt.Printf("  %s", response)

	// Encode and decode the response to demonstrate wire format
	respBytes, err := response.Encode()
	if err != nil {
		fmt.Printf("Error encoding response: %v\n", err)
		return
	}
	fmt.Printf("  Encoded size: %d bytes\n", len(respBytes))

	// Decode the response to verify round-trip encoding
	var decoded dnsserver.Message
	if err := decoded.Decode(respBytes); err != nil {
		fmt.Printf("Error decoding response: %v\n", err)
		return
	}
	fmt.Println("\nDecoded Response (verifying round-trip):")
	fmt.Printf("  %s", &decoded)

	// Demonstrate domain name compression
	fmt.Println("\n--- Domain Name Compression Demo ---")
	demonstrateCompression()
}

// demonstrateCompression shows how domain name compression reduces packet size.
func demonstrateCompression() {
	// Without compression: each full name is repeated
	longName := "www.subdomain.example.com"
	uncompressed, _ := dnsserver.EncodeDomainName(longName)
	fmt.Printf("  Name: %s\n", longName)
	fmt.Printf("  Uncompressed wire format: %d bytes\n", len(uncompressed))

	// With compression: the common suffix can be referenced via pointer
	// In a real packet, "example.com" might appear first, then a pointer
	// to it would be used in the CNAME answer section
	fmt.Println("  With compression: same domain name can be referenced with a 2-byte pointer")
	fmt.Println("  (Pointer format: 0xC0 + offset to the original name)")
}
	query.SetRD(true) // Set Recursion Desired flag

	// Display the query
	fmt.Println("DNS Query:")
	fmt.Printf("  %s\n", query)

	// Encode the query to wire format
	queryBytes, err := query.Encode()
	if err != nil {
		fmt.Printf("Error encoding query: %v\n", err)
		return
	}
	fmt.Printf("  Encoded size: %d bytes\n", len(queryBytes))
	fmt.Printf("  Hex dump:\n")
	for i := 0; i < len(queryBytes); i += 16 {
		end := i + 16
		if end > len(queryBytes) {
			end = len(queryBytes)
		}
		fmt.Printf("    ")
		for j := i; j < end; j++ {
			fmt.Printf("%02x ", queryBytes[j])
		}
		fmt.Print(" ")
		for j := i; j < end; j++ {
			c := queryBytes[j]
			if c >= 0x20 && c < 0x7f {
				fmt.Printf("%c", c)
			} else {
				fmt.Print(".")
			}
		}
		fmt.Println()
	}

	// Create a DNS response message
	// This simulates what a real DNS server would return
	response := dns.NewResponse(0x1234)
	response.Header.ANCount = 2
	response.Answers = []dns.ResourceRecord{
		{
			Name:  "www.example.com",
			Type:  dns.TypeCNAME,
			Class: dns.ClassIN,
			TTL:   300,
			Data:  mustEncode(dns.DomainNameRecord{Name: "example.com"}),
			RawData: &dns.DomainNameRecord{Name: "example.com"},
		},
		{
			Name:  "example.com",
			Type:  dns.TypeA,
			Class: dns.ClassIN,
			TTL:   3600,
			Data:  []byte{93, 184, 216, 34}, // 93.184.216.34
			RawData: &dns.IPv4Address{IP: []byte{93, 184, 216, 34}},
		},
	}

	fmt.Println("\nDNS Response:")
	fmt.Printf("  %s", response)

	// Encode and decode the response to demonstrate wire format
	respBytes, err := response.Encode()
	if err != nil {
		fmt.Printf("Error encoding response: %v\n", err)
		return
	}
	fmt.Printf("  Encoded size: %d bytes\n", len(respBytes))

	// Decode the response to verify round-trip encoding
	var decoded dns.Message
	if err := decoded.Decode(respBytes); err != nil {
		fmt.Printf("Error decoding response: %v\n", err)
		return
	}
	fmt.Println("\nDecoded Response (verifying round-trip):")
	fmt.Printf("  %s", &decoded)

	// Demonstrate domain name compression
	fmt.Println("\n--- Domain Name Compression Demo ---")
	demonstrateCompression()
}

// demonstrateCompression shows how domain name compression reduces packet size.
func demonstrateCompression() {
	// Without compression: each full name is repeated
	longName := "www.subdomain.example.com"
	uncompressed, _ := dns.EncodeDomainName(longName)
	fmt.Printf("  Name: %s\n", longName)
	fmt.Printf("  Uncompressed wire format: %d bytes\n", len(uncompressed))

	// With compression: the common suffix can be referenced via pointer
	// In a real packet, "example.com" might appear first, then a pointer
	// to it would be used in the CNAME answer section
	fmt.Println("  With compression: same domain name can be referenced with a 2-byte pointer")
	fmt.Println("  (Pointer format: 0xC0 + offset to the original name)")
}

// mustEncode is a helper that encodes and panics on error.
func mustEncode(rr dns.ResourceRecord) []byte {
	return rr.Data
}
