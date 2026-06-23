/// 条件执行示例
///
/// 演示如何使用 JUMPI 操作码实现条件分支。
/// 模拟 if-else 逻辑：如果 a > b，返回 1，否则返回 0。
///
/// 运行方式:
/// ```bash
/// cargo run --example conditional
/// ```

use smart_contract_vm::{Assembler, ExecutionContext, Vm, VmResult};

fn main() {
    println!("=== 条件执行示例 ===\n");

    // 示例 1: a > b (10 > 5 => 1)
    println!("示例 1: 10 > 5");
    println!("------------------------");
    execute_conditional(10, 5);

    // 示例 2: a > b (3 > 7 => 0)
    println!("\n示例 2: 3 > 7");
    println!("------------------------");
    execute_conditional(3, 7);

    // 示例 3: a > b (5 > 5 => 0)
    println!("\n示例 3: 5 > 5 (相等)");
    println!("------------------------");
    execute_conditional(5, 5);

    // 示例 4: 复杂条件 - 取较大值
    println!("\n示例 4: 取较大值 max(15, 8)");
    println!("------------------------");
    execute_max(15, 8);

    println!("\n示例 5: 取较大值 max(3, 12)");
    println!("------------------------");
    execute_max(3, 12);

    println!("\n=== 示例结束 ===");
}

/// 执行条件比较: 如果 a > b 返回 1，否则返回 0
fn execute_conditional(a: u64, b: u64) {
    println!("  比较: {} > {} = {}", a, b, a > b);

    // 字节码布局:
    //   0-1: PUSH1 a
    //   2-3: PUSH1 b
    //   4: GT
    //   5-6: PUSH1 13 (true branch)
    //   7: JUMPI
    //   8-9: PUSH1 0 (false result)
    //  10-11: PUSH1 16 (end)
    //  12: JUMP
    //  13: JUMPDEST (true branch)
    //  14-15: PUSH1 1 (true result)
    //  16: JUMPDEST (end)
    //  17-18: PUSH1 0 (memory offset)
    //  19: MSTORE
    //  20-21: PUSH1 32 (return size)
    //  22-23: PUSH1 0 (return offset)
    //  24: RETURN
    let code = Assembler::new()
        // 压入操作数 (b 先入栈在底部，a 后入栈在顶部)
        .push1(b as u8)     // b (栈底)
        .push1(a as u8)     // a (栈顶)

        // 比较 a > b
        // GT: 弹出 a (栈顶), 弹出 b, 返回 a > b
        .gt()               // a > b ? 1 : 0

        // 如果结果为 1，跳转到 true 分支
        .push1(13)          // true 分支位置 (JUMPDEST)
        .jumpi()            // 如果 gt 结果为 1，跳转

        // false 分支: 返回 0
        .push1(0)           // 返回 0
        .push1(16)          // 跳转到结束 (JUMPDEST)
        .jump()

        // true 分支 (位置 13)
        .jumpdest()         // JUMPDEST
        .push1(1)           // 返回 1

        // 结束 (位置 16)
        .jumpdest()         // JUMPDEST

        // 存储结果到内存并返回
        .push1(0)           // 内存地址
        .mstore()           // 存储结果到内存[0]
        .push1(32)          // 返回数据大小
        .push1(0)           // 返回数据起始地址
        .return_op()        // 返回结果
        .build();

    execute_and_print(code, 10000);
}

/// 执行取较大值: max(a, b)
fn execute_max(a: u64, b: u64) {
    let expected = if a > b { a } else { b };
    println!("  计算: max({}, {}) = {}", a, b, expected);

    // 字节码布局:
    //   0-1: PUSH1 a
    //   2-3: PUSH1 b
    //   4: DUP2 (copy a)
    //   5: DUP2 (copy b)
    //   6: GT
    //   7-8: PUSH1 15 (true branch)
    //   9: JUMPI
    //  10: SWAP1 (swap a and b)
    //  11: POP (remove a, keep b)
    //  12-13: PUSH1 17 (end)
    //  14: JUMP
    //  15: JUMPDEST (true branch - return a)
    //  16: POP (remove b, keep a)
    //  17: JUMPDEST (end)
    //  18-19: PUSH1 0
    //  20: MSTORE
    //  21-22: PUSH1 32
    //  23-24: PUSH1 0
    //  25: RETURN
    // 栈布局: [b, a] (b 先入栈在底部, a 后入栈在顶部)
    let code = Assembler::new()
        // 压入操作数 (b 先入栈在底部，a 后入栈在顶部)
        .push1(b as u8)     // b (栈底)
        .push1(a as u8)     // a (栈顶)

        // 比较 a > b
        // 需要复制 a 和 b 进行比较，同时保留原始值
        .dup2()             // 复制 b (depth 1)
        .dup2()             // 复制 a (depth 1)
        .gt()               // a > b ? 1 : 0

        // 如果 a > b，跳转到返回 a
        .push1(14)          // 返回 a 的位置 (JUMPDEST)
        .jumpi()            // 如果 gt 结果为 1，跳转

        // 否则返回 b (a <= b)
        // 栈: [b, a], 弹出 a 保留 b
        .pop()              // 弹出 a (栈顶)，保留 b
        .push1(17)          // 跳转到结束 (JUMPDEST)
        .jump()

        // 返回 a (位置 14)
        // 栈: [b, a], 需要交换后弹出 b 保留 a
        .jumpdest()         // JUMPDEST
        .swap1()            // [a, b]
        .pop()              // 弹出 b，保留 a

        // 结束 (位置 17)
        .jumpdest()         // JUMPDEST

        // 存储结果到内存并返回
        .push1(0)           // 内存地址
        .mstore()           // 存储结果到内存[0]
        .push1(32)          // 返回数据大小
        .push1(0)           // 返回数据起始地址
        .return_op()        // 返回结果
        .build();

    execute_and_print(code, 10000);
}

/// 执行字节码并打印结果
fn execute_and_print(code: Vec<u8>, gas_limit: u64) {
    let context = ExecutionContext {
        code,
        calldata: Vec::new(),
        caller: 0,
        address: 0,
        value: 0,
    };

    let mut vm = Vm::new(context, gas_limit);
    let result = vm.execute();

    println!("  Gas 消耗: {}", vm.gas_used());

    match result {
        VmResult::Success(data) => {
            println!("  状态: 成功");
            if data.len() >= 32 {
                let value = u64::from_be_bytes([
                    data[24], data[25], data[26], data[27],
                    data[28], data[29], data[30], data[31],
                ]);
                println!("  返回值: {}", value);
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
}
