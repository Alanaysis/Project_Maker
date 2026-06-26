// Package dns implements a DNS protocol parser, server, cache, and resolver
// for educational purposes.
//
// DNS (Domain Name System) is a hierarchical naming system that translates
// domain names to IP addresses and other information. This package demonstrates:
//   - DNS packet format and binary encoding
//   - Domain name compression (label compression)
//   - Resource record types (A, AAAA, CNAME, MX, TXT, NS, SOA, PTR)
//   - DNS caching with TTL
//   - Recursive query resolution
//   - Zone file parsing
//   - Upstream DNS forwarding
//
// DNS Packet Format (RFC 1035):
//
//   Header (12 bytes):
//   +---------------------+
//   |        ID           |
//   +---------------------+
//   | Flags               |
//   +---------------------+
//   |     Questions       |
//   +---------------------+
//   |      Answers        |
//   +---------------------+
//   |    Authority        |
//   +---------------------+
//   |   Additional        |
//   +---------------------+
//
// Each section contains zero or more resource records.
package dns

import (
	"encoding/binary"
	"fmt"
	"time"
)

// RecordType represents a DNS resource record type.
// These are defined in RFC 1035 and subsequent RFCs.
type RecordType uint16

// DNS record type constants defined in RFC 1035 and extensions.
const (
	TypeA     RecordType = 1   // IPv4 address record
	TypeNS    RecordType = 2   // Nameserver record
	TypeCNAME RecordType = 5   // Canonical name record
	TypeSOA   RecordType = 6   // Start of authority record
	TypePTR   RecordType = 12  // Pointer record (reverse DNS)
	TypeMX    RecordType = 15  // Mail exchange record
	TypeTXT   RecordType = 16  // Text record
	TypeAAAA  RecordType = 28  // IPv6 address record
	TypeSRV   RecordType = 33  // Service locator record
	TypeOPT   RecordType = 41  // EDNS0 option (not a real record)
	TypeDNSKEY RecordType = 48 // DNS security key
	TypeRRSIG RecordType = 46  // Resource record signature
	TypeNSEC  RecordType = 47  // Next secure record
	TypeAXFR  RecordType = 252 // Zone transfer request
	TypeANY   RecordType = 255 // Any record type wildcard
)

// String returns the human-readable name of the record type.
func (t RecordType) String() string {
	switch t {
	case TypeA:
		return "A"
	case TypeNS:
		return "NS"
	case TypeCNAME:
		return "CNAME"
	case TypeSOA:
		return "SOA"
	case TypePTR:
		return "PTR"
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
	case TypeDNSKEY:
		return "DNSKEY"
	case TypeRRSIG:
		return "RRSIG"
	case TypeNSEC:
		return "NSEC"
	case TypeAXFR:
		return "AXFR"
	case TypeANY:
		return "ANY"
	default:
		return fmt.Sprintf("TYPE%d", t)
	}
}

// ClassType represents a DNS class type (IN, CH, HS, ANY).
type ClassType uint16

const (
	ClassIN  ClassType = 1 // Internet
	ClassCH  ClassType = 3 // Chaosnet
	ClassHS  ClassType = 4 // Hesiod
	ClassANY ClassType = 255
)

func (c ClassType) String() string {
	switch c {
	case ClassIN:
		return "IN"
	case ClassCH:
		return "CH"
	case ClassHS:
		return "HS"
	case ClassANY:
		return "ANY"
	default:
		return fmt.Sprintf("CLASS%d", c)
	}
}

// Opcode represents the DNS opcode.
type Opcode uint8

const (
	OpcodeQuery  Opcode = 0 // Standard query
	OpcodeIQuery Opcode = 1 // Inverse query
	OpcodeStatus Opcode = 2 // Server status request
	OpcodeNotify Opcode = 4 // Zone transfer notify
	OpcodeUpdate Opcode = 5 // Dynamic update
)

func (o Opcode) String() string {
	switch o {
	case OpcodeQuery:
		return "QUERY"
	case OpcodeIQuery:
		return "IQUERY"
	case OpcodeStatus:
		return "STATUS"
	case OpcodeNotify:
		return "NOTIFY"
	case OpcodeUpdate:
		return "UPDATE"
	default:
		return fmt.Sprintf("OPCODE%d", o)
	}
}

