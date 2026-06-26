// Package frame implements HTTP/2 HPACK header compression.
// HPACK is used to efficiently encode HTTP headers in HTTP/2.
package frame

import (
	"bytes"
	"fmt"
	"strings"
)

// Static table entries as defined in RFC 7541 Appendix A
type HeaderField struct {
	Name  string
	Value string
}

var staticTable = []HeaderField{
	{":authority", ""},                    // 1
	{":method", "GET"},                    // 2
	{":method", "POST"},                   // 3
	{":path", "/"},                        // 4
	{":path", "/index.html"},              // 5
	{":scheme", "http"},                   // 6
	{":scheme", "https"},                  // 7
	{":status", "200"},                    // 8
	{":status", "204"},                    // 9
	{":status", "206"},                    // 10
	{":status", "304"},                    // 11
	{":status", "400"},                    // 12
	{":status", "404"},                    // 13
	{":status", "500"},                    // 14
	{"accept-charset", ""},               // 15
	{"accept-encoding", "gzip, deflate"}, // 16
	{"accept-language", ""},              // 17
	{"accept-ranges", ""},                // 18
	{"accept", ""},                        // 19
	{"access-control-allow-origin", ""},  // 20
	{"age", ""},                           // 21
	{"allow", ""},                         // 22
	{"authorization", ""},                // 23
	{"cache-control", ""},                // 24
	{"content-disposition", ""},          // 25
	{"content-encoding", ""},             // 26
	{"content-language", ""},             // 27
	{"content-length", ""},               // 28
	{"content-location", ""},             // 29
	{"content-range", ""},                // 30
	{"content-type", ""},                 // 31
	{"cookie", ""},                        // 32
	{"date", ""},                          // 33
	{"etag", ""},                          // 34
	{"expect", ""},                        // 35
	{"expires", ""},                       // 36
	{"from", ""},                          // 37
	{"host", ""},                          // 38
	{"if-match", ""},                      // 39
	{"if-modified-since", ""},            // 40
	{"if-none-match", ""},                // 41
	{"if-range", ""},                      // 42
	{"if-unmodified-since", ""},          // 43
	{"last-modified", ""},                // 44
	{"link", ""},                          // 45
	{"location", ""},                      // 46
	{"max-forwards", ""},                  // 47
	{"proxy-authenticate", ""},           // 48
	{"proxy-authorization", ""},          // 49
	{"range", ""},                         // 50
	{"referer", ""},                       // 51
	{"refresh", ""},                       // 52
	{"retry-after", ""},                   // 53
	{"server", ""},                        // 54
	{"set-cookie", ""},                    // 55
	{"strict-transport-security", ""},    // 56
	{"transfer-encoding", ""},            // 57
	{"user-agent", ""},                    // 58
	{"vary", ""},                          // 59
	{"via", ""},                           // 60
	{"www-authenticate", ""},             // 61
}

// HPACKEncoder handles HPACK encoding
type HPACKEncoder struct {
	dynamicTable []HeaderField
	maxSize      uint32
	currentSize  uint32
}

// NewHPACKEncoder creates a new HPACK encoder
func NewHPACKEncoder(maxTableSize uint32) *HPACKEncoder {
	return &HPACKEncoder{
		dynamicTable: make([]HeaderField, 0),
		maxSize:      maxTableSize,
		currentSize:  0,
	}
}

// MaxSize returns the maximum table size
func (e *HPACKEncoder) MaxSize() uint32 {
	return e.maxSize
}

// EncodeHeaders encodes a set of headers into HPACK format
func (e *HPACKEncoder) EncodeHeaders(headers []HeaderField) ([]byte, error) {
	var buf bytes.Buffer

	for _, h := range headers {
		// Try to find in static table
		if idx := findInStaticTable(h); idx > 0 {
			// Indexed header field: 1xxxxxxx pattern
			// Write the index with high bit set
			if idx < 127 {
				buf.WriteByte(byte(idx) | 0x80)
			} else {
				buf.WriteByte(0xFF)
				writeInt(&buf, uint64(idx-127), 7)
			}
			continue
		}

		// Literal header with incremental indexing (01xxxxxx)
		// Combine type bits with name length in first byte
		name := strings.ToLower(h.Name)
		nameLen := len(name)

		if nameLen < 63 {
			buf.WriteByte(byte(nameLen) | 0x40)
		} else {
			buf.WriteByte(0x7F)
			writeInt(&buf, uint64(nameLen-63), 7)
		}
		buf.WriteString(name)

		// Write value length and value
		writeInt(&buf, uint64(len(h.Value)), 7)
		buf.WriteString(h.Value)

		// Add to dynamic table
		e.addToDynamicTable(h)
	}

	return buf.Bytes(), nil
}

// HPACKDecoder handles HPACK decoding
type HPACKDecoder struct {
	dynamicTable []HeaderField
	maxSize      uint32
	currentSize  uint32
}

// NewHPACKDecoder creates a new HPACK decoder
func NewHPACKDecoder(maxTableSize uint32) *HPACKDecoder {
	return &HPACKDecoder{
		dynamicTable: make([]HeaderField, 0),
		maxSize:      maxTableSize,
		currentSize:  0,
	}
}

