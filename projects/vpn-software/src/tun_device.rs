//! TUN device management for VPN tunnel
//!
//! Handles creation and management of TUN virtual network interfaces.

use std::io::{Read, Write};
use std::net::Ipv4Addr;

use crate::error::{Result, VpnError};

/// Configuration for TUN device
#[derive(Debug, Clone)]
pub struct TunConfig {
    /// Device name (e.g., "tun0")
    pub name: String,
    /// Local IP address
    pub address: Ipv4Addr,
    /// Network mask
    pub netmask: Ipv4Addr,
    /// MTU size
    pub mtu: u32,
}

impl Default for TunConfig {
    fn default() -> Self {
        Self {
            name: "tun0".to_string(),
            address: Ipv4Addr::new(10, 0, 0, 1),
            netmask: Ipv4Addr::new(255, 255, 255, 0),
            mtu: 1500,
        }
    }
}

/// Represents a TUN virtual network interface
pub struct TunDevice {
    /// Underlying TUN device
    device: tun::platform::Device,
    /// Device configuration
    config: TunConfig,
}

impl TunDevice {
    /// Create a new TUN device with the given configuration
    pub fn new(config: TunConfig) -> Result<Self> {
        let mut tun_config = tun::Configuration::default();
        tun_config
            .address(config.address)
            .netmask(config.netmask)
            .mtu(config.mtu as i32)
            .up();

        // Set device name if specified
        if !config.name.is_empty() {
            tun_config.name(&config.name);
        }

        let device = tun::create(&tun_config)
            .map_err(|e| VpnError::TunDeviceError(format!("Failed to create TUN device: {}", e)))?;

        Ok(Self { device, config })
    }

    /// Get the device configuration
    pub fn config(&self) -> &TunConfig {
        &self.config
    }

    /// Get the device name
    pub fn name(&self) -> &str {
        &self.config.name
    }

    /// Read a packet from the TUN device
    pub fn read_packet(&mut self) -> Result<Vec<u8>> {
        let mut buf = vec![0u8; self.config.mtu as usize];
        let n = self.device.read(&mut buf)
            .map_err(|e| VpnError::TunDeviceError(format!("Failed to read from TUN: {}", e)))?;
        buf.truncate(n);
        Ok(buf)
    }

    /// Write a packet to the TUN device
    pub fn write_packet(&mut self, packet: &[u8]) -> Result<()> {
        self.device.write_all(packet)
            .map_err(|e| VpnError::TunDeviceError(format!("Failed to write to TUN: {}", e)))?;
        Ok(())
    }

    /// Set the device IP address
    pub fn set_address(&mut self, address: Ipv4Addr) -> Result<()> {
        // Note: This would require platform-specific implementation
        self.config.address = address;
        Ok(())
    }

    /// Set the device MTU
    pub fn set_mtu(&mut self, mtu: u32) -> Result<()> {
        self.config.mtu = mtu;
        Ok(())
    }
}

/// Route management for VPN
pub struct RouteManager {
    /// VPN subnet
    vpn_subnet: Ipv4Addr,
    /// VPN netmask
    vpn_netmask: Ipv4Addr,
    /// Gateway address
    gateway: Ipv4Addr,
}

impl RouteManager {
    /// Create a new route manager
    pub fn new(vpn_subnet: Ipv4Addr, vpn_netmask: Ipv4Addr, gateway: Ipv4Addr) -> Self {
        Self {
            vpn_subnet,
            vpn_netmask,
            gateway,
        }
    }

    /// Add a route for the VPN subnet
    pub fn add_vpn_route(&self) -> Result<()> {
        // This would use platform-specific commands (ip route, route add, etc.)
        // For now, this is a placeholder
        tracing::info!("Adding route: {} via {}", self.vpn_subnet, self.gateway);
        Ok(())
    }

    /// Remove the VPN route
    pub fn remove_vpn_route(&self) -> Result<()> {
        tracing::info!("Removing route: {} via {}", self.vpn_subnet, self.gateway);
        Ok(())
    }

    /// Add a route for a specific peer
    pub fn add_peer_route(&self, peer_ip: Ipv4Addr) -> Result<()> {
        tracing::info!("Adding route for peer: {} via {}", peer_ip, self.gateway);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tun_config_default() {
        let config = TunConfig::default();
        assert_eq!(config.name, "tun0");
        assert_eq!(config.address, Ipv4Addr::new(10, 0, 0, 1));
        assert_eq!(config.netmask, Ipv4Addr::new(255, 255, 255, 0));
        assert_eq!(config.mtu, 1500);
    }

    #[test]
    fn test_route_manager() {
        let manager = RouteManager::new(
            Ipv4Addr::new(10, 0, 0, 0),
            Ipv4Addr::new(255, 255, 255, 0),
            Ipv4Addr::new(10, 0, 0, 1),
        );

        // These would fail without root privileges, but we can test the creation
        assert_eq!(manager.vpn_subnet, Ipv4Addr::new(10, 0, 0, 0));
        assert_eq!(manager.gateway, Ipv4Addr::new(10, 0, 0, 1));
    }
}
