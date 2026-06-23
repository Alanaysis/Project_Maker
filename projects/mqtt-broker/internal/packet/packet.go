// Package packet implements MQTT 3.1.1 packet encoding and decoding.
// Reference: https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html
package packet

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
)

// MQTT Control Packet types
const (
	CONNECT     byte = 1
	CONNACK     byte = 2
	PUBLISH     byte = 3
	PUBACK      byte = 4
	PUBREC      byte = 5
	PUBREL      byte = 6
	PUBCOMP     byte = 7
	SUBSCRIBE   byte = 8
	SUBACK      byte = 9
	UNSUBSCRIBE byte = 10
	UNSUBACK    byte = 11
	PINGREQ     byte = 12
	PINGRESP    byte = 13
	DISCONNECT  byte = 14
)

// CONNACK return codes
const (
	ConnAccepted          byte = 0x00
	ConnRefusedProtocol   byte = 0x01
	ConnRefusedIdentifier byte = 0x02
	ConnRefusedServer     byte = 0x03
	ConnRefusedBadUser    byte = 0x04
	ConnRefusedNotAuth    byte = 0x05
)

// Common errors
var (
	ErrProtocolViolation = errors.New("mqtt: protocol violation")
	ErrMalformedPacket   = errors.New("mqtt: malformed packet")
	ErrPacketTooLarge    = errors.New("mqtt: packet too large")
)

// FixedHeader represents the MQTT fixed header.
type FixedHeader struct {
	Type      byte
	Dup       bool
	QoS       byte
	Retain    bool
	Remaining int // remaining length
}

// Packet is the interface for all MQTT packets.
type Packet interface {
	Type() byte
	Encode() ([]byte, error)
}

// ConnectPacket represents an MQTT CONNECT packet.
type ConnectPacket struct {
	ProtocolName    string
	ProtocolLevel   byte
	CleanSession    bool
	KeepAlive       uint16
	ClientID        string
	WillTopic       string
	WillMessage     []byte
	WillQoS         byte
	WillRetain      bool
	WillFlag        bool
	Username        string
	Password        []byte
	UsernameFlag    bool
	PasswordFlag    bool
}

func (p *ConnectPacket) Type() byte { return CONNECT }

// ConnackPacket represents an MQTT CONNACK packet.
type ConnackPacket struct {
	SessionPresent bool
	ReturnCode     byte
}

func (p *ConnackPacket) Type() byte { return CONNACK }

// PublishPacket represents an MQTT PUBLISH packet.
type PublishPacket struct {
	Dup       bool
	QoS       byte
	Retain    bool
	TopicName string
	PacketID  uint16
	Payload   []byte
}

func (p *PublishPacket) Type() byte { return PUBLISH }

// PubackPacket represents an MQTT PUBACK packet (QoS 1 acknowledgement).
type PubackPacket struct {
	PacketID uint16
}

func (p *PubackPacket) Type() byte { return PUBACK }

// PubrecPacket represents an MQTT PUBREC packet (QoS 2, step 1).
type PubrecPacket struct {
	PacketID uint16
}

func (p *PubrecPacket) Type() byte { return PUBREC }

// PubrelPacket represents an MQTT PUBREL packet (QoS 2, step 2).
type PubrelPacket struct {
	PacketID uint16
}

func (p *PubrelPacket) Type() byte { return PUBREL }

// PubcompPacket represents an MQTT PUBCOMP packet (QoS 2, step 3).
type PubcompPacket struct {
	PacketID uint16
}

func (p *PubcompPacket) Type() byte { return PUBCOMP }

// SubscribePacket represents an MQTT SUBSCRIBE packet.
type SubscribePacket struct {
	PacketID   uint16
	Topics     []string
	QoSs       []byte
}

func (p *SubscribePacket) Type() byte { return SUBSCRIBE }

// SubackPacket represents an MQTT SUBACK packet.
type SubackPacket struct {
	PacketID    uint16
	ReturnCodes []byte
}

func (p *SubackPacket) Type() byte { return SUBACK }

// UnsubscribePacket represents an MQTT UNSUBSCRIBE packet.
type UnsubscribePacket struct {
	PacketID uint16
	Topics   []string
}

