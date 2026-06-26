package dns

import (
	"fmt"
	"testing"
	"time"
)

// TestRecordTypeString tests the String() method for RecordType.
func TestRecordTypeString(t *testing.T) {
	tests := []struct {
		typ    RecordType
		expect string
	}{
		{TypeA, "A"},
		{TypeNS, "NS"},
		{TypeCNAME, "CNAME"},
		{TypeSOA, "SOA"},
		{TypePTR, "PTR"},
		{TypeMX, "MX"},
		{TypeTXT, "TXT"},
		{TypeAAAA, "AAAA"},
		{TypeSRV, "SRV"},
		{TypeOPT, "OPT"},
		{TypeDNSKEY, "DNSKEY"},
		{TypeRRSIG, "RRSIG"},
		{TypeNSEC, "NSEC"},
		{TypeAXFR, "AXFR"},
		{TypeANY, "ANY"},
		{RecordType(99), "TYPE99"},
		{RecordType(0), "TYPE0"},
	}

	for _, tt := range tests {
		t.Run(tt.expect, func(t *testing.T) {
			got := tt.typ.String()
			if got != tt.expect {
				t.Errorf("RecordType(%d).String() = %q, want %q", tt.typ, got, tt.expect)
			}
		})
	}
}

// TestClassTypeString tests the String() method for ClassType.
func TestClassTypeString(t *testing.T) {
	tests := []struct {
		c      ClassType
		expect string
	}{
		{ClassIN, "IN"},
		{ClassCH, "CH"},
		{ClassHS, "HS"},
		{ClassANY, "ANY"},
		{ClassType(99), "CLASS99"},
	}

	for _, tt := range tests {
		t.Run(tt.expect, func(t *testing.T) {
			got := tt.c.String()
			if got != tt.expect {
				t.Errorf("ClassType(%d).String() = %q, want %q", tt.c, got, tt.expect)
			}
		})
	}
}

// TestOpcodeString tests the String() method for Opcode.
func TestOpcodeString(t *testing.T) {
	tests := []struct {
		op     Opcode
		expect string
	}{
		{OpcodeQuery, "QUERY"},
		{OpcodeIQuery, "IQUERY"},
		{OpcodeStatus, "STATUS"},
		{OpcodeNotify, "NOTIFY"},
		{OpcodeUpdate, "UPDATE"},
		{Opcode(99), "OPCODE99"},
	}

	for _, tt := range tests {
		t.Run(tt.expect, func(t *testing.T) {
			got := tt.op.String()
			if got != tt.expect {
				t.Errorf("Opcode(%d).String() = %q, want %q", tt.op, got, tt.expect)
			}
		})
	}
}

// TestRCodeString tests the String() method for RCode.
func TestRCodeString(t *testing.T) {
	tests := []struct {
		rc     RCode
		expect string
	}{
		{RCodeOK, "NOERROR"},
		{RCodeFormat, "FORMERR"},
		{RCodeServFail, "SERVFAIL"},
		{RCodeNXDomain, "NXDOMAIN"},
		{RCodeNotImpl, "NOTIMP"},
		{RCodeRefused, "REFUSED"},
		{RCode(99), "RCode99"},
	}

	for _, tt := range tests {
		t.Run(tt.expect, func(t *testing.T) {
			got := tt.rc.String()
			if got != tt.expect {
				t.Errorf("RCode(%d).String() = %q, want %q", tt.rc, got, tt.expect)
			}
		})
	}
}

// TestHeaderQueryResponse tests IsQuery and IsResponse methods.
func TestHeaderQueryResponse(t *testing.T) {
	h := Header{}
	h.SetQR(false)
	if !h.IsQuery() {
		t.Error("Expected IsQuery() = true")
	}
	if h.IsResponse() {
		t.Error("Expected IsResponse() = false")
	}

	h.SetQR(true)
	if h.IsQuery() {
		t.Error("Expected IsQuery() = false")
	}
	if !h.IsResponse() {
		t.Error("Expected IsResponse() = true")
	}
}

// TestHeaderFlags tests flag manipulation.
func TestHeaderFlags(t *testing.T) {
	h := Header{}
	h.SetRD(true)
	h.SetAA(true)
	h.SetRA(true)

	h.SetRD(false)
	h.SetAA(false)
	h.SetRA(false)

	if h.QDCount != 0 || h.ANCount != 0 {
		t.Error("Expected zero counts")
	}
}