// RCode represents the DNS response code.
type RCode uint8

const (
	RCodeOK      RCode = 0 // No error
	RCodeFormat  RCode = 1 // Format error
	RCodeServFail RCode = 2 // Server failure
	RCodeNXDomain RCode = 3 // Non-existent domain
	RCodeNotImpl RCode = 4 // Not implemented
	RCodeRefused RCode = 5 // Query refused
	RCodeYXDomain RCode = 6 // Name exists
	RCodeYXRRSet RCode = 7 // RR set exists
	RCodeNXRRSet RCode = 8 // RR set does not exist
)

func (r RCode) String() string {
	switch r {
	case RCodeOK:
		return "NOERROR"
	case RCodeFormat:
		return "FORMERR"
	case RCodeServFail:
		return "SERVFAIL"
	case RCodeNXDomain:
		return "NXDOMAIN"
	case RCodeNotImpl:
		return "NOTIMP"
	case RCodeRefused:
		return "REFUSED"
	case RCodeYXDomain:
		return "YXDOMAIN"
	case RCodeYXRRSet:
		return "YXRRSET"
	case RCodeNXRRSet:
		return "NXRRSET"
	default:
		return fmt.Sprintf("RCode%d", r)
	}
}

// DNS flags bit positions
const (
	FlagQR byte = 1 << 7 // Query/Response (0=query, 1=response)
	FlagAA byte = 1 << 2 // Authoritative Answer
	FlagTC byte = 1 << 1 // Truncation
	FlagRD byte = 1 << 0 // Recursion Desired
	FlagRA byte = 1 << 7 // Recursion Available (in response)
)

// Header is the DNS message header (12 bytes).
// The header contains:
//   - ID: 16-bit identifier for matching responses to queries
//   - Flags: 16 bits containing QR, opcode, rcode, and control flags
//   - QDCOUNT: Number of question records
//   - ANCOUNT: Number of answer records
//   - NSCOUNT: Number of authority records
//   - ARCOUNT: Number of additional records
type Header struct {
	ID          uint16
	Flags       uint16
	QDCount     uint16 // Question count
	ANCount     uint16 // Answer count
	NSCount     uint16 // Authority count
	ARCount     uint16 // Additional count
}

// IsQuery returns true if this is a query message (QR=0).
func (h *Header) IsQuery() bool {
	return (h.Flags & FlagQR) == 0
}

// IsResponse returns true if this is a response message (QR=1).
func (h *Header) IsResponse() bool {
	return (h.Flags & FlagQR) != 0
}

// SetQR sets the QR flag.
func (h *Header) SetQR(isResponse bool) {
	if isResponse {
		h.Flags |= FlagQR
	} else {
		h.Flags &^= FlagQR
	}
}

// SetRD sets the Recursion Desired flag.
func (h *Header) SetRD(rd bool) {
	if rd {
		h.Flags |= FlagRD
	} else {
		h.Flags &^= FlagRD
	}
}

// SetAA sets the Authoritative Answer flag.
func (h *Header) SetAA(aa bool) {
	if aa {
		h.Flags |= FlagAA
	} else {
		h.Flags &^= FlagAA
	}
}

// SetRA sets the Recursion Available flag.
func (h *Header) SetRA(ra bool) {
	if ra {
		h.Flags |= FlagRA
	} else {
		h.Flags &^= FlagRA
	}
}

// String returns a human-readable representation of the header.
func (h *Header) String() string {
	return fmt.Sprintf("ID:%d QR:%d Opcode:%d RCode:%d Q:%d A:%d NS:%d AR:%d",
		h.ID, (h.Flags>>7)&0x1, (h.Flags>>11)&0xF, h.Flags&0xF,
		h.QDCount, h.ANCount, h.NSCount, h.ARCount)
}

// Question represents a DNS question record.
// Each question specifies a domain name and type to look up.
type Question struct {
	Name   string      // Domain name (e.g., "www.example.com")
	Answer string      // Alias name (filled during decoding for CNAME chains)
	Type   RecordType  // Record type (A, AAAA, CNAME, etc.)
	Class  ClassType   // Record class (usually IN)
}

