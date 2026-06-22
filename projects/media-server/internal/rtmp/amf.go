package rtmp

import (
	"encoding/binary"
	"fmt"
	"math"
)

// AMF0 data types
const (
	AMF0Number      = 0x00
	AMF0Boolean     = 0x01
	AMF0String      = 0x02
	AMF0Object      = 0x03
	AMF0Null        = 0x05
	AMF0Undefined   = 0x06
	AMF0EcmaArray   = 0x08
	AMF0ObjectEnd   = 0x09
)

// AMFObject represents an AMF0 object
type AMFObject map[string]interface{}

// AMFEncoder encodes AMF0 data
type AMFEncoder struct {
	data []byte
}

// NewAMFEncoder creates a new AMF0 encoder
func NewAMFEncoder() *AMFEncoder {
	return &AMFEncoder{}
}

// Encode encodes a value to AMF0 format
func (e *AMFEncoder) Encode(value interface{}) error {
	switch v := value.(type) {
	case string:
		return e.encodeString(v)
	case float64:
		return e.encodeNumber(v)
	case int:
		return e.encodeNumber(float64(v))
	case bool:
		return e.encodeBoolean(v)
	case nil:
		return e.encodeNull()
	case AMFObject:
		return e.encodeObject(v)
	default:
		return fmt.Errorf("unsupported AMF type: %T", value)
	}
}

// Bytes returns the encoded data
func (e *AMFEncoder) Bytes() []byte {
	return e.data
}

func (e *AMFEncoder) encodeNumber(value float64) error {
	e.data = append(e.data, AMF0Number)
	bits := math.Float64bits(value)
	b := make([]byte, 8)
	binary.BigEndian.PutUint64(b, bits)
	e.data = append(e.data, b...)
	return nil
}

func (e *AMFEncoder) encodeBoolean(value bool) error {
	e.data = append(e.data, AMF0Boolean)
	if value {
		e.data = append(e.data, 1)
	} else {
		e.data = append(e.data, 0)
	}
	return nil
}

func (e *AMFEncoder) encodeString(value string) error {
	if len(value) > 0xFFFF {
		// Use long string type
		e.data = append(e.data, AMF0String)
		b := make([]byte, 4)
		binary.BigEndian.PutUint32(b, uint32(len(value)))
		e.data = append(e.data, b...)
	} else {
		e.data = append(e.data, AMF0String)
		b := make([]byte, 2)
		binary.BigEndian.PutUint16(b, uint16(len(value)))
		e.data = append(e.data, b...)
	}
	e.data = append(e.data, []byte(value)...)
	return nil
}

func (e *AMFEncoder) encodeNull() error {
	e.data = append(e.data, AMF0Null)
	return nil
}

func (e *AMFEncoder) encodeObject(obj AMFObject) error {
	e.data = append(e.data, AMF0Object)
	for key, value := range obj {
		// Property name
		b := make([]byte, 2)
		binary.BigEndian.PutUint16(b, uint16(len(key)))
		e.data = append(e.data, b...)
		e.data = append(e.data, []byte(key)...)

		// Property value
		if err := e.Encode(value); err != nil {
			return err
		}
	}
	e.data = append(e.data, 0, 0, AMF0ObjectEnd)
	return nil
}

// AMFDecoder decodes AMF0 data
type AMFDecoder struct {
	data   []byte
	offset int
}

// NewAMFDecoder creates a new AMF0 decoder
func NewAMFDecoder(data []byte) *AMFDecoder {
	return &AMFDecoder{data: data}
}