func (p *UnsubscribePacket) Type() byte { return UNSUBSCRIBE }

// UnsubackPacket represents an MQTT UNSUBACK packet.
type UnsubackPacket struct {
	PacketID uint16
}

func (p *UnsubackPacket) Type() byte { return UNSUBACK }

// PingreqPacket represents an MQTT PINGREQ packet.
type PingreqPacket struct{}

func (p *PingreqPacket) Type() byte { return PINGREQ }

// PingrespPacket represents an MQTT PINGRESP packet.
type PingrespPacket struct{}

func (p *PingrespPacket) Type() byte { return PINGRESP }

// DisconnectPacket represents an MQTT DISCONNECT packet.
type DisconnectPacket struct{}

func (p *DisconnectPacket) Type() byte { return DISCONNECT }

// --- Encoding helpers ---

// encodeLength encodes the remaining length field using MQTT variable-length encoding.
func encodeLength(length int) []byte {
	var encoded []byte
	for {
		digit := byte(length % 128)
		length /= 128
		if length > 0 {
			digit |= 0x80
		}
		encoded = append(encoded, digit)
		if length == 0 {
			break
		}
	}
	return encoded
}

// decodeLength decodes the remaining length field.
func decodeLength(r io.Reader) (int, error) {
	var value int
	var multiplier = 1
	buf := make([]byte, 1)
	for {
		if _, err := io.ReadFull(r, buf); err != nil {
			return 0, err
		}
		digit := buf[0]
		value += int(digit&0x7F) * multiplier
		if multiplier > 128*128*128 {
			return 0, ErrMalformedPacket
		}
		if digit&0x80 == 0 {
			break
		}
		multiplier *= 128
	}
	return value, nil
}

// encodeString encodes a UTF-8 string with a 2-byte length prefix.
func encodeString(s string) []byte {
	b := make([]byte, 2+len(s))
	binary.BigEndian.PutUint16(b[0:2], uint16(len(s)))
	copy(b[2:], s)
	return b
}

// decodeString reads a length-prefixed string.
func decodeString(r io.Reader) (string, error) {
	buf := make([]byte, 2)
	if _, err := io.ReadFull(r, buf); err != nil {
		return "", err
	}
	length := binary.BigEndian.Uint16(buf)
	strBuf := make([]byte, length)
	if _, err := io.ReadFull(r, strBuf); err != nil {
		return "", err
	}
	return string(strBuf), nil
}

// encodeUint16 encodes a uint16 in big-endian.
func encodeUint16(v uint16) []byte {
	b := make([]byte, 2)
	binary.BigEndian.PutUint16(b, v)
	return b
}

// decodeUint16 reads a uint16 in big-endian.
func decodeUint16(r io.Reader) (uint16, error) {
	buf := make([]byte, 2)
	if _, err := io.ReadFull(r, buf); err != nil {
		return 0, err
	}
	return binary.BigEndian.Uint16(buf), nil
}

// --- Encode methods ---

func (p *ConnectPacket) Encode() ([]byte, error) {
	var body bytes.Buffer

	// Variable header
	body.Write(encodeString(p.ProtocolName))
	body.WriteByte(p.ProtocolLevel)

	// Connect flags
	var flags byte
	if p.CleanSession {
		flags |= 0x02
	}
	if p.WillFlag {
		flags |= 0x04
		flags |= (p.WillQoS & 0x03) << 3
		if p.WillRetain {
			flags |= 0x20
		}
	}
	if p.PasswordFlag {
		flags |= 0x40
	}
	if p.UsernameFlag {
		flags |= 0x80
	}
	body.WriteByte(flags)
	body.Write(encodeUint16(p.KeepAlive))

	// Payload
	body.Write(encodeString(p.ClientID))
	if p.WillFlag {
		body.Write(encodeString(p.WillTopic))
		body.Write(encodeUint16(uint16(len(p.WillMessage))))
		body.Write(p.WillMessage)
	}
	if p.UsernameFlag {
		body.Write(encodeString(p.Username))
	}
	if p.PasswordFlag {
		body.Write(encodeUint16(uint16(len(p.Password))))
		body.Write(p.Password)
	}

	// Fixed header
	var header bytes.Buffer
	header.WriteByte(CONNECT << 4)
	header.Write(encodeLength(body.Len()))
	header.Write(body.Bytes())

	return header.Bytes(), nil
}

