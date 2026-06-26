package dns

import (
	"encoding/binary"
	"fmt"
	"strings"
)

// ZoneFile represents a parsed DNS zone file.
// A zone file contains resource records for a specific domain zone.
//
// Zone file format (RFC 1035):
//   $ORIGIN example.com.    ; Default origin for relative names
//   $TTL 3600               ; Default TTL in seconds
//
//   @       IN  SOA   ns1.example.com. admin.example.com. (
//                   2024010101 ; Serial
//                   3600       ; Refresh
//                   900        ; Retry
//                   604800     ; Expire
//                   86400      ; Minimum TTL
//                   )
//
//   @       IN  NS    ns1.example.com.
//   @       IN  NS    ns2.example.com.
//   ns1     IN  A     192.168.1.1
//   ns2     IN  A     192.168.1.2
//   www     IN  A     192.168.1.10
//   mail    IN  A     192.168.1.20
//   @       IN  MX    10 mail.example.com.
//   @       IN  TXT   "v=spf1 include:_spf.example.com ~all"
type ZoneFile struct {
	Origin    string            // Default origin domain
	DefaultTTL uint32           // Default TTL for records without explicit TTL
	Records   []ResourceRecord // Parsed resource records
}

// ParseZoneFile parses a zone file string into a ZoneFile.
// It supports the most common zone file directives and record formats.
func ParseZoneFile(content string) (*ZoneFile, error) {
	zone := &ZoneFile{
		Origin:     "",
		DefaultTTL: 3600, // Default 1 hour TTL
		Records:    make([]ResourceRecord, 0),
	}

	lines := strings.Split(content, "\n")
	currentOrigin := ""

	for _, line := range lines {
		// Remove comments (but not inside quotes)
		line = removeComments(line)
		// Trim whitespace
		line = strings.TrimSpace(line)

		// Skip empty lines
		if line == "" {
			continue
		}

		// Handle directives
		if strings.HasPrefix(line, "$ORIGIN") {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				currentOrigin = stripTrailingDot(parts[1])
				zone.Origin = currentOrigin
			}
			continue
		}

		if strings.HasPrefix(line, "$TTL") {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				ttl, err := parseTTL(parts[1])
				if err == nil {
					zone.DefaultTTL = ttl
				}
			}
			continue
		}

		// Parse resource record
		rr, err := parseResourceRecord(line, currentOrigin, zone.DefaultTTL)
		if err != nil {
			return nil, fmt.Errorf("parse zone record: %w", err)
		}
		if rr != nil {
			zone.Records = append(zone.Records, *rr)
		}
	}

	return zone, nil
}

// parseResourceRecord parses a single zone file line into a ResourceRecord.
func parseResourceRecord(line, origin string, defaultTTL uint32) (*ResourceRecord, error) {
	// Handle multi-line records (with parentheses)
	line = flattenMultiLine(line)

	fields := tokenizeZoneLine(line)
	if len(fields) == 0 {
		return nil, nil
	}

	// Parse fields
	name := fields[0]
	ttlOrClass := ""
	rtype := ""
	rdata := ""

	idx := 1
	if idx < len(fields) {
		ttlOrClass = fields[idx]
		idx++
	}

	if idx < len(fields) {
		// Check if this is a class field (IN, CH, HS)
		if isClass(ttlOrClass) {
			// TTL is optional, next field might be TTL or type
			if idx < len(fields) && !isType(fields[idx]) {
				// Next field is TTL
				ttl, err := parseTTL(fields[idx])
				if err != nil {
					return nil, fmt.Errorf("parse TTL: %w", err)
				}
				defaultTTL = ttl
				idx++
			}
			// Next field is type
			if idx < len(fields) {
				rtype = fields[idx]
				idx++
			}
		} else {
			// TTL field
			ttl, err := parseTTL(ttlOrClass)
			if err != nil {
				return nil, fmt.Errorf("parse TTL: %w", err)
			}
			defaultTTL = ttl
			if idx < len(fields) {
				// Check for class field
				if isClass(fields[idx]) {
					idx++
				}
				if idx < len(fields) {
					rtype = fields[idx]
					idx++
				}
			}
		}
	}

	// Remaining fields are rdata
	if idx < len(fields) {
		rdata = strings.Join(fields[idx:], " ")
	}

	if rtype == "" {
		return nil, nil
	}

	// Resolve name (handle @ and relative names)
	if name == "@" {
		name = origin
	} else if origin != "" && !strings.Contains(name, ".") {
		name = name + "." + origin
	}

	// Parse record type
	recType, err := parseRecordType(rtype)
	if err != nil {
		return nil, fmt.Errorf("parse record type %s: %w", rtype, err)
	}

	// Parse record data
	data, raw, err := parseRData(recType, rdata, origin)
	if err != nil {
		return nil, fmt.Errorf("parse rdata: %w", err)
	}

	return &ResourceRecord{
		Name:    name,
		Type:    recType,
		Class:   ClassIN,
		TTL:     defaultTTL,
		Data:    data,
		RawData: raw,
	}, nil
}

