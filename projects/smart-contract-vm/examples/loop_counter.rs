/// 循环计数器示例
///
/// 演示如何使用循环计算 1+2+...+10 的累加和。
/// 展示 JUMP、JUMPI 和 JUMPDEST 操作码的使用。
///
/// 运行方式:
/// ```bash
/// cargo run --example loop_counter
/// ```

use smart_contract_vm::{Assembler, ExecutionContext, Vm, VmResult};

fn main() {
    println!("=== 循环计数器示例 ===\n");

    // 计算 1+2+...+10 = 55
    let n: u64 = 10;
    println!("计算 1+2+...+{} = {}\n", n, n * (n + 1) / 2);

    // 使用汇编器构建字节码
    // 算法: sum = 0; counter = n; while counter > 0 { sum += counter; counter--; }
    let code = Assembler::new()
        // 初始化
        .push1(0)       // sum = 0
        .push1(n as u8) // counter = n

        // 循环开始 (位置 4)
        .jumpdest()     // 位置 4: 循环起点

        // 检查 counter == 0
        .dup1()         // 复制 counter
        .iszero()       // 检查是否为 0
        .push1(22)      // 跳转目标 (结束位置)
        .jumpi()        // 如果 counter == 0，跳转到结束

        // sum += counter
        .dup2()         // 复制 sum
        .dup2()         // 复制 counter
        .add()          // sum + counter
        .swap2()        // 将新 sum 移到正确位置
        .pop()          // 弹出旧 sum

        // counter--
        .push1(1)       // 压入 1
        .swap1()        // 交换 counter 和 1
        .sub()          // counter - 1

        // 跳转回循环开始
        .push1(4)       // 循环开始位置
        .jump()         // 无条件跳转

        // 结束 (位置 22)
        .jumpdest()     // 位置 22: 结束点

        // 清理栈: [sum, 0] -> [sum]
        .pop()          // 弹出 counter (0)，保留 sum

        // 存储结果到内存并返回
        .push1(0)       // 内存地址
        .mstore()       // 存储结果到内存[0]
        .push1(32)      // 返回数据大小
        .push1(0)       // 返回数据起始地址
        .return_op()    // 返回结果
        .build();

    println!("字节码长度: {} 字节\n", code.len());

    // 创建执行上下文
    let context = ExecutionContext {
        code,
        calldata: Vec::new(),
        caller: 0,
        address: 0,
        value: 0,
    };

    // 创建虚拟机
    let mut vm = Vm::new(context, 100000);

    // 执行字节码
    let result = vm.execute();

    // 输出结果
    println!("执行结果:");
    println!("  Gas 消耗: {}", vm.gas_used());
    println!("  栈大小: {}", vm.stack_size());

    match result {
        VmResult::Success(data) => {
            println!("  状态: 成功");
            if data.len() >= 32 {
                let value = u64::from_be_bytes([
                    data[24], data[25], data[26], data[27],
                    data[28], data[29], data[30], data[31],
                ]);
                println!("  1+2+...+{} = {}", n, value);
            }
        }
        VmResult::Revert(data) => {
            println!("  状态: 回滚");
            println!("  返回数据: {:02x?}", data);
        }
        VmResult::Error(err) => {
            println!("  状态: 错误");
            println!("  错误: {}", err);
        }
    }

    // 验证结果
    let expected: u64 = (1..=n).sum();
    println!("\n验证:");
    println!("  Rust 计算结果: 1+2+...+{} = {}", n, expected);

    println!("\n=== 示例结束 ===");
}
