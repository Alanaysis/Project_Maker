use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
pub struct Message {
    pub id: u64,
    pub topic: String,
    pub payload: Vec<u8>,
    pub timestamp: u128,
    pub offset: u64,
}

static mut NEXT_ID: u64 = 0;

impl Message {
    pub fn new(topic: &str, payload: Vec<u8>) -> Self {
        let id = unsafe {
            let id = NEXT_ID;
            NEXT_ID += 1;
            id
        };
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis();
        Message {
            id,
            topic: topic.to_string(),
            payload,
            timestamp,
            offset: 0,
        }
    }

    pub fn with_id(
        id: u64,
        topic: &str,
        payload: Vec<u8>,
        timestamp: u128,
        offset: u64,
    ) -> Self {
        Message {
            id,
            topic: topic.to_string(),
            payload,
            timestamp,
            offset,
        }
    }

    pub fn size(&self) -> usize {
        8 + 4 + self.topic.len() + 8 + self.payload.len() + 16 + 8
    }

    pub fn serialize(&self) -> Vec<u8> {
        let topic_bytes = self.topic.as_bytes();
        let mut buf = Vec::with_capacity(self.size());
        buf.extend_from_slice(&self.id.to_le_bytes());
        buf.extend_from_slice(&(topic_bytes.len() as u32).to_le_bytes());
        buf.extend_from_slice(topic_bytes);
        buf.extend_from_slice(&self.payload.len().to_le_bytes());
        buf.extend_from_slice(&self.payload);
        buf.extend_from_slice(&self.timestamp.to_le_bytes());
        buf.extend_from_slice(&self.offset.to_le_bytes());
        buf
    }

    pub fn deserialize(data: &[u8]) -> Option<Self> {
        if data.len() < 8 {
            return None;
        }
        let mut off = 0;
        let id = u64::from_le_bytes(data[off..off + 8].try_into().ok()?);
        off += 8;

        if off + 4 > data.len() {
            return None;
        }
        let topic_len = u32::from_le_bytes(data[off..off + 4].try_into().ok()?) as usize;
        off += 4;

        if off + topic_len > data.len() {
            return None;
        }
        let topic =
            String::from_utf8(data[off..off + topic_len].to_vec()).ok()?;
        off += topic_len;

        if off + 8 > data.len() {
            return None;
        }
        let payload_len = usize::from_le_bytes(data[off..off + 8].try_into().ok()?);
        off += 8;

        if off + payload_len > data.len() {
            return None;
        }
        let payload = data[off..off + payload_len].to_vec();
        off += payload_len;

        if off + 16 > data.len() {
            return None;
        }
        let timestamp = u128::from_le_bytes(data[off..off + 16].try_into().ok()?);
        off += 16;

        if off + 8 > data.len() {
            return None;
        }
        let offset = u64::from_le_bytes(data[off..off + 8].try_into().ok()?);

        Some(Message {
            id,
            topic,
            payload,
            timestamp,
            offset,
        })
    }
}
