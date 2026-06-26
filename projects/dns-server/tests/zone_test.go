package dns

import (
	"testing"
)

// TestParseZoneFile tests basic zone file parsing.
func TestParseZoneFile(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

@       IN  SOA   ns1.example.com.  admin.example.com. (
                    2024010101  3600  900  604800  86400
                )

@       IN  NS      ns1.example.com.
ns1     IN  A       192.168.1.1
www     IN  A       93.184.216.34
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	if zone.Origin != "example.com" {
		t.Errorf("Origin: got %q, want %q", zone.Origin, "example.com")
	}

	if zone.DefaultTTL != 3600 {
		t.Errorf("DefaultTTL: got %d, want 3600", zone.DefaultTTL)
	}

	if len(zone.Records) == 0 {
		t.Error("Expected at least one record")
	}
}

// TestParseZoneFileSOA tests SOA record parsing.
func TestParseZoneFileSOA(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

@       IN  SOA   ns1.example.com.  admin.example.com. (
                    2024010101  3600  900  604800  86400
                )
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	var soaFound bool
	for _, rr := range zone.Records {
		if rr.Type == TypeSOA {
			soaFound = true
			if soa, ok := rr.RawData.(*SOARecord); ok {
				if soa.Serial != 2024010101 {
					t.Errorf("Serial: got %d, want 2024010101", soa.Serial)
				}
				if soa.Refresh != 3600 {
					t.Errorf("Refresh: got %d, want 3600", soa.Refresh)
				}
			}
		}
	}

	if !soaFound {
		t.Error("Expected SOA record to be parsed")
	}
}

// TestParseZoneFileARecord tests A record parsing.
func TestParseZoneFileARecord(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

www     IN  A       93.184.216.34
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	var aFound bool
	for _, rr := range zone.Records {
		if rr.Type == TypeA && rr.Name == "www.example.com" {
			aFound = true
			if ipv4, ok := rr.RawData.(*IPv4Address); ok {
				if ipv4.String() != "93.184.216.34" {
					t.Errorf("IPv4: got %s, want 93.184.216.34", ipv4.String())
				}
			}
		}
	}

	if !aFound {
		t.Error("Expected A record for www.example.com")
	}
}

// TestParseZoneFileMXRecord tests MX record parsing.
func TestParseZoneFileMXRecord(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

@       IN  MX      10  mail.example.com.
@       IN  MX      20  mail2.example.com.
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	mxCount := 0
	for _, rr := range zone.Records {
		if rr.Type == TypeMX {
			mxCount++
			if mx, ok := rr.RawData.(*MXRecord); ok {
				if mx.Preference != 10 && mx.Preference != 20 {
					t.Errorf("MX preference: got %d, want 10 or 20", mx.Preference)
				}
			}
		}
	}

	if mxCount != 2 {
		t.Errorf("Expected 2 MX records, got %d", mxCount)
	}
}

// TestParseZoneFileTXTRecord tests TXT record parsing.
func TestParseZoneFileTXTRecord(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

@       IN  TXT     "v=spf1 include:_spf.example.com ~all"
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	var txtFound bool
	for _, rr := range zone.Records {
		if rr.Type == TypeTXT {
			txtFound = true
			if txt, ok := rr.RawData.(*TXTRecord); ok {
				if len(txt.Texts) == 0 {
					t.Error("Expected at least one TXT text")
				}
			}
		}
	}

	if !txtFound {
		t.Error("Expected TXT record to be parsed")
	}
}

// TestParseZoneFileTXTRecordSimple tests simple TXT record parsing.
func TestParseZoneFileTXTRecordSimple(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

@       IN  TXT     "hello world"
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	if len(zone.Records) != 1 {
		t.Errorf("Expected 1 record, got %d", len(zone.Records))
	}
}

// TestParseZoneFileCNAME tests CNAME record parsing.
func TestParseZoneFileCNAME(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

blog    IN  CNAME   www.example.com.
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	var cnameFound bool
	for _, rr := range zone.Records {
		if rr.Type == TypeCNAME && rr.Name == "blog.example.com" {
			cnameFound = true
			if cname, ok := rr.RawData.(*DomainNameRecord); ok {
				if cname.Name != "www.example.com" {
					t.Errorf("CNAME target: got %s, want www.example.com", cname.Name)
				}
			}
		}
	}

	if !cnameFound {
		t.Error("Expected CNAME record for blog.example.com")
	}
}

// TestParseZoneFileNS tests NS record parsing.
func TestParseZoneFileNS(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

@       IN  NS      ns1.example.com.
@       IN  NS      ns2.example.com.
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	nsCount := 0
	for _, rr := range zone.Records {
		if rr.Type == TypeNS {
			nsCount++
		}
	}

	if nsCount != 2 {
		t.Errorf("Expected 2 NS records, got %d", nsCount)
	}
}

