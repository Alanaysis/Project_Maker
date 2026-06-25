use message_queue::Queue;

fn main() -> std::io::Result<()> {
    let mut queue = Queue::new("demo", "/tmp/mq-demo")?;

    println!("=== 消息队列基础示例 ===");

    queue.push("orders", b"order_12345".to_vec())?;
    queue.push("orders", b"order_12346".to_vec())?;
    queue.push("payments", b"payment_98765".to_vec())?;
    println!("已发送 3 条消息, 当前队列长度: {}", queue.len());

    while let Some(msg) = queue.pop() {
        let payload = String::from_utf8_lossy(&msg.payload);
        println!(
            "消费: [{}] id={} topic={} payload={}",
            msg.timestamp, msg.id, msg.topic, payload
        );
    }
    println!("队列已清空");

    Ok(())
}
