# RISC-V 汇编示例: 计算 1+2+...+10
#
# 演示: ADDI, ADD, BLT 循环
# 结果: a0 = 55

# 初始化
addi a0, zero, 0     # sum = 0
addi t0, zero, 11    # upper bound (exclusive)
addi t1, zero, 1     # i = 1

# 循环: sum += i, i++, if i < 11 goto loop
loop:
  add a0, a0, t1     # sum += i
  addi t1, t1, 1     # i++
  blt t1, t0, loop   # if i < 11, goto loop

# 停止
ebreak
