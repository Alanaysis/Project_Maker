//! Simple VPN Example
//!
//! Demonstrates basic VPN tunnel setup and usage.

use std::net::Ipv4Addr;

use vpn_software::crypto::CryptoState;
use vpn_software::tun_device::TunConfig;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    println!("=== Simple VPN Example ===\n");

    // 1. Demonstrate key exchange
    println!("1. Key Exchange");
    let mut alice = CryptoState::new();
    let mut bob = CryptoState::new();

    let alice_pub = *alice.public_key();
    let bob_pub = *bob.public_key();

    println!("   Alice public key: {:?}", alice_pub.as_bytes());
    println!("   Bob public key: {:?}", bob_pub.as_bytes());

    // Perform key exchange
    alice.key_exchange(&bob_pub)?;
    bob.key_exchange(&alice_pub)?;

    println!("   Key exchange completed successfully!\n");

    // 2. Demonstrate encryption/decryption
    println!("2. Encryption/Decryption");
    let message = b"Hello, VPN Tunnel!";
    println!("   Original message: {:?}", String::from_utf8_lossy(message));

    let encrypted = alice.encrypt(message)?;
    println!("   Encrypted ({} bytes): {:?}...", encrypted.len(), &encrypted[..20]);

    let decrypted = bob.decrypt(&encrypted)?;
    println!("   Decrypted: {:?}", String::from_utf8_lossy(&decrypted));

    assert_eq!(message.as_slice(), decrypted.as_slice());
    println!("   Message integrity verified!\n");

    // 3. Demonstrate TUN device configuration
    println!("3. TUN Device Configuration");
    let tun_config = TunConfig {
        name: "tun0".to_string(),
        address: Ipv4Addr::new(10, 0, 0, 1),
        netmask: Ipv4Addr::new(255, 255, 255, 0),
        mtu: 1500,
    };
    println!("   Device name: {}", tun_config.name);
    println!("   Address: {}", tun_config.address);
    println!("   Netmask: {}", tun_config.netmask);
    println!("   MTU: {}\n", tun_config.mtu);

    // 4. Demonstrate packet processing
    println!("4. Packet Processing");
    let sample_packet = create_sample_packet();
    println!("   Sample packet: {} bytes", sample_packet.len());
    println!("   First 20 bytes: {:?}\n", &sample_packet[..20]);

    println!("=== Example completed successfully ===");

    Ok(())
}

/// Create a sample IP packet for demonstration
fn create_sample_packet() -> Vec<u8> {
    let mut packet = Vec::with_capacity(28);

    // IPv4 header
    packet.push(0x45); // Version=4, IHL=5
    packet.push(0x00); // DSCP=0, ECN=0
    packet.extend_from_slice(&28u16.to_be_bytes()); // Total length
    packet.extend_from_slice(&1u16.to_be_bytes()); // Identification
    packet.push(0x40); // Flags=DF
    packet.push(0x00); // Fragment offset
    packet.push(0x40); // TTL=64
    packet.push(0x11); // Protocol=UDP
    packet.extend_from_slice(&0u16.to_be_bytes()); // Checksum
    packet.extend_from_slice(&[10, 0, 0, 1]); // Source IP
    packet.extend_from_slice(&[10, 0, 0, 2]); // Destination IP

    // UDP header (simplified)
    packet.extend_from_slice(&1234u16.to_be_bytes()); // Source port
    packet.extend_from_slice(&5678u16.to_be_bytes()); // Destination port
    packet.extend_from_slice(&8u16.to_be_bytes()); // Length
    packet.extend_from_slice(&0u16.to_be_bytes()); // Checksum

    packet
}
