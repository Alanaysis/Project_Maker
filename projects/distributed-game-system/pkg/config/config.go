package config

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

// ServerConfig 服务器配置
type ServerConfig struct {
	Server ServerSection `yaml:"server"`
	Game   GameSection   `yaml:"game"`
	Network NetworkSection `yaml:"network"`
}

// ServerSection 服务器基本配置
type ServerSection struct {
	ID         string `yaml:"id"`
	Host       string `yaml:"host"`
	UDPPort    int    `yaml:"udp_port"`
	TCPPort    int    `yaml:"tcp_port"`
	MaxPlayers int    `yaml:"max_players"`
}

// GameSection 游戏配置
type GameSection struct {
	TickRate     int     `yaml:"tick_rate"`
	SnapshotRate int     `yaml:"snapshot_rate"`
	WorldWidth   float64 `yaml:"world_width"`
	WorldHeight  float64 `yaml:"world_height"`
}

// NetworkSection 网络配置
type NetworkSection struct {
	HeartbeatInterval int `yaml:"heartbeat_interval"`
	ConnectionTimeout int `yaml:"connection_timeout"`
	MaxPacketSize     int `yaml:"max_packet_size"`
}

// DefaultConfig 返回默认配置
func DefaultConfig() *ServerConfig {
	return &ServerConfig{
		Server: ServerSection{
			ID:         "server-1",
			Host:       "0.0.0.0",
			UDPPort:    8080,
			TCPPort:    8081,
			MaxPlayers: 100,
		},
		Game: GameSection{
			TickRate:     20,
			SnapshotRate: 10,
			WorldWidth:   2000,
			WorldHeight:  2000,
		},
		Network: NetworkSection{
			HeartbeatInterval: 5,
			ConnectionTimeout: 30,
			MaxPacketSize:     1024,
		},
	}
}

// LoadConfig 从文件加载配置
func LoadConfig(path string) (*ServerConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read config file: %w", err)
	}

	config := DefaultConfig()
	if err := yaml.Unmarshal(data, config); err != nil {
		return nil, fmt.Errorf("parse config file: %w", err)
	}

	return config, nil
}

// SaveConfig 保存配置到文件
func SaveConfig(config *ServerConfig, path string) error {
	data, err := yaml.Marshal(config)
	if err != nil {
		return fmt.Errorf("marshal config: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("write config file: %w", err)
	}

	return nil
}

// Validate 验证配置
func (c *ServerConfig) Validate() error {
	if c.Server.UDPPort <= 0 || c.Server.UDPPort > 65535 {
		return fmt.Errorf("invalid UDP port: %d", c.Server.UDPPort)
	}
	if c.Game.TickRate <= 0 || c.Game.TickRate > 120 {
		return fmt.Errorf("invalid tick rate: %d", c.Game.TickRate)
	}
	if c.Game.WorldWidth <= 0 || c.Game.WorldHeight <= 0 {
		return fmt.Errorf("invalid world size")
	}
	return nil
}
