package protocol

import (
	"encoding/binary"
	"testing"
)

func TestHeaderPackUnpack(t *testing.T) {
	original := Header{
		ID:      0xABCD,
		QR:      QRResponse,
		Opcode:  OpcodeQuery,
		AA:      true,
		TC:      false,
		RD:      true,
		RA:      true,
		Z:       0,
		RCODE:   RcodeNoError,
		QDCount: 1,
		ANCount: 2,
		NSCount: 0,
		ARCount: 0,
	}

	packed := original.Pack()
	if len(packed) != HeaderSize {
		t.Fatalf("expected header size %d, got %d", HeaderSize, len(packed))
	}

	parsed, err := UnpackHeader(packed)
	if err != nil {
		t.Fatalf("UnpackHeader failed: %v", err)
	}

	assertEqual(t, "ID", original.ID, parsed.ID)
	assertEqual(t, "QR", original.QR, parsed.QR)
	assertEqual(t, "Opcode", original.Opcode, parsed.Opcode)
	assertEqualBool(t, "AA", original.AA, parsed.AA)
	assertEqualBool(t, "TC", original.TC, parsed.TC)
	assertEqualBool(t, "RD", original.RD, parsed.RD)
	assertEqualBool(t, "RA", original.RA, parsed.RA)
	assertEqual(t, "RCODE", original.RCODE, parsed.RCODE)
	assertEqual(t, "QDCount", original.QDCount, parsed.QDCount)
	assertEqual(t, "ANCount", original.ANCount, parsed.ANCount)
	assertEqual(t, "NSCount", original.NSCount, parsed.NSCount)
	assertEqual(t, "ARCount", original.ARCount, parsed.ARCount)
}

func TestPackDomainName(t *testing.T) {
	tests := []struct {
		name     string
		expected []byte
	}{
		{"www.example.com", []byte("\x03www\x07example\x03com\x00")},
		{"example.com", []byte("\x07example\x03com\x00")},
		{".", []byte{0}},
		{"", []byte{0}},
	}

	for _, tt := range tests {
		result := packDomainName(tt.name)
		if len(result) != len(tt.expected) {
			t.Errorf("packDomainName(%q): expected len %d, got %d", tt.name, len(tt.expected), len(result))
			continue
		}
		for i := range result {
			if result[i] != tt.expected[i] {
				t.Errorf("packDomainName(%q): byte[%d] expected %d, got %d", tt.name, i, tt.expected[i], result[i])
			}
		}
	}
}

func TestUnpackDomainName(t *testing.T) {
	tests := []struct {
		input    []byte
		name     string
		offset   int
	}{
		{[]byte("\x03www\x07example\x03com\x00"), "www.example.com", 0},
		{[]byte("\x07example\x03com\x00"), "example.com", 0},
		{[]byte("\x00"), "", 0},
	}

	for _, tt := range tests {
		name, newOffset, err := unpackDomainName(tt.input, 0)
		if err != nil {
			t.Errorf("unpackDomainName(%v): unexpected error: %v", tt.input, err)
			continue
		}
		if name != tt.name {
			t.Errorf("unpackDomainName(%v): expected %q, got %q", tt.input, tt.name, name)
		}
		if newOffset != len(tt.input) {
			t.Errorf("unpackDomainName(%v): expected offset %d, got %d", tt.input, len(tt.input), newOffset)
		}
	}
}

func TestCompressionPointer(t *testing.T) {
	// Build a message with compression:
	// Question: www.example.com (starts at offset 12)
	// Answer: mail.example.com -> pointer to offset 15 ("example.com")
	data := make([]byte, 12) // Header placeholder
	data[4] = 0              // QDCount high
	data[5] = 1              // QDCount low
	data[6] = 0              // ANCount high
	data[7] = 1              // ANCount low

	// Question: www.example.com
	question := packDomainName("www.example.com")
	data = append(data, question...)
	data = append(data, 0, 1) // Type A
	data = append(data, 0, 1) // Class IN

	// Answer: mail.example.com using compression pointer
	// "mail" label at current position, then pointer to offset 12+4=16 (start of "example")
	data = append(data, 4) // label length
	data = append(data, "mail"...)
	// Pointer to where "example" starts: offset 12 + 4 (length of "www") = 16
	pointer := uint16(16) | 0xC000
	pData := make([]byte, 2)
	binary.BigEndian.PutUint16(pData, pointer)
	data = append(data, pData...)

	// Type A, Class IN, TTL, RDLen, RData
	data = append(data, 0, 1, 0, 1) // Type A, Class IN
	data = append(data, 0, 0, 0, 60) // TTL = 60
	data = append(data, 0, 4)        // RDLen = 4
	data = append(data, 192, 168, 1, 1) // RData = 192.168.1.1

	msg, err := Unpack(data)
	if err != nil {
		t.Fatalf("Unpack with compression pointer failed: %v", err)
	}

	if len(msg.Question) != 1 {
		t.Fatalf("expected 1 question, got %d", len(msg.Question))
	}
	if msg.Question[0].Name != "www.example.com" {
		t.Errorf("expected question name www.example.com, got %s", msg.Question[0].Name)
	}

	if len(msg.Answer) != 1 {
		t.Fatalf("expected 1 answer, got %d", len(msg.Answer))
	}
	if msg.Answer[0].Name != "mail.example.com" {
		t.Errorf("expected answer name mail.example.com, got %s", msg.Answer[0].Name)
	}
	if msg.Answer[0].Type != TypeA {
		t.Errorf("expected answer type A, got %d", msg.Answer[0].Type)
	}
	if len(msg.Answer[0].RData) != 4 {
		t.Fatalf("expected RData length 4, got %d", len(msg.Answer[0].RData))
	}
	if msg.Answer[0].RData[0] != 192 || msg.Answer[0].RData[1] != 168 ||
		msg.Answer[0].RData[2] != 1 || msg.Answer[0].RData[3] != 1 {
		t.Errorf("expected RData 192.168.1.1, got %v", msg.Answer[0].RData)
	}
}