// TestParseZoneFileWildcard tests wildcard record parsing.
func TestParseZoneFileWildcard(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

*       IN  A       127.0.0.1
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	var wildcardFound bool
	for _, rr := range zone.Records {
		if rr.Name == "*" && rr.Type == TypeA {
			wildcardFound = true
		}
	}

	if !wildcardFound {
		t.Error("Expected wildcard A record")
	}
}

// TestParseZoneFileComments tests comment handling.
func TestParseZoneFileComments(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

; This is a comment
www     IN  A       93.184.216.34  ; inline comment
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	if len(zone.Records) != 1 {
		t.Errorf("Expected 1 record, got %d (comments should be ignored)", len(zone.Records))
	}
}

// TestParseZoneFileTTL tests TTL parsing with suffixes.
func TestParseZoneFileTTL(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 1h

www     IN  A       93.184.216.34
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	if zone.DefaultTTL != 3600 {
		t.Errorf("DefaultTTL: got %d, want 3600 (1h)", zone.DefaultTTL)
	}
}

// TestParseZoneFilePerRecordTTL tests per-record TTL.
func TestParseZoneFilePerRecordTTL(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

www     600     IN  A       93.184.216.34
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	for _, rr := range zone.Records {
		if rr.Name == "www.example.com" && rr.TTL != 600 {
			t.Errorf("TTL: got %d, want 600", rr.TTL)
		}
	}
}

// TestZoneFileLookup tests zone file record lookups.
func TestZoneFileLookup(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

www     IN  A       93.184.216.34
mail    IN  A       192.168.1.1
@       IN  MX      10  mail.example.com.
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	// Test A record lookup
	aRecords := zone.Lookup("www.example.com", TypeA)
	if len(aRecords) != 1 {
		t.Errorf("Expected 1 A record, got %d", len(aRecords))
	}

	// Test MX record lookup
	mxRecords := zone.Lookup("example.com", TypeMX)
	if len(mxRecords) != 1 {
		t.Errorf("Expected 1 MX record, got %d", len(mxRecords))
	}

	// Test non-existent lookup
	none := zone.Lookup("nonexistent.example.com", TypeA)
	if len(none) != 0 {
		t.Errorf("Expected 0 records, got %d", len(none))
	}
}

// TestZoneFileLookupAny tests LookupAny function.
func TestZoneFileLookupAny(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

www     IN  A       93.184.216.34
www     IN  AAAA    2606:2800:220:1:248:1893:25c8:1946
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	records := zone.LookupAny("www.example.com")
	if len(records) != 2 {
		t.Errorf("Expected 2 records, got %d", len(records))
	}
}

// TestParseTTL tests TTL parsing with various formats.
func TestParseTTL(t *testing.T) {
	tests := []struct {
		input  string
		expect uint32
	}{
		{"3600", 3600},
		{"1h", 3600},
		{"30m", 1800},
		{"1d", 86400},
		{"1w", 604800},
		{"60s", 60},
		{"0", 0},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got, err := parseTTL(tt.input)
			if err != nil {
				t.Fatalf("parseTTL(%q) error: %v", tt.input, err)
			}
			if got != tt.expect {
				t.Errorf("parseTTL(%q) = %d, want %d", tt.input, got, tt.expect)
			}
		})
	}
}

// TestRemoveComments tests comment removal.
func TestRemoveComments(t *testing.T) {
	tests := []struct {
		input  string
		expect string
	}{
		{"www IN A 1.2.3.4 ; comment", "www IN A 1.2.3.4 "},
		{"; full comment line", ""},
		{"www IN A 1.2.3.4", "www IN A 1.2.3.4"},
		{"\"# not a comment\" IN A 1.2.3.4", "\"# not a comment\" IN A 1.2.3.4"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got := removeComments(tt.input)
			if got != tt.expect {
				t.Errorf("removeComments(%q) = %q, want %q", tt.input, got, tt.expect)
			}
		})
	}
}

// TestIsClass tests class detection.
func TestIsClass(t *testing.T) {
	if !isClass("IN") {
		t.Error("Expected IN to be a class")
	}
	if !isClass("CH") {
		t.Error("Expected CH to be a class")
	}
	if isClass("A") {
		t.Error("Expected A not to be a class")
	}
	if isClass("192.168.1.1") {
		t.Error("Expected IP not to be a class")
	}
}

// TestIsType tests type detection.
func TestIsType(t *testing.T) {
	if !isType("A") {
		t.Error("Expected A to be a type")
	}
	if !isType("AAAA") {
		t.Error("Expected AAAA to be a type")
	}
	if !isType("MX") {
		t.Error("Expected MX to be a type")
	}
	if isType("192.168.1.1") {
		t.Error("Expected IP not to be a type")
	}
}