// String returns a human-readable representation of the question.
func (q *Question) String() string {
	return fmt.Sprintf("%s %s %s", q.Name, q.Class, q.Type)
}

// ResourceRecord represents a DNS resource record (answer, authority, or additional).
// The exact fields depend on the record type.
type ResourceRecord struct {
	Name      string      // Domain name
	Type      RecordType  // Record type
	Class     ClassType   // Record class
	TTL       uint32      // Time to live in seconds
	Data      []byte      // Raw record data
	RawData   interface{} // Parsed record data (type-specific)
}

// String returns a human-readable representation of the resource record.
func (r *ResourceRecord) String() string {
	return fmt.Sprintf("%s %d %s %s (%d bytes)", r.Name, r.TTL, r.Class, r.Type, len(r.Data))
}

// Message represents a complete DNS message (header + sections).
type Message struct {
	Header    Header
	Questions []Question
	Answers   []ResourceRecord
	Authority []ResourceRecord
	Additional []ResourceRecord
}

// IsQuery returns true if this message is a query.
func (m *Message) IsQuery() bool {
	return m.Header.IsQuery()
}

// IsResponse returns true if this message is a response.
func (m *Message) IsResponse() bool {
	return m.Header.IsResponse()
}

// String returns a human-readable representation of the message.
func (m *Message) String() string {
	var sb string
	sb += fmt.Sprintf("DNS Message: %s\n", m.Header)
	sb += fmt.Sprintf("  Questions (%d):\n", len(m.Questions))
	for i, q := range m.Questions {
		sb += fmt.Sprintf("    [%d] %s\n", i, q)
	}
	sb += fmt.Sprintf("  Answers (%d):\n", len(m.Answers))
	for i, a := range m.Answers {
		sb += fmt.Sprintf("    [%d] %s\n", i, a)
	}
	sb += fmt.Sprintf("  Authority (%d):\n", len(m.Authority))
	for i, a := range m.Authority {
		sb += fmt.Sprintf("    [%d] %s\n", i, a)
	}
	sb += fmt.Sprintf("  Additional (%d):\n", len(m.Additional))
	for i, a := range m.Additional {
		sb += fmt.Sprintf("    [%d] %s\n", i, a)
	}
	return sb
}

// NewMessage creates a new DNS query message.
func NewMessage(id uint16) *Message {
	return &Message{
		Header: Header{
			ID:    id,
			Flags: uint16(OpcodeQuery) << 11, // Set opcode to QUERY
		},
	}
}

// NewResponse creates a new DNS response message.
func NewResponse(id uint16) *Message {
	msg := NewMessage(id)
	msg.Header.SetQR(true)
	msg.Header.SetRA(true)
	return msg
}

// NewErrorResponse creates a DNS error response.
func NewErrorResponse(id uint16, rcode RCode) *Message {
	msg := NewResponse(id)
	msg.Header.Flags = (msg.Header.Flags &^ 0xF) | uint16(rcode)
	return msg
}

