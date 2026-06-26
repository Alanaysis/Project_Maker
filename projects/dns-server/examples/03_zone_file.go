package main

import (
	"fmt"

	dnsserver "dns-server/src"
)

// This demo shows zone file parsing and loading.
//
// A zone file is a text file that defines DNS records for a domain.
// It follows the format specified in RFC 1035 and is used by DNS servers
// like BIND, PowerDNS, and CoreDNS.
//
// Zone file syntax:
//   [name] [TTL] [class] type rdata
//
// Special symbols:
//   @     - Represents the current origin (zone name)
//   $ORIG  - Sets the default origin domain
//   $TTL   - Sets the default time-to-live
//
// Common record types:
//   A      - IPv4 address
//   AAAA   - IPv6 address
//   CNAME  - Canonical name (alias)
//   MX     - Mail exchange server
//   NS     - Nameserver
//   SOA    - Start of authority
//   TXT    - Text record (SPF, DKIM, etc.)
//   PTR    - Pointer (reverse DNS)
func main() {
	fmt.Println("=== Zone File Loading Demo ===\n")

	// Example zone file content (simulating a real zone file)
	zoneContent := `
; Zone file for example.com
; This is a comment line
$ORIGIN example.com.
$TTL 3600

; SOA record - Start of Authority
; Format: @ IN SOA primary_ns admin_email ( serial refresh retry expire minimum )
@       IN  SOA   ns1.example.com.  admin.example.com. (
                    2024010101  ; Serial number
                    3600        ; Refresh (1 hour)
                    900         ; Retry (15 minutes)
                    604800      ; Expire (1 week)
                    86400       ; Minimum TTL (1 day)
                )

; NS records - Nameservers
@       IN  NS      ns1.example.com.
@       IN  NS      ns2.example.com.

; A records - IPv4 addresses
ns1     IN  A       192.168.1.1
ns2     IN  A       192.168.1.2
www     IN  A       93.184.216.34
mail    IN  A       192.168.1.20
api     IN  A       10.0.0.1

; AAAA record - IPv6 address
www     IN  AAAA    2606:2800:220:1:248:1893:25c8:1946

; CNAME record - Canonical name (alias)
blog    IN  CNAME   www.example.com.
shop    IN  CNAME   www.example.com.

; MX record - Mail exchange
@       IN  MX      10  mail.example.com.
@       IN  MX      20  mail2.example.com.

; TXT record - Text record (commonly used for SPF)
@       IN  TXT     "v=spf1 include:_spf.example.com ~all"

; PTR record - Reverse DNS (in reverse zone)
; 34.216.184.93.in-addr.arpa. IN PTR www.example.com.
`

	// Parse the zone file
	zone, err := dnsserver.ParseZoneFile(zoneContent)
	if err != nil {
		fmt.Printf("Error parsing zone file: %v\n", err)
		return
	}

	fmt.Printf("Zone Origin: %s\n", zone.Origin)
	fmt.Printf("Default TTL: %d seconds\n", zone.DefaultTTL)
	fmt.Printf("Total Records: %d\n\n", len(zone.Records))

	// Display all records
	fmt.Println("All Records:")
	fmt.Println("--------------------------------------------------------------")
	for i, rr := range zone.Records {
		fmt.Printf("  [%d] %s  %s  TTL:%d\n", i+1, rr.Name, rr.Type, rr.TTL)
		if rr.RawData != nil {
			switch data := rr.RawData.(type) {
			case *dns.IPv4Address:
				fmt.Printf("      -> A: %s\n", data.String())
			case *dns.IPv6Address:
				fmt.Printf("      -> AAAA: %s\n", data.String())
			case *dns.DomainNameRecord:
				fmt.Printf("      -> %s: %s\n", rr.Type, data.Name)
			case *dns.MXRecord:
				fmt.Printf("      -> MX: %s\n", data.String())
			case *dns.TXTRecord:
				fmt.Printf("      -> TXT: %s\n", data.String())
			case *dns.SOARecord:
				fmt.Printf("      -> SOA: %s\n", data.String())
			}
		}
	}

	// Demonstrate lookups
	fmt.Println("\n--- Lookups ---")

	// Lookup A record for www
	records := zone.Lookup("www.example.com", dnsserver.TypeA)
	fmt.Printf("\nA records for www.example.com: %d found\n", len(records))
	for _, rr := range records {
		if data, ok := rr.RawData.(*dnsserver.IPv4Address); ok {
			fmt.Printf("  -> %s\n", data.String())
		}
	}

	// Lookup MX records
	records = zone.Lookup("example.com", dnsserver.TypeMX)
	fmt.Printf("\nMX records for example.com: %d found\n", len(records))
	for _, rr := range records {
		if data, ok := rr.RawData.(*dnsserver.MXRecord); ok {
			fmt.Printf("  -> Preference: %d, Exchange: %s\n", data.Preference, data.Exchange)
		}
	}

	// Lookup CNAME records
	records = zone.Lookup("blog.example.com", dnsserver.TypeCNAME)
	fmt.Printf("\nCNAME records for blog.example.com: %d found\n", len(records))
	for _, rr := range records {
		if data, ok := rr.RawData.(*dns.DomainNameRecord); ok {
			fmt.Printf("  -> CNAME: %s\n", data.Name)
		}
	}

	// Lookup all records for a name
	records = zone.LookupAny("www.example.com")
	fmt.Printf("\nAll records for www.example.com: %d found\n", len(records))
	for _, rr := range records {
		fmt.Printf("  -> %s %s\n", rr.Type, rr)
	}

	// Lookup NS records
	records = zone.Lookup("example.com", dnsserver.TypeNS)
	fmt.Printf("\nNS records for example.com: %d found\n", len(records))
	for _, rr := range records {
		if data, ok := rr.RawData.(*dns.DomainNameRecord); ok {
			fmt.Printf("  -> NS: %s\n", data.Name)
		}
	}

	// Lookup TXT records
	records = zone.Lookup("example.com", dnsserver.TypeTXT)
	fmt.Printf("\nTXT records for example.com: %d found\n", len(records))
	for _, rr := range records {
		if data, ok := rr.RawData.(*dnsserver.TXTRecord); ok {
			fmt.Printf("  -> TXT: %s\n", data.String())
		}
	}
}
