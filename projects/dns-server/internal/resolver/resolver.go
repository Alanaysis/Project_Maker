// Package resolver implements DNS name resolution by forwarding queries
// to upstream DNS servers and combining results with local configuration.
//
// Resolution strategy:
//  1. Check local zone records (authoritative answers)
//  2. Forward to upstream DNS server (e.g., 8.8.8.8)
//  3. Return NXDOMAIN if upstream returns no results
//
// This is a "recursive resolver" -- it handles the full resolution on behalf
// of the client rather than returning referrals to other nameservers.
package resolver

import (
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"time"

	"github.com/anthropic/dns-server/internal/protocol"
)

// UpstreamServer is the default upstream DNS server address.
const UpstreamServer = "8.8.8.8:53"

// QueryTimeout is the maximum time to wait for an upstream response.
const QueryTimeout = 5 * time.Second

// Resolver handles DNS name resolution.
type Resolver struct {
	// upstream is the address of the upstream DNS server.
	upstream string
	// zones holds local zone records for authoritative responses.
	zones map[string][]protocol.ResourceRecord
	// timeout for upstream queries.
	timeout time.Duration
}

// Option is a functional option for Resolver.
type Option func(*Resolver)

// WithUpstream sets the upstream DNS server address.
func WithUpstream(addr string) Option {
	return func(r *Resolver) {
		r.upstream = addr
	}
}

// WithTimeout sets the query timeout.
func WithTimeout(d time.Duration) Option {
	return func(r *Resolver) {
		r.timeout = d
	}
}

// New creates a new Resolver.
func New(opts ...Option) *Resolver {
	r := &Resolver{
		upstream: UpstreamServer,
		zones:    make(map[string][]protocol.ResourceRecord),
		timeout:  QueryTimeout,
	}
	for _, opt := range opts {
		opt(r)
	}
	return r
}

// AddZoneRecord adds a local zone record for authoritative answers.
func (r *Resolver) AddZoneRecord(name string, record protocol.ResourceRecord) {
	r.zones[name] = append(r.zones[name], record)
}

// AddARecord is a convenience method to add an A record to the local zone.
func (r *Resolver) AddARecord(name string, ip net.IP) {
	r.AddZoneRecord(name, protocol.ResourceRecord{
		Name:  name,
		Type:  protocol.TypeA,
		Class: protocol.ClassIN,
		TTL:   86400, // 24 hours for local records
		RDLen: 4,
		RData: ip.To4(),
	})
}

// Resolve performs DNS resolution for a single question.
// Returns resource records and a response code.
func (r *Resolver) Resolve(q protocol.Question) ([]protocol.ResourceRecord, uint8) {
	// Step 1: Check local zones
	if records, ok := r.zones[q.Name]; ok {
		var matched []protocol.ResourceRecord
		for _, rr := range records {
			if rr.Type == q.Type || q.Type == protocol.TypeANY {
				matched = append(matched, rr)
			}
		}
		if len(matched) > 0 {
			log.Printf("[resolver] local zone hit: %s %s -> %d records",
				q.Name, protocol.TypeName(q.Type), len(matched))
			return matched, protocol.RcodeNoError
		}
	}

	// Step 2: Forward to upstream
	log.Printf("[resolver] forwarding to upstream: %s %s", q.Name, protocol.TypeName(q.Type))
	records, rcode := r.forwardToUpstream(q)
	if rcode != protocol.RcodeNoError {
		return nil, rcode
	}

	log.Printf("[resolver] upstream returned %d records for %s", len(records), q.Name)
	return records, protocol.RcodeNoError
}

// forwardToUpstream sends a query to the upstream DNS server and returns the answer.
func (r *Resolver) forwardToUpstream(q protocol.Question) ([]protocol.ResourceRecord, uint8) {
	// Build the query message
	query := &protocol.Message{
		Header: protocol.Header{
			ID:      generateID(),
			QR:      protocol.QRQuery,
			Opcode:  protocol.OpcodeQuery,
			RD:      true, // Request recursion
			QDCount: 1,
		},
		Question: []protocol.Question{q},
	}

	queryData, err := query.Pack()
	if err != nil {
		log.Printf("[resolver] failed to pack query: %v", err)
		return nil, protocol.RcodeServFail
	}

	// Send via UDP
	conn, err := net.DialTimeout("udp", r.upstream, r.timeout)
	if err != nil {
		log.Printf("[resolver] failed to connect to upstream %s: %v", r.upstream, err)
		return nil, protocol.RcodeServFail
	}
	defer conn.Close()

	if err := conn.SetDeadline(time.Now().Add(r.timeout)); err != nil {
		log.Printf("[resolver] failed to set deadline: %v", err)
		return nil, protocol.RcodeServFail
	}

	_, err = conn.Write(queryData)
	if err != nil {
		log.Printf("[resolver] failed to send query: %v", err)
		return nil, protocol.RcodeServFail
	}

	// Read response
	buf := make([]byte, protocol.MaxUDPPayloadSize)
	n, err := conn.Read(buf)
	if err != nil {
		log.Printf("[resolver] failed to read response: %v", err)
		return nil, protocol.RcodeServFail
	}

	// Parse response
	resp, err := protocol.Unpack(buf[:n])
	if err != nil {
		log.Printf("[resolver] failed to parse response: %v", err)
		return nil, protocol.RcodeServFail
	}

	if resp.Header.RCODE != protocol.RcodeNoError {
		return nil, resp.Header.RCODE
	}

	return resp.Answer, protocol.RcodeNoError
}

