package resolver

import (
	"net"
	"testing"

	"github.com/anthropic/dns-server/internal/protocol"
)

func TestResolverLocalZone(t *testing.T) {
	r := New()

	// Add local zone records
	r.AddARecord("local.test", net.ParseIP("10.0.0.1"))
	r.AddARecord("local.test", net.ParseIP("10.0.0.2"))

	q := protocol.Question{
		Name:  "local.test",
		Type:  protocol.TypeA,
		Class: protocol.ClassIN,
	}

	records, rcode := r.Resolve(q)
	if rcode != protocol.RcodeNoError {
		t.Fatalf("expected NOERROR, got %d", rcode)
	}
	if len(records) != 2 {
		t.Fatalf("expected 2 records, got %d", len(records))
	}
	if records[0].RData[3] != 1 {
		t.Errorf("expected last octet 1, got %d", records[0].RData[3])
	}
}

func TestResolverLocalZoneTypeMismatch(t *testing.T) {
	r := New()
	r.AddARecord("only-a.test", net.ParseIP("10.0.0.1"))

	// Query for AAAA when only A exists -- should fall through to upstream
	q := protocol.Question{
		Name:  "only-a.test",
		Type:  protocol.TypeAAAA,
		Class: protocol.ClassIN,
	}

	// This will try upstream and likely fail (no network), but should not crash
	records, rcode := r.Resolve(q)
	_ = records
	// We accept any result here; the important thing is it doesn't panic
	_ = rcode
}

func TestZoneBuilder(t *testing.T) {
	records := NewZoneBuilder("example.test").
		A(net.ParseIP("192.168.1.1")).
		AAAA(net.ParseIP("::1")).
		Build()

	if len(records) != 2 {
		t.Fatalf("expected 2 records, got %d", len(records))
	}
	if records[0].Type != protocol.TypeA {
		t.Errorf("expected first record type A, got %d", records[0].Type)
	}
	if records[1].Type != protocol.TypeAAAA {
		t.Errorf("expected second record type AAAA, got %d", records[1].Type)
	}
}

func TestBuildARecord(t *testing.T) {
	ip := net.ParseIP("1.2.3.4")
	rr := BuildARecord("test.com", ip, 60)

	if rr.Name != "test.com" {
		t.Errorf("expected name test.com, got %s", rr.Name)
	}
	if rr.Type != protocol.TypeA {
		t.Errorf("expected type A, got %d", rr.Type)
	}
	if rr.TTL != 60 {
		t.Errorf("expected TTL 60, got %d", rr.TTL)
	}
	if len(rr.RData) != 4 {
		t.Fatalf("expected RData length 4, got %d", len(rr.RData))
	}
	if rr.RData[0] != 1 || rr.RData[1] != 2 || rr.RData[2] != 3 || rr.RData[3] != 4 {
		t.Errorf("expected RData 1.2.3.4, got %v", rr.RData)
	}
}

func TestParseAResponse(t *testing.T) {
	rdata := []byte{192, 168, 0, 1}
	ip, err := ParseAResponse(rdata)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if ip.String() != "192.168.0.1" {
		t.Errorf("expected 192.168.0.1, got %s", ip.String())
	}

	// Invalid length
	_, err = ParseAResponse([]byte{1, 2})
	if err == nil {
		t.Error("expected error for invalid RData length")
	}
}

func TestFormatResponse(t *testing.T) {
	q := protocol.Question{Name: "example.com", Type: protocol.TypeA, Class: protocol.ClassIN}
	records := []protocol.ResourceRecord{
		{Name: "example.com", Type: protocol.TypeA, TTL: 300, RDLen: 4, RData: []byte{93, 184, 216, 34}},
	}

	result := FormatResponse(q, records, protocol.RcodeNoError)
	if result == "" {
		t.Error("expected non-empty response format")
	}
}

func TestUInt16ToBytes(t *testing.T) {
	b := UInt16ToBytes(0x0100)
	if b[0] != 1 || b[1] != 0 {
		t.Errorf("expected [1, 0], got %v", b)
	}
}

func TestEncodeCNAME(t *testing.T) {
	rdata := encodeCNAME("target.example.com")
	expected := byte(6)
	if rdata[0] != expected {
		t.Errorf("expected first byte %d (label len for 'target'), got %d", expected, rdata[0])
	}
}

func TestMakeResponseRData(t *testing.T) {
	ip := net.ParseIP("10.0.0.1")
	rdata := MakeResponseRData(ip)
	if len(rdata) != 4 {
		t.Fatalf("expected 4 bytes, got %d", len(rdata))
	}
	if rdata[0] != 10 || rdata[3] != 1 {
		t.Errorf("expected 10.x.x.1, got %v", rdata)
	}

	// IPv6 should return nil for To4
	ip6 := net.ParseIP("::1")
	rdata = MakeResponseRData(ip6)
	if rdata != nil {
		t.Error("expected nil for IPv6 address in MakeResponseRData")
	}
}
