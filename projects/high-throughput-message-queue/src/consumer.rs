#[derive(Debug, Clone)]
pub struct Consumer {
    name: String,
    offset: u64,
}

impl Consumer {
    pub fn new(name: &str, start_offset: u64) -> Self {
        Consumer {
            name: name.to_string(),
            offset: start_offset,
        }
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn offset(&self) -> u64 {
        self.offset
    }

    pub fn commit(&mut self, offset: u64) {
        self.offset = offset;
    }
}
