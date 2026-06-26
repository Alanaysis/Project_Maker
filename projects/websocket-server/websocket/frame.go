// Package frame implements WebSocket frame parsing and framing per RFC 6455.
//
// WebSocket 帧是 WebSocket 协议的基本数据单元。每个帧由以下部分组成：
//
//   0                   1                   2                   3
//   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
//  +-+-+-+-+-------+-+-------------+-------------------------------+
//  |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
//  |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
//  |N|V|V|V|       |S|             |   (if payload len==126/127)   |
//  | |1|2|3|       |K|             |                               |
//  +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
//  |     Extended payload length continued, if payload len == 127  |
//  + - - - - - - - - - - - - - - - +-------------------------------+
//  |                               |Masking-key, if MASK set to 1  |
//  +-------------------------------+-------------------------------+
//  | Masking-key (continued)       |          Payload Data         |
//  +-------------------------------- - - - - - - - - - - - - - - - +
//  :                     Payload Data continued ...                :
//  + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
//  |                     Payload Data continued                    |
//  +---------------------------------------------------------------+
//
//  FIN:    1 bit - 是否为最后一个分帧
//  RSV1-3: 1 bit each - 必须为0（除非扩展定义）
//  Opcode: 4 bits - 帧类型（0x0延续, 0x1文本, 0x2二进制, 0x8关闭, 0x9心跳ping, 0xA心跳pong）
//  MASK:   1 bit - 负载数据是否加密
//  Payload Length: 7/23/71 bits - 负载长度
//  Masking Key: 0 or 32 bits - 掩码密钥
//  Payload Data: 可变长度 - 负载数据
package websocket

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
)

// Opcode defines the WebSocket frame operation code.
// 定义 WebSocket 帧操作码
type Opcode int

const (
	OpcodeContinuation Opcode = 0x0 // 延续帧 - 继续上一个消息
	OpcodeText         Opcode = 0x1 // 文本帧 - 携带文本数据
	OpcodeBinary       Opcode = 0x2 // 二进制帧 - 携带二进制数据
	OpcodeClose        Opcode = 0x8 // 关闭帧 - 开始关闭连接
	OpcodePing         Opcode = 0x9 // Ping 帧 - 心跳检测
	OpcodePong         Opcode = 0xA // Pong 帧 - 心跳响应
)

// String returns the string representation of the opcode.
func (o Opcode) String() string {
	switch o {
	case OpcodeContinuation:
		return "CONTINUATION"
	case OpcodeText:
		return "TEXT"
	case OpcodeBinary:
		return "BINARY"
	case OpcodeClose:
		return "CLOSE"
	case OpcodePing:
		return "PING"
	case OpcodePong:
		return "PONG"
	default:
		return fmt.Sprintf("UNKNOWN(%d)", o)
	}
}

// CloseStatusCode defines standard WebSocket close codes per RFC 6455 Section 7.4.
// 定义 WebSocket 标准关闭状态码
type CloseStatusCode int

const (
	CloseNormalClosure           CloseStatusCode = 1000 // 正常关闭
	CloseGoingAway               CloseStatusCode = 1001 // 端点离开（如浏览器标签关闭）
	CloseProtocolError           CloseStatusCode = 1002 // 协议错误
	CloseUnsupportedData         CloseStatusCode = 1003 // 不支持的数据类型
	CloseReserved1004            CloseStatusCode = 1004 // 保留（由客户端/服务器定义）
	CloseNoStatusReceived        CloseStatusCode = 1005 // 保留（实际未使用）
	CloseAbnormalClosure         CloseStatusCode = 1006 // 保留（异常关闭，无关闭帧）
	CloseInvalidPayload          CloseStatusCode = 1007 // 无效负载数据
	ClosePolicyViolation         CloseStatusCode = 1008 // 策略违规
	CloseMessageTooBig           CloseStatusCode = 1009 // 消息过大
	CloseMandatoryExtension      CloseStatusCode = 1010 // 缺少必需的扩展
	CloseInternalServerErr       CloseStatusCode = 1011 // 内部服务器错误
	CloseServiceRestart          CloseStatusCode = 1012 // 服务重启
	CloseTryAgainLater           CloseStatusCode = 1013 // 稍后重试
	CloseTLSHandshake            CloseStatusCode = 1015 // TLS 握手失败（保留）
)

