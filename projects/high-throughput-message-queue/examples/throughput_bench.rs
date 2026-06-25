use std::time::Instant;

use message_queue::Queue;

fn main() -> std::io::Result<()> {
    let mut queue = Queue::new("bench", "/tmp/mq-bench-example")?;
    let payload = vec![0u8; 512];
    let n = 50_000;

    println!("吞吐量测试: {} 条消息, 每条 {} 字节\n", n, payload.len());

    let start = Instant::now();
    for i in 0..n {
        queue.push(&format!("t{}", i % 5), payload.clone())?;
    }
    let write_time = start.elapsed();
    let write_tps = n as f64 / write_time.as_secs_f64();

    let start = Instant::now();
    let mut count = 0;
    while queue.pop().is_some() {
        count += 1;
    }
    let read_time = start.elapsed();
    let read_tps = count as f64 / read_time.as_secs_f64();

    println!("写入: {:?} ({:.0} msg/s)", write_time, write_tps);
    println!("读取: {:?} ({:.0} msg/s)", read_time, read_tps);

    Ok(())
}
