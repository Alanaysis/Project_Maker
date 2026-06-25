use std::time::Instant;

use message_queue::Queue;

fn main() -> std::io::Result<()> {
    println!("=== 高吞吐消息队列基准测试 ===\n");

    let mut queue = Queue::new("bench", "/tmp/mq-bench")?;

    let n = 100_000;
    let payload = vec![0u8; 256];

    let start = Instant::now();
    for i in 0..n {
        let topic = format!("topic_{}", i % 10);
        queue.push(&topic, payload.clone())?;
    }
    let elapsed = start.elapsed();
    let throughput = n as f64 / elapsed.as_secs_f64();

    println!("写入 {} 条消息, 每条 {} 字节", n, payload.len());
    println!("耗时: {:?}", elapsed);
    println!("吞吐: {:.0} msg/s", throughput);

    let start = Instant::now();
    let mut count = 0;
    while queue.pop().is_some() {
        count += 1;
    }
    let elapsed = start.elapsed();
    let throughput = count as f64 / elapsed.as_secs_f64();

    println!("\n读取 {} 条消息", count);
    println!("耗时: {:?}", elapsed);
    println!("吞吐: {:.0} msg/s", throughput);

    Ok(())
}
