//! TUN Device Demo
//!
//! Demonstrates TUN device creation and usage.
//!
//! Note: This example requires root privileges to create TUN devices.

use std::net::Ipv4Addr;

use vpn_software::tun_device::{TunConfig, TunDevice};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    println!("=== TUN Device Demo ===\n");

    // Check if running as root
    if !is_root() {
        println!("Warning: This example requires root privileges to create TUN devices.");
        println!("Run with: sudo cargo run --example tun_demo\n");
    }

    // Create TUN device configuration
    let config = TunConfig {
        name: "tun0".to_string(),
        address: Ipv4Addr::new(10, 0, 0, 1),
        netmask: Ipv4Addr::new(255, 255, 255, 0),
        mtu: 1500,
    };

    println!("TUN Device Configuration:");
    println!("  Name: {}", config.name);
    println!("  Address: {}", config.address);
    println!("  Netmask: {}", config.netmask);
    println!("  MTU: {}", config.mtu);
    println!();

    // Try to create TUN device
    match TunDevice::new(config) {
        Ok(mut tun) => {
            println!("TUN device created successfully!");
            println!("Device name: {}", tun.name());
            println!();

            // Read a packet (this will block until a packet is received)
            println!("Waiting for packets on TUN device...");
            println!("(Press Ctrl+C to exit)\n");

            match tun.read_packet() {
                Ok(packet) => {
                    println!("Received packet: {} bytes", packet.len());
                    println!("First 20 bytes: {:?}", &packet[..20.min(packet.len())]);
                }
                Err(e) => {
                    println!("Error reading packet: {}", e);
                }
            }
        }
        Err(e) => {
            println!("Failed to create TUN device: {}", e);
            println!();
            println!("This is expected if:");
            println!("  1. Not running as root");
            println!("  2. TUN device support not available");
            println!("  3. Device name already in use");
        }
    }

    Ok(())
}

/// Check if running as root
fn is_root() -> bool {
    unsafe { libc::getuid() == 0 }
}

extern "C" {
    fn getuid() -> u32;
}

mod libc {
    extern "C" {
        pub fn getuid() -> u32;
    }
}