// String returns the string representation of the close code.
func (c CloseStatusCode) String() string {
	switch c {
	case CloseNormalClosure:
		return "Normal Closure"
	case CloseGoingAway:
		return "Going Away"
	case CloseProtocolError:
		return "Protocol Error"
	case CloseUnsupportedData:
		return "Unsupported Data"
	case CloseNoStatusReceived:
		return "No Status Received"
	case CloseAbnormalClosure:
		return "Abnormal Closure"
	case CloseInvalidPayload:
		return "Invalid Payload"
	case ClosePolicyViolation:
		return "Policy Violation"
	case CloseMessageTooBig:
		return "Message Too Big"
	case CloseTLSHandshake:
		return "TLS Handshake Failed"
	default:
		return fmt.Sprintf("Close(%d)", int(c))
	}
}

// Frame represents a parsed WebSocket frame.
// 表示一个解析后的 WebSocket 帧
type Frame struct {
	FIN        bool      // FIN 标志 - 是否为消息的最后一帧
	Opcode     Opcode    // 操作码 - 帧类型
	Masked     bool      // MASK 标志 - 是否被掩码
	Payload    []byte    // 负载数据
	RemoteAddr string    // 远程地址（用于掩码解算）
}

// IsControl returns true if the frame is a control frame (ping/pong/close).
// 判断是否为控制帧
func (f *Frame) IsControl() bool {
	return f.Opcode >= 0x8
}

// MessageType returns a human-readable message type string.
func (f *Frame) MessageType() string {
	if f.FIN {
		return f.Opcode.String()
	}
	return fmt.Sprintf("%s (fragmented)", f.Opcode.String())
}

// ParseFrame reads a single WebSocket frame from the reader.
// 从 reader 读取并解析一个 WebSocket 帧
//
// WebSocket 帧解析流程：
// 1. 读取前 2 字节（FIN+opcode, MASK+payload length）
// 2. 解析负载长度（可能跨 2/8 字节）
// 3. 如果 MASK=1，读取 4 字节掩码密钥
// 4. 读取负载数据并解掩码
func ParseFrame(r io.Reader) (*Frame, error) {
	// Step 1: Read the first 2 bytes
	// 读取前 2 字节
	header := make([]byte, 2)
	if _, err := io.ReadFull(r, header); err != nil {
		return nil, fmt.Errorf("read frame header: %w", err)
	}

	fin := header[0]&0x80 != 0
	opcode := Opcode(header[0] & 0x0F)
	masked := header[1]&0x80 != 0
	payloadLen := uint64(header[1] & 0x7F)

	// Step 2: Read extended payload length if needed
	// 如果长度 >= 126，读取扩展长度
	switch payloadLen {
	case 126:
		extLen := make([]byte, 2)
		if _, err := io.ReadFull(r, extLen); err != nil {
			return nil, fmt.Errorf("read extended length: %w", err)
		}
		payloadLen = uint64(binary.BigEndian.Uint16(extLen))
	case 127:
		extLen := make([]byte, 8)
		if _, err := io.ReadFull(r, extLen); err != nil {
			return nil, fmt.Errorf("read extended length: %w", err)
		}
		payloadLen = binary.BigEndian.Uint64(extLen)
	}

	// Step 3: Read masking key if masked
	// 如果客户端帧被掩码，读取掩码密钥
	var maskingKey [4]byte
	if masked {
		if _, err := io.ReadFull(r, maskingKey[:]); err != nil {
			return nil, fmt.Errorf("read masking key: %w", err)
		}
	}

	// Step 4: Read payload
	// 读取负载数据
	payload := make([]byte, payloadLen)
	if payloadLen > 0 {
		if _, err := io.ReadFull(r, payload); err != nil {
			return nil, fmt.Errorf("read payload: %w", err)
		}

		// Step 5: Unmask payload data
		// 解掩码：每个字节与掩码密钥循环异或
		if masked {
			for i := uint64(0); i < payloadLen; i++ {
				payload[i] ^= maskingKey[i%4]
			}
		}
	}

	return &Frame{
		FIN:      fin,
		Opcode:   opcode,
		Masked:   masked,
		Payload:  payload,
	}, nil
}

