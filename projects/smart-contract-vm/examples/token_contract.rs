/// ERC20 代币合约示例
///
/// 演示如何使用虚拟机实现一个简化的 ERC20 代币合约。
/// 支持: 部署(mint)、余额查询、转账、事件日志
///
/// 运行方式:
/// ```bash
/// cargo run --example token_contract
/// ```

use smart_contract_vm::{Assembler, ExecutionContext, Vm, VmResult};

/// 存储布局:
///   storage[0] = totalSupply
///   storage[100 + addr] = balance

fn main() {
    println!("=== ERC20 代币合约示例 ===\n");

    let total_supply = 1_000_000u64;
    let transfer_amount = 500_000u64;

    // 示例 1: 部署合约 + 查询初始余额
    println!("示例 1: 部署代币合约并查询余额");
    println!("  总供应量: {} MTK", total_supply);

    let deploy_and_query = Assembler::new()
        // 初始化: storage[0] = totalSupply
        .push8(total_supply)
        .push1(0)
        .sstore()
        // 给地址1分配初始余额: storage[101] = totalSupply
        .push8(total_supply)
        .push1(101)
        .sstore()
        // 查询地址1余额并返回
        .push1(101)
        .sload()
        .push1(0)
        .mstore()
        .push1(32)
        .push1(0)
        .return_op()
        .build();

    let context = ExecutionContext {
        code: deploy_and_query,
        calldata: Vec::new(),
        caller: 1,
        address: 100,
        value: 0,
    };

    let mut vm = Vm::new(context, 100000);
    match vm.execute() {
        VmResult::Success(data) => {
            println!("  部署成功! Gas: {}", vm.gas_used());
            if data.len() >= 32 {
                let balance = u64::from_be_bytes([
                    data[24], data[25], data[26], data[27],
                    data[28], data[29], data[30], data[31],
                ]);
                println!("  地址1 余额: {} MTK", balance);
            }
        }
        VmResult::Error(e) => println!("  失败: {}", e),
        VmResult::Revert(_) => println!("  失败: Revert"),
    }

    // 示例 2: 转账操作 + 查询余额
    println!("\n示例 2: 转账 {} MTK 从地址1到地址2", transfer_amount);

    let transfer_and_query = Assembler::new()
        // 初始化 (模拟已部署的合约状态)
        .push8(total_supply)
        .push1(0)
        .sstore()
        .push8(total_supply)
        .push1(101)
        .sstore()

        // 转账: storage[101] -= amount, storage[102] += amount
        // 更新发送者余额
        .push1(101)
        .sload()
        .push8(transfer_amount)
        .sub()
        .push1(101)
        .sstore()

        // 更新接收者余额
        .push1(102)
        .sload()
        .push8(transfer_amount)
        .add()
        .push1(102)
        .sstore()

        // 写入 Transfer 事件数据到内存
        .push8(transfer_amount)
        .push1(0)
        .mstore()

        // 触发 Transfer 事件 (from=1, to=2, amount)
        // LOG3: offset=0, size=32, topic1=from, topic2=to, topic3=amount
        .push8(transfer_amount)  // topic3 = amount
        .push1(2)                // topic2 = to
        .push1(1)                // topic1 = from
        .push1(32)               // data size
        .push1(0)                // data offset
        .log3()

        // 返回地址1余额
        .push1(101)
        .sload()
        .push1(0)
        .mstore()
        .push1(32)
        .push1(0)
        .return_op()
        .build();

    let context = ExecutionContext {
        code: transfer_and_query,
        calldata: Vec::new(),
        caller: 1,
        address: 100,
        value: 0,
    };

    let mut vm = Vm::new(context, 200000);
    match vm.execute() {
        VmResult::Success(data) => {
            println!("  转账成功! Gas: {}", vm.gas_used());
            println!("  日志事件数: {}", vm.logs().len());
            if !vm.logs().is_empty() {
                println!("  Transfer 事件: from={}, to={}, amount={}",
                    vm.logs()[0].topics[0],
                    vm.logs()[0].topics[1],
                    vm.logs()[0].topics[2],
                );
            }
            if data.len() >= 32 {
                let balance = u64::from_be_bytes([
                    data[24], data[25], data[26], data[27],
                    data[28], data[29], data[30], data[31],
                ]);
                println!("  地址1 余额: {} MTK", balance);
            }
        }
        VmResult::Error(e) => println!("  转账失败: {}", e),
        VmResult::Revert(_) => println!("  转账失败: Revert"),
    }

    // 示例 3: 查询地址2余额
    println!("\n示例 3: 查询转账后地址2余额");

    let query_receiver = Assembler::new()
        // 初始化
        .push8(total_supply)
        .push1(0)
        .sstore()
        .push8(total_supply)
        .push1(101)
        .sstore()

        // 执行转账
        .push1(101)
        .sload()
        .push8(transfer_amount)
        .sub()
        .push1(101)
        .sstore()

        .push1(102)
        .sload()
        .push8(transfer_amount)
        .add()
        .push1(102)
        .sstore()

        // 返回地址2余额
        .push1(102)
        .sload()
        .push1(0)
        .mstore()
        .push1(32)
        .push1(0)
        .return_op()
        .build();

    let context = ExecutionContext {
        code: query_receiver,
        calldata: Vec::new(),
        caller: 1,
        address: 100,
        value: 0,
    };

    let mut vm = Vm::new(context, 200000);
    match vm.execute() {
        VmResult::Success(data) => {
            if data.len() >= 32 {
                let balance = u64::from_be_bytes([
                    data[24], data[25], data[26], data[27],
                    data[28], data[29], data[30], data[31],
                ]);
                println!("  地址2 余额: {} MTK", balance);
            }
        }
        VmResult::Error(e) => println!("  查询失败: {}", e),
        _ => {}
    }

    println!("\n=== 示例结束 ===");
}
