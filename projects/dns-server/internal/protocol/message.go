// Package protocol implements DNS message parsing and serialization
// according to RFC 1035 (Domain Names - Implementation and Specification).
//
// DNS Message Format:
//   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
//   |                      ID                           |
//   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
//   |QR|   Opcode  |AA|TC|RD| RA|   Z    |   RCODE    |
//   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
//   |                    QDCOUNT                         |
//   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
//   |                    ANCOUNT                         |
//   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
//   |                    NSCOUNT                         |
//   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
//   |                    ARCOUNT                         |
//   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
package protocol

import (
	"encoding/binary"
	"errors"
	"fmt"
)

// ─── Constants ───────────────────────────────────────────────────────────────

// DNS header size in bytes (fixed 12 bytes).
const HeaderSize = 12

// Maximum UDP payload size for DNS.
const MaxUDPPayloadSize = 512

// ─── Header Flags ────────────────────────────────────────────────────────────

// QR bit values.
const (
	QRQuery    uint8 = 0 // Query
	QRResponse uint8 = 1 // Response
)

// Opcodes.
const (
	OpcodeQuery  uint8 = 0 // Standard query
	OpcodeIQuery uint8 = 1 // Inverse query
	OpcodeStatus uint8 = 2 // Status
)

// Response codes (RCODE).
const (
	RcodeNoError   uint8 = 0
	RcodeFormErr   uint8 = 1 // Format error
	RcodeServFail  uint8 = 2 // Server failure
	RcodeNXDomain  uint8 = 3 // Non-existent domain
	RcodeNotImp    uint8 = 4 // Not implemented
	RcodeRefused   uint8 = 5 // Query refused
)

// ─── Record Types ────────────────────────────────────────────────────────────

// DNS record types.
const (
	TypeA     uint16 = 1   // A record (IPv4 address)
	TypeNS    uint16 = 2   // NS record (name server)
	TypeCNAME uint16 = 5   // CNAME record (canonical name)
	TypeSOA   uint16 = 6   // SOA record (start of authority)
	TypeMX    uint16 = 15  // MX record (mail exchange)
	TypeTXT   uint16 = 16  // TXT record (text)
	TypeAAAA  uint16 = 28  // AAAA record (IPv6 address)
	TypeSRV   uint16 = 33  // SRV record (service)
	TypeOPT   uint16 = 41  // OPT record (EDNS)
	TypeANY   uint16 = 255 // ANY record
)

// ─── Record Classes ──────────────────────────────────────────────────────────

// DNS record classes.
const (
	ClassIN  uint16 = 1   // Internet
	ClassCS  uint16 = 2   // CSNET (obsolete)
	ClassCH  uint16 = 3   // Chaos
	ClassHS  uint16 = 4   // Hesiod
	ClassAny uint16 = 255 // Any class
)

// ─── Errors ──────────────────────────────────────────────────────────────────

var (
	ErrMalformedMessage  = errors.New("dns: malformed message")
	ErrMessageTooShort   = errors.New("dns: message too short")
	ErrInvalidDomainName = errors.New("dns: invalid domain name")
	ErrCompressionLoop   = errors.New("dns: compression pointer loop detected")
)

// ─── Header ──────────────────────────────────────────────────────────────────

// Header represents the 12-byte DNS message header.
//
// Bits layout:
//   ID(16) | QR(1) | OPCODE(4) | AA(1) | TC(1) | RD(1) | RA(1) | Z(3) | RCODE(4)
type Header struct {
	ID      uint16 // Transaction ID
	QR      uint8  // Query (0) or Response (1)
	Opcode  uint8  // Operation code
	AA      bool   // Authoritative Answer
	TC      bool   // Truncation
	RD      bool   // Recursion Desired
	RA      bool   // Recursion Available
	Z       uint8  // Reserved (must be zero)
	RCODE   uint8  // Response code
	QDCount uint16 // Number of entries in the question section
	ANCount uint16 // Number of resource records in the answer section
	NSCount uint16 // Number of name server resource records in the authority section
	ARCount uint16 // Number of resource records in the additional records section
}

// Pack serializes the header into 12 bytes.
func (h *Header) Pack() []byte {
	buf := make([]byte, HeaderSize)
	binary.BigEndian.PutUint16(buf[0:2], h.ID)

	// Third byte: QR(1) | OPCODE(4) | AA(1) | TC(1) | RD(1)
	flags1 := uint8(0)
	if h.QR == 1 {
		flags1 |= 0x80
	}
	flags1 |= (h.Opcode & 0x0F) << 3
	if h.AA {
		flags1 |= 0x04
	}
	if h.TC {
		flags1 |= 0x02
	}
	if h.RD {
		flags1 |= 0x01
	}
	buf[2] = flags1

	// Fourth byte: RA(1) | Z(3) | RCODE(4)
	flags2 := uint8(0)
	if h.RA {
		flags2 |= 0x80
	}
	flags2 |= (h.Z & 0x07) << 4
	flags2 |= h.RCODE & 0x0F
	buf[3] = flags2

	binary.BigEndian.PutUint16(buf[4:6], h.QDCount)
	binary.BigEndian.PutUint16(buf[6:8], h.ANCount)
	binary.BigEndian.PutUint16(buf[8:10], h.NSCount)
	binary.BigEndian.PutUint16(buf[10:12], h.ARCount)
	return buf
}