// Marshal serializes a WebSocket frame to bytes.
// 将 WebSocket 帧序列化为字节数组
//
// 服务端帧不需要掩码（只有客户端→服务端需要掩码）
func (f *Frame) Marshal() ([]byte, error) {
	var buf bytes.Buffer

	// Write first byte: FIN + opcode
	// 写入第一字节：FIN 标志 + 操作码
	firstByte := byte(f.Opcode)
	if f.FIN {
		firstByte |= 0x80
	}
	if err := buf.WriteByte(firstByte); err != nil {
		return nil, fmt.Errorf("write first byte: %w", err)
	}

	// Write payload length
	// 写入负载长度
	payloadLen := len(f.Payload)
	secondByte := byte(0) // 服务端帧不设置 MASK 位
	switch {
	case payloadLen <= 125:
		secondByte |= byte(payloadLen)
		if err := buf.WriteByte(secondByte); err != nil {
			return nil, fmt.Errorf("write length byte: %w", err)
		}
	case payloadLen <= 65535:
		secondByte |= 126
		if err := buf.WriteByte(secondByte); err != nil {
			return nil, fmt.Errorf("write length byte: %w", err)
		}
		extLen := make([]byte, 2)
		binary.BigEndian.PutUint16(extLen, uint16(payloadLen))
		if _, err := buf.Write(extLen); err != nil {
			return nil, fmt.Errorf("write extended length: %w", err)
		}
	default:
		secondByte |= 127
		if err := buf.WriteByte(secondByte); err != nil {
			return nil, fmt.Errorf("write length byte: %w", err)
		}
		extLen := make([]byte, 8)
		binary.BigEndian.PutUint64(extLen, uint64(payloadLen))
		if _, err := buf.Write(extLen); err != nil {
			return nil, fmt.Errorf("write extended length: %w", err)
		}
	}

	// Write payload
	if _, err := buf.Write(f.Payload); err != nil {
		return nil, fmt.Errorf("write payload: %w", err)
	}

	return buf.Bytes(), nil
}

// CloseFrame creates a close frame with the given status code and reason.
// 创建关闭帧
func CloseFrame(code CloseStatusCode, reason string) *Frame {
	payload := make([]byte, 2+len(reason))
	binary.BigEndian.PutUint16(payload, uint16(code))
	copy(payload[2:], reason)
	return &Frame{
		FIN:      true,
		Opcode:   OpcodeClose,
		Masked:   false,
		Payload:  payload,
		RemoteAddr: "",
	}
}

// PingFrame creates a ping frame with optional data.
// 创建 Ping 心跳帧
func PingFrame(data []byte) *Frame {
	payload := make([]byte, len(data))
	copy(payload, data)
	return &Frame{
		FIN:      true,
		Opcode:   OpcodePing,
		Masked:   false,
		Payload:  payload,
		RemoteAddr: "",
	}
}

// PongFrame creates a pong frame with optional data.
// 创建 Pong 心跳响应帧
func PongFrame(data []byte) *Frame {
	payload := make([]byte, len(data))
	copy(payload, data)
	return &Frame{
		FIN:      true,
		Opcode:   OpcodePong,
		Masked:   false,
		Payload:  payload,
		RemoteAddr: "",
	}
}

// TextFrame creates a text frame.
// 创建文本帧
func TextFrame(data []byte) *Frame {
	return &Frame{
		FIN:      true,
		Opcode:   OpcodeText,
		Masked:   false,
		Payload:  make([]byte, len(data)),
		RemoteAddr: "",
	}
}

// BinaryFrame creates a binary frame.
// 创建二进制帧
func BinaryFrame(data []byte) *Frame {
	return &Frame{
		FIN:      true,
		Opcode:   OpcodeBinary,
		Masked:   false,
		Payload:  make([]byte, len(data)),
		RemoteAddr: "",
	}
}

// ErrCloseSent is returned when a close frame has already been sent.
var ErrCloseSent = errors.New("close frame already sent")

// ErrMessageTooBig is returned when a message exceeds the maximum size.
var ErrMessageTooBig = errors.New("message too big")

// CloseMessage extracts the close code and reason from a close frame payload.
// 从关闭帧负载中提取关闭码和原因
func CloseMessage(payload []byte) (CloseStatusCode, string) {
	if len(payload) < 2 {
		return CloseNoStatusReceived, ""
	}
	code := CloseStatusCode(binary.BigEndian.Uint16(payload))
	reason := string(payload[2:])
	return code, reason
}
