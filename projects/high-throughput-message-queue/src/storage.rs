use std::fs::{self, File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::PathBuf;

use crate::message::Message;

const SEGMENT_SIZE: u64 = 64 * 1024 * 1024;

pub struct Storage {
    base_dir: PathBuf,
    segments: Vec<Segment>,
    active_segment: Segment,
    active_writer: File,
    active_size: u64,
}

#[derive(Clone)]
struct Segment {
    path: PathBuf,
    start_offset: u64,
    end_offset: u64,
}

impl Storage {
    pub fn new(base_dir: &str) -> std::io::Result<Self> {
        let dir = PathBuf::from(base_dir);
        fs::create_dir_all(&dir)?;
        let active_path = dir.join("segment_00000.log");
        let active_writer = OpenOptions::new()
            .create(true)
            .append(true)
            .read(true)
            .open(&active_path)?;
        let active_size = active_writer.metadata()?.len();
        let active_segment = Segment {
            path: active_path.clone(),
            start_offset: 0,
            end_offset: active_size,
        };
        Ok(Storage {
            base_dir: dir,
            segments: Vec::new(),
            active_segment,
            active_writer,
            active_size,
        })
    }

    pub fn append(&mut self, msg: &Message) -> std::io::Result<u64> {
        let data = msg.serialize();
        let len = data.len() as u64;
        self.active_writer.write_all(&len.to_le_bytes())?;
        self.active_writer.write_all(&data)?;
        self.active_writer.flush()?;
        let offset = self.active_size;
        self.active_size += 8 + len;
        self.active_segment.end_offset = self.active_size;
        if self.active_size >= SEGMENT_SIZE {
            self.rotate()?;
        }
        Ok(offset)
    }

    fn rotate(&mut self) -> std::io::Result<()> {
        let old_path = self.active_segment.path.clone();
        let end_offset = self.active_segment.end_offset;
        let old_segment = Segment {
            path: old_path,
            start_offset: self.active_segment.start_offset,
            end_offset,
        };
        self.segments.push(old_segment);
        let seg_idx = self.segments.len();
        let new_path = self
            .base_dir
            .join(format!("segment_{:05}.log", seg_idx));
        let writer = OpenOptions::new()
            .create(true)
            .append(true)
            .read(true)
            .open(&new_path)?;
        self.active_writer = writer;
        self.active_size = 0;
        self.active_segment = Segment {
            path: new_path,
            start_offset: end_offset,
            end_offset,
        };
        Ok(())
    }

    pub fn read_at(&self, offset: u64) -> std::io::Result<Option<Message>> {
        let mut file = OpenOptions::new().read(true).open(&self.active_segment.path)?;
        file.seek(SeekFrom::Start(offset))?;
        let mut len_buf = [0u8; 8];
        if file.read_exact(&mut len_buf).is_err() {
            return Ok(None);
        }
        let len = u64::from_le_bytes(len_buf);
        let mut data = vec![0u8; len as usize];
        if file.read_exact(&mut data).is_err() {
            return Ok(None);
        }
        Ok(Message::deserialize(&data))
    }

    pub fn replay(&self) -> std::io::Result<Vec<Message>> {
        let mut messages = Vec::new();
        let mut file = OpenOptions::new().read(true).open(&self.active_segment.path)?;
        loop {
            let mut len_buf = [0u8; 8];
            match file.read_exact(&mut len_buf) {
                Ok(_) => {}
                Err(_) => break,
            }
            let len = u64::from_le_bytes(len_buf);
            let mut data = vec![0u8; len as usize];
            if file.read_exact(&mut data).is_err() {
                break;
            }
            if let Some(msg) = Message::deserialize(&data) {
                messages.push(msg);
            }
        }
        Ok(messages)
    }
}