func (p *ConnackPacket) Encode() ([]byte, error) {
	var body bytes.Buffer
	body.WriteByte(0) // reserved
	if p.SessionPresent {
		body.WriteByte(1)
	} else {
		body.WriteByte(p.ReturnCode)
	}

	var header bytes.Buffer
	header.WriteByte(CONNACK << 4)
	header.Write(encodeLength(2))
	header.Write(body.Bytes())
	return header.Bytes(), nil
}

func (p *PublishPacket) Encode() ([]byte, error) {
	var body bytes.Buffer

	body.Write(encodeString(p.TopicName))
	if p.QoS > 0 {
		body.Write(encodeUint16(p.PacketID))
	}
	body.Write(p.Payload)

	// Fixed header
	var header byte = PUBLISH << 4
	if p.Dup {
		header |= 0x08
	}
	header |= (p.QoS & 0x03) << 1
	if p.Retain {
		header |= 0x01
	}

	var result bytes.Buffer
	result.WriteByte(header)
	result.Write(encodeLength(body.Len()))
	result.Write(body.Bytes())

	return result.Bytes(), nil
}

func (p *PubackPacket) Encode() ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte(PUBACK << 4)
	buf.Write(encodeLength(2))
	buf.Write(encodeUint16(p.PacketID))
	return buf.Bytes(), nil
}

func (p *PubrecPacket) Encode() ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte(PUBREC << 4)
	buf.Write(encodeLength(2))
	buf.Write(encodeUint16(p.PacketID))
	return buf.Bytes(), nil
}

func (p *PubrelPacket) Encode() ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte(PUBREL<<4 | 0x02) // PUBREL has fixed flags 0010
	buf.Write(encodeLength(2))
	buf.Write(encodeUint16(p.PacketID))
	return buf.Bytes(), nil
}

func (p *PubcompPacket) Encode() ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte(PUBCOMP << 4)
	buf.Write(encodeLength(2))
	buf.Write(encodeUint16(p.PacketID))
	return buf.Bytes(), nil
}

func (p *SubscribePacket) Encode() ([]byte, error) {
	var body bytes.Buffer
	body.Write(encodeUint16(p.PacketID))
	for i, topic := range p.Topics {
		body.Write(encodeString(topic))
		body.WriteByte(p.QoSs[i])
	}

	var buf bytes.Buffer
	buf.WriteByte(SUBSCRIBE<<4 | 0x02) // fixed flags 0010
	buf.Write(encodeLength(body.Len()))
	buf.Write(body.Bytes())
	return buf.Bytes(), nil
}

func (p *SubackPacket) Encode() ([]byte, error) {
	var body bytes.Buffer
	body.Write(encodeUint16(p.PacketID))
	for _, rc := range p.ReturnCodes {
		body.WriteByte(rc)
	}

	var buf bytes.Buffer
	buf.WriteByte(SUBACK << 4)
	buf.Write(encodeLength(body.Len()))
	buf.Write(body.Bytes())
	return buf.Bytes(), nil
}

func (p *UnsubscribePacket) Encode() ([]byte, error) {
	var body bytes.Buffer
	body.Write(encodeUint16(p.PacketID))
	for _, topic := range p.Topics {
		body.Write(encodeString(topic))
	}

	var buf bytes.Buffer
	buf.WriteByte(UNSUBSCRIBE<<4 | 0x02)
	buf.Write(encodeLength(body.Len()))
	buf.Write(body.Bytes())
	return buf.Bytes(), nil
}

func (p *UnsubackPacket) Encode() ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte(UNSUBACK << 4)
	buf.Write(encodeLength(2))
	buf.Write(encodeUint16(p.PacketID))
	return buf.Bytes(), nil
}

func (p *PingreqPacket) Encode() ([]byte, error) {
	return []byte{PINGREQ << 4, 0}, nil
}

func (p *PingrespPacket) Encode() ([]byte, error) {
	return []byte{PINGRESP << 4, 0}, nil
}

func (p *DisconnectPacket) Encode() ([]byte, error) {
	return []byte{DISCONNECT << 4, 0}, nil
}

