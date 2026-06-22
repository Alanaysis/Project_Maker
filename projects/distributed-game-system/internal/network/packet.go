package network

import (
	"encoding/binary"
	"fmt"
	"time"
)

// 消息类型常量
type MessageType uint8

const (
	// 连接管理
	MsgConnect     MessageType = 1
	MsgConnectAck  MessageType = 2
	MsgDisconnect  MessageType = 3
	MsgHeartbeat   MessageType = 4

	// 游戏状态
	MsgPlayerInput   MessageType = 10
	MsgStateSnapshot MessageType = 11
	MsgStateDelta    MessageType = 12

	// 游戏事件
	MsgPlayerJoin   MessageType = 20
	MsgPlayerLeave  MessageType = 21
	MsgPlayerAttack MessageType = 22
	MsgPlayerDamage MessageType = 23
)

// 数据包头大小
const PacketHeaderSize = 9 // Type(1) + Sequence(2) + Timestamp(4) + Length(2)

// PacketHeader 数据包头
type PacketHeader struct {
	Type      MessageType
	Sequence  uint16
	Timestamp uint32
	Length    uint16
}

// Packet 数据包
type Packet struct {
	Header  PacketHeader
	Payload []byte
}

// EncodePacket 编码数据包
func EncodePacket(msgType MessageType, sequence uint16, payload []byte) ([]byte, error) {
	header := PacketHeader{
		Type:      msgType,
		Sequence:  sequence,
		Timestamp: uint32(time.Now().UnixMilli() / 1000),
		Length:    uint16(len(payload)),
	}

	buf := make([]byte, PacketHeaderSize+len(payload))

	// 编码头部
	buf[0] = uint8(header.Type)
	binary.BigEndian.PutUint16(buf[1:3], header.Sequence)
	binary.BigEndian.PutUint32(buf[3:7], header.Timestamp)
	binary.BigEndian.PutUint16(buf[7:9], header.Length)

	// 复制负载
	copy(buf[PacketHeaderSize:], payload)

	return buf, nil
}

// DecodePacket 解码数据包
func DecodePacket(data []byte) (*Packet, error) {
	if len(data) < PacketHeaderSize {
		return nil, fmt.Errorf("packet too short: %d bytes", len(data))
	}

	header := PacketHeader{
		Type:      MessageType(data[0]),
		Sequence:  binary.BigEndian.Uint16(data[1:3]),
		Timestamp: binary.BigEndian.Uint32(data[3:7]),
		Length:    binary.BigEndian.Uint16(data[7:9]),
	}

	if len(data) < PacketHeaderSize+int(header.Length) {
		return nil, fmt.Errorf("packet payload incomplete")
	}

	payload := make([]byte, header.Length)
	copy(payload, data[PacketHeaderSize:PacketHeaderSize+header.Length])

	return &Packet{
		Header:  header,
		Payload: payload,
	}, nil
}