// Encode serializes the message to bytes following RFC 1035 format.
// The encoding uses domain name compression to reduce packet size.
//
// Domain name compression: Instead of repeating full domain names,
// a pointer (0xC0 prefix) points to a previous occurrence of the name
// in the packet. This is essential for keeping DNS messages under 512 bytes
// (UDP limit) and reducing bandwidth usage.
func (m *Message) Encode() ([]byte, error) {
	buf := make([]byte, 0, 512)

	// Encode header (always 12 bytes)
	buf = appendUint16(buf, m.Header.ID)
	buf = appendUint16(buf, m.Header.Flags)
	buf = appendUint16(buf, m.Header.QDCount)
	buf = appendUint16(buf, m.Header.ANCount)
	buf = appendUint16(buf, m.Header.NSCount)
	buf = appendUint16(buf, m.Header.ARCount)

	// Encode questions section
	for _, q := range m.Questions {
		nameBytes, err := encodeDomainName(q.Name)
		if err != nil {
			return nil, fmt.Errorf("encode question name: %w", err)
		}
		buf = append(buf, nameBytes...)
		buf = appendUint16(buf, uint16(q.Type))
		buf = appendUint16(buf, uint16(q.Class))
	}

	// Encode answers section
	for _, r := range m.Answers {
		nameBytes, offset, err := encodeDomainNameWithOffset(r.Name)
		if err != nil {
			return nil, fmt.Errorf("encode answer name: %w", err)
		}
		buf = append(buf, nameBytes...)
		buf = appendUint16(buf, uint16(r.Type))
		buf = appendUint16(buf, uint16(r.Class))
		buf = appendUint32(buf, r.TTL)
		buf = appendUint16(buf, uint16(len(r.Data)))
		buf = append(buf, r.Data...)
		_ = offset
	}

	// Encode authority section
	for _, r := range m.Authority {
		nameBytes, _, err := encodeDomainNameWithOffset(r.Name)
		if err != nil {
			return nil, fmt.Errorf("encode authority name: %w", err)
		}
		buf = append(buf, nameBytes...)
		buf = appendUint16(buf, uint16(r.Type))
		buf = appendUint16(buf, uint16(r.Class))
		buf = appendUint32(buf, r.TTL)
		buf = appendUint16(buf, uint16(len(r.Data)))
		buf = append(buf, r.Data...)
	}

	// Encode additional section
	for _, r := range m.Additional {
		nameBytes, _, err := encodeDomainNameWithOffset(r.Name)
		if err != nil {
			return nil, fmt.Errorf("encode additional name: %w", err)
		}
		buf = append(buf, nameBytes...)
		buf = appendUint16(buf, uint16(r.Type))
		buf = appendUint16(buf, uint16(r.Class))
		buf = appendUint32(buf, r.TTL)
		buf = appendUint16(buf, uint16(len(r.Data)))
		buf = append(buf, r.Data...)
	}

	return buf, nil
}

// Decode deserializes a DNS message from bytes.
// It parses the header, questions, answers, authority, and additional sections.
func (m *Message) Decode(data []byte) error {
	if len(data) < 12 {
		return fmt.Errorf("message too short: %d bytes (minimum 12)", len(data))
	}

	// Parse header
	m.Header.ID = binary.BigEndian.Uint16(data[0:2])
	m.Header.Flags = binary.BigEndian.Uint16(data[2:4])
	m.Header.QDCount = binary.BigEndian.Uint16(data[4:6])
	m.Header.ANCount = binary.BigEndian.Uint16(data[6:8])
	m.Header.NSCount = binary.BigEndian.Uint16(data[8:10])
	m.Header.ARCount = binary.BigEndian.Uint16(data[10:12])

	offset := 12

	// Parse questions
	for i := 0; i < int(m.Header.QDCount); i++ {
		name, n, err := decodeDomainName(data, offset)
		if err != nil {
			return fmt.Errorf("decode question %d name: %w", i, err)
		}
		offset += n

		if offset+4 > len(data) {
			return fmt.Errorf("truncated question record at offset %d", offset)
		}
		qtype := RecordType(binary.BigEndian.Uint16(data[offset : offset+2]))
		qclass := ClassType(binary.BigEndian.Uint16(data[offset+2 : offset+4]))
		offset += 4

		m.Questions = append(m.Questions, Question{
			Name:  name,
			Type:  qtype,
			Class: qclass,
		})
	}

	// Parse resource records (answers, authority, additional)
	sections := [][]ResourceRecord{&m.Answers, &m.Authority, &m.Additional}
	counts := []uint16{m.Header.ANCount, m.Header.NSCount, m.Header.ARCount}

	sectionNames := []string{"answers", "authority", "additional"}
	for s := 0; s < 3; s++ {
		for i := 0; i < int(counts[s]); i++ {
			name, n, err := decodeDomainName(data, offset)
			if err != nil {
				return fmt.Errorf("decode %s %d name: %w", sectionNames[s], i, err)
			}
			offset += n

			if offset+10 > len(data) {
				return fmt.Errorf("truncated %s record at offset %d", sectionNames[s], offset)
			}
			rtype := RecordType(binary.BigEndian.Uint16(data[offset : offset+2]))
			rclass := ClassType(binary.BigEndian.Uint16(data[offset+2 : offset+4]))
			ttl := binary.BigEndian.Uint32(data[offset+4 : offset+8])
			rdlength := binary.BigEndian.Uint16(data[offset+8 : offset+10])
			offset += 10

			if offset+int(rdlength) > len(data) {
				return fmt.Errorf("truncated %s data at offset %d", sectionNames[s], offset)
			}
			rdata := make([]byte, rdlength)
			copy(rdata, data[offset:offset+int(rdlength)])
			offset += int(rdlength)

			rr := ResourceRecord{
				Name: name,
				Type: rtype,
				Class: rclass,
				TTL:  ttl,
				Data: rdata,
			}
			rr.RawData = parseRecordData(rtype, rdata)

			switch s {
			case 0:
				m.Answers = append(m.Answers, rr)
			case 1:
				m.Authority = append(m.Authority, rr)
			case 2:
				m.Additional = append(m.Additional, rr)
			}
		}
	}

	return nil
}

