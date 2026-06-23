/// 简单加法示例
///
/// 演示如何使用汇编器构建字节码并执行简单的加法运算。
///
/// 运行方式:
/// ```bash
/// cargo run --example simple_add
/// ```

use smart_contract_vm::{Assembler, ExecutionContext, Vm, VmResult};

fn main() {
    println!("=== 简单加法示例 ===\n");

    // 使用汇编器构建字节码: 10 + 20 = 30
    // 将结果存储到内存并使用 RETURN 返回
    let code = Assembler::new()
        .push1(10)   // 将 10 压入栈
        .push1(20)   // 将 20 压入栈
        .add()       // 弹出两个值，相加后压入结果 (30)
        .push1(0)    // 内存地址
        .mstore()    // 将结果存储到内存[0]
        .push1(32)   // 返回数据大小 (32 字节)
        .push1(0)    // 返回数据起始地址
        .return_op() // 返回内存[0..32]的数据
        .build();

    println!("字节码: {:02x?}", code);
    println!("字节码长度: {} 字节\n", code.len());

    // 创建执行上下文
    let context = ExecutionContext {
        code,
        calldata: Vec::new(),
        caller: 0,
        address: 0,
        value: 0,
    };

    // 创建虚拟机，设置 Gas 限制为 1000
    let mut vm = Vm::new(context, 1000);

    // 执行字节码
    let result = vm.execute();

    // 输出结果
    println!("执行结果:");
    println!("  Gas 消耗: {}", vm.gas_used());
    println!("  Gas 剩余: {}", vm.gas_remaining());
    println!("  栈大小: {}", vm.stack_size());
    println!("  内存大小: {} 字节", vm.memory_size());

    match result {
        VmResult::Success(data) => {
            println!("  状态: 成功");
            println!("  返回数据长度: {} 字节", data.len());
            if data.len() >= 32 {
                // 返回数据是 32 字节的大端序，取最后 8 字节作为 u64
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

    println!("\n=== 示例结束 ===");
}
