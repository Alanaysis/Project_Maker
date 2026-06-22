//! VPN protocol implementation
//!
//! Implements the WireGuard-inspired VPN protocol with:
//! - Noise Protocol Framework for key exchange
//! - Cookie-based DoS protection
//! - Underload and flood protection

use crate::error::{Result, VpnError};

/// Protocol version
pub const PROTOCOL_VERSION: u8 = 1;

/// Message types
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MessageType {
    /// Handshake initiation
    HandshakeInitiation = 1,
    /// Handshake response
    HandshakeResponse = 2,
    /// Cookie reply (for DoS protection)
    CookieReply = 3,
    /// Transport data
    TransportData = 4,
}

impl TryFrom<u8> for MessageType {
    type Error = VpnError;

    fn try_from(value: u8) -> Result<Self> {
        match value {
            1 => Ok(MessageType::HandshakeInitiation),
            2 => Ok(MessageType::HandshakeResponse),
            3 => Ok(MessageType::CookieReply),
            4 => Ok(MessageType::TransportData),
            _ => Err(VpnError::ProtocolError(format!("Invalid message type: {}", value))),
        }
    }
}

/// Handshake initiation message
#[derive(Debug, Clone)]
pub struct HandshakeInitiation {
    /// Message type (always 1)
    pub message_type: u8,
    /// Reserved field
    pub reserved: [u8; 3],
    /// Sender index
    pub sender_index: u32,
    /// Encrypted ephemeral key
    pub encrypted_ephemeral: [u8; 32],
    /// Encrypted static key
    pub encrypted_static: [u8; 48],
    /// Encrypted timestamp
    pub encrypted_timestamp: [u8; 28],
    /// MAC1
    pub mac1: [u8; 16],
    /// MAC2
    pub mac2: [u8; 16],
}

impl HandshakeInitiation {
    /// Total size of the message
    pub const SIZE: usize = 148;

    /// Parse from bytes
    pub fn parse(data: &[u8]) -> Result<Self> {
        if data.len() < Self::SIZE {
            return Err(VpnError::ProtocolError("Handshake initiation too short".to_string()));
        }

        let message_type = data[0];
        if message_type != MessageType::HandshakeInitiation as u8 {
            return Err(VpnError::ProtocolError("Invalid message type for initiation".to_string()));
        }

        let mut reserved = [0u8; 3];
        reserved.copy_from_slice(&data[1..4]);

        let sender_index = u32::from_be_bytes([data[4], data[5], data[6], data[7]]);

        let mut encrypted_ephemeral = [0u8; 32];
        encrypted_ephemeral.copy_from_slice(&data[8..40]);

        let mut encrypted_static = [0u8; 48];
        encrypted_static.copy_from_slice(&data[40..88]);

        let mut encrypted_timestamp = [0u8; 28];
        encrypted_timestamp.copy_from_slice(&data[88..116]);

        let mut mac1 = [0u8; 16];
        mac1.copy_from_slice(&data[116..132]);

        let mut mac2 = [0u8; 16];
        mac2.copy_from_slice(&data[132..148]);

        Ok(Self {
            message_type,
            reserved,
            sender_index,
            encrypted_ephemeral,
            encrypted_static,
            encrypted_timestamp,
            mac1,
            mac2,
        })
    }

    /// Serialize to bytes
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::SIZE);
        bytes.push(self.message_type);
        bytes.extend_from_slice(&self.reserved);
        bytes.extend_from_slice(&self.sender_index.to_be_bytes());
        bytes.extend_from_slice(&self.encrypted_ephemeral);
        bytes.extend_from_slice(&self.encrypted_static);
        bytes.extend_from_slice(&self.encrypted_timestamp);
        bytes.extend_from_slice(&self.mac1);
        bytes.extend_from_slice(&self.mac2);
        bytes
    }
}

/// Handshake response message
#[derive(Debug, Clone)]
pub struct HandshakeResponse {
    /// Message type (always 2)
    pub message_type: u8,
    /// Reserved field
    pub reserved: [u8; 3],
    /// Sender index
    pub sender_index: u32,
    /// Receiver index (from initiation)
    pub receiver_index: u32,
    /// Encrypted ephemeral key
    pub encrypted_ephemeral: [u8; 32],
    /// Encrypted nothing (empty)
    pub encrypted_nothing: [u8; 16],
    /// MAC1
    pub mac1: [u8; 16],
    /// MAC2
    pub mac2: [u8; 16],
}

impl HandshakeResponse {
    /// Total size of the message
    pub const SIZE: usize = 92;

    /// Parse from bytes
    pub fn parse(data: &[u8]) -> Result<Self> {
        if data.len() < Self::SIZE {
            return Err(VpnError::ProtocolError("Handshake response too short".to_string()));
        }

        let message_type = data[0];
        if message_type != MessageType::HandshakeResponse as u8 {
            return Err(VpnError::ProtocolError("Invalid message type for response".to_string()));
        }

        let mut reserved = [0u8; 3];
        reserved.copy_from_slice(&data[1..4]);

        let sender_index = u32::from_be_bytes([data[4], data[5], data[6], data[7]]);
        let receiver_index = u32::from_be_bytes([data[8], data[9], data[10], data[11]]);

        let mut encrypted_ephemeral = [0u8; 32];
        encrypted_ephemeral.copy_from_slice(&data[12..44]);

        let mut encrypted_nothing = [0u8; 16];
        encrypted_nothing.copy_from_slice(&data[44..60]);

        let mut mac1 = [0u8; 16];
        mac1.copy_from_slice(&data[60..76]);

        let mut mac2 = [0u8; 16];
        mac2.copy_from_slice(&data[76..92]);

        Ok(Self {
            message_type,
            reserved,
            sender_index,
            receiver_index,
            encrypted_ephemeral,
            encrypted_nothing,
            mac1,
            mac2,
        })
    }