// generateID generates a random 16-bit transaction ID.
func generateID() uint16 {
	return uint16(time.Now().UnixNano() & 0xFFFF)
}

// ─── Local Zone Builder ──────────────────────────────────────────────────────

// ZoneBuilder provides a fluent API for building local zone records.
type ZoneBuilder struct {
	domain  string
	records []protocol.ResourceRecord
}

// NewZoneBuilder creates a new zone builder for a domain.
func NewZoneBuilder(domain string) *ZoneBuilder {
	return &ZoneBuilder{domain: domain}
}

// A adds an A record.
func (zb *ZoneBuilder) A(ip net.IP) *ZoneBuilder {
	zb.records = append(zb.records, protocol.ResourceRecord{
		Name:  zb.domain,
		Type:  protocol.TypeA,
		Class: protocol.ClassIN,
		TTL:   3600,
		RDLen: 4,
		RData: ip.To4(),
	})
	return zb
}

// AAAA adds an AAAA record.
func (zb *ZoneBuilder) AAAA(ip net.IP) *ZoneBuilder {
	zb.records = append(zb.records, protocol.ResourceRecord{
		Name:  zb.domain,
		Type:  protocol.TypeAAAA,
		Class: protocol.ClassIN,
		TTL:   3600,
		RDLen: 16,
		RData: ip.To16(),
	})
	return zb
}

// CNAME adds a CNAME record.
func (zb *ZoneBuilder) CNAME(target string) *ZoneBuilder {
	rdata := encodeCNAME(target)
	zb.records = append(zb.records, protocol.ResourceRecord{
		Name:  zb.domain,
		Type:  protocol.TypeCNAME,
		Class: protocol.ClassIN,
		TTL:   3600,
		RDLen: uint16(len(rdata)),
		RData: rdata,
	})
	return zb
}

// Build returns the accumulated records.
func (zb *ZoneBuilder) Build() []protocol.ResourceRecord {
	return zb.records
}

// encodeCNAME encodes a CNAME target into DNS wire format.
func encodeCNAME(target string) []byte {
	var buf []byte
	if target[len(target)-1] != '.' {
		target += "."
	}
	start := 0
	for i := 0; i < len(target); i++ {
		if target[i] == '.' {
			if i > start {
				buf = append(buf, byte(i-start))
				buf = append(buf, target[start:i]...)
			}
			start = i + 1
		}
	}
	buf = append(buf, 0)
	return buf
}

// FormatResponse formats a DNS response for logging.
func FormatResponse(q protocol.Question, records []protocol.ResourceRecord, rcode uint8) string {
	s := fmt.Sprintf("%s %s -> %s (%d answers)",
		q.Name, protocol.TypeName(q.Type), protocol.RcodeName(rcode), len(records))
	for _, rr := range records {
		switch rr.Type {
		case protocol.TypeA:
			s += fmt.Sprintf("\n  A %s (TTL=%d)", protocol.FormatRecordA(rr.RData), rr.TTL)
		case protocol.TypeAAAA:
			s += fmt.Sprintf("\n  AAAA %s (TTL=%d)", protocol.FormatRecordAAAA(rr.RData), rr.TTL)
		default:
			s += fmt.Sprintf("\n  %s (TTL=%d, len=%d)", protocol.TypeName(rr.Type), rr.TTL, rr.RDLen)
		}
	}
	return s
}

// MakeResponseRData creates RData for an A record from an IP address.
func MakeResponseRData(ip net.IP) []byte {
	ip4 := ip.To4()
	if ip4 == nil {
		return nil
	}
	buf := make([]byte, 4)
	copy(buf, ip4)
	return buf
}

// ParseAResponse extracts the IP address from an A record's RData.
func ParseAResponse(rdata []byte) (net.IP, error) {
	if len(rdata) != 4 {
		return nil, fmt.Errorf("invalid A record RData length: %d", len(rdata))
	}
	return net.IPv4(rdata[0], rdata[1], rdata[2], rdata[3]), nil
}

// BuildARecord builds a ResourceRecord for an A answer.
func BuildARecord(name string, ip net.IP, ttl uint32) protocol.ResourceRecord {
	ip4 := ip.To4()
	return protocol.ResourceRecord{
		Name:  name,
		Type:  protocol.TypeA,
		Class: protocol.ClassIN,
		TTL:   ttl,
		RDLen: 4,
		RData: ip4,
	}
}

// UInt16ToBytes converts a uint16 to big-endian bytes.
func UInt16ToBytes(v uint16) []byte {
	b := make([]byte, 2)
	binary.BigEndian.PutUint16(b, v)
	return b
}
