use std::collections::{HashMap, VecDeque};

use crate::consumer::Consumer;
use crate::message::Message;
use crate::producer::Producer;
use crate::storage::Storage;

pub struct Queue {
    name: String,
    storage: Storage,
    messages: VecDeque<Message>,
    consumers: HashMap<String, Consumer>,
    next_offset: u64,
}

impl Queue {
    pub fn new(name: &str, data_dir: &str) -> std::io::Result<Self> {
        let storage = Storage::new(data_dir)?;
        let mut queue = Queue {
            name: name.to_string(),
            storage,
            messages: VecDeque::new(),
            consumers: HashMap::new(),
            next_offset: 0,
        };
        let recovered = queue.storage.replay()?;
        for msg in &recovered {
            queue.messages.push_back(msg.clone());
        }
        queue.next_offset = recovered.len() as u64;
        Ok(queue)
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn len(&self) -> usize {
        self.messages.len()
    }

    pub fn push(&mut self, topic: &str, payload: Vec<u8>) -> std::io::Result<u64> {
        let mut msg = Message::new(topic, payload);
        let offset = self.storage.append(&msg)?;
        msg.offset = offset;
        self.messages.push_back(msg);
        self.next_offset += 1;
        Ok(offset)
    }

    pub fn pop(&mut self) -> Option<Message> {
        self.messages.pop_front()
    }

    pub fn peek(&self) -> Option<&Message> {
        self.messages.front()
    }

    pub fn register_consumer(&mut self, name: &str) {
        self.consumers
            .insert(name.to_string(), Consumer::new(name, self.next_offset));
    }

    pub fn get_consumer(&self, name: &str) -> Option<&Consumer> {
        self.consumers.get(name)
    }
}

impl Producer for Queue {
    fn send(&mut self, topic: &str, payload: Vec<u8>) -> std::io::Result<u64> {
        self.push(topic, payload)
    }
}