// UnpackHeader parses a DNS header from the first 12 bytes of data.
func UnpackHeader(data []byte) (*Header, error) {
	if len(data) < HeaderSize {
		return nil, ErrMessageTooShort
	}

	h := &Header{
		ID:      binary.BigEndian.Uint16(data[0:2]),
		QDCount: binary.BigEndian.Uint16(data[4:6]),
		ANCount: binary.BigEndian.Uint16(data[6:8]),
		NSCount: binary.BigEndian.Uint16(data[8:10]),
		ARCount: binary.BigEndian.Uint16(data[10:12]),
	}

	flags1 := data[2]
	h.QR = (flags1 >> 7) & 0x01
	h.Opcode = (flags1 >> 3) & 0x0F
	h.AA = (flags1>>2)&0x01 != 0
	h.TC = (flags1>>1)&0x01 != 0
	h.RD = flags1 & 0x01 != 0

	flags2 := data[3]
	h.RA = (flags2>>7)&0x01 != 0
	h.Z = (flags2 >> 4) & 0x07
	h.RCODE = flags2 & 0x0F

	return h, nil
}

// ─── Question ────────────────────────────────────────────────────────────────

// Question represents a DNS query question section.
type Question struct {
	Name  string // Domain name to query
	Type  uint16 // Record type (A, AAAA, CNAME, etc.)
	Class uint16 // Record class (usually IN=1)
}

// Pack serializes the question into bytes.
func (q *Question) Pack() []byte {
	buf := packDomainName(q.Name)
	buf = append(buf, 0, 0) // Placeholder for compression-free packing
	binary.BigEndian.PutUint16(buf[len(buf)-2:], q.Type)
	buf = append(buf, 0, 0)
	binary.BigEndian.PutUint16(buf[len(buf)-2:], q.Class)
	return buf
}

// ─── Resource Record ─────────────────────────────────────────────────────────

// ResourceRecord represents a DNS resource record (answer, authority, or additional).
type ResourceRecord struct {
	Name   string // Domain name
	Type   uint16 // Record type
	Class  uint16 // Record class
	TTL    uint32 // Time to live in seconds
	RDLen  uint16 // Length of RData
	RData  []byte // Raw record data
}

// Pack serializes the resource record into bytes.
func (rr *ResourceRecord) Pack() []byte {
	buf := packDomainName(rr.Name)
	var tmp [10]byte
	binary.BigEndian.PutUint16(tmp[0:2], rr.Type)
	binary.BigEndian.PutUint16(tmp[2:4], rr.Class)
	binary.BigEndian.PutUint32(tmp[4:8], rr.TTL)
	binary.BigEndian.PutUint16(tmp[8:10], rr.RDLen)
	buf = append(buf, tmp[:]...)
	buf = append(buf, rr.RData...)
	return buf
}

// A returns the IPv4 address from an A record's RData (4 bytes).
func (rr *ResourceRecord) A() []byte {
	if rr.Type == TypeA && len(rr.RData) == 4 {
		return rr.RData
	}
	return nil
}

// AAAA returns the IPv6 address from an AAAA record's RData (16 bytes).
func (rr *ResourceRecord) AAAA() []byte {
	if rr.Type == TypeAAAA && len(rr.RData) == 16 {
		return rr.RData
	}
	return nil
}

// ─── Message ─────────────────────────────────────────────────────────────────

// Message represents a complete DNS message.
type Message struct {
	Header     Header
	Question   []Question
	Answer     []ResourceRecord
	Authority  []ResourceRecord
	Additional []ResourceRecord
}

// Pack serializes the complete DNS message into bytes.
func (m *Message) Pack() ([]byte, error) {
	// Recount sections before packing
	m.Header.QDCount = uint16(len(m.Question))
	m.Header.ANCount = uint16(len(m.Answer))
	m.Header.NSCount = uint16(len(m.Authority))
	m.Header.ARCount = uint16(len(m.Additional))

	buf := m.Header.Pack()

	for _, q := range m.Question {
		buf = append(buf, q.Pack()...)
	}
	for _, rr := range m.Answer {
		buf = append(buf, rr.Pack()...)
	}
	for _, rr := range m.Authority {
		buf = append(buf, rr.Pack()...)
	}
	for _, rr := range m.Additional {
		buf = append(buf, rr.Pack()...)
	}

	if len(buf) > MaxUDPPayloadSize {
		m.Header.TC = true
		// Re-pack with TC flag set
		buf = m.Header.Pack()
		for _, q := range m.Question {
			buf = append(buf, q.Pack()...)
		}
	}

	return buf, nil
}

