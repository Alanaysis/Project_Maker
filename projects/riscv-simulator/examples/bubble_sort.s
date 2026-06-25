# RISC-V 汇编示例: 冒泡排序 (简化版)
#
# 对 5 个元素排序
# 数据区在内存高地址

# 初始化数据区地址
lui t0, 0x1000       # t0 = 0x1000000 (数据区)
addi t0, t0, 0x100   # t0 = 0x1000100

# 存储 5 个测试数据: 5, 3, 1, 4, 2
addi t1, zero, 5
sw t1, 0(t0)
addi t1, zero, 3
sw t1, 4(t0)
addi t1, zero, 1
sw t1, 8(t0)
addi t1, zero, 4
sw t1, 12(t0)
addi t1, zero, 2
sw t1, 16(t0)

# 冒泡排序
addi t2, zero, 5     # n = 5
addi t3, zero, 0     # i = 0

outer_loop:
  addi t4, zero, 0   # j = 0
  addi t5, t2, -1    # n-1

  inner_loop:
    # 计算地址
    slli t6, t4, 2   # j * 4
    add a1, t0, t6   # addr = base + j*4

    # 读取 arr[j] 和 arr[j+1]
    lw a2, 0(a1)     # a2 = arr[j]
    lw a3, 4(a1)     # a3 = arr[j+1]

    # 比较
    blt a2, a3, no_swap  # if arr[j] < arr[j+1], skip

    # 交换
    sw a3, 0(a1)
    sw a2, 4(a1)

    no_swap:
    addi t4, t4, 1   # j++
    blt t4, t5, inner_loop  # if j < n-1, goto inner_loop

  addi t3, t3, 1     # i++
  addi t6, t2, -1
  blt t3, t6, outer_loop  # if i < n-1, goto outer_loop

# 读取排序后的第一个元素 (最小值)
lw a0, 0(t0)
ebreak