// Decode decodes the next AMF0 value
func (d *AMFDecoder) Decode() (interface{}, error) {
	if d.offset >= len(d.data) {
		return nil, fmt.Errorf("unexpected end of data")
	}

	// Read type marker
	amfType := d.data[d.offset]
	d.offset++

	switch amfType {
	case AMF0Number:
		return d.decodeNumber()
	case AMF0Boolean:
		return d.decodeBoolean()
	case AMF0String:
		return d.decodeString()
	case AMF0Object:
		return d.decodeObject()
	case AMF0Null:
		return nil, nil
	case AMF0Undefined:
		return nil, nil
	case AMF0EcmaArray:
		return d.decodeEcmaArray()
	default:
		return nil, fmt.Errorf("unsupported AMF type: %d", amfType)
	}
}

func (d *AMFDecoder) decodeNumber() (float64, error) {
	if d.offset+8 > len(d.data) {
		return 0, fmt.Errorf("not enough data for number")
	}
	bits := binary.BigEndian.Uint64(d.data[d.offset : d.offset+8])
	d.offset += 8
	return math.Float64frombits(bits), nil
}

func (d *AMFDecoder) decodeBoolean() (bool, error) {
	if d.offset >= len(d.data) {
		return false, fmt.Errorf("not enough data for boolean")
	}
	value := d.data[d.offset] != 0
	d.offset++
	return value, nil
}

func (d *AMFDecoder) decodeString() (string, error) {
	if d.offset+2 > len(d.data) {
		return "", fmt.Errorf("not enough data for string length")
	}
	length := int(binary.BigEndian.Uint16(d.data[d.offset : d.offset+2]))
	d.offset += 2

	if d.offset+length > len(d.data) {
		return "", fmt.Errorf("not enough data for string")
	}
	value := string(d.data[d.offset : d.offset+length])
	d.offset += length
	return value, nil
}

func (d *AMFDecoder) decodeObject() (AMFObject, error) {
	obj := make(AMFObject)
	for {
		// Read property name
		if d.offset+2 > len(d.data) {
			return nil, fmt.Errorf("not enough data for property name length")
		}
		nameLen := int(binary.BigEndian.Uint16(d.data[d.offset : d.offset+2]))
		d.offset += 2

		if nameLen == 0 {
			// Check for object end marker
			if d.offset < len(d.data) && d.data[d.offset] == AMF0ObjectEnd {
				d.offset++
				break
			}
		}

		if d.offset+nameLen > len(d.data) {
			return nil, fmt.Errorf("not enough data for property name")
		}
		name := string(d.data[d.offset : d.offset+nameLen])
		d.offset += nameLen

		// Read property value
		value, err := d.Decode()
		if err != nil {
			return nil, err
		}
		obj[name] = value
	}
	return obj, nil
}

func (d *AMFDecoder) decodeEcmaArray() (AMFObject, error) {
	// Skip array count (4 bytes)
	if d.offset+4 > len(d.data) {
		return nil, fmt.Errorf("not enough data for ecma array count")
	}
	d.offset += 4

	// Read as object
	return d.decodeObject()
}

// DecodeCommand decodes an RTMP command from AMF0 data
func DecodeCommand(data []byte) (string, []interface{}, error) {
	decoder := NewAMFDecoder(data)

	// First value is command name
	nameVal, err := decoder.Decode()
	if err != nil {
		return "", nil, fmt.Errorf("failed to decode command name: %w", err)
	}

	name, ok := nameVal.(string)
	if !ok {
		return "", nil, fmt.Errorf("invalid command name type: %T", nameVal)
	}

	// Decode remaining values
	var args []interface{}
	for decoder.offset < len(data) {
		val, err := decoder.Decode()
		if err != nil {
			break
		}
		args = append(args, val)
	}

	return name, args, nil
}

// EncodeCommand encodes an RTMP command to AMF0 data
func EncodeCommand(name string, args ...interface{}) ([]byte, error) {
	encoder := NewAMFEncoder()

	// Encode command name
	if err := encoder.Encode(name); err != nil {
		return nil, err
	}

	// Encode arguments
	for _, arg := range args {
		if err := encoder.Encode(arg); err != nil {
			return nil, err
		}
	}

	return encoder.Bytes(), nil
}