// ─── Parsing Functions ───────────────────────────────────────────────────────

// Unpack parses raw bytes into a DNS Message.
func Unpack(data []byte) (*Message, error) {
	if len(data) < HeaderSize {
		return nil, ErrMessageTooShort
	}

	msg := &Message{}
	var err error

	msg.Header, err = UnpackHeader(data)
	if err != nil {
		return nil, err
	}

	offset := HeaderSize

	// Parse question section
	msg.Question, offset, err = unpackQuestions(data, offset, int(msg.Header.QDCount))
	if err != nil {
		return nil, fmt.Errorf("parsing questions: %w", err)
	}

	// Parse answer section
	msg.Answer, offset, err = unpackResourceRecords(data, offset, int(msg.Header.ANCount))
	if err != nil {
		return nil, fmt.Errorf("parsing answers: %w", err)
	}

	// Parse authority section
	msg.Authority, offset, err = unpackResourceRecords(data, offset, int(msg.Header.NSCount))
	if err != nil {
		return nil, fmt.Errorf("parsing authority: %w", err)
	}

	// Parse additional section
	msg.Additional, _, err = unpackResourceRecords(data, offset, int(msg.Header.ARCount))
	if err != nil {
		return nil, fmt.Errorf("parsing additional: %w", err)
	}

	return msg, nil
}

// unpackQuestions parses N question entries starting at offset.
func unpackQuestions(data []byte, offset int, count int) ([]Question, int, error) {
	questions := make([]Question, 0, count)
	for i := 0; i < count; i++ {
		q, newOffset, err := unpackQuestion(data, offset)
		if err != nil {
			return nil, 0, err
		}
		questions = append(questions, *q)
		offset = newOffset
	}
	return questions, offset, nil
}

// unpackQuestion parses a single question entry.
func unpackQuestion(data []byte, offset int) (*Question, int, error) {
	name, newOffset, err := unpackDomainName(data, offset)
	if err != nil {
		return nil, 0, err
	}
	if newOffset+4 > len(data) {
		return nil, 0, ErrMalformedMessage
	}
	q := &Question{
		Name:  name,
		Type:  binary.BigEndian.Uint16(data[newOffset : newOffset+2]),
		Class: binary.BigEndian.Uint16(data[newOffset+2 : newOffset+4]),
	}
	return q, newOffset + 4, nil
}

// unpackResourceRecords parses N resource records starting at offset.
func unpackResourceRecords(data []byte, offset int, count int) ([]ResourceRecord, int, error) {
	records := make([]ResourceRecord, 0, count)
	for i := 0; i < count; i++ {
		rr, newOffset, err := unpackResourceRecord(data, offset)
		if err != nil {
			return nil, 0, err
		}
		records = append(records, *rr)
		offset = newOffset
	}
	return records, offset, nil
}

// unpackResourceRecord parses a single resource record.
func unpackResourceRecord(data []byte, offset int) (*ResourceRecord, int, error) {
	name, newOffset, err := unpackDomainName(data, offset)
	if err != nil {
		return nil, 0, err
	}
	if newOffset+10 > len(data) {
		return nil, 0, ErrMalformedMessage
	}

	rr := &ResourceRecord{
		Name:  name,
		Type:  binary.BigEndian.Uint16(data[newOffset : newOffset+2]),
		Class: binary.BigEndian.Uint16(data[newOffset+2 : newOffset+4]),
		TTL:   binary.BigEndian.Uint32(data[newOffset+4 : newOffset+8]),
		RDLen: binary.BigEndian.Uint16(data[newOffset+8 : newOffset+10]),
	}

	rdataStart := newOffset + 10
	rdataEnd := rdataStart + int(rr.RDLen)
	if rdataEnd > len(data) {
		return nil, 0, ErrMalformedMessage
	}
	rr.RData = data[rdataStart:rdataEnd]

	return rr, rdataEnd, nil
}

// ─── Domain Name Encoding ────────────────────────────────────────────────────

// packDomainName encodes a domain name into DNS wire format.
//
// Example: "www.example.com" becomes:
//   \x03www\x07example\x03com\x00
func packDomainName(name string) []byte {
	if name == "" || name == "." {
		return []byte{0} // Root domain
	}

	var buf []byte
	// Remove trailing dot if present
	if name[len(name)-1] == '.' {
		name = name[:len(name)-1]
	}
	for _, label := range splitLabels(name) {
		if len(label) > 63 {
			label = label[:63] // Max label length is 63
		}
		buf = append(buf, byte(len(label)))
		buf = append(buf, []byte(label)...)
	}
	buf = append(buf, 0) // Terminating zero-length label
	return buf
}

