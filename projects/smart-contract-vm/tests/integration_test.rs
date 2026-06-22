use smart_contract_vm::{Vm, ExecutionContext, VmResult, Assembler};

fn create_vm(code: Vec<u8>, gas_limit: u64) -> Vm {
    let context = ExecutionContext {
        code,
        calldata: Vec::new(),
        caller: 1000,
        address: 2000,
        value: 0,
    };
    Vm::new(context, gas_limit)
}

#[test]
fn test_fibonacci() {
    // Fibonacci using iterative approach: a=0, b=1, loop 10 times
    //
    // Bytecode layout:
    //   0: PUSH1 0       (a=0)
    //   2: PUSH1 1       (b=1)
    //   4: PUSH1 10      (counter=10)
    //   6: JUMPDEST      (loop_start)
    //   7: DUP1          (dup counter)
    //   8: ISZERO        (counter==0?)
    //   9: PUSH1 <end>   (jump target)
    //  11: JUMPI
    //  12: DUP3          (dup a)
    //  13: DUP2          (dup b)
    //  14: ADD           (temp = a+b)
    //  15: SWAP3         (swap temp with a)
    //  16: POP           (pop old a)
    //  17: SWAP2         (swap with counter)
    //  18: SWAP1         (swap b with a)
    //  19: PUSH1 1
    //  21: SWAP1
    //  22: SUB           (counter--)
    //  23: PUSH1 6       (loop_start)
    //  25: JUMP
    //  26: JUMPDEST      (loop_end)
    //  27: POP           (pop counter)
    //  28: POP           (pop a)
    //  29: STOP
    let code = vec![
        0x60, 0x00,       // PUSH1 0
        0x60, 0x01,       // PUSH1 1
        0x60, 0x0a,       // PUSH1 10
        0x5b,             // JUMPDEST (loop_start = 6)
        0x80,             // DUP1
        0x13,             // ISZERO
        0x60, 0x1a,       // PUSH1 26 (loop_end)
        0x57,             // JUMPI
        0x82,             // DUP3
        0x81,             // DUP2
        0x01,             // ADD
        0x92,             // SWAP3
        0x50,             // POP
        0x91,             // SWAP2
        0x90,             // SWAP1
        0x60, 0x01,       // PUSH1 1
        0x90,             // SWAP1
        0x03,             // SUB
        0x60, 0x06,       // PUSH1 6 (loop_start)
        0x56,             // JUMP
        0x5b,             // JUMPDEST (loop_end = 26)
        0x50,             // POP
        0x50,             // POP
        0x00,             // STOP
    ];

    let mut vm = create_vm(code, 10000);
    let result = vm.execute();
    assert!(matches!(result, VmResult::Success(_)), "Expected success but got {:?}", result);
}

#[test]
fn test_gas_tracking() {
    let code = Assembler::new()
        .push1(1)
        .push1(2)
        .add()
        .push1(3)
        .mul()
        .stop()
        .build();

    let mut vm = create_vm(code, 1000);
    vm.execute();

    // PUSH1 (3) * 2 + ADD (3) + PUSH1 (3) + MUL (3) + STOP (0) = 15
    assert_eq!(vm.gas_used(), 15);
}

#[test]
fn test_memory_store_load() {
    let code = Assembler::new()
        .push1(0xAB)
        .push1(0)
        .mstore()
        .push1(0)
        .mload()
        .stop()
        .build();

    let mut vm = create_vm(code, 1000);
    vm.execute();
    assert_eq!(vm.stack_size(), 1);
}

#[test]
fn test_storage_persistence() {
    let code = Assembler::new()
        .push1(42)
        .push1(1)
        .sstore()
        .push1(1)
        .sload()
        .stop()
        .build();

    let mut vm = create_vm(code, 50000);
    vm.execute();
    assert_eq!(vm.stack_size(), 1);
}