// flattenMultiLine merges multi-line records enclosed in parentheses.
func flattenMultiLine(line string) string {
	var result strings.Builder
	inParens := false
	for _, c := range line {
		if c == '(' {
			inParens = true
			continue
		}
		if c == ')' {
			inParens = false
			continue
		}
		if inParens && c == '\n' {
			result.WriteRune(' ')
		} else {
			result.WriteRune(c)
		}
	}
	return result.String()
}

// tokenizeZoneLine tokenizes a zone file line, respecting quoted strings.
func tokenizeZoneLine(line string) []string {
	var tokens []string
	var current strings.Builder
	inQuotes := false

	for _, c := range line {
		switch c {
		case '"':
			inQuotes = !inQuotes
			current.WriteRune(c)
		case '\t', ' ':
			if inQuotes {
				current.WriteRune(c)
			} else if current.Len() > 0 {
				tokens = append(tokens, current.String())
				current.Reset()
			}
		default:
			current.WriteRune(c)
		}
	}
	if current.Len() > 0 {
		tokens = append(tokens, current.String())
	}
	return tokens
}

// isClass checks if a string is a DNS class identifier.
func isClass(s string) bool {
	return s == "IN" || s == "CH" || s == "HS" || s == "ANY"
}

// isType checks if a string looks like a DNS record type.
func isType(s string) bool {
	_, err := parseRecordType(s)
	return err == nil
}

// parseRecordType converts a string to a RecordType.
func parseRecordType(s string) (RecordType, error) {
	switch strings.ToUpper(s) {
	case "A":
		return TypeA, nil
	case "NS":
		return TypeNS, nil
	case "CNAME":
		return TypeCNAME, nil
	case "SOA":
		return TypeSOA, nil
	case "PTR":
		return TypePTR, nil
	case "MX":
		return TypeMX, nil
	case "TXT":
		return TypeTXT, nil
	case "AAAA":
		return TypeAAAA, nil
	case "SRV":
		return TypeSRV, nil
	default:
		return 0, fmt.Errorf("unknown record type: %s", s)
	}
}