// parseRecordData parses raw record data into a type-specific structure.
func parseRecordData(rtype RecordType, data []byte) interface{} {
	switch rtype {
	case TypeA:
		if len(data) == 4 {
			return &IPv4Address{IP: data}
		}
	case TypeAAAA:
		if len(data) == 16 {
			return &IPv6Address{IP: data}
		}
	case TypeCNAME, TypeNS, TypePTR:
		name, err := decodeDomainName(data, 0)
		if err == nil {
			return &DomainNameRecord{Name: name}
		}
	case TypeMX:
		if len(data) >= 3 {
			pref := binary.BigEndian.Uint16(data[0:2])
			name, err := decodeDomainName(data, 2)
			if err == nil {
				return &MXRecord{Preference: pref, Exchange: name}
			}
		}
	case TypeTXT:
		var texts []string
		idx := 0
		for idx < len(data) {
			tlen := int(data[idx])
			idx++
			if idx+tlen > len(data) {
				break
			}
			texts = append(texts, string(data[idx:idx+tlen]))
			idx += tlen
		}
		return &TXTRecord{Texts: texts}
	case TypeSOA:
		if len(data) >= 13 {
			mname, err := decodeDomainName(data, 0)
			if err != nil {
				break
			}
			rname, n, err := decodeDomainName(data, 1)
			if err != nil {
				break
			}
			soa := &SOARecord{
				MName:       mname,
				RName:       rname,
				Serial:      binary.BigEndian.Uint32(data[1+n : 5+n]),
				Refresh:     binary.BigEndian.Uint32(data[5+n : 9+n]),
				Retry:       binary.BigEndian.Uint32(data[9+n : 13+n]),
				Expire:      binary.BigEndian.Uint32(data[13+n : 17+n]),
				MinimumTTL:  binary.BigEndian.Uint32(data[17+n : 21+n]),
			}
			return soa
		}
	}
	return &RawRecord{Data: data}
}

// IPv4Address represents an A record (IPv4 address).
type IPv4Address struct {
	IP []byte // 4 bytes
}

func (r *IPv4Address) String() string {
	return fmt.Sprintf("%d.%d.%d.%d", r.IP[0], r.IP[1], r.IP[2], r.IP[3])
}

// IPv6Address represents an AAAA record (IPv6 address).
type IPv6Address struct {
	IP []byte // 16 bytes
}

func (r *IPv6Address) String() string {
	return fmt.Sprintf("%x:%x:%x:%x:%x:%x:%x:%x",
		binary.BigEndian.Uint16(r.IP[0:2]),
		binary.BigEndian.Uint16(r.IP[2:4]),
		binary.BigEndian.Uint16(r.IP[4:6]),
		binary.BigEndian.Uint16(r.IP[6:8]),
		binary.BigEndian.Uint16(r.IP[8:10]),
		binary.BigEndian.Uint16(r.IP[10:12]),
		binary.BigEndian.Uint16(r.IP[12:14]),
		binary.BigEndian.Uint16(r.IP[14:16]),
	)
}

// DomainNameRecord represents a CNAME, NS, or PTR record.
type DomainNameRecord struct {
	Name string
}

func (r *DomainNameRecord) String() string {
	return r.Name
}

// MXRecord represents an MX (Mail Exchange) record.
type MXRecord struct {
	Preference uint16
	Exchange   string
}