// unpackDomainName decodes a domain name from DNS wire format, handling
// compression pointers (RFC 1035 Section 4.1.4).
//
// DNS compression uses the top two bits of a byte as flags:
//   00 - Normal label (length 0-63)
//   01 - Extended label type (not used in standard DNS)
//   10 - Compression pointer (remaining 14 bits = offset into message)
//   11 - Reserved for future use
func unpackDomainName(data []byte, offset int) (string, int, error) {
	if offset >= len(data) {
		return "", 0, ErrMalformedMessage
	}

	var name []byte
	jumped := false
	startOffset := offset
	jumpOffset := offset
	maxJumps := 10 // Prevent infinite loops from malformed messages
	jumps := 0

	for {
		if offset >= len(data) {
			return "", 0, ErrMalformedMessage
		}

		length := data[offset]

		// Check if this is a compression pointer (top 2 bits = 11)
		if length&0xC0 == 0xC0 {
			if !jumped {
				jumpOffset = offset + 2 // After the pointer, advance the "real" offset
			}
			if offset+2 > len(data) {
				return "", 0, ErrMalformedMessage
			}
			pointer := int(binary.BigEndian.Uint16(data[offset:offset+2]) & 0x3FFF)
			if pointer >= offset {
				return "", 0, ErrCompressionLoop
			}
			offset = pointer
			jumped = true
			jumps++
			if jumps > maxJumps {
				return "", 0, ErrCompressionLoop
			}
			continue
		}

		// Normal label
		if length == 0 {
			offset++
			break
		}

		offset++
		if offset+int(length) > len(data) {
			return "", 0, ErrMalformedMessage
		}
		if len(name) > 0 {
			name = append(name, '.')
		}
		name = append(name, data[offset:offset+int(length)]...)
		offset += int(length)
	}

	if !jumped {
		return string(name), offset, nil
	}
	return string(name), jumpOffset, nil
}

// splitLabels splits a domain name into its labels.
func splitLabels(name string) []string {
	var labels []string
	start := 0
	for i := 0; i < len(name); i++ {
		if name[i] == '.' {
			if i > start {
				labels = append(labels, name[start:i])
			}
			start = i + 1
		}
	}
	if start < len(name) {
		labels = append(labels, name[start:])
	}
	return labels
}

// ─── Helper Functions ────────────────────────────────────────────────────────

// TypeName returns the human-readable name of a DNS record type.
func TypeName(t uint16) string {
	switch t {
	case TypeA:
		return "A"
	case TypeNS:
		return "NS"
	case TypeCNAME:
		return "CNAME"
	case TypeSOA:
		return "SOA"
	case TypeMX:
		return "MX"
	case TypeTXT:
		return "TXT"
	case TypeAAAA:
		return "AAAA"
	case TypeSRV:
		return "SRV"
	case TypeOPT:
		return "OPT"
	case TypeANY:
		return "ANY"
	default:
		return fmt.Sprintf("TYPE%d", t)
	}
}

// RcodeName returns the human-readable name of a DNS response code.
func RcodeName(r uint8) string {
	switch r {
	case RcodeNoError:
		return "NOERROR"
	case RcodeFormErr:
		return "FORMERR"
	case RcodeServFail:
		return "SERVFAIL"
	case RcodeNXDomain:
		return "NXDOMAIN"
	case RcodeNotImp:
		return "NOTIMP"
	case RcodeRefused:
		return "REFUSED"
	default:
		return fmt.Sprintf("RCODE%d", r)
	}
}

// FormatRecordA formats an A record's RData as a dotted IP string.
func FormatRecordA(rdata []byte) string {
	if len(rdata) != 4 {
		return "<invalid>"
	}
	return fmt.Sprintf("%d.%d.%d.%d", rdata[0], rdata[1], rdata[2], rdata[3])
}

// FormatRecordAAAA formats an AAAA record's RData as a colon-hex IPv6 string.
func FormatRecordAAAA(rdata []byte) string {
	if len(rdata) != 16 {
		return "<invalid>"
	}
	return fmt.Sprintf("%x:%x:%x:%x:%x:%x:%x:%x",
		rdata[0]<<8|rdata[1], rdata[2]<<8|rdata[3],
		rdata[4]<<8|rdata[5], rdata[6]<<8|rdata[7],
		rdata[8]<<8|rdata[9], rdata[10]<<8|rdata[11],
		rdata[12]<<8|rdata[13], rdata[14]<<8|rdata[15])
}