// --- Decoding ---

// ReadPacket reads one MQTT packet from the reader.
func ReadPacket(r io.Reader) (Packet, *FixedHeader, error) {
	// Read fixed header byte
	headerBuf := make([]byte, 1)
	if _, err := io.ReadFull(r, headerBuf); err != nil {
		return nil, nil, err
	}

	fh := &FixedHeader{
		Type:   (headerBuf[0] >> 4) & 0x0F,
		Dup:    (headerBuf[0] & 0x08) != 0,
		QoS:    (headerBuf[0] >> 1) & 0x03,
		Retain: (headerBuf[0] & 0x01) != 0,
	}

	remaining, err := decodeLength(r)
	if err != nil {
		return nil, nil, err
	}
	fh.Remaining = remaining

	// Read the remaining bytes
	body := make([]byte, remaining)
	if remaining > 0 {
		if _, err := io.ReadFull(r, body); err != nil {
			return nil, nil, err
		}
	}
	bodyReader := bytes.NewReader(body)

	switch fh.Type {
	case CONNECT:
		return decodeConnect(bodyReader, fh)
	case PUBLISH:
		return decodePublish(bodyReader, fh)
	case PUBACK:
		return decodePuback(bodyReader)
	case PUBREC:
		return decodePubrec(bodyReader)
	case PUBREL:
		return decodePubrel(bodyReader)
	case PUBCOMP:
		return decodePubcomp(bodyReader)
	case SUBSCRIBE:
		return decodeSubscribe(bodyReader)
	case SUBACK:
		return decodeSuback(bodyReader)
	case UNSUBSCRIBE:
		return decodeUnsubscribe(bodyReader)
	case UNSUBACK:
		return decodeUnsuback(bodyReader)
	case PINGREQ:
		return &PingreqPacket{}, fh, nil
	case PINGRESP:
		return &PingrespPacket{}, fh, nil
	case DISCONNECT:
		return &DisconnectPacket{}, fh, nil
	default:
		return nil, fh, fmt.Errorf("mqtt: unknown packet type %d", fh.Type)
	}
}

func decodeConnect(r io.Reader, fh *FixedHeader) (*ConnectPacket, *FixedHeader, error) {
	p := &ConnectPacket{}

	protocolName, err := decodeString(r)
	if err != nil {
		return nil, fh, err
	}
	p.ProtocolName = protocolName

	level, err := decodeByte(r)
	if err != nil {
		return nil, fh, err
	}
	p.ProtocolLevel = level

	flags, err := decodeByte(r)
	if err != nil {
		return nil, fh, err
	}
	p.CleanSession = (flags & 0x02) != 0
	p.WillFlag = (flags & 0x04) != 0
	p.WillQoS = (flags >> 3) & 0x03
	p.WillRetain = (flags & 0x20) != 0
	p.PasswordFlag = (flags & 0x40) != 0
	p.UsernameFlag = (flags & 0x80) != 0

	keepAlive, err := decodeUint16(r)
	if err != nil {
		return nil, fh, err
	}
	p.KeepAlive = keepAlive

	// Payload
	clientID, err := decodeString(r)
	if err != nil {
		return nil, fh, err
	}
	p.ClientID = clientID

	if p.WillFlag {
		willTopic, err := decodeString(r)
		if err != nil {
			return nil, fh, err
		}
		p.WillTopic = willTopic

		willLen, err := decodeUint16(r)
		if err != nil {
			return nil, fh, err
		}
		willMsg := make([]byte, willLen)
		if _, err := io.ReadFull(r, willMsg); err != nil {
			return nil, fh, err
		}
		p.WillMessage = willMsg
	}

	if p.UsernameFlag {
		username, err := decodeString(r)
		if err != nil {
			return nil, fh, err
		}
		p.Username = username
	}

	if p.PasswordFlag {
		passLen, err := decodeUint16(r)
		if err != nil {
			return nil, fh, err
		}
		password := make([]byte, passLen)
		if _, err := io.ReadFull(r, password); err != nil {
			return nil, fh, err
		}
		p.Password = password
	}

	return p, fh, nil
}

