use message_queue::Queue;

fn main() -> std::io::Result<()> {
    let mut queue = Queue::new("group-demo", "/tmp/mq-group-demo")?;

    queue.register_consumer("worker-1");
    queue.register_consumer("worker-2");
    queue.register_consumer("worker-3");

    for i in 0..10 {
        queue.push("tasks", format!("task_{}", i).into_bytes())?;
    }

    println!("队列长度: {}", queue.len());
    println!("消费者数: 3");

    while let Some(msg) = queue.pop() {
        let task = String::from_utf8_lossy(&msg.payload);
        println!("处理: {}", task);
    }

    for name in &["worker-1", "worker-2", "worker-3"] {
        if let Some(c) = queue.get_consumer(name) {
            println!("消费者 {} 已处理到 offset {}", c.name(), c.offset());
        }
    }

    Ok(())
}