// parseRData parses resource record data based on type.
// Returns (wireData, rawParsedData, error).
func parseRData(rtype RecordType, rdata, origin string) ([]byte, interface{}, error) {
	switch rtype {
	case TypeA:
		// Parse IPv4 address
		ip := netIPToBytes(parseIPv4(rdata))
		if ip == nil {
			return nil, nil, fmt.Errorf("invalid IPv4 address: %s", rdata)
		}
		return ip, &IPv4Address{IP: ip}, nil

	case TypeAAAA:
		ip := netIPToBytes(parseIPv6(rdata))
		if ip == nil {
			return nil, nil, fmt.Errorf("invalid IPv6 address: %s", rdata)
		}
		return ip, &IPv6Address{IP: ip}, nil

	case TypeCNAME, TypeNS, TypePTR:
		// Domain name - resolve relative names
		name := rdata
		if origin != "" && !strings.HasSuffix(name, ".") && !strings.Contains(name, ".") {
			name = name + "." + origin + "."
		}
		wire, err := encodeDomainName(name)
		if err != nil {
			return nil, nil, err
		}
		return wire, &DomainNameRecord{Name: name}, nil

	case TypeMX:
		// Parse preference and exchange
		parts := strings.Fields(rdata)
		if len(parts) < 2 {
			return nil, nil, fmt.Errorf("MX record needs preference and exchange")
		}
		var pref uint16
		fmt.Sscanf(parts[0], "%d", &pref)
		exchange := parts[1]
		if origin != "" && !strings.HasSuffix(exchange, ".") {
			exchange = exchange + "." + origin + "."
		}
		exchangeBytes, err := encodeDomainName(exchange)
		if err != nil {
			return nil, nil, err
		}
		result := make([]byte, 2+len(exchangeBytes))
		binary.BigEndian.PutUint16(result, pref)
		copy(result[2:], exchangeBytes)
		return result, &MXRecord{Preference: pref, Exchange: exchange}, nil

	case TypeTXT:
		// Parse text data (remove quotes)
		text := rdata
		if len(text) >= 2 && text[0] == '"' && text[len(text)-1] == '"' {
			text = text[1 : len(text)-1]
		}
		return []byte(text), &TXTRecord{Texts: []string{text}}, nil

	case TypeSOA:
		// Parse SOA record
		wire, raw, err := parseSOARData(rdata, origin)
		if err != nil {
			return nil, nil, err
		}
		return wire, raw, nil

	default:
		return []byte(rdata), &RawRecord{Data: []byte(rdata)}, nil
	}
}

// parseSOARData parses SOA record data.
// Returns (wireData, rawParsedData, error).
func parseSOARData(rdata, origin string) ([]byte, *SOARecord, error) {
	// SOA format: mname rname serial refresh retry expire minimum
	fields := strings.Fields(rdata)
	if len(fields) < 7 {
		return nil, nil, fmt.Errorf("SOA record needs at least 7 fields")
	}

	mname := fields[0]
	rname := fields[1]

	if origin != "" {
		if !strings.HasSuffix(mname, ".") && !strings.Contains(mname, ".") {
			mname = mname + "." + origin + "."
		}
		if !strings.HasSuffix(rname, ".") && !strings.Contains(rname, ".") {
			rname = rname + "." + origin + "."
		}
	}

	soa := &SOARecord{
		MName:    mname,
		RName:    rname,
		Serial:   parseUint32(fields[2]),
		Refresh:  parseUint32(fields[3]),
		Retry:    parseUint32(fields[4]),
		Expire:   parseUint32(fields[5]),
		MinimumTTL: parseUint32(fields[6]),
	}

	mnameBytes, _ := encodeDomainName(mname)
	rnameBytes, _ := encodeDomainName(rname)

	result := make([]byte, 2+len(mnameBytes)+len(rnameBytes)+20)
	offset := 0

	// MNAME
	copy(result[offset:], mnameBytes)
	offset += len(mnameBytes)

	// RNAME
	copy(result[offset:], rnameBytes)
	offset += len(rnameBytes)

	// Serial, Refresh, Retry, Expire, Minimum
	vals := []uint32{
		soa.Serial, soa.Refresh, soa.Retry, soa.Expire, soa.MinimumTTL,
	}
	for _, v := range vals {
		binary.BigEndian.PutUint32(result[offset:offset+4], v)
		offset += 4
	}

	return result, soa, nil
}