    /// Serialize to bytes
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::SIZE);
        bytes.push(self.message_type);
        bytes.extend_from_slice(&self.reserved);
        bytes.extend_from_slice(&self.sender_index.to_be_bytes());
        bytes.extend_from_slice(&self.receiver_index.to_be_bytes());
        bytes.extend_from_slice(&self.encrypted_ephemeral);
        bytes.extend_from_slice(&self.encrypted_nothing);
        bytes.extend_from_slice(&self.mac1);
        bytes.extend_from_slice(&self.mac2);
        bytes
    }
}

/// Transport data message
#[derive(Debug, Clone)]
pub struct TransportData {
    /// Message type (always 4)
    pub message_type: u8,
    /// Reserved field
    pub reserved: [u8; 3],
    /// Receiver index
    pub receiver_index: u32,
    /// Counter
    pub counter: u64,
    /// Encrypted payload
    pub encrypted_payload: Vec<u8>,
}

impl TransportData {
    /// Header size (without payload)
    pub const HEADER_SIZE: usize = 16;

    /// Parse from bytes
    pub fn parse(data: &[u8]) -> Result<Self> {
        if data.len() < Self::HEADER_SIZE {
            return Err(VpnError::ProtocolError("Transport data too short".to_string()));
        }

        let message_type = data[0];
        if message_type != MessageType::TransportData as u8 {
            return Err(VpnError::ProtocolError("Invalid message type for transport data".to_string()));
        }

        let mut reserved = [0u8; 3];
        reserved.copy_from_slice(&data[1..4]);

        let receiver_index = u32::from_be_bytes([data[4], data[5], data[6], data[7]]);
        let counter = u64::from_be_bytes([
            data[8], data[9], data[10], data[11],
            data[12], data[13], data[14], data[15],
        ]);

        let encrypted_payload = data[16..].to_vec();

        Ok(Self {
            message_type,
            reserved,
            receiver_index,
            counter,
            encrypted_payload,
        })
    }

    /// Serialize to bytes
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::HEADER_SIZE + self.encrypted_payload.len());
        bytes.push(self.message_type);
        bytes.extend_from_slice(&self.reserved);
        bytes.extend_from_slice(&self.receiver_index.to_be_bytes());
        bytes.extend_from_slice(&self.counter.to_be_bytes());
        bytes.extend_from_slice(&self.encrypted_payload);
        bytes
    }
}

/// Cookie reply message (for DoS protection)
#[derive(Debug, Clone)]
pub struct CookieReply {
    /// Message type (always 3)
    pub message_type: u8,
    /// Reserved field
    pub reserved: [u8; 3],
    /// Receiver index
    pub receiver_index: u32,
    /// Encrypted cookie
    pub encrypted_cookie: [u8; 48],
}

impl CookieReply {
    /// Total size of the message
    pub const SIZE: usize = 64;

    /// Parse from bytes
    pub fn parse(data: &[u8]) -> Result<Self> {
        if data.len() < Self::SIZE {
            return Err(VpnError::ProtocolError("Cookie reply too short".to_string()));
        }

        let message_type = data[0];
        if message_type != MessageType::CookieReply as u8 {
            return Err(VpnError::ProtocolError("Invalid message type for cookie reply".to_string()));
        }

        let mut reserved = [0u8; 3];
        reserved.copy_from_slice(&data[1..4]);

        let receiver_index = u32::from_be_bytes([data[4], data[5], data[6], data[7]]);

        let mut encrypted_cookie = [0u8; 48];
        encrypted_cookie.copy_from_slice(&data[8..56]);

        Ok(Self {
            message_type,
            reserved,
            receiver_index,
            encrypted_cookie,
        })
    }

    /// Serialize to bytes
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(Self::SIZE);
        bytes.push(self.message_type);
        bytes.extend_from_slice(&self.reserved);
        bytes.extend_from_slice(&self.receiver_index.to_be_bytes());
        bytes.extend_from_slice(&self.encrypted_cookie);
        bytes
    }
}

/// Parse any protocol message
pub fn parse_message(data: &[u8]) -> Result<MessageType> {
    if data.is_empty() {
        return Err(VpnError::ProtocolError("Empty message".to_string()));
    }

    MessageType::try_from(data[0])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_handshake_initiation_parse_serialize() {
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
    fn test_handshake_response_parse_serialize() {
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
    fn test_transport_data_parse_serialize() {
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
    fn test_cookie_reply_parse_serialize() {
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
    fn test_parse_message_type() {
        assert_eq!(
            parse_message(&[MessageType::HandshakeInitiation as u8]).unwrap(),
            MessageType::HandshakeInitiation
        );
        assert_eq!(
            parse_message(&[MessageType::HandshakeResponse as u8]).unwrap(),
            MessageType::HandshakeResponse
        );
        assert_eq!(
            parse_message(&[MessageType::CookieReply as u8]).unwrap(),
            MessageType::CookieReply
        );
        assert_eq!(
            parse_message(&[MessageType::TransportData as u8]).unwrap(),
            MessageType::TransportData
        );
    }

    #[test]
    fn test_invalid_message_type() {
        assert!(parse_message(&[0xFF]).is_err());
        assert!(parse_message(&[]).is_err());
    }
}