func (r *MXRecord) String() string {
	return fmt.Sprintf("%d %s", r.Preference, r.Exchange)
}

// TXTRecord represents a TXT (Text) record.
type TXTRecord struct {
	Texts []string
}

func (r *TXTRecord) String() string {
	return fmt.Sprintf("%v", r.Texts)
}

// SOARecord represents a SOA (Start of Authority) record.
type SOARecord struct {
	MName       string // Primary nameserver
	RName       string // Responsible authority's email (with . instead of @)
	Serial      uint32 // Serial number
	Refresh     uint32 // Refresh interval (seconds)
	Retry       uint32 // Retry interval (seconds)
	Expire      uint32 // Expire time (seconds)
	MinimumTTL  uint32 // Minimum TTL
}

func (r *SOARecord) String() string {
	return fmt.Sprintf("%s %s %d %d %d %d %d",
		r.MName, r.RName, r.Serial, r.Refresh, r.Retry, r.Expire, r.MinimumTTL)
}

// RawRecord represents unparsed record data.
type RawRecord struct {
	Data []byte
}

func (r *RawRecord) String() string {
	return fmt.Sprintf("<%d bytes>", len(r.Data))
}

// Helper functions for binary encoding

func appendUint16(b []byte, v uint16) []byte {
	return append(b, byte(v>>8), byte(v))
}

func appendUint32(b []byte, v uint32) []byte {
	return append(b, byte(v>>24), byte(v>>16), byte(v>>8), byte(v))
}

// encodeDomainName converts a domain name to DNS wire format.
// Domain names are encoded as a sequence of labels, each prefixed by its length.
// The name is terminated by a zero-length label (0x00).
//
// Example: "www.example.com" -> [3 'w' 'w' 'w' 7 'e' 'x' 'a' 'm' 'p' 'l' 'e' 3 'c' 'o' 'm' 0]
func encodeDomainName(name string) ([]byte, error) {
	// Normalize: remove trailing dot if present
	name = stripTrailingDot(name)

	if name == "" {
		return []byte{0}, nil // Root domain
	}

	labels := splitDomainName(name)
	result := make([]byte, 0, len(name)+len(labels)+1)

	for _, label := range labels {
		if len(label) == 0 {
			continue
		}
		if len(label) > 63 {
			return nil, fmt.Errorf("label too long: %d bytes", len(label))
		}
		result = append(result, byte(len(label)))
		result = append(result, []byte(label)...)
	}
	result = append(result, 0) // Null terminator

	return result, nil
}

// encodeDomainNameWithOffset is like encodeDomainName but returns the byte count.
func encodeDomainNameWithOffset(name string) ([]byte, int, error) {
	name = stripTrailingDot(name)
	if name == "" {
		return []byte{0}, 1, nil
	}
	labels := splitDomainName(name)
	result := make([]byte, 0, len(name)+len(labels)+1)
	for _, label := range labels {
		if len(label) == 0 {
			continue
		}
		if len(label) > 63 {
			return nil, 0, fmt.Errorf("label too long: %d bytes", len(label))
		}
		result = append(result, byte(len(label)))
		result = append(result, []byte(label)...)
	}
	result = append(result, 0)
	return result, len(result), nil
}

// decodeDomainName reads a domain name from DNS wire format.
// It handles label compression pointers (0xC0 prefix).
//
// Label compression: A two-byte pointer where the top 2 bits are 11 (0xC0).
// The remaining 14 bits give an offset into the message. This allows the same
// domain name to be referenced multiple times without repeating bytes.
//
// Example: if "example.com" appears at offset 12, a pointer to it is [0xC0, 0x0C].
func decodeDomainName(data []byte, offset int) (string, int, error) {
	var labels []string
	originalOffset := offset
	jumped := false
	jumpOffset := -1
	bytesConsumed := 0

	for offset < len(data) {
		if !jumped {
			bytesConsumed++
		}

		length := int(data[offset])

		// Check for compression pointer (top 2 bits = 11)
		if length >= 0xC0 {
			if offset+1 >= len(data) {
				return "", bytesConsumed, fmt.Errorf("compression pointer at offset %d truncated", offset)
			}
			if !jumped {
				jumpOffset = offset + 2
			}
			// Pointer: next 14 bits are the offset
			ptr := int((length&0x3F)<<8) | int(data[offset+1])
			offset = ptr
			jumped = true
		} else if length == 0 {
			// End of name
			if !jumped {
				offset++
			}
			break
		} else {
			// Regular label
			offset++
			if offset+length > len(data) {
				return "", bytesConsumed, fmt.Errorf("label extends beyond packet at offset %d", offset)
			}
			labels = append(labels, string(data[offset:offset+length]))
			offset += length
		}
	}

	name := joinDomainName(labels)

	if jumped && jumpOffset >= 0 {
		bytesConsumed = jumpOffset - originalOffset
	}

	return name, bytesConsumed, nil
}

