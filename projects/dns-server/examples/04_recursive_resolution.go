package main

import (
	"fmt"

	dnsserver "dns-server/src"
)

// This demo shows recursive DNS resolution.
//
// Recursive resolution is the process of resolving a domain name by
// following a chain of DNS servers:
//
//  1. Client sends query to local resolver (recursion desired)
//  2. Local resolver checks cache
//  3. If not cached, resolver queries root nameservers
//  4. Root returns TLD nameserver (e.g., .com)
//  5. Resolver queries TLD nameserver
//  6. TLD returns authoritative nameserver (e.g., example.com)
//  7. Resolver queries authoritative nameserver
//  8. Authoritative returns the final answer
//  9. Resolver caches the answer and returns to client
//
// This demo simulates this process using local zone files.
func main() {
	fmt.Println("=== Recursive Resolution Demo ===\n")

	// Create a resolver with cache and forwarder
	forwarder := dnsserver.NewForwarder([]string{"8.8.8.8:53", "1.1.1.1:53"}, 5)
	resolver := dnsserver.NewResolver(1024, 3600, forwarder)

	// Register a local zone
	zoneContent := `
$ORIGIN example.com.
$TTL 3600

@       IN  SOA   ns1.example.com.  admin.example.com. (
                    2024010101  3600  900  604800  86400
                )

@       IN  NS      ns1.example.com.
@       IN  NS      ns2.example.com.

ns1     IN  A       192.168.1.1
ns2     IN  A       192.168.1.2
www     IN  A       93.184.216.34
mail    IN  A       192.168.1.20
api     IN  A       10.0.0.1
blog    IN  CNAME   www.example.com.
shop    IN  CNAME   www.example.com.
@       IN  MX      10  mail.example.com.
@       IN  TXT     "v=spf1 include:_spf.example.com ~all"
`

	zone, _ := dnsserver.ParseZoneFile(zoneContent)
	resolver.AddZone("example.com", zone)

	fmt.Println("Registered zone: example.com")
	fmt.Println("Records in zone:")
	for _, rr := range zone.Records {
		fmt.Printf("  %s %s\n", rr.Name, rr.Type)
	}

	// Perform recursive resolution
	fmt.Println("\n--- Resolution Tests ---")

	// Test 1: Resolve A record for www.example.com
	fmt.Println("\n1. Resolving A record for www.example.com:")
	result := resolve(resolver, "www.example.com", dnsserver.TypeA)
	printResult(result)

	// Test 2: Resolve AAAA record (should return NXDOMAIN)
	fmt.Println("\n2. Resolving AAAA record for www.example.com:")
	result = resolve(resolver, "www.example.com", dnsserver.TypeAAAA)
	printResult(result)

	// Test 3: Resolve MX record
	fmt.Println("\n3. Resolving MX record for example.com:")
	result = resolve(resolver, "example.com", dnsserver.TypeMX)
	printResult(result)

	// Test 4: Resolve CNAME (blog -> www)
	fmt.Println("\n4. Resolving CNAME for blog.example.com:")
	result = resolve(resolver, "blog.example.com", dnsserver.TypeCNAME)
	printResult(result)

	// Test 5: Resolve TXT record
	fmt.Println("\n5. Resolving TXT record for example.com:")
	result = resolve(resolver, "example.com", dnsserver.TypeTXT)
	printResult(result)

	// Test 6: Resolve non-existent domain
	fmt.Println("\n6. Resolving non-existent domain (ghost.example.com):")
	result = resolve(resolver, "ghost.example.com", dnsserver.TypeA)
	printResult(result)

	// Test 7: Resolve NS record
	fmt.Println("\n7. Resolving NS record for example.com:")
	result = resolve(resolver, "example.com", dnsserver.TypeNS)
	printResult(result)

	// Test 8: Cache behavior
	fmt.Println("\n8. Testing cache behavior:")
	fmt.Printf("   Cache size before: %d\n", resolver.Cache().Size())
	for i := 0; i < 3; i++ {
		resolve(resolver, "www.example.com", dnsserver.TypeA)
	}
	fmt.Printf("   Cache size after 3 queries: %d\n", resolver.Cache().Size())
	fmt.Println("   (www.example.com A record is cached, no additional lookups needed)")

	// Test 9: Wildcard resolution
	fmt.Println("\n9. Testing wildcard resolution:")
	addWildcardZone(resolver)
	result = resolve(resolver, "random.example.com", dns.TypeA)
	printResult(result)
}

// resolve is a helper that performs resolution and prints the result.
func resolve(resolver *dnsserver.Resolver, name string, rtype dnsserver.RecordType) *dnsserver.Message {
	result, err := resolver.Resolve(name, rtype)
	if err != nil {
		fmt.Printf("   Error: %v\n", err)
		return nil
	}
	return result
}

// printResult displays a DNS response in a readable format.
func printResult(result *dnsserver.Message) {
	if result == nil {
		fmt.Println("   No result")
		return
	}

	// Check response code
	rcode := dnsserver.RCode(result.Header.Flags & 0xF)
	if !result.IsResponse() {
		fmt.Println("   (Not a response)")
		return
	}

	if rcode != dnsserver.RCodeOK {
		fmt.Printf("   Response code: %s\n", rcode)
		return
	}

	if len(result.Answers) == 0 {
		fmt.Println("   No answers")
		return
	}

	fmt.Printf("   Response code: %s\n", rcode)
	fmt.Printf("   Answers (%d):\n", len(result.Answers))
	for i, ans := range result.Answers {
		fmt.Printf("   [%d] %s %s\n", i+1, ans.Name, ans.Type)
		if ans.RawData != nil {
			switch data := ans.RawData.(type) {
			case *dnsserver.IPv4Address:
				fmt.Printf("       -> %s (TTL: %ds)\n", data.String(), ans.TTL)
			case *dnsserver.IPv6Address:
				fmt.Printf("       -> %s (TTL: %ds)\n", data.String(), ans.TTL)
			case *dnsserver.DomainNameRecord:
				fmt.Printf("       -> %s (TTL: %ds)\n", data.Name, ans.TTL)
			case *dnsserver.MXRecord:
				fmt.Printf("       -> %s (TTL: %ds)\n", data.String(), ans.TTL)
			case *dnsserver.TXTRecord:
				fmt.Printf("       -> %s (TTL: %ds)\n", data.String(), ans.TTL)
			}
		}
	}
}

// addWildcardZone adds a wildcard entry for testing.
func addWildcardZone(resolver *dns.Resolver) {
	wildcardZoneContent := `
$ORIGIN example.com.
$TTL 3600

@       IN  SOA   ns1.example.com.  admin.example.com. (
                    2024010101  3600  900  604800  86400
                )

*       IN  A       127.0.0.1
`
	wildcardZone, _ := dnsserver.ParseZoneFile(wildcardZoneContent)
	resolver.AddZone("example.com", wildcardZone)
}
