//! Packet parsing and construction for VPN protocol

use std::net::{Ipv4Addr, Ipv6Addr};

use crate::error::{Result, VpnError};

/// IP protocol numbers
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum IpProtocol {
    ICMP = 1,
    TCP = 6,
    UDP = 17,
    ICMPv6 = 58,
    Other(u8),
}

impl From<u8> for IpProtocol {
    fn from(value: u8) -> Self {
        match value {
            1 => IpProtocol::ICMP,
            6 => IpProtocol::TCP,
            17 => IpProtocol::UDP,
            58 => IpProtocol::ICMPv6,
            _ => IpProtocol::Other(value),
        }
    }
}

/// IPv4 packet header
#[derive(Debug, Clone)]
pub struct Ipv4Header {
    pub version: u8,
    pub ihl: u8,
    pub dscp: u8,
    pub ecn: u8,
    pub total_length: u16,
    pub identification: u16,
    pub flags: u8,
    pub fragment_offset: u16,
    pub ttl: u8,
    pub protocol: IpProtocol,
    pub checksum: u16,
    pub source: Ipv4Addr,
    pub destination: Ipv4Addr,
}

impl Ipv4Header {
    /// Minimum header size (20 bytes)
    pub const MIN_SIZE: usize = 20;

    /// Parse IPv4 header from bytes
    pub fn parse(data: &[u8]) -> Result<Self> {
        if data.len() < Self::MIN_SIZE {
            return Err(VpnError::InvalidPacket("IPv4 header too short".to_string()));
        }

        let version = (data[0] >> 4) & 0x0F;
        if version != 4 {
            return Err(VpnError::InvalidPacket(format!("Not IPv4: version={}", version)));
        }

        let ihl = data[0] & 0x0F;
        let header_len = (ihl as usize) * 4;

        if data.len() < header_len {
            return Err(VpnError::InvalidPacket("IPv4 header length mismatch".to_string()));
        }

        Ok(Self {
            version,
            ihl,
            dscp: (data[1] >> 2) & 0x3F,
            ecn: data[1] & 0x03,
            total_length: u16::from_be_bytes([data[2], data[3]]),
            identification: u16::from_be_bytes([data[4], data[5]]),
            flags: (data[6] >> 5) & 0x07,
            fragment_offset: u16::from_be_bytes([data[6] & 0x1F, data[7]]),
            ttl: data[8],
            protocol: IpProtocol::from(data[9]),
            checksum: u16::from_be_bytes([data[10], data[11]]),
            source: Ipv4Addr::new(data[12], data[13], data[14], data[15]),
            destination: Ipv4Addr::new(data[16], data[17], data[18], data[19]),
        })
    }

    /// Get header length in bytes
    pub fn header_len(&self) -> usize {
        (self.ihl as usize) * 4
    }

    /// Serialize header to bytes
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::MIN_SIZE);

        bytes.push((self.version << 4) | self.ihl);
        bytes.push((self.dscp << 2) | self.ecn);
        bytes.extend_from_slice(&self.total_length.to_be_bytes());
        bytes.extend_from_slice(&self.identification.to_be_bytes());
        bytes.push((self.flags << 5) | ((self.fragment_offset >> 8) as u8 & 0x1F));
        bytes.push((self.fragment_offset & 0xFF) as u8);
        bytes.push(self.ttl);
        bytes.push(self.protocol as u8);
        bytes.extend_from_slice(&self.checksum.to_be_bytes());
        bytes.extend_from_slice(&self.source.octets());
        bytes.extend_from_slice(&self.destination.octets());

        bytes
    }
}

/// VPN packet wrapper
#[derive(Debug, Clone)]
pub enum VpnPacket {
    /// IPv4 packet
    IPv4(Ipv4Packet),
    /// Handshake packet
    Handshake(HandshakePacket),
    /// Data packet (encrypted)
    Data(DataPacket),
}

/// IPv4 packet with payload
#[derive(Debug, Clone)]
pub struct Ipv4Packet {
    pub header: Ipv4Header,
    pub payload: Vec<u8>,
}

impl Ipv4Packet {
    /// Parse an IPv4 packet from raw bytes
    pub fn parse(data: &[u8]) -> Result<Self> {
        let header = Ipv4Header::parse(data)?;
        let header_len = header.header_len();
        let payload = data[header_len..header.total_length as usize].to_vec();

        Ok(Self { header, payload })
    }

    /// Serialize packet to bytes
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = self.header.to_bytes();
        bytes.extend_from_slice(&self.payload);
        bytes
    }
}

/// Handshake packet for key exchange
#[derive(Debug, Clone)]
pub struct HandshakePacket {
    /// Packet type (1 = initiation, 2 = response)
    pub packet_type: u8,
    /// Sender's public key
    pub public_key: [u8; 32],
    /// Encrypted payload
    pub encrypted_payload: Vec<u8>,
}

impl HandshakePacket {
    /// Packet size constant
    pub const INITIATION_SIZE: usize = 148; // type(1) + reserved(3) + key(32) + encrypted(96) + mac(16)