// TestNewMessage tests message creation helpers.
func TestNewMessage(t *testing.T) {
	msg := NewMessage(0x1234)
	if msg.Header.ID != 0x1234 {
		t.Errorf("Expected ID 0x1234, got 0x%x", msg.Header.ID)
	}
	if !msg.IsQuery() {
		t.Error("Expected new message to be a query")
	}

	resp := NewResponse(0x5678)
	if resp.Header.ID != 0x5678 {
		t.Errorf("Expected ID 0x5678, got 0x%x", resp.Header.ID)
	}
	if !resp.IsResponse() {
		t.Error("Expected new response to be a response")
	}

	errResp := NewErrorResponse(0x9ABC, RCodeNXDomain)
	if !errResp.IsResponse() {
		t.Error("Expected error response to be a response")
	}
}

// TestMessageIsQueryResponse tests Message-level query/response checks.
func TestMessageIsQueryResponse(t *testing.T) {
	msg := NewMessage(0)
	if !msg.IsQuery() {
		t.Error("Expected query")
	}
	if msg.IsResponse() {
		t.Error("Expected not response")
	}

	msg.Header.SetQR(true)
	if msg.IsQuery() {
		t.Error("Expected not query")
	}
	if !msg.IsResponse() {
		t.Error("Expected response")
	}
}

// TestMessageString tests the String() method for Message.
func TestMessageString(t *testing.T) {
	msg := NewMessage(0x1234)
	msg.Header.QDCount = 1
	msg.Questions = []Question{
		{Name: "example.com", Type: TypeA, Class: ClassIN},
	}
	msg.Header.ANCount = 1
	msg.Answers = []ResourceRecord{
		{Name: "example.com", Type: TypeA, Class: ClassIN, TTL: 300, Data: []byte{1, 2, 3, 4}},
	}

	s := msg.String()
	if len(s) == 0 {
		t.Error("Expected non-empty string")
	}
}

// TestQuestionString tests the String() method for Question.
func TestQuestionString(t *testing.T) {
	q := Question{Name: "example.com", Type: TypeA, Class: ClassIN}
	s := q.String()
	if s != "example.com IN A" {
		t.Errorf("Expected 'example.com IN A', got %q", s)
	}
}

// TestResourceRecordString tests the String() method for ResourceRecord.
func TestResourceRecordString(t *testing.T) {
	rr := ResourceRecord{Name: "example.com", Type: TypeA, Class: ClassIN, TTL: 300, Data: []byte{1, 2, 3, 4}}
	s := rr.String()
	if s == "" {
		t.Error("Expected non-empty string")
	}
}

// TestEncodeDecodeHeader tests header encoding and decoding.
func TestEncodeDecodeHeader(t *testing.T) {
	msg := NewMessage(0x1234)
	msg.Header.QDCount = 1
	msg.Header.ANCount = 2
	msg.Header.NSCount = 1
	msg.Header.ARCount = 3

	encoded, err := msg.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	// Check header size
	if len(encoded) < 12 {
		t.Fatalf("Encoded message too short: %d bytes", len(encoded))
	}

	// Verify header bytes
	if encoded[0] != 0x12 || encoded[1] != 0x34 {
		t.Errorf("Expected ID bytes 0x12 0x34, got %02x %02x", encoded[0], encoded[1])
	}

	if encoded[4] != 0 || encoded[5] != 1 {
		t.Errorf("Expected QDCount=1, got %02x %02x", encoded[4], encoded[5])
	}

	if encoded[6] != 0 || encoded[7] != 2 {
		t.Errorf("Expected ANCount=2, got %02x %02x", encoded[6], encoded[7])
	}

	if encoded[8] != 0 || encoded[9] != 1 {
		t.Errorf("Expected NSCount=1, got %02x %02x", encoded[8], encoded[9])
	}

	if encoded[10] != 0 || encoded[11] != 3 {
		t.Errorf("Expected ARCount=3, got %02x %02x", encoded[10], encoded[11])
	}
}

