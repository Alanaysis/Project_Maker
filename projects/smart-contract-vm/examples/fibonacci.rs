/// 斐波那契数列示例
///
/// 演示如何使用循环和跳转指令计算斐波那契数列。
/// 计算第 10 个斐波那契数 (0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55)
///
/// 运行方式:
/// ```bash
/// cargo run --example fibonacci
/// ```

use smart_contract_vm::{Assembler, ExecutionContext, Vm, VmResult};

fn main() {
    println!("=== 斐波那契数列示例 ===\n");

    // 计算第 10 个斐波那契数
    let n: u64 = 10;
    println!("计算第 {} 个斐波那契数\n", n);

    // 字节码布局 (栈: [a, b, counter], a 在栈底, counter 在栈顶):
    //   0: PUSH1 0       (a=0)
    //   2: PUSH1 1       (b=1)
    //   4: PUSH1 10      (counter=10)
    //   6: JUMPDEST      (loop_start)
    //   7: DUP1          (dup counter)
    //   8: ISZERO        (counter==0?)
    //   9: PUSH1 27      (jump to loop_end)
    //  11: JUMPI
    //  12: DUP2          (dup b)
    //  13: DUP4          (dup a)
    //  14: ADD           (temp = a+b)
    //  15: SWAP3         [temp, b, counter, a]
    //  16: POP           [temp, b, counter]
    //  17: SWAP1         [temp, counter, b]
    //  18: SWAP2         [b, counter, temp]
    //  19: SWAP1         [b, temp, counter]
    //  20: PUSH1 1
    //  22: SWAP1         [b, temp, 1, counter]
    //  23: SUB           [b, temp, counter-1]
    //  24: PUSH1 6       (loop_start)
    //  26: JUMP
    //  27: JUMPDEST      (loop_end)
    //  28: POP           (remove counter)
    //  29: SWAP1         [b, a]
    //  30: POP           (remove a)
    //  31: PUSH1 0       (memory offset)
    //  33: MSTORE        (store b to memory[0])
    //  34: PUSH1 32      (return size)
    //  36: PUSH1 0       (return offset)
    //  38: RETURN
    let code = Assembler::new()
        // 初始化: [a=0, b=1, counter=n]
        .push1(0)
        .push1(1)
        .push1(n as u8)

        // 循环开始 (位置 6)
        .jumpdest()

        // 检查 counter == 0
        .dup1()
        .iszero()
        .push1(27)
        .jumpi()

        // 计算 temp = a + b
        .dup2()         // dup b (depth 1)
        .dup4()         // dup a (depth 3)
        .add()          // temp = a + b

        // 重排栈: [a, b, counter, temp] -> [b, temp, counter]
        .swap3()        // [temp, b, counter, a]
        .pop()          // [temp, b, counter]
        .swap1()        // [temp, counter, b]
        .swap2()        // [b, counter, temp]
        .swap1()        // [b, temp, counter]

        // counter--
        .push1(1)
        .swap1()        // [b, temp, 1, counter]
        .sub()          // [b, temp, counter-1]

        // 跳转回循环开始
        .push1(6)
        .jump()

        // 结束 (位置 27)
        .jumpdest()

        // 清理栈: [a, b, 0] -> [a] (a = fib(n))
        .pop()          // [a, b]
        .pop()          // [a]

        // 存储结果到内存并返回
        .push1(0)
        .mstore()
        .push1(32)
        .push1(0)
        .return_op()
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

    // 创建虚拟机，设置较高的 Gas 限制
    let mut vm = Vm::new(context, 100000);

    // 执行字节码
    let result = vm.execute();

    // 输出结果
    println!("执行结果:");
    println!("  Gas 消耗: {}", vm.gas_used());

    match result {
        VmResult::Success(data) => {
            println!("  状态: 成功");
            if data.len() >= 32 {
                let value = u64::from_be_bytes([
                    data[24], data[25], data[26], data[27],
                    data[28], data[29], data[30], data[31],
                ]);
                println!("  fib({}) = {}", n, value);
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
    let expected = fibonacci(n);
    println!("\n验证:");
    println!("  Rust 计算结果: fib({}) = {}", n, expected);

    println!("\n=== 示例结束 ===");
}

/// 使用 Rust 计算斐波那契数列（用于验证）
fn fibonacci(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    let mut a: u64 = 0;
    let mut b: u64 = 1;
    for _ in 2..=n {
        let temp = a + b;
        a = b;
        b = temp;
    }
    b
}
