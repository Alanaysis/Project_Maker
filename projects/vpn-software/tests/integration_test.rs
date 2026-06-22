//! Integration tests for VPN software

use std::net::Ipv4Addr;

use vpn_software::crypto::CryptoState;
use vpn_software::packet::{DataPacket, HandshakePacket, Ipv4Header, Ipv4Packet, IpProtocol};
use vpn_software::peer::{Peer, PeerManager, PeerState};
use vpn_software::protocol::{
    HandshakeInitiation, HandshakeResponse, MessageType, TransportData, CookieReply,
};
use vpn_software::tun_device::TunConfig;

#[test]
fn test_crypto_key_exchange_and_encryption() {
    // Create two crypto states (simulating two peers)
    let mut alice = CryptoState::new();
    let mut bob = CryptoState::new();

    let alice_pub = *alice.public_key();
    let bob_pub = *bob.public_key();

    // Perform key exchange
    alice.key_exchange(&bob_pub).unwrap();
    bob.key_exchange(&alice_pub).unwrap();

    // Verify keys match by testing encryption/decryption works both ways
    let test_data = b"key-verification-test";

    // Alice encrypts, Bob decrypts
    let ciphertext1 = alice.encrypt(test_data).unwrap();
    let decrypted1 = bob.decrypt(&ciphertext1).unwrap();
    assert_eq!(test_data.as_slice(), decrypted1.as_slice());

    // Bob encrypts, Alice decrypts
    let ciphertext2 = bob.encrypt(test_data).unwrap();
    let decrypted2 = alice.decrypt(&ciphertext2).unwrap();
    assert_eq!(test_data.as_slice(), decrypted2.as_slice());

    // Test encryption/decryption
    let plaintext = b"Hello, VPN Tunnel!";
    let ciphertext = alice.encrypt(plaintext).unwrap();
    let decrypted = bob.decrypt(&ciphertext).unwrap();

    assert_eq!(plaintext.as_slice(), decrypted.as_slice());
}

#[test]
fn test_crypto_large_data_encryption() {
    let mut alice = CryptoState::new();
    let mut bob = CryptoState::new();

    let alice_pub = *alice.public_key();
    let bob_pub = *bob.public_key();

    alice.key_exchange(&bob_pub).unwrap();
    bob.key_exchange(&alice_pub).unwrap();

    // Test with various data sizes
    for size in [64, 256, 1024, 1500, 4096] {
        let plaintext = vec![0xAA; size];
        let ciphertext = alice.encrypt(&plaintext).unwrap();
        let decrypted = bob.decrypt(&ciphertext).unwrap();

        assert_eq!(plaintext, decrypted, "Failed for size {}", size);
    }
}

#[test]
fn test_crypto_tamper_detection() {
    let mut alice = CryptoState::new();
    let mut bob = CryptoState::new();

    let alice_pub = *alice.public_key();
    let bob_pub = *bob.public_key();

    alice.key_exchange(&bob_pub).unwrap();
    bob.key_exchange(&alice_pub).unwrap();

    let plaintext = b"Hello, VPN!";
    let mut ciphertext = alice.encrypt(plaintext).unwrap();

    // Tamper with ciphertext
    if let Some(byte) = ciphertext.last_mut() {
        *byte ^= 0xFF;
    }

    // Decryption should fail
    assert!(bob.decrypt(&ciphertext).is_err());
}

#[test]
fn test_ipv4_packet_parsing() {
    // Create a minimal IPv4 packet
    let mut packet = Vec::new();

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

    // UDP header
    packet.extend_from_slice(&1234u16.to_be_bytes()); // Source port
    packet.extend_from_slice(&5678u16.to_be_bytes()); // Destination port
    packet.extend_from_slice(&8u16.to_be_bytes()); // Length
    packet.extend_from_slice(&0u16.to_be_bytes()); // Checksum

    // Parse the packet
    let ip_packet = Ipv4Packet::parse(&packet).unwrap();

    assert_eq!(ip_packet.header.version, 4);
    assert_eq!(ip_packet.header.ihl, 5);
    assert_eq!(ip_packet.header.total_length, 28);
    assert_eq!(ip_packet.header.protocol, IpProtocol::UDP);
    assert_eq!(ip_packet.header.source, Ipv4Addr::new(10, 0, 0, 1));
    assert_eq!(ip_packet.header.destination, Ipv4Addr::new(10, 0, 0, 2));
    assert_eq!(ip_packet.payload.len(), 8); // UDP header
}

#[test]
fn test_peer_management() {
    let mut manager = PeerManager::new();

    // Create peers
    let peer1 = Peer::new([0xAA; 32], None);
    let peer2 = Peer::new([0xBB; 32], None);

    manager.add_peer(peer1);
    manager.add_peer(peer2);

    assert_eq!(manager.peer_count(), 2);

    // Test IP-based lookup
    let mut peer3 = Peer::new([0xCC; 32], None);
    peer3.add_allowed_ip(Ipv4Addr::new(10, 0, 0, 2));
    manager.add_peer(peer3);

    let found = manager.find_peer_by_ip(&Ipv4Addr::new(10, 0, 0, 2));
    assert!(found.is_some());
    assert_eq!(found.unwrap().public_key(), &[0xCC; 32]);

    // Test peer removal
    let removed = manager.remove_peer(&[0xAA; 32]);
    assert!(removed.is_some());
    assert_eq!(manager.peer_count(), 2);
}

