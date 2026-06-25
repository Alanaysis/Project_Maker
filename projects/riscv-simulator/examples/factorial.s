# RISC-V 汇编示例: 阶乘计算
#
# 计算 6! = 720
# 演示: 循环乘法

# 初始化
addi t0, zero, 6     # n = 6
addi t1, zero, 1     # result = 1
addi t2, zero, 1     # i = 1

# 循环: result *= i, i++
loop:
  # 乘法通过移位和加法实现 (简化版: 用 SLT 判断)
  # 这里用一个简单的累加模拟乘法
  # result = result * i
  # 为了简化，我们直接计算 6! = 6*5*4*3*2*1

  addi t3, zero, 0   # temp = 0
  add t4, t1, zero   # copy = result

  # 简单乘法: result * i (通过循环加法)
  addi t5, zero, 0   # j = 0
  mul_loop:
    add t3, t3, t4   # temp += copy
    addi t5, t5, 1   # j++
    blt t5, t2, mul_loop  # if j < i, goto mul_loop

  add t1, t3, zero   # result = temp
  addi t2, t2, 1     # i++
  blt t2, t0, loop   # if i <= n, goto loop

# 结果在 t1 中
add a0, t1, zero
ebreak