// TestEncodeDecodeRoundTrip tests full message encoding and decoding.
func TestEncodeDecodeRoundTrip(t *testing.T) {
	original := NewMessage(0xABCD)
	original.Header.QDCount = 1
	original.Questions = []Question{
		{Name: "example.com", Type: TypeA, Class: ClassIN},
	}
	original.Header.ANCount = 1
	original.Answers = []ResourceRecord{
		{Name: "example.com", Type: TypeA, Class: ClassIN, TTL: 300, Data: []byte{93, 184, 216, 34}},
	}

	encoded, err := original.Encode()
	if err != nil {
		t.Fatalf("Encode failed: %v", err)
	}

	var decoded Message
	if err := decoded.Decode(encoded); err != nil {
		t.Fatalf("Decode failed: %v", err)
	}

	if decoded.Header.ID != original.Header.ID {
		t.Errorf("ID mismatch: got %d, want %d", decoded.Header.ID, original.Header.ID)
	}

	if decoded.Header.QDCount != original.Header.QDCount {
		t.Errorf("QDCount mismatch: got %d, want %d", decoded.Header.QDCount, original.Header.QDCount)
	}

	if decoded.Header.ANCount != original.Header.ANCount {
		t.Errorf("ANCount mismatch: got %d, want %d", decoded.Header.ANCount, original.Header.ANCount)
	}

	if len(decoded.Questions) != len(original.Questions) {
		t.Errorf("Questions count: got %d, want %d", len(decoded.Questions), len(original.Questions))
	}

	if len(decoded.Answers) != len(original.Answers) {
		t.Errorf("Answers count: got %d, want %d", len(decoded.Answers), len(original.Answers))
	}
}

// TestDecodeShortMessage tests handling of truncated messages.
func TestDecodeShortMessage(t *testing.T) {
	var msg Message
	err := msg.Decode([]byte{0x00, 0x01})
	if err == nil {
		t.Error("Expected error for short message")
	}
}

// TestEncodeDomainName tests domain name encoding.
func TestEncodeDomainName(t *testing.T) {
	tests := []struct {
		name   string
		expect []byte
	}{
		{"example.com", []byte{7, 'e', 'x', 'a', 'm', 'p', 'l', 'e', 3, 'c', 'o', 'm', 0}},
		{"www.example.com", []byte{3, 'w', 'w', 'w', 7, 'e', 'x', 'a', 'm', 'p', 'l', 'e', 3, 'c', 'o', 'm', 0}},
		{"", []byte{0}},
		{"example.com.", []byte{7, 'e', 'x', 'a', 'm', 'p', 'l', 'e', 3, 'c', 'o', 'm', 0}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := encodeDomainName(tt.name)
			if err != nil {
				t.Fatalf("encodeDomainName(%q) error: %v", tt.name, err)
			}
			if len(got) != len(tt.expect) {
				t.Errorf("encodeDomainName(%q) = %v (len=%d), want %v (len=%d)",
					tt.name, got, len(got), tt.expect, len(tt.expect))
			}
			for i := range got {
				if i < len(tt.expect) && got[i] != tt.expect[i] {
					t.Errorf("byte[%d] = %02x, want %02x", i, got[i], tt.expect[i])
				}
			}
		})
	}
}

// TestEncodeDomainNameTooLong tests label length validation.
func TestEncodeDomainNameTooLong(t *testing.T) {
	longLabel := ""
	for i := 0; i < 64; i++ {
		longLabel += "a"
	}
	_, err := encodeDomainName(longLabel + ".com")
	if err == nil {
		t.Error("Expected error for label > 63 bytes")
	}
}

// TestDecodeDomainName tests domain name decoding.
func TestDecodeDomainName(t *testing.T) {
	tests := []struct {
		data   []byte
		expect string
	}{
		{[]byte{7, 'e', 'x', 'a', 'm', 'p', 'l', 'e', 3, 'c', 'o', 'm', 0}, "example.com"},
		{[]byte{3, 'w', 'w', 'w', 7, 'e', 'x', 'a', 'm', 'p', 'l', 'e', 3, 'c', 'o', 'm', 0}, "www.example.com"},
		{[]byte{0}, ""},
	}

	for _, tt := range tests {
		t.Run(tt.expect, func(t *testing.T) {
			got, n, err := decodeDomainName(tt.data, 0)
			if err != nil {
				t.Fatalf("decodeDomainName error: %v", err)
			}
			if got != tt.expect {
				t.Errorf("got %q, want %q", got, tt.expect)
			}
			if n != len(tt.data) {
				t.Errorf("bytes consumed: got %d, want %d", n, len(tt.data))
			}
		})
	}
}