#[test]
fn test_handshake_initiation() {
    let initiation = HandshakeInitiation {
        message_type: MessageType::HandshakeInitiation as u8,
        reserved: [0; 3],
        sender_index: 12345,
        encrypted_ephemeral: [0xAA; 32],
        encrypted_static: [0xBB; 48],
        encrypted_timestamp: [0xCC; 28],
        mac1: [0xDD; 16],
        mac2: [0xEE; 16],
    };

    let bytes = initiation.to_bytes();
    assert_eq!(bytes.len(), HandshakeInitiation::SIZE);

    let parsed = HandshakeInitiation::parse(&bytes).unwrap();
    assert_eq!(parsed.sender_index, 12345);
    assert_eq!(parsed.encrypted_ephemeral, [0xAA; 32]);
}

#[test]
fn test_handshake_response() {
    let response = HandshakeResponse {
        message_type: MessageType::HandshakeResponse as u8,
        reserved: [0; 3],
        sender_index: 54321,
        receiver_index: 12345,
        encrypted_ephemeral: [0xAA; 32],
        encrypted_nothing: [0xBB; 16],
        mac1: [0xCC; 16],
        mac2: [0xDD; 16],
    };

    let bytes = response.to_bytes();
    assert_eq!(bytes.len(), HandshakeResponse::SIZE);

    let parsed = HandshakeResponse::parse(&bytes).unwrap();
    assert_eq!(parsed.sender_index, 54321);
    assert_eq!(parsed.receiver_index, 12345);
}

#[test]
fn test_transport_data() {
    let data = TransportData {
        message_type: MessageType::TransportData as u8,
        reserved: [0; 3],
        receiver_index: 12345,
        counter: 67890,
        encrypted_payload: vec![0xAA; 100],
    };

    let bytes = data.to_bytes();
    let parsed = TransportData::parse(&bytes).unwrap();

    assert_eq!(parsed.receiver_index, 12345);
    assert_eq!(parsed.counter, 67890);
    assert_eq!(parsed.encrypted_payload, vec![0xAA; 100]);
}

#[test]
fn test_cookie_reply() {
    let reply = CookieReply {
        message_type: MessageType::CookieReply as u8,
        reserved: [0; 3],
        receiver_index: 12345,
        encrypted_cookie: [0xAA; 48],
    };

    let bytes = reply.to_bytes();
    assert_eq!(bytes.len(), CookieReply::SIZE);

    let parsed = CookieReply::parse(&bytes).unwrap();
    assert_eq!(parsed.receiver_index, 12345);
    assert_eq!(parsed.encrypted_cookie, [0xAA; 48]);
}

#[test]
fn test_tun_config() {
    let config = TunConfig::default();
    assert_eq!(config.name, "tun0");
    assert_eq!(config.address, Ipv4Addr::new(10, 0, 0, 1));
    assert_eq!(config.netmask, Ipv4Addr::new(255, 255, 255, 0));
    assert_eq!(config.mtu, 1500);
}

#[test]
fn test_peer_state_transitions() {
    let mut peer = Peer::new([0xAA; 32], None);

    assert_eq!(*peer.state(), PeerState::Disconnected);

    peer.set_state(PeerState::Handshaking);
    assert_eq!(*peer.state(), PeerState::Handshaking);

    peer.set_state(PeerState::Connected);
    assert_eq!(*peer.state(), PeerState::Connected);

    peer.set_state(PeerState::TimingOut);
    assert_eq!(*peer.state(), PeerState::TimingOut);
}

#[test]
fn test_peer_statistics() {
    let mut peer = Peer::new([0xAA; 32], None);

    assert_eq!(peer.rx_bytes(), 0);
    assert_eq!(peer.tx_bytes(), 0);

    peer.update_rx_bytes(1024);
    peer.update_tx_bytes(2048);

    assert_eq!(peer.rx_bytes(), 1024);
    assert_eq!(peer.tx_bytes(), 2048);
}

#[test]
fn test_full_packet_flow() {
    // Create crypto states
    let mut sender = CryptoState::new();
    let mut receiver = CryptoState::new();

    let sender_pub = *sender.public_key();
    let receiver_pub = *receiver.public_key();

    sender.key_exchange(&receiver_pub).unwrap();
    receiver.key_exchange(&sender_pub).unwrap();

    // Create a packet
    let mut packet = Vec::new();
    packet.push(0x45); // IPv4
    packet.push(0x00);
    packet.extend_from_slice(&28u16.to_be_bytes());
    packet.extend_from_slice(&1u16.to_be_bytes());
    packet.push(0x40);
    packet.push(0x00);
    packet.push(0x40);
    packet.push(0x11);
    packet.extend_from_slice(&0u16.to_be_bytes());
    packet.extend_from_slice(&[10, 0, 0, 1]);
    packet.extend_from_slice(&[10, 0, 0, 2]);
    packet.extend_from_slice(&1234u16.to_be_bytes());
    packet.extend_from_slice(&5678u16.to_be_bytes());
    packet.extend_from_slice(&8u16.to_be_bytes());
    packet.extend_from_slice(&0u16.to_be_bytes());

    // Encrypt the packet
    let encrypted = sender.encrypt(&packet).unwrap();

    // Create transport data message
    let transport = TransportData {
        message_type: MessageType::TransportData as u8,
        reserved: [0; 3],
        receiver_index: 1,
        counter: 0,
        encrypted_payload: encrypted,
    };

    // Serialize
    let bytes = transport.to_bytes();

    // Parse on receiver side
    let parsed = TransportData::parse(&bytes).unwrap();
    assert_eq!(parsed.receiver_index, 1);

    // Decrypt
    let decrypted = receiver.decrypt(&parsed.encrypted_payload).unwrap();
    assert_eq!(decrypted, packet);
}
