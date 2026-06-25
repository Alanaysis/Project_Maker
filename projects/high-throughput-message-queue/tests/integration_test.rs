use message_queue::Message;

#[test]
fn test_message_create() {
    let msg = Message::new("test", b"hello".to_vec());
    assert_eq!(msg.topic, "test");
    assert_eq!(msg.payload, b"hello");
}

#[test]
fn test_message_serialize_roundtrip() {
    let msg = Message::new("test_topic", b"hello world".to_vec());
    let data = msg.serialize();
    let deserialized = Message::deserialize(&data).unwrap();
    assert_eq!(deserialized.topic, msg.topic);
    assert_eq!(deserialized.payload, msg.payload);
    assert_eq!(deserialized.id, msg.id);
    assert_eq!(deserialized.timestamp, msg.timestamp);
}

#[test]
fn test_message_with_id() {
    let msg = Message::with_id(42, "test", b"data".to_vec(), 12345, 99);
    assert_eq!(msg.id, 42);
    assert_eq!(msg.offset, 99);
    assert_eq!(msg.timestamp, 12345);
}

#[test]
fn test_message_size_calculation() {
    let msg = Message::new("topic", b"1234".to_vec());
    assert!(msg.size() > 0);
}

#[test]
fn test_message_deserialize_invalid() {
    assert!(Message::deserialize(&[]).is_none());
    assert!(Message::deserialize(&[0u8; 3]).is_none());
}

#[test]
fn test_queue_push_pop() {
    let dir = "/tmp/mq_test_push_pop";
    let _ = std::fs::remove_dir_all(dir);
    let mut queue = message_queue::Queue::new("test", dir).unwrap();
    assert_eq!(queue.len(), 0);

    queue.push("events", b"msg1".to_vec()).unwrap();
    queue.push("events", b"msg2".to_vec()).unwrap();
    assert_eq!(queue.len(), 2);

    let msg1 = queue.pop().unwrap();
    assert_eq!(msg1.payload, b"msg1");

    let msg2 = queue.pop().unwrap();
    assert_eq!(msg2.payload, b"msg2");

    assert!(queue.pop().is_none());
    let _ = std::fs::remove_dir_all(dir);
}

#[test]
fn test_queue_recovery() {
    let dir = "/tmp/mq_test_recovery";
    let _ = std::fs::remove_dir_all(dir);

    {
        let mut queue = message_queue::Queue::new("test", dir).unwrap();
        queue.push("t", b"data1".to_vec()).unwrap();
        queue.push("t", b"data2".to_vec()).unwrap();
    }

    {
        let queue = message_queue::Queue::new("test", dir).unwrap();
        assert_eq!(queue.len(), 2);
    }

    let _ = std::fs::remove_dir_all(dir);
}

#[test]
fn test_queue_multi_topic() {
    let dir = "/tmp/mq_test_multi_topic";
    let _ = std::fs::remove_dir_all(dir);
    let mut queue = message_queue::Queue::new("multi", dir).unwrap();

    queue.push("order", b"order1".to_vec()).unwrap();
    queue.push("payment", b"pay1".to_vec()).unwrap();
    queue.push("order", b"order2".to_vec()).unwrap();

    assert_eq!(queue.len(), 3);
    let _ = std::fs::remove_dir_all(dir);
}

#[test]
fn test_consumer_offset() {
    let dir = "/tmp/mq_test_consumer";
    let _ = std::fs::remove_dir_all(dir);
    let mut queue = message_queue::Queue::new("test", dir).unwrap();
    queue.register_consumer("worker1");
    let consumer = queue.get_consumer("worker1").unwrap();
    assert_eq!(consumer.offset(), 0);
    assert_eq!(consumer.name(), "worker1");
    let _ = std::fs::remove_dir_all(dir);
}

#[test]
fn test_storage_append_replay() {
    let dir = "/tmp/mq_test_storage";
    let _ = std::fs::remove_dir_all(dir);
    let mut storage = message_queue::Storage::new(dir).unwrap();

    let msg1 = Message::new("t", b"hello".to_vec());
    let offset = storage.append(&msg1).unwrap();
    assert!(offset == 0 || offset > 0);

    let msgs = storage.replay().unwrap();
    assert!(!msgs.is_empty());
    assert_eq!(msgs[0].payload, b"hello");

    let _ = std::fs::remove_dir_all(dir);
}