// parseTTL parses a TTL string (supports suffixes like 1h, 7d, 3600s).
func parseTTL(s string) (uint32, error) {
	// Try parsing as plain number first
	var val uint32
	_, err := fmt.Sscanf(s, "%d", &val)
	if err == nil {
		return val, nil
	}

	// Parse with suffix
	if len(s) < 2 {
		return 0, fmt.Errorf("invalid TTL: %s", s)
	}
	unit := s[len(s)-1]
	numStr := s[:len(s)-1]

	var multiplier uint32
	switch unit {
	case 's', 'S':
		multiplier = 1
	case 'm', 'M':
		multiplier = 60
	case 'h', 'H':
		multiplier = 3600
	case 'd', 'D':
		multiplier = 86400
	case 'w', 'W':
		multiplier = 604800
	default:
		return 0, fmt.Errorf("unknown TTL unit: %c", unit)
	}

	var num uint32
	_, err = fmt.Sscanf(numStr, "%d", &num)
	if err != nil {
		return 0, fmt.Errorf("invalid TTL number: %s", numStr)
	}

	return num * multiplier, nil
}

// removeComments removes DNS zone file comments (# to end of line).
func removeComments(line string) string {
	inQuotes := false
	for i, c := range line {
		if c == '"' {
			inQuotes = !inQuotes
		} else if c == '#' && !inQuotes {
			return line[:i]
		}
	}
	return line
}

// Look up domain name records in a zone file.
func (z *ZoneFile) Lookup(name string, rtype RecordType) []ResourceRecord {
	name = strings.ToLower(stripTrailingDot(name))
	var results []ResourceRecord
	for _, rr := range z.Records {
		if strings.ToLower(stripTrailingDot(rr.Name)) == name && rr.Type == rtype {
			results = append(results, rr)
		}
	}
	return results
}



// LookupWildcard returns records matching a wildcard pattern (*.example.com).
func (z *ZoneFile) LookupWildcard(pattern string) []ResourceRecord {
	pattern = strings.ToLower(stripTrailingDot(pattern))
	var results []ResourceRecord
	for _, rr := range z.Records {
		name := strings.ToLower(stripTrailingDot(rr.Name))
		if name == pattern {
			results = append(results, rr)
		}
	}
	return results
}

// netIPToBytes converts a net.IP-like byte slice to DNS wire format bytes.
func netIPToBytes(ip []byte) []byte {
	if ip == nil {
		return nil
	}
	return ip
}

// parseIPv4 parses an IPv4 address string.
func parseIPv4(s string) []byte {
	var ip [4]byte
	n, err := fmt.Sscanf(s, "%d.%d.%d.%d", &ip[0], &ip[1], &ip[2], &ip[3])
	if err != nil || n != 4 {
		return nil
	}
	return ip[:]
}

// parseIPv6 parses an IPv6 address string.
func parseIPv6(s string) []byte {
	// Simple IPv6 parsing for standard format
	var ip [16]byte
	parts := splitIPv6(s)
	if len(parts) != 8 {
		return nil
	}
	for i, part := range parts {
		var val uint16
		fmt.Sscanf(part, "%x", &val)
		ip[i*2] = byte(val >> 8)
		ip[i*2+1] = byte(val)
	}
	return ip[:]
}

func splitIPv6(s string) []string {
	// Handle :: expansion
	if s == "::" {
		return make([]string, 8)
	}

	// Check for ::
	if idx := findDoubleColon(s); idx >= 0 {
		var before, after []string
		if idx > 0 {
			before = strings.Split(s[:idx], ":")
		}
		if idx < len(s)-2 {
			after = strings.Split(s[idx+2:], ":")
		}
		total := len(before) + len(after)
		missing := 8 - total
		result := make([]string, 0, 8)
		result = append(result, before...)
		for i := 0; i < missing; i++ {
			result = append(result, "0")
		}
		result = append(result, after...)
		return result
	}
	return strings.Split(s, ":")
}

func findDoubleColon(s string) int {
	for i := 0; i < len(s)-1; i++ {
		if s[i] == ':' && s[i+1] == ':' {
			return i
		}
	}
	return -1
}

func parseUint32(s string) uint32 {
	var val uint32
	fmt.Sscanf(s, "%d", &val)
	return val
}
