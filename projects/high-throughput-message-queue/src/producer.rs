use std::io;

pub trait Producer {
    fn send(&mut self, topic: &str, payload: Vec<u8>) -> io::Result<u64>;
}
