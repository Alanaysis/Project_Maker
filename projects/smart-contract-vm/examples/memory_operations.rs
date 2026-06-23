/// 内存操作示例
///
/// 演示如何使用 MSTORE 和 MLOAD 操作码进行内存读写。
/// 展示内存的线性寻址和数据存储。
///
/// 运行方式:
/// ```bash
/// cargo run --example memory_operations
/// ```

use smart_contract_vm::{Assembler, ExecutionContext, Vm, VmResult};

fn main() {
    println!("=== 内存操作示例 ===\n");

    // 示例 1: 基本内存读写
    println!("示例 1: 基本内存读写");
    println!("------------------------");

    let code = Assembler::new()
        // 将值 42 存储到内存地址 0
        .push1(42)      // 要存储的值
        .push1(0)       // 内存地址
        .mstore()       // 内存[0] = 42

        // 从内存地址 0 读取值
        .push1(0)       // 内存地址
        .mload()        // 读取内存[0]

        // 存储结果到内存并返回
        .push1(32)      // 新的内存地址
        .mstore()       // 存储结果到内存[32]
        .push1(32)      // 返回数据大小
        .push1(32)      // 返回数据起始地址
        .return_op()    // 返回结果
        .build();

    execute_and_print(code, 10000);

    // 示例 2: 多个内存地址
    println!("\n示例 2: 多个内存地址");
    println!("------------------------");

    let code = Assembler::new()
        // 存储值到不同地址
        .push1(100)
        .push1(0)       // 地址 0
        .mstore()

        .push1(200)
        .push1(32)      // 地址 32 (每个值占 32 字节)
        .mstore()

        .push2(300)
        .push1(64)      // 地址 64
        .mstore()

        // 读取地址 32 的值
        .push1(32)
        .mload()

        // 存储结果到内存并返回
        .push1(96)      // 新的内存地址
        .mstore()       // 存储结果到内存[96]
        .push1(32)      // 返回数据大小
        .push1(96)      // 返回数据起始地址
        .return_op()    // 返回结果
        .build();

    execute_and_print(code, 50000);

    // 示例 3: 内存中的算术运算
    println!("\n示例 3: 内存中的算术运算");
    println!("------------------------");
    println!("  计算: (10 + 20) * 3 = 90");

    let code = Assembler::new()
        // 存储 10 到地址 0
        .push1(10)
        .push1(0)
        .mstore()

        // 存储 20 到地址 32
        .push1(20)
        .push1(32)
        .mstore()

        // 读取并相加
        .push1(0)
        .mload()        // 读取 10
        .push1(32)
        .mload()        // 读取 20
        .add()          // 10 + 20 = 30

        // 存储结果到地址 64
        .push1(64)
        .mstore()

        // 乘以 3
        .push1(64)
        .mload()        // 读取 30
        .push1(3)
        .mul()          // 30 * 3 = 90

        // 存储最终结果到地址 96
        .push1(96)
        .mstore()

        // 读取最终结果
        .push1(96)
        .mload()

        // 存储结果到内存并返回
        .push1(128)     // 新的内存地址
        .mstore()       // 存储结果到内存[128]
        .push1(32)      // 返回数据大小
        .push1(128)     // 返回数据起始地址
        .return_op()    // 返回结果
        .build();

    execute_and_print(code, 50000);

    // 示例 4: 交换内存中的值
    println!("\n示例 4: 交换内存中的值");
    println!("------------------------");

    let code = Assembler::new()
        // 初始化: 内存[0] = 111, 内存[32] = 222
        .push1(111)
        .push1(0)
        .mstore()

        .push1(222)
        .push1(32)
        .mstore()

        // 交换: temp = 内存[0]; 内存[0] = 内存[32]; 内存[32] = temp
        .push1(0)
        .mload()        // 读取 111 到栈

        .push1(32)
        .mload()        // 读取 222 到栈

        // 现在栈: [111, 222]
        .push1(0)
        .mstore()       // 内存[0] = 222

        .push1(32)
        .mstore()       // 内存[32] = 111

        // 读取交换后的值
        .push1(0)
        .mload()        // 应该是 222

        // 存储结果到内存并返回
        .push1(64)      // 新的内存地址
        .mstore()       // 存储结果到内存[64]
        .push1(32)      // 返回数据大小
        .push1(64)      // 返回数据起始地址
        .return_op()    // 返回结果
        .build();

    execute_and_print(code, 50000);

    println!("\n=== 示例结束 ===");
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
    println!("  内存大小: {} 字节", vm.memory_size());

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