    /// Parse handshake packet
    pub fn parse(data: &[u8]) -> Result<Self> {
        if data.len() < 4 {
            return Err(VpnError::InvalidPacket("Handshake packet too short".to_string()));
        }

        let packet_type = data[0];
        if packet_type != 1 && packet_type != 2 {
            return Err(VpnError::InvalidPacket(format!("Invalid handshake type: {}", packet_type)));
        }

        let mut public_key = [0u8; 32];
        public_key.copy_from_slice(&data[4..36]);

        let encrypted_payload = data[36..].to_vec();

        Ok(Self {
            packet_type,
            public_key,
            encrypted_payload,
        })
    }

    /// Serialize handshake packet
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(4 + 32 + self.encrypted_payload.len());
        bytes.push(self.packet_type);
        bytes.extend_from_slice(&[0, 0, 0]); // reserved
        bytes.extend_from_slice(&self.public_key);
        bytes.extend_from_slice(&self.encrypted_payload);
        bytes
    }
}

/// Data packet (encrypted payload)
#[derive(Debug, Clone)]
pub struct DataPacket {
    /// Receiver index
    pub receiver_index: u32,
    /// Counter for nonce generation
    pub counter: u64,
    /// Encrypted payload
    pub encrypted_payload: Vec<u8>,
}

impl DataPacket {
    /// Parse data packet
    pub fn parse(data: &[u8]) -> Result<Self> {
        if data.len() < 16 {
            return Err(VpnError::InvalidPacket("Data packet too short".to_string()));
        }

        let receiver_index = u32::from_be_bytes([data[0], data[1], data[2], data[3]]);
        let counter = u64::from_be_bytes([
            data[4], data[5], data[6], data[7],
            data[8], data[9], data[10], data[11],
        ]);
        let encrypted_payload = data[12..].to_vec();

        Ok(Self {
            receiver_index,
            counter,
            encrypted_payload,
        })
    }

    /// Serialize data packet
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(12 + self.encrypted_payload.len());
        bytes.extend_from_slice(&self.receiver_index.to_be_bytes());
        bytes.extend_from_slice(&self.counter.to_be_bytes());
        bytes.extend_from_slice(&self.encrypted_payload);
        bytes
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ipv4_header_parse() {
        // Create a minimal IPv4 header
        let data = vec![
            0x45, 0x00, // version=4, IHL=5, DSCP=0, ECN=0
            0x00, 0x1C, // total length = 28
            0x00, 0x01, // identification = 1
            0x40, 0x00, // flags=0x4 (DF), fragment offset=0
            0x40, 0x11, // TTL=64, protocol=UDP (17)
            0x00, 0x00, // checksum = 0 (placeholder)
            0x0A, 0x00, 0x00, 0x01, // source = 10.0.0.1
            0x0A, 0x00, 0x00, 0x02, // destination = 10.0.0.2
        ];

        let header = Ipv4Header::parse(&data).unwrap();
        assert_eq!(header.version, 4);
        assert_eq!(header.ihl, 5);
        assert_eq!(header.total_length, 28);
        assert_eq!(header.protocol, IpProtocol::UDP);
        assert_eq!(header.source, Ipv4Addr::new(10, 0, 0, 1));
        assert_eq!(header.destination, Ipv4Addr::new(10, 0, 0, 2));
    }

    #[test]
    fn test_ipv4_header_serialize() {
        let header = Ipv4Header {
            version: 4,
            ihl: 5,
            dscp: 0,
            ecn: 0,
            total_length: 28,
            identification: 1,
            flags: 0x4,
            fragment_offset: 0,
            ttl: 64,
            protocol: IpProtocol::UDP,
            checksum: 0,
            source: Ipv4Addr::new(10, 0, 0, 1),
            destination: Ipv4Addr::new(10, 0, 0, 2),
        };

        let bytes = header.to_bytes();
        assert_eq!(bytes.len(), 20);

        // Parse it back
        let parsed = Ipv4Header::parse(&bytes).unwrap();
        assert_eq!(parsed.source, header.source);
        assert_eq!(parsed.destination, header.destination);
    }

    #[test]
    fn test_handshake_packet() {
        let packet = HandshakePacket {
            packet_type: 1,
            public_key: [0xAA; 32],
            encrypted_payload: vec![0xBB; 64],
        };

        let bytes = packet.to_bytes();
        let parsed = HandshakePacket::parse(&bytes).unwrap();

        assert_eq!(parsed.packet_type, 1);
        assert_eq!(parsed.public_key, [0xAA; 32]);
        assert_eq!(parsed.encrypted_payload, vec![0xBB; 64]);
    }

    #[test]
    fn test_data_packet() {
        let packet = DataPacket {
            receiver_index: 12345,
            counter: 67890,
            encrypted_payload: vec![0xCC; 100],
        };

        let bytes = packet.to_bytes();
        let parsed = DataPacket::parse(&bytes).unwrap();

        assert_eq!(parsed.receiver_index, 12345);
        assert_eq!(parsed.counter, 67890);
        assert_eq!(parsed.encrypted_payload, vec![0xCC; 100]);
    }
}
