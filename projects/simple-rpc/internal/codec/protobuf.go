package codec

import (
	"fmt"
	"io"

	"google.golang.org/protobuf/proto"
)

// ProtobufCodec Protobuf 编解码器
type ProtobufCodec struct{}

// NewProtobufCodec 创建 Protobuf 编解码器
func NewProtobufCodec() *ProtobufCodec {
	return &ProtobufCodec{}
}

func (c *ProtobufCodec) Encode(writer io.Writer, v interface{}) error {
	msg, ok := v.(proto.Message)
	if !ok {
		return fmt.Errorf("protobuf codec: value does not implement proto.Message")
	}

	data, err := proto.Marshal(msg)
	if err != nil {
		return fmt.Errorf("protobuf codec: marshal error: %w", err)
	}

	// 写入长度前缀（4 字节）
	lenBytes := make([]byte, 4)
	lenBytes[0] = byte(len(data) >> 24)
	lenBytes[1] = byte(len(data) >> 16)
	lenBytes[2] = byte(len(data) >> 8)
	lenBytes[3] = byte(len(data))

	if _, err := writer.Write(lenBytes); err != nil {
		return fmt.Errorf("protobuf codec: write length error: %w", err)
	}

	if _, err := writer.Write(data); err != nil {
		return fmt.Errorf("protobuf codec: write data error: %w", err)
	}

	return nil
}

func (c *ProtobufCodec) Decode(reader io.Reader, v interface{}) error {
	msg, ok := v.(proto.Message)
	if !ok {
		return fmt.Errorf("protobuf codec: value does not implement proto.Message")
	}

	// 读取长度前缀（4 字节）
	lenBytes := make([]byte, 4)
	if _, err := io.ReadFull(reader, lenBytes); err != nil {
		return fmt.Errorf("protobuf codec: read length error: %w", err)
	}

	dataLen := int(lenBytes[0])<<24 | int(lenBytes[1])<<16 | int(lenBytes[2])<<8 | int(lenBytes[3])

	// 读取数据
	data := make([]byte, dataLen)
	if _, err := io.ReadFull(reader, data); err != nil {
		return fmt.Errorf("protobuf codec: read data error: %w", err)
	}

	if err := proto.Unmarshal(data, msg); err != nil {
		return fmt.Errorf("protobuf codec: unmarshal error: %w", err)
	}

	return nil
}

func (c *ProtobufCodec) Name() string {
	return "protobuf"
}

func init() {
	DefaultRegistry.Register(NewProtobufCodec())
}