// stripTrailingDot removes a trailing dot from a domain name.
func stripTrailingDot(name string) string {
	if len(name) > 0 && name[len(name)-1] == '.' {
		return name[:len(name)-1]
	}
	return name
}

// splitDomainName splits a domain name into labels.
func splitDomainName(name string) []string {
	labels := make([]string, 0)
	start := 0
	for i, c := range name {
		if c == '.' {
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

// joinDomainName joins labels back into a domain name.
func joinDomainName(labels []string) string {
	if len(labels) == 0 {
		return ""
	}
	result := labels[0]
	for i := 1; i < len(labels); i++ {
		result += "." + labels[i]
	}
	return result
}

// DNSCache stores DNS responses with TTL-based expiration.
type DNSCache struct {
	entries map[string]*CacheEntry
	maxSize int
}

// CacheEntry holds a cached DNS response with expiration time.
type CacheEntry struct {
	Message   *Message
	ExpiresAt time.Time
	CreatedAt time.Time
}

// IsExpired checks if this cache entry has expired.
func (e *CacheEntry) IsExpired() bool {
	return time.Now().After(e.ExpiresAt)
}

// NewDNSCache creates a new DNS cache with the given maximum size.
func NewDNSCache(maxSize int) *DNSCache {
	return &DNSCache{
		entries: make(map[string]*CacheEntry),
		maxSize: maxSize,
	}
}

// Get retrieves a cached entry by key.
// The key is typically "name:type:class" (e.g., "www.example.com:A:IN").
func (c *DNSCache) Get(key string) (*Message, bool) {
	entry, ok := c.entries[key]
	if !ok {
		return nil, false
	}
	if entry.IsExpired() {
		delete(c.entries, key)
		return nil, false
	}
	// Return a copy to avoid mutation
	resp := *entry.Message
	return &resp, true
}

// Put adds a response to the cache.
func (c *DNSCache) Put(key string, msg *Message, defaultTTL uint32) {
	// Calculate TTL as minimum of record TTLs and default
	ttl := defaultTTL
	for _, rr := range msg.Answers {
		if rr.TTL < ttl {
			ttl = rr.TTL
		}
	}
	if ttl == 0 {
		ttl = defaultTTL
	}

	// Evict oldest entry if cache is full
	if len(c.entries) >= c.maxSize {
		c.evictOldest()
	}

	c.entries[key] = &CacheEntry{
		Message:   msg,
		ExpiresAt: time.Now().Add(time.Duration(ttl) * time.Second),
		CreatedAt: time.Now(),
	}
}

// Delete removes an entry from the cache.
func (c *DNSCache) Delete(key string) {
	delete(c.entries, key)
}

// evictOldest removes the oldest cache entry.
func (c *DNSCache) evictOldest() {
	var oldestKey string
	var oldestTime time.Time
	first := true
	for key, entry := range c.entries {
		if first || entry.CreatedAt.Before(oldestTime) {
			oldestKey = key
			oldestTime = entry.CreatedAt
			first = false
		}
	}
	if !first {
		delete(c.entries, oldestKey)
	}
}

// Clear removes all entries from the cache.
func (c *DNSCache) Clear() {
	c.entries = make(map[string]*CacheEntry)
}

// Size returns the number of entries in the cache.
func (c *DNSCache) Size() int {
	return len(c.entries)
}

// CacheKey generates a cache key from a question.
func CacheKey(name string, qtype RecordType, qclass ClassType) string {
	return fmt.Sprintf("%s:%s:%s", name, qtype, qclass)
}
