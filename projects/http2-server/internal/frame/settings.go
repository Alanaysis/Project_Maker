package frame

import (
	"encoding/binary"
	"fmt"
)

// Settings identifiers as defined in RFC 7540
const (
	SettingsHeaderTableSize      uint16 = 0x1
	SettingsEnablePush           uint16 = 0x2
	SettingsMaxConcurrentStreams uint16 = 0x3
	SettingsInitialWindowSize    uint16 = 0x4
	SettingsMaxFrameSize         uint16 = 0x5
	SettingsMaxHeaderListSize    uint16 = 0x6
)

// Settings represents HTTP/2 settings
type Settings struct {
	HeaderTableSize      uint32
	EnablePush           uint32
	MaxConcurrentStreams uint32
	InitialWindowSize    uint32
	MaxFrameSize         uint32
	MaxHeaderListSize    uint32
}

// DefaultSettings returns the default HTTP/2 settings
func DefaultSettings() *Settings {
	return &Settings{
		HeaderTableSize:      4096,
		EnablePush:           1,
		MaxConcurrentStreams:  100,
		InitialWindowSize:    65535,
		MaxFrameSize:         16384,
		MaxHeaderListSize:    0, // No limit
	}
}

// ParseSettingsFrame parses a SETTINGS frame payload
func ParseSettingsFrame(payload []byte) (*Settings, error) {
	if len(payload)%6 != 0 {
		return nil, fmt.Errorf("invalid settings frame length: %d", len(payload))
	}

	settings := DefaultSettings()

	for i := 0; i < len(payload); i += 6 {
		id := binary.BigEndian.Uint16(payload[i : i+2])
		value := binary.BigEndian.Uint32(payload[i+2 : i+6])

		switch id {
		case SettingsHeaderTableSize:
			settings.HeaderTableSize = value
		case SettingsEnablePush:
			if value > 1 {
				return nil, fmt.Errorf("invalid ENABLE_PUSH value: %d", value)
			}
			settings.EnablePush = value
		case SettingsMaxConcurrentStreams:
			settings.MaxConcurrentStreams = value
		case SettingsInitialWindowSize:
			if value > 2147483647 { // 2^31 - 1
				return nil, fmt.Errorf("invalid INITIAL_WINDOW_SIZE value: %d", value)
			}
			settings.InitialWindowSize = value
		case SettingsMaxFrameSize:
			if value < 16384 || value > 16777215 {
				return nil, fmt.Errorf("invalid MAX_FRAME_SIZE value: %d", value)
			}
			settings.MaxFrameSize = value
		case SettingsMaxHeaderListSize:
			settings.MaxHeaderListSize = value
		}
	}

	return settings, nil
}

// EncodeSettings encodes settings into a SETTINGS frame payload
func EncodeSettings(s *Settings) []byte {
	payload := make([]byte, 0, 36) // Max 6 settings * 6 bytes each

	// Only include non-default values
	if s.HeaderTableSize != 4096 {
		payload = appendSetting(payload, SettingsHeaderTableSize, s.HeaderTableSize)
	}
	if s.EnablePush != 1 {
		payload = appendSetting(payload, SettingsEnablePush, s.EnablePush)
	}
	if s.MaxConcurrentStreams != 100 {
		payload = appendSetting(payload, SettingsMaxConcurrentStreams, s.MaxConcurrentStreams)
	}
	if s.InitialWindowSize != 65535 {
		payload = appendSetting(payload, SettingsInitialWindowSize, s.InitialWindowSize)
	}
	if s.MaxFrameSize != 16384 {
		payload = appendSetting(payload, SettingsMaxFrameSize, s.MaxFrameSize)
	}
	if s.MaxHeaderListSize != 0 {
		payload = appendSetting(payload, SettingsMaxHeaderListSize, s.MaxHeaderListSize)
	}

	return payload
}

func appendSetting(payload []byte, id uint16, value uint32) []byte {
	var buf [6]byte
	binary.BigEndian.PutUint16(buf[0:2], id)
	binary.BigEndian.PutUint32(buf[2:6], value)
	return append(payload, buf[:]...)
}

// CreateSettingsFrame creates a SETTINGS frame
func CreateSettingsFrame(s *Settings, flags uint8) *Frame {
	payload := EncodeSettings(s)
	return NewFrame(FrameSettings, flags, 0, payload)
}

// CreateSettingsAckFrame creates a SETTINGS ACK frame
func CreateSettingsAckFrame() *Frame {
	return NewFrame(FrameSettings, FlagAck, 0, nil)
}