func decodePublish(r io.Reader, fh *FixedHeader) (*PublishPacket, *FixedHeader, error) {
	p := &PublishPacket{
		Dup:    fh.Dup,
		QoS:    fh.QoS,
		Retain: fh.Retain,
	}

	topic, err := decodeString(r)
	if err != nil {
		return nil, fh, err
	}
	p.TopicName = topic

	if fh.QoS > 0 {
		pid, err := decodeUint16(r)
		if err != nil {
			return nil, fh, err
		}
		p.PacketID = pid
	}

	// Remaining bytes are the payload
	var payload bytes.Buffer
	if _, err := io.Copy(&payload, r); err != nil {
		return nil, fh, err
	}
	p.Payload = payload.Bytes()

	return p, fh, nil
}

func decodePuback(r io.Reader) (*PubackPacket, *FixedHeader, error) {
	pid, err := decodeUint16(r)
	if err != nil {
		return nil, nil, err
	}
	return &PubackPacket{PacketID: pid}, &FixedHeader{Type: PUBACK}, nil
}

func decodePubrec(r io.Reader) (*PubrecPacket, *FixedHeader, error) {
	pid, err := decodeUint16(r)
	if err != nil {
		return nil, nil, err
	}
	return &PubrecPacket{PacketID: pid}, &FixedHeader{Type: PUBREC}, nil
}

func decodePubrel(r io.Reader) (*PubrelPacket, *FixedHeader, error) {
	pid, err := decodeUint16(r)
	if err != nil {
		return nil, nil, err
	}
	return &PubrelPacket{PacketID: pid}, &FixedHeader{Type: PUBREL}, nil
}

func decodePubcomp(r io.Reader) (*PubcompPacket, *FixedHeader, error) {
	pid, err := decodeUint16(r)
	if err != nil {
		return nil, nil, err
	}
	return &PubcompPacket{PacketID: pid}, &FixedHeader{Type: PUBCOMP}, nil
}

func decodeSubscribe(r io.Reader) (*SubscribePacket, *FixedHeader, error) {
	p := &SubscribePacket{}
	pid, err := decodeUint16(r)
	if err != nil {
		return nil, nil, err
	}
	p.PacketID = pid

	for {
		topic, err := decodeString(r)
		if err == io.EOF || err == io.ErrUnexpectedEOF {
			break
		}
		if err != nil {
			return nil, nil, err
		}
		qos, err := decodeByte(r)
		if err != nil {
			return nil, nil, err
		}
		p.Topics = append(p.Topics, topic)
		p.QoSs = append(p.QoSs, qos)
	}

	return p, &FixedHeader{Type: SUBSCRIBE}, nil
}

func decodeSuback(r io.Reader) (*SubackPacket, *FixedHeader, error) {
	p := &SubackPacket{}
	pid, err := decodeUint16(r)
	if err != nil {
		return nil, nil, err
	}
	p.PacketID = pid

	var codes []byte
	buf := make([]byte, 1)
	for {
		if _, err := io.ReadFull(r, buf); err != nil {
			break
		}
		codes = append(codes, buf[0])
	}
	p.ReturnCodes = codes

	return p, &FixedHeader{Type: SUBACK}, nil
}

func decodeUnsubscribe(r io.Reader) (*UnsubscribePacket, *FixedHeader, error) {
	p := &UnsubscribePacket{}
	pid, err := decodeUint16(r)
	if err != nil {
		return nil, nil, err
	}
	p.PacketID = pid

	for {
		topic, err := decodeString(r)
		if err == io.EOF || err == io.ErrUnexpectedEOF {
			break
		}
		if err != nil {
			return nil, nil, err
		}
		p.Topics = append(p.Topics, topic)
	}

	return p, &FixedHeader{Type: UNSUBSCRIBE}, nil
}

func decodeUnsuback(r io.Reader) (*UnsubackPacket, *FixedHeader, error) {
	pid, err := decodeUint16(r)
	if err != nil {
		return nil, nil, err
	}
	return &UnsubackPacket{PacketID: pid}, &FixedHeader{Type: UNSUBACK}, nil
}

func decodeByte(r io.Reader) (byte, error) {
	buf := make([]byte, 1)
	if _, err := io.ReadFull(r, buf); err != nil {
		return 0, err
	}
	return buf[0], nil
}