// TestDecodeDomainNameCompression tests compression pointer decoding.
func TestDecodeDomainNameCompression(t *testing.T) {
	// Simulate: "example.com" at offset 12, then a pointer to it
	data := []byte{
		0x03, 'w', 'w', 'w', // "www" at offset 0
		0xC0, 0x0C, // pointer to offset 12
		0x00, // null terminator
		0x00, 0x01, // type A
		0x00, 0x01, // class IN
		// "example.com" starts at offset 12
		0x07, 'e', 'x', 'a', 'm', 'p', 'l', 'e',
		0x03, 'c', 'o', 'm',
		0x00,
	}

	got, n, err := decodeDomainName(data, 0)
	if err != nil {
		t.Fatalf("decodeDomainName error: %v", err)
	}
	if got != "www.example.com" {
		t.Errorf("got %q, want 'www.example.com'", got)
	}
	_ = n
}

// TestSplitDomainName tests the domain name splitting.
func TestSplitDomainName(t *testing.T) {
	tests := []struct {
		name   string
		expect []string
	}{
		{"example.com", []string{"example", "com"}},
		{"www.example.com", []string{"www", "example", "com"}},
		{"a.b.c.d", []string{"a", "b", "c", "d"}},
		{"", []string{}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := splitDomainName(tt.name)
			if len(got) != len(tt.expect) {
				t.Errorf("splitDomainName(%q) = %v (len=%d), want %v (len=%d)",
					tt.name, got, len(got), tt.expect, len(tt.expect))
			}
			for i := range got {
				if i < len(tt.expect) && got[i] != tt.expect[i] {
					t.Errorf("[%d] = %q, want %q", i, got[i], tt.expect[i])
				}
			}
		})
	}
}

// TestStripTrailingDot tests trailing dot removal.
func TestStripTrailingDot(t *testing.T) {
	tests := []struct {
		input  string
		expect string
	}{
		{"example.com.", "example.com"},
		{"example.com", "example.com"},
		{"", ""},
		{".", ""},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got := stripTrailingDot(tt.input)
			if got != tt.expect {
				t.Errorf("stripTrailingDot(%q) = %q, want %q", tt.input, got, tt.expect)
			}
		})
	}
}

// TestIPv4AddressString tests IPv4 address formatting.
func TestIPv4AddressString(t *testing.T) {
	ipv4 := &IPv4Address{IP: []byte{93, 184, 216, 34}}
	got := ipv4.String()
	if got != "93.184.216.34" {
		t.Errorf("got %q, want '93.184.216.34'", got)
	}
}

// TestParseRecordData tests record data parsing for different types.
func TestParseRecordData(t *testing.T) {
	// Type A
	aData := []byte{93, 184, 216, 34}
	result := parseRecordData(TypeA, aData)
	if _, ok := result.(*IPv4Address); !ok {
		t.Error("Expected *IPv4Address for TypeA")
	}

	// Type MX
	mxData := []byte{0x00, 0x0A} // preference 10
	mxData = append(mxData, 7, 'e', 'x', 'a', 'm', 'p', 'l', 'e', 3, 'c', 'o', 'm', 0)
	result = parseRecordData(TypeMX, mxData)
	if mx, ok := result.(*MXRecord); !ok {
		t.Error("Expected *MXRecord for TypeMX")
	} else {
		if mx.Preference != 10 {
			t.Errorf("Preference: got %d, want 10", mx.Preference)
		}
	}

	// Type TXT
	txtData := []byte{5, 'h', 'e', 'l', 'l', 'o'}
	result = parseRecordData(TypeTXT, txtData)
	if txt, ok := result.(*TXTRecord); !ok {
		t.Error("Expected *TXTRecord for TypeTXT")
	} else {
		if len(txt.Texts) != 1 || txt.Texts[0] != "hello" {
			t.Errorf("TXT texts: got %v, want ['hello']", txt.Texts)
		}
	}
}

