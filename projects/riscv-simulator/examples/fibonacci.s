# RISC-V 汇编示例: 斐波那契数列
#
# 计算前 10 个斐波那契数
# 结果: a0 = 第 10 个斐波那契数 (55)

# 初始化
addi t0, zero, 0     # fib(0) = 0
addi t1, zero, 1     # fib(1) = 1
addi t2, zero, 11    # upper bound (exclusive)
addi t3, zero, 2     # i = 2

# 循环
loop:
  add t4, t0, t1     # next = fib(n-2) + fib(n-1)
  add t0, t1, zero   # fib(n-2) = fib(n-1)
  add t1, t4, zero   # fib(n-1) = next
  addi t3, t3, 1     # i++
  blt t3, t2, loop   # if i < count, goto loop

# 结果在 t1 中
add a0, t1, zero
ebreak