// DecodeHeaders decodes HPACK encoded headers
func (d *HPACKDecoder) DecodeHeaders(data []byte) ([]HeaderField, error) {
	var headers []HeaderField
	reader := bytes.NewReader(data)

	for reader.Len() > 0 {
		b, err := reader.ReadByte()
		if err != nil {
			return nil, fmt.Errorf("failed to read byte: %w", err)
		}

		if b&0x80 != 0 {
			// Indexed header field (1xxxxxxx)
			idx, err := readInt(reader, b, 7)
			if err != nil {
				return nil, err
			}
			hf, err := d.getHeaderByIndex(int(idx))
			if err != nil {
				return nil, err
			}
			headers = append(headers, hf)
		} else if b&0x40 != 0 {
			// Literal header with incremental indexing (01xxxxxx)
			name, err := readString(reader, b, 6)
			if err != nil {
				return nil, err
			}
			value, err := readString(reader, 0, 0)
			if err != nil {
				return nil, err
			}
			hf := HeaderField{Name: name, Value: value}
			headers = append(headers, hf)
			d.addToDynamicTable(hf)
		} else if b&0x20 != 0 {
			// Dynamic table size update (001xxxxx)
			newSize, err := readInt(reader, b, 5)
			if err != nil {
				return nil, err
			}
			d.updateMaxSize(uint32(newSize))
		} else {
			// Literal header without indexing (0000xxxx)
			name, err := readString(reader, b, 4)
			if err != nil {
				return nil, err
			}
			value, err := readString(reader, 0, 0)
			if err != nil {
				return nil, err
			}
			headers = append(headers, HeaderField{Name: name, Value: value})
		}
	}

	return headers, nil
}

func findInStaticTable(hf HeaderField) int {
	for i, entry := range staticTable {
		if strings.EqualFold(entry.Name, hf.Name) && entry.Value == hf.Value {
			return i + 1
		}
	}
	return 0
}

func (e *HPACKEncoder) addToDynamicTable(hf HeaderField) {
	entrySize := uint32(len(hf.Name) + len(hf.Value) + 32)

	// Remove entries if necessary
	for e.currentSize+entrySize > e.maxSize && len(e.dynamicTable) > 0 {
		e.currentSize -= uint32(len(e.dynamicTable[0].Name) + len(e.dynamicTable[0].Value) + 32)
		e.dynamicTable = e.dynamicTable[1:]
	}

	if entrySize <= e.maxSize {
		e.dynamicTable = append([]HeaderField{hf}, e.dynamicTable...)
		e.currentSize += entrySize
	}
}

func (d *HPACKDecoder) addToDynamicTable(hf HeaderField) {
	entrySize := uint32(len(hf.Name) + len(hf.Value) + 32)

	for d.currentSize+entrySize > d.maxSize && len(d.dynamicTable) > 0 {
		d.currentSize -= uint32(len(d.dynamicTable[0].Name) + len(d.dynamicTable[0].Value) + 32)
		d.dynamicTable = d.dynamicTable[1:]
	}

	if entrySize <= d.maxSize {
		d.dynamicTable = append([]HeaderField{hf}, d.dynamicTable...)
		d.currentSize += entrySize
	}
}

func (d *HPACKDecoder) updateMaxSize(newSize uint32) {
	d.maxSize = newSize
	for d.currentSize > d.maxSize && len(d.dynamicTable) > 0 {
		d.currentSize -= uint32(len(d.dynamicTable[0].Name) + len(d.dynamicTable[0].Value) + 32)
		d.dynamicTable = d.dynamicTable[1:]
	}
}

func (d *HPACKDecoder) getHeaderByIndex(idx int) (HeaderField, error) {
	if idx == 0 {
		return HeaderField{}, fmt.Errorf("invalid index 0")
	}

	// Static table (1-based)
	if idx <= len(staticTable) {
		return staticTable[idx-1], nil
	}

	// Dynamic table
	dynIdx := idx - len(staticTable) - 1
	if dynIdx >= len(d.dynamicTable) {
		return HeaderField{}, fmt.Errorf("index %d out of range", idx)
	}

	return d.dynamicTable[dynIdx], nil
}

func writeInt(buf *bytes.Buffer, value uint64, n uint8) {
	if value < (1<<n)-1 {
		buf.WriteByte(byte(value))
		return
	}

	buf.WriteByte(byte((1 << n) - 1))
	value -= (1 << n) - 1
	for value >= 128 {
		buf.WriteByte(byte(value&0x7f) | 0x80)
		value >>= 7
	}
	buf.WriteByte(byte(value))
}

func readInt(reader *bytes.Reader, first byte, n uint8) (uint64, error) {
	mask := byte((1 << n) - 1)
	value := uint64(first & mask)
	if value < uint64((1<<n)-1) {
		return value, nil
	}

	m := uint64(0)
	for {
		b, err := reader.ReadByte()
		if err != nil {
			return 0, err
		}
		value += uint64(b&0x7f) << m
		if b&0x80 == 0 {
			break
		}
		m += 7
	}

	return value, nil
}

func writeString(buf *bytes.Buffer, s string) {
	writeInt(buf, uint64(len(s)), 7)
	buf.WriteString(s)
}

func readString(reader *bytes.Reader, first byte, n uint8) (string, error) {
	var length uint64
	var err error

	if n > 0 {
		// Use the first byte with n-bit prefix
		length, err = readInt(reader, first, n)
	} else {
		// Read the next byte and use 7-bit prefix
		b, err := reader.ReadByte()
		if err != nil {
			return "", err
		}
		length, err = readInt(reader, b, 7)
		if err != nil {
			return "", err
		}
	}
	if err != nil {
		return "", err
	}

	buf := make([]byte, length)
	if _, err := reader.Read(buf); err != nil {
		return "", err
	}

	return string(buf), nil
}