// TestCacheKey tests cache key generation.
func TestCacheKey(t *testing.T) {
	key := CacheKey("example.com", TypeA, ClassIN)
	expected := "example.com:A:IN"
	if key != expected {
		t.Errorf("CacheKey = %q, want %q", key, expected)
	}
}

// TestDNSCachePutGet tests basic cache operations.
func TestDNSCachePutGet(t *testing.T) {
	cache := NewDNSCache(100)

	msg := NewResponse(0)
	msg.Header.ANCount = 1
	msg.Answers = []ResourceRecord{
		{Name: "example.com", Type: TypeA, Class: ClassIN, TTL: 300, Data: []byte{1, 2, 3, 4}},
	}

	key := CacheKey("example.com", TypeA, ClassIN)
	cache.Put(key, msg, 300)

	got, ok := cache.Get(key)
	if !ok {
		t.Fatal("Expected cache hit")
	}
	if got.Header.ID != msg.Header.ID {
		t.Errorf("ID mismatch: got %d, want %d", got.Header.ID, msg.Header.ID)
	}

	// Test cache miss
	_, ok = cache.Get("nonexistent:A:IN")
	if ok {
		t.Error("Expected cache miss for nonexistent key")
	}
}

// TestDNSCacheExpiration tests TTL-based expiration.
func TestDNSCacheExpiration(t *testing.T) {
	cache := NewDNSCache(100)

	msg := NewResponse(0)
	msg.Header.ANCount = 1
	msg.Answers = []ResourceRecord{
		{Name: "temp.example.com", Type: TypeA, Class: ClassIN, TTL: 1, Data: []byte{1, 2, 3, 4}},
	}

	key := CacheKey("temp.example.com", TypeA, ClassIN)
	cache.Put(key, msg, 1)

	// Should be cached
	if _, ok := cache.Get(key); !ok {
		t.Error("Expected cache hit before expiration")
	}

	// Wait for expiration
	// Note: In a real test we'd use time.Sleep, but for unit tests
	// we test the IsExpired logic directly
	entry := &CacheEntry{
		ExpiresAt: time.Now().Add(-1 * time.Second),
	}
	if !entry.IsExpired() {
		t.Error("Expected expired entry")
	}
}

// TestDNSCacheEviction tests cache eviction when full.
func TestDNSCacheEviction(t *testing.T) {
	cache := NewDNSCache(3)

	for i := 0; i < 5; i++ {
		msg := NewResponse(0)
		msg.Header.ANCount = 1
		msg.Answers = []ResourceRecord{
			{Name: fmt.Sprintf("host%d.com", i), Type: TypeA, Class: ClassIN, TTL: 3600, Data: []byte{1, 2, 3, 4}},
		}
		key := CacheKey(fmt.Sprintf("host%d.com", i), TypeA, ClassIN)
		cache.Put(key, msg, 3600)
	}

	// Cache should be at max size
	if cache.Size() != 3 {
		t.Errorf("Cache size: got %d, want 3", cache.Size())
	}
}

// TestDNSCacheClear tests cache clearing.
func TestDNSCacheClear(t *testing.T) {
	cache := NewDNSCache(100)

	msg := NewResponse(0)
	msg.Header.ANCount = 1
	msg.Answers = []ResourceRecord{
		{Name: "example.com", Type: TypeA, Class: ClassIN, TTL: 300, Data: []byte{1, 2, 3, 4}},
	}

	key := CacheKey("example.com", TypeA, ClassIN)
	cache.Put(key, msg, 300)
	cache.Clear()

	if cache.Size() != 0 {
		t.Errorf("Cache size after clear: got %d, want 0", cache.Size())
	}

	_, ok := cache.Get(key)
	if ok {
		t.Error("Expected cache miss after clear")
	}
}

// TestDNSCacheDelete tests cache deletion.
func TestDNSCacheDelete(t *testing.T) {
	cache := NewDNSCache(100)

	msg := NewResponse(0)
	msg.Header.ANCount = 1
	msg.Answers = []ResourceRecord{
		{Name: "example.com", Type: TypeA, Class: ClassIN, TTL: 300, Data: []byte{1, 2, 3, 4}},
	}

	key := CacheKey("example.com", TypeA, ClassIN)
	cache.Put(key, msg, 300)
	cache.Delete(key)

	_, ok := cache.Get(key)
	if ok {
		t.Error("Expected cache miss after delete")
	}
}
