/// 存储合约示例
///
/// 演示如何使用 SSTORE 和 SLOAD 操作码进行持久化存储。
/// 模拟一个简单的存储合约：存储和读取值。
///
/// 运行方式:
/// ```bash
/// cargo run --example storage_contract
/// ```

use smart_contract_vm::{Assembler, ExecutionContext, Vm, VmResult};

fn main() {
    println!("=== 存储合约示例 ===\n");

    // 示例 1: 存储单个值
    println!("示例 1: 存储和读取单个值");
    println!("------------------------");

    let code = Assembler::new()
        // 存储值 42 到存储槽 0
        .push1(42)      // 要存储的值
        .push1(0)       // 存储槽键
        .sstore()       // 存储: storage[0] = 42

        // 从存储槽 0 读取值
        .push1(0)       // 存储槽键
        .sload()        // 加载: stack.push(storage[0])

        // 存储结果到内存并返回
        .push1(0)       // 内存地址
        .mstore()       // 存储结果到内存[0]
        .push1(32)      // 返回数据大小
        .push1(0)       // 返回数据起始地址
        .return_op()    // 返回结果
        .build();

    execute_and_print(code, 50000);

    // 示例 2: 存储多个值
    println!("\n示例 2: 存储和读取多个值");
    println!("------------------------");

    let code = Assembler::new()
        // 存储值 100 到存储槽 0
        .push1(100)
        .push1(0)
        .sstore()

        // 存储值 200 到存储槽 1
        .push1(200)
        .push1(1)
        .sstore()

        // 存储值 250 到存储槽 2
        .push1(250)
        .push1(2)
        .sstore()

        // 读取存储槽 1 的值
        .push1(1)
        .sload()

        // 存储结果到内存并返回
        .push1(0)       // 内存地址
        .mstore()       // 存储结果到内存[0]
        .push1(32)      // 返回数据大小
        .push1(0)       // 返回数据起始地址
        .return_op()    // 返回结果
        .build();

    execute_and_print(code, 100000);

    // 示例 3: 更新存储值
    println!("\n示例 3: 更新存储值");
    println!("------------------------");

    let code = Assembler::new()
        // 初始存储: storage[0] = 10
        .push1(10)
        .push1(0)
        .sstore()

        // 更新: storage[0] = 20
        .push1(20)
        .push1(0)
        .sstore()

        // 读取更新后的值
        .push1(0)
        .sload()

        // 存储结果到内存并返回
        .push1(0)       // 内存地址
        .mstore()       // 存储结果到内存[0]
        .push1(32)      // 返回数据大小
        .push1(0)       // 返回数据起始地址
        .return_op()    // 返回结果
        .build();

    execute_and_print(code, 100000);

    // 示例 4: 删除存储值（存储 0）
    println!("\n示例 4: 删除存储值");
    println!("------------------------");

    let code = Assembler::new()
        // 存储值 42
        .push1(42)
        .push1(0)
        .sstore()

        // 删除值（存储 0）
        .push1(0)
        .push1(0)
        .sstore()

        // 读取删除后的值（应为 0）
        .push1(0)
        .sload()

        // 存储结果到内存并返回
        .push1(0)       // 内存地址
        .mstore()       // 存储结果到内存[0]
        .push1(32)      // 返回数据大小
        .push1(0)       // 返回数据起始地址
        .return_op()    // 返回结果
        .build();

    execute_and_print(code, 100000);

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

    match result {
        VmResult::Success(data) => {
            println!("  状态: 成功");
            if data.len() >= 32 {
                let value = u64::from_be_bytes([
                    data[24], data[25], data[26], data[27],
                    data[28], data[29], data[30], data[31],
                ]);
                println!("  返回值: {}", value);
            } else if data.is_empty() {
                println!("  返回值: (无)");
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
