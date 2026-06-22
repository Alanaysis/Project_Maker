//! Configuration management for VPN software

use std::net::Ipv4Addr;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::{Result, VpnError};

/// Main VPN configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VpnConfig {
    /// Server configuration
    pub server: ServerConfig,
    /// Client configuration
    pub client: ClientConfig,
    /// TUN device configuration
    pub tun: TunConfig,
    /// Security configuration
    pub security: SecurityConfig,
    /// Logging configuration
    pub logging: LoggingConfig,
}

/// Server-specific configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    /// Listening port
    pub port: u16,
    /// Maximum number of clients
    pub max_clients: usize,
    /// Keepalive interval in seconds
    pub keepalive_interval: u64,
}

/// Client-specific configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientConfig {
    /// Server address
    pub server: String,
    /// Server port
    pub port: u16,
    /// Connection timeout in seconds
    pub connection_timeout: u64,
}

/// TUN device configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TunConfig {
    /// Device name
    pub name: String,
    /// IP address
    pub address: Ipv4Addr,
    /// Netmask
    pub netmask: Ipv4Addr,
    /// MTU
    pub mtu: u32,
}

/// Security configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityConfig {
    /// Encryption algorithm
    pub encryption: String,
    /// Key exchange algorithm
    pub key_exchange: String,
    /// Handshake timeout in seconds
    pub handshake_timeout: u64,
}

/// Logging configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingConfig {
    /// Log level
    pub level: String,
    /// Log file path
    pub file: Option<String>,
}

impl Default for VpnConfig {
    fn default() -> Self {
        Self {
            server: ServerConfig {
                port: 51820,
                max_clients: 100,
                keepalive_interval: 25,
            },
            client: ClientConfig {
                server: "0.0.0.0".to_string(),
                port: 51820,
                connection_timeout: 30,
            },
            tun: TunConfig {
                name: "tun0".to_string(),
                address: Ipv4Addr::new(10, 0, 0, 1),
                netmask: Ipv4Addr::new(255, 255, 255, 0),
                mtu: 1500,
            },
            security: SecurityConfig {
                encryption: "chacha20poly1305".to_string(),
                key_exchange: "x25519".to_string(),
                handshake_timeout: 10,
            },
            logging: LoggingConfig {
                level: "info".to_string(),
                file: None,
            },
        }
    }
}

impl VpnConfig {
    /// Load configuration from a TOML file
    pub fn load_from_file(path: &Path) -> Result<Self> {
        let content = std::fs::read_to_string(path)
            .map_err(|e| VpnError::ConfigError(format!("Failed to read config file: {}", e)))?;

        Self::from_toml(&content)
    }

    /// Parse configuration from TOML string
    pub fn from_toml(content: &str) -> Result<Self> {
        toml::from_str(content)
            .map_err(|e| VpnError::ConfigError(format!("Failed to parse config: {}", e)))
    }

    /// Save configuration to a TOML file
    pub fn save_to_file(&self, path: &Path) -> Result<()> {
        let content = self.to_toml()?;
        std::fs::write(path, content)
            .map_err(|e| VpnError::ConfigError(format!("Failed to write config file: {}", e)))?;
        Ok(())
    }

    /// Serialize configuration to TOML string
    pub fn to_toml(&self) -> Result<String> {
        toml::to_string_pretty(self)
            .map_err(|e| VpnError::ConfigError(format!("Failed to serialize config: {}", e)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = VpnConfig::default();
        assert_eq!(config.server.port, 51820);
        assert_eq!(config.tun.name, "tun0");
        assert_eq!(config.tun.address, Ipv4Addr::new(10, 0, 0, 1));
    }

    #[test]
    fn test_config_serialization() {
        let config = VpnConfig::default();
        let toml_str = config.to_toml().unwrap();

        assert!(toml_str.contains("[server]"));
        assert!(toml_str.contains("[tun]"));
        assert!(toml_str.contains("[security]"));
    }

    #[test]
    fn test_config_deserialization() {
        let toml_str = r#"
[server]
port = 51820
max_clients = 100
keepalive_interval = 25

[client]
server = "0.0.0.0"
port = 51820
connection_timeout = 30

[tun]
name = "tun0"
address = "10.0.0.1"
netmask = "255.255.255.0"
mtu = 1500

[security]
encryption = "chacha20poly1305"
key_exchange = "x25519"
handshake_timeout = 10

[logging]
level = "info"
"#;

        let config = VpnConfig::from_toml(toml_str).unwrap();
        assert_eq!(config.server.port, 51820);
        assert_eq!(config.tun.address, Ipv4Addr::new(10, 0, 0, 1));
    }
}
