package test

import (
	"bytes"
	"testing"

	"github.com/simple-rpc/internal/codec"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestJSONCodec(t *testing.T) {
	c := codec.NewJSONCodec()

	assert.Equal(t, "json", c.Name())

	// 测试编码
	buf := new(bytes.Buffer)
	data := map[string]interface{}{
		"name": "test",
		"age":  25,
	}

	err := c.Encode(buf, data)
	require.NoError(t, err)

	// 测试解码
	var result map[string]interface{}
	err = c.Decode(buf, &result)
	require.NoError(t, err)

	assert.Equal(t, "test", result["name"])
	assert.Equal(t, float64(25), result["age"]) // JSON 解析为 float64
}

func TestGobCodec(t *testing.T) {
	c := codec.NewGobCodec()

	assert.Equal(t, "gob", c.Name())

	// 测试编码
	buf := new(bytes.Buffer)
	data := map[string]interface{}{
		"name": "test",
		"age":  25,
	}

	err := c.Encode(buf, data)
	require.NoError(t, err)

	// 测试解码
	var result map[string]interface{}
	err = c.Decode(buf, &result)
	require.NoError(t, err)

	assert.Equal(t, "test", result["name"])
	assert.Equal(t, 25, result["age"])
}

func TestCodecRegistry(t *testing.T) {
	reg := codec.NewRegistry()

	// 注册编解码器
	reg.Register(codec.NewJSONCodec())
	reg.Register(codec.NewGobCodec())

	// 获取 JSON 编解码器
	jsonCodec, err := reg.Get("json")
	require.NoError(t, err)
	assert.Equal(t, "json", jsonCodec.Name())

	// 获取 Gob 编解码器
	gobCodec, err := reg.Get("gob")
	require.NoError(t, err)
	assert.Equal(t, "gob", gobCodec.Name())

	// 获取不存在的编解码器
	_, err = reg.Get("protobuf")
	assert.Error(t, err)
}

func TestDefaultRegistry(t *testing.T) {
	// 默认注册表应该有 JSON 和 Gob
	jsonCodec, err := codec.DefaultRegistry.Get("json")
	require.NoError(t, err)
	assert.NotNil(t, jsonCodec)

	gobCodec, err := codec.DefaultRegistry.Get("gob")
	require.NoError(t, err)
	assert.NotNil(t, gobCodec)
}

func TestJSONCodecStruct(t *testing.T) {
	type TestStruct struct {
		Name  string `json:"name"`
		Value int    `json:"value"`
	}

	c := codec.NewJSONCodec()
	buf := new(bytes.Buffer)

	// 编码
	original := TestStruct{Name: "test", Value: 42}
	err := c.Encode(buf, original)
	require.NoError(t, err)

	// 解码
	var decoded TestStruct
	err = c.Decode(buf, &decoded)
	require.NoError(t, err)

	assert.Equal(t, original, decoded)
}

func TestGobCodecStruct(t *testing.T) {
	type TestStruct struct {
		Name  string
		Value int
	}

	c := codec.NewGobCodec()
	buf := new(bytes.Buffer)

	// 编码
	original := TestStruct{Name: "test", Value: 42}
	err := c.Encode(buf, original)
	require.NoError(t, err)

	// 解码
	var decoded TestStruct
	err = c.Decode(buf, &decoded)
	require.NoError(t, err)

	assert.Equal(t, original, decoded)
}

func TestCodecEmptyData(t *testing.T) {
	c := codec.NewJSONCodec()
	buf := new(bytes.Buffer)

	// 编码空对象
	err := c.Encode(buf, map[string]string{})
	require.NoError(t, err)

	// 解码
	var result map[string]string
	err = c.Decode(buf, &result)
	require.NoError(t, err)

	assert.Empty(t, result)
}

func TestCodecNilData(t *testing.T) {
	c := codec.NewJSONCodec()
	buf := new(bytes.Buffer)

	// 编码 nil
	err := c.Encode(buf, nil)
	require.NoError(t, err)

	// 解码
	var result interface{}
	err = c.Decode(buf, &result)
	require.NoError(t, err)

	assert.Nil(t, result)
}
