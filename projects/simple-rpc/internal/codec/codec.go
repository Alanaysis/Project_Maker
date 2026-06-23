package codec

import (
	"encoding/gob"
	"encoding/json"
	"fmt"
	"io"
)

// Codec 定义编解码接口
type Codec interface {
	// Encode 将数据编码到 writer
	Encode(writer io.Writer, v interface{}) error
	// Decode 从 reader 解码数据
	Decode(reader io.Reader, v interface{}) error
	// Name 返回编解码器名称
	Name() string
}

// JSONCodec JSON 编解码器
type JSONCodec struct{}

// NewJSONCodec 创建 JSON 编解码器
func NewJSONCodec() *JSONCodec {
	return &JSONCodec{}
}

func (c *JSONCodec) Encode(writer io.Writer, v interface{}) error {
	return json.NewEncoder(writer).Encode(v)
}

func (c *JSONCodec) Decode(reader io.Reader, v interface{}) error {
	return json.NewDecoder(reader).Decode(v)
}

func (c *JSONCodec) Name() string {
	return "json"
}

// GobCodec Gob 编解码器
type GobCodec struct{}

// NewGobCodec 创建 Gob 编解码器
func NewGobCodec() *GobCodec {
	return &GobCodec{}
}

func (c *GobCodec) Encode(writer io.Writer, v interface{}) error {
	return gob.NewEncoder(writer).Encode(v)
}

func (c *GobCodec) Decode(reader io.Reader, v interface{}) error {
	return gob.NewDecoder(reader).Decode(v)
}

func (c *GobCodec) Name() string {
	return "gob"
}

// Registry 编解码器注册表
type Registry struct {
	codecs map[string]Codec
}

// NewRegistry 创建编解码器注册表
func NewRegistry() *Registry {
	return &Registry{
		codecs: make(map[string]Codec),
	}
}

// Register 注册编解码器
func (r *Registry) Register(codec Codec) {
	r.codecs[codec.Name()] = codec
}

// Get 获取编解码器
func (r *Registry) Get(name string) (Codec, error) {
	codec, ok := r.codecs[name]
	if !ok {
		return nil, fmt.Errorf("codec not found: %s", name)
	}
	return codec, nil
}

// DefaultRegistry 默认编解码器注册表
var DefaultRegistry = NewRegistry()

func init() {
	DefaultRegistry.Register(NewJSONCodec())
	DefaultRegistry.Register(NewGobCodec())
}