func TestRoundTrip(t *testing.T) {
	// Build a message, pack it, then unpack and verify
	original := &Message{
		Header: Header{
			ID:      1234,
			QR:      QRResponse,
			Opcode:  OpcodeQuery,
			RD:      true,
			RA:      true,
			QDCount: 1,
			ANCount: 1,
		},
		Question: []Question{
			{Name: "example.com", Type: TypeA, Class: ClassIN},
		},
		Answer: []ResourceRecord{
			{
				Name:  "example.com",
				Type:  TypeA,
				Class: ClassIN,
				TTL:   300,
				RDLen: 4,
				RData: []byte{93, 184, 216, 34},
			},
		},
	}

	packed, err := original.Pack()
	if err != nil {
		t.Fatalf("Pack failed: %v", err)
	}

	parsed, err := Unpack(packed)
	if err != nil {
		t.Fatalf("Unpack failed: %v", err)
	}

	if parsed.Header.ID != original.Header.ID {
		t.Errorf("ID mismatch: %d != %d", parsed.Header.ID, original.Header.ID)
	}
	if parsed.Header.QR != original.Header.QR {
		t.Errorf("QR mismatch")
	}
	if len(parsed.Question) != 1 {
		t.Fatalf("expected 1 question, got %d", len(parsed.Question))
	}
	if parsed.Question[0].Name != "example.com" {
		t.Errorf("question name mismatch: %q", parsed.Question[0].Name)
	}
	if len(parsed.Answer) != 1 {
		t.Fatalf("expected 1 answer, got %d", len(parsed.Answer))
	}
	if parsed.Answer[0].TTL != 300 {
		t.Errorf("TTL mismatch: %d", parsed.Answer[0].TTL)
	}
	if parsed.Answer[0].RData[0] != 93 {
		t.Errorf("RData mismatch")
	}
}

func TestTypeName(t *testing.T) {
	tests := []struct {
		t    uint16
		want string
	}{
		{TypeA, "A"},
		{TypeAAAA, "AAAA"},
		{TypeCNAME, "CNAME"},
		{TypeMX, "MX"},
		{999, "TYPE999"},
	}
	for _, tt := range tests {
		if got := TypeName(tt.t); got != tt.want {
			t.Errorf("TypeName(%d) = %q, want %q", tt.t, got, tt.want)
		}
	}
}

func TestRcodeName(t *testing.T) {
	tests := []struct {
		r    uint8
		want string
	}{
		{RcodeNoError, "NOERROR"},
		{RcodeNXDomain, "NXDOMAIN"},
		{RcodeServFail, "SERVFAIL"},
		{99, "RCODE99"},
	}
	for _, tt := range tests {
		if got := RcodeName(tt.r); got != tt.want {
			t.Errorf("RcodeName(%d) = %q, want %q", tt.r, got, tt.want)
		}
	}
}

func TestMalformedMessage(t *testing.T) {
	tests := []struct {
		name string
		data []byte
	}{
		{"empty", []byte{}},
		{"too short", []byte{0, 1, 2}},
		{"truncated question", func() []byte {
			h := Header{ID: 1, QDCount: 1}
			data := h.Pack()
			data = append(data, 3) // label length 3 but no label data
			return data
		}()},
	}
	for _, tt := range tests {
		_, err := Unpack(tt.data)
		if err == nil {
			t.Errorf("%s: expected error, got nil", tt.name)
		}
	}
}

func TestFormatRecordA(t *testing.T) {
	rdata := []byte{192, 168, 1, 1}
	result := FormatRecordA(rdata)
	if result != "192.168.1.1" {
		t.Errorf("FormatRecordA: expected 192.168.1.1, got %s", result)
	}

	// Invalid length
	result = FormatRecordA([]byte{1, 2})
	if result != "<invalid>" {
		t.Errorf("FormatRecordA invalid: expected <invalid>, got %s", result)
	}
}

func TestSplitLabels(t *testing.T) {
	tests := []struct {
		input string
		want  []string
	}{
		{"www.example.com", []string{"www", "example", "com"}},
		{"example.com", []string{"example", "com"}},
		{"com", []string{"com"}},
	}
	for _, tt := range tests {
		got := splitLabels(tt.input)
		if len(got) != len(tt.want) {
			t.Errorf("splitLabels(%q): expected %v, got %v", tt.input, tt.want, got)
			continue
		}
		for i := range got {
			if got[i] != tt.want[i] {
				t.Errorf("splitLabels(%q)[%d]: expected %q, got %q", tt.input, i, tt.want[i], got[i])
			}
		}
	}
}

// Helper assertions
func assertEqual[T comparable](t *testing.T, field string, expected, actual T) {
	t.Helper()
	if expected != actual {
		t.Errorf("%s: expected %v, got %v", field, expected, actual)
	}
}

func assertEqualBool(t *testing.T, field string, expected, actual bool) {
	t.Helper()
	if expected != actual {
		t.Errorf("%s: expected %v, got %v", field, expected, actual)
	}
}