// TestDomainNameCompression tests the compression pointer format.
func TestDomainNameCompression(t *testing.T) {
	// Create a packet with a compression pointer
	// Offset 0: "example.com" (the original name)
	// Offset 12: "www" + pointer to offset 12
	data := []byte{
		0x07, 'e', 'x', 'a', 'm', 'p', 'l', 'e', // "example" at offset 0
		0x03, 'c', 'o', 'm',                        // ".com" at offset 7
		0x00,                                         // null terminator at offset 12
		0x03, 'w', 'w', 'w',                        // "www" at offset 13
		0xC0, 0x0C,                                 // pointer to offset 12
		0x00,                                         // null terminator
	}

	name, n, err := decodeDomainName(data, 13)
	if err != nil {
		t.Fatalf("decodeDomainName error: %v", err)
	}
	if name != "www.example.com" {
		t.Errorf("got %q, want 'www.example.com'", name)
	}
	if n != 5 { // 3 (www) + 2 (pointer)
		t.Errorf("bytes consumed: got %d, want 5", n)
	}
}

// TestEncodeDomainNameRoot tests encoding the root domain.
func TestEncodeDomainNameRoot(t *testing.T) {
	result, err := encodeDomainName(".")
	if err != nil {
		t.Fatalf("encodeDomainName(\".\") error: %v", err)
	}
	if len(result) != 1 || result[0] != 0 {
		t.Errorf("Expected [0], got %v", result)
	}
}

// TestParseRecordTypeUnknown tests unknown record type handling.
func TestParseRecordTypeUnknown(t *testing.T) {
	_, err := parseRecordType("UNKNOWN")
	if err == nil {
		t.Error("Expected error for unknown record type")
	}
}

// TestParseZoneFileEmpty tests empty zone file handling.
func TestParseZoneFileEmpty(t *testing.T) {
	zone, err := ParseZoneFile("")
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}
	if zone == nil {
		t.Fatal("Expected non-nil zone")
	}
	if len(zone.Records) != 0 {
		t.Errorf("Expected 0 records, got %d", len(zone.Records))
	}
}

// TestParseZoneFileWithBlankLines tests zone file with blank lines.
func TestParseZoneFileWithBlankLines(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600


www     IN  A       93.184.216.34


`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	if len(zone.Records) != 1 {
		t.Errorf("Expected 1 record, got %d", len(zone.Records))
	}
}

// TestParseZoneFileMultipleARecords tests multiple A records for same name.
func TestParseZoneFileMultipleARecords(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

www     IN  A       93.184.216.34
www     IN  A       93.184.216.35
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	records := zone.Lookup("www.example.com", TypeA)
	if len(records) != 2 {
		t.Errorf("Expected 2 A records, got %d", len(records))
	}
}

// TestParseZoneFileMixedCase tests case handling in zone files.
func TestParseZoneFileMixedCase(t *testing.T) {
	content := `
$ORIGIN EXAMPLE.COM.
$TTL 3600

WWW     IN  A       93.184.216.34
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	if len(zone.Records) != 1 {
		t.Errorf("Expected 1 record, got %d", len(zone.Records))
	}
}

// TestParseZoneFileSOAWithLongForm tests SOA in long form.
func TestParseZoneFileSOAWithLongForm(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

@       IN  SOA   ns1.example.com.  admin.example.com. 2024010101 3600 900 604800 86400
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	var soaFound bool
	for _, rr := range zone.Records {
		if rr.Type == TypeSOA {
			soaFound = true
			if soa, ok := rr.RawData.(*SOARecord); ok {
				if soa.Serial != 2024010101 {
					t.Errorf("Serial: got %d, want 2024010101", soa.Serial)
				}
			}
		}
	}

	if !soaFound {
		t.Error("Expected SOA record to be parsed")
	}
}

// TestLookupWildcard tests wildcard lookups.
func TestLookupWildcard(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

*.example.com.    IN  A       127.0.0.1
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	records := zone.LookupWildcard("*.example.com")
	if len(records) != 1 {
		t.Errorf("Expected 1 wildcard record, got %d", len(records))
	}
}

// TestParseZoneFilePTR tests PTR record parsing.
func TestParseZoneFilePTR(t *testing.T) {
	content := `
$ORIGIN 1.168.192.in-addr.arpa.
$TTL 3600

34      IN  PTR     www.example.com.
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	var ptrFound bool
	for _, rr := range zone.Records {
		if rr.Type == TypePTR {
			ptrFound = true
			if ptr, ok := rr.RawData.(*DomainNameRecord); ok {
				if ptr.Name != "www.example.com" {
					t.Errorf("PTR target: got %s, want www.example.com", ptr.Name)
				}
			}
		}
	}

	if !ptrFound {
		t.Error("Expected PTR record to be parsed")
	}
}

// TestParseZoneFilePTRRelative tests PTR record with relative name.
func TestParseZoneFilePTRRelative(t *testing.T) {
	content := `
$ORIGIN example.com.
$TTL 3600

mail    IN  PTR     mail2.example.com.
`

	zone, err := ParseZoneFile(content)
	if err != nil {
		t.Fatalf("ParseZoneFile error: %v", err)
	}

	if len(zone.Records) != 1 {
		t.Errorf("Expected 1 record, got %d", len(zone.Records))
	}
}