#[test]
fn test_loop_with_counter() {
    // sum = 1+2+...+10 = 55
    //
    // Bytecode layout:
    //   0: PUSH1 0       (sum=0)
    //   2: PUSH1 10      (counter=10)
    //   4: JUMPDEST      (loop_start)
    //   5: DUP1          (dup counter)
    //   6: ISZERO        (counter==0?)
    //   7: PUSH1 <end>   (jump target)
    //   9: JUMPI
    //  10: DUP2          (dup sum)
    //  11: DUP2          (dup counter)
    //  12: ADD           (sum += counter)
    //  13: SWAP2
    //  14: POP
    //  15: PUSH1 1
    //  17: SWAP1
    //  18: SUB           (counter--)
    //  19: PUSH1 4       (loop_start)
    //  21: JUMP
    //  22: JUMPDEST      (loop_end)
    //  23: POP           (pop counter)
    //  24: STOP
    let code = vec![
        0x60, 0x00,       // PUSH1 0
        0x60, 0x0a,       // PUSH1 10
        0x5b,             // JUMPDEST (loop_start = 4)
        0x80,             // DUP1
        0x13,             // ISZERO
        0x60, 0x16,       // PUSH1 22 (loop_end)
        0x57,             // JUMPI
        0x81,             // DUP2
        0x81,             // DUP2
        0x01,             // ADD
        0x91,             // SWAP2
        0x50,             // POP
        0x60, 0x01,       // PUSH1 1
        0x90,             // SWAP1
        0x03,             // SUB
        0x60, 0x04,       // PUSH1 4 (loop_start)
        0x56,             // JUMP
        0x5b,             // JUMPDEST (loop_end = 22)
        0x50,             // POP
        0x00,             // STOP
    ];

    let mut vm = create_vm(code, 10000);
    vm.execute();
    assert_eq!(vm.stack_size(), 1);
}

#[test]
fn test_max_stack_depth() {
    let mut asm = Assembler::new();
    for i in 0..100 {
        asm = asm.push1(i);
    }
    asm = asm.stop();
    let code = asm.build();

    let mut vm = create_vm(code, 100000);
    vm.execute();
    assert_eq!(vm.stack_size(), 100);
}

#[test]
fn test_conditional_execution() {
    // if (5 > 3) then result = 1 else result = 0
    //
    // Bytecode layout:
    //   0: PUSH1 5
    //   2: PUSH1 3
    //   4: GT
    //   5: PUSH1 <false_target>  (13 = true branch JUMPDEST)
    //   7: JUMPI
    //   8: PUSH1 0               (false branch: result = 0)
    //  10: PUSH1 <merge>         (18 = merge JUMPDEST)
    //  12: JUMP
    //  13: JUMPDEST              (true branch)
    //  14: PUSH1 1               (result = 1)
    //  16: PUSH1 <merge>         (18)
    //  18: JUMP                  -- actually we don't need this if merge is next
    //
    // Actually simpler: true branch doesn't need to jump
    //   0: PUSH1 5
    //   2: PUSH1 3
    //   4: GT
    //   5: PUSH1 11 (true_branch JUMPDEST)
    //   7: JUMPI
    //   8: PUSH1 0               (false: result = 0)
    //  10: PUSH1 15 (merge JUMPDEST)
    //  12: JUMP
    //  13: JUMPDEST              (true_branch)
    //  14: PUSH1 1               (true: result = 1)
    //  -- fall through to merge --
    //  -- wait, we need same number of items on stack for both paths
    //  -- true path: PUSH1 1 -> stack has [1]
    //  -- false path: PUSH1 0, PUSH1 15, JUMP -> stack has [0] at merge
    //  16: JUMPDEST              (merge)
    //  17: STOP
    let code = vec![
        0x60, 0x05,       // PUSH1 5
        0x60, 0x03,       // PUSH1 3
        0x11,             // GT (5 > 3 = true)
        0x60, 0x0d,       // PUSH1 13 (true_branch)
        0x57,             // JUMPI
        0x60, 0x00,       // PUSH1 0 (false branch)
        0x60, 0x10,       // PUSH1 16 (merge)
        0x56,             // JUMP
        0x5b,             // JUMPDEST (true_branch = 13)
        0x60, 0x01,       // PUSH1 1
        0x5b,             // JUMPDEST (merge = 16)
        0x00,             // STOP
    ];

    let mut vm = create_vm(code, 1000);
    vm.execute();
    assert_eq!(vm.stack_size(), 1);
}

#[test]
fn test_byte_manipulation() {
    let code = Assembler::new()
        .push1(0b1010)  // 10
        .push1(0b1100)  // 12
        .and()           // 1010 & 1100 = 1000 = 8
        .stop()
        .build();

    let mut vm = create_vm(code, 1000);
    vm.execute();
    assert_eq!(vm.stack_size(), 1);
}

#[test]
fn test_swap_operations() {
    let code = Assembler::new()
        .push1(1)
        .push1(2)
        .push1(3)
        .push1(4)
        .swap4()       // swap top with 5th element (4 <-> 1)
        .stop()
        .build();

    let mut vm = create_vm(code, 1000);
    vm.execute();
    assert_eq!(vm.stack_size(), 4);
}
