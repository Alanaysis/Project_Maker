#!/usr/bin/env python3
"""
Mini语言解释器 - 主入口

支持两种模式：
1. REPL（交互式）：直接运行 `python main.py`
2. 脚本执行：运行 `python main.py script.mini`

用法：
    python main.py                    # 启动REPL
    python main.py script.mini        # 执行脚本
    python main.py -e "print(42)"     # 执行表达式
    python main.py --ast script.mini  # 显示AST
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.interpreter import Interpreter, RuntimeError
from src.parser import Parser, ParserError
from src.lexer import Lexer, LexerError


VERSION = "1.0.0"


def repl():
    """交互式REPL"""
    print(f"Mini语言解释器 v{VERSION}")
    print("输入 `help` 查看帮助，输入 `exit` 退出")
    print()

    interpreter = Interpreter()

    while True:
        try:
            line = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        line = line.strip()
        if not line:
            continue

        if line == "exit" or line == "quit":
            print("再见！")
            break

        if line == "help":
            _show_help()
            continue

        if line == "env":
            _show_env(interpreter)
            continue

        if line == "clear":
            os.system("clear" if os.name != "nt" else "cls")
            continue

        try:
            result = interpreter.run(line)
            if result.type().name != "NULL":
                print(f"=> {result.inspect()}")
        except (RuntimeError, ParserError, LexerError) as e:
            print(f"错误: {e}")
        except Exception as e:
            print(f"内部错误: {e}")


def run_file(filepath: str, show_ast: bool = False):
    """执行脚本文件"""
    if not os.path.exists(filepath):
        print(f"错误: 文件不存在: {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    if show_ast:
        parser = Parser(source)
        program = parser.parse()
        print("AST:")
        for stmt in program.statements:
            print(f"  {stmt}")
        return

    interpreter = Interpreter()
    try:
        result = interpreter.run(source)
        # 脚本执行完毕，不输出结果（除非有错误）
    except (RuntimeError, ParserError, LexerError) as e:
        print(f"错误: {e}")
        sys.exit(1)


def run_expression(expr: str):
    """执行表达式"""
    interpreter = Interpreter()
    try:
        result = interpreter.run(expr)
        print(result.inspect())
    except (RuntimeError, ParserError, LexerError) as e:
        print(f"错误: {e}")
        sys.exit(1)


def _show_help():
    """显示帮助信息"""
    print("""
命令:
  help    - 显示帮助
  env     - 显示当前环境中的变量
  clear   - 清屏
  exit    - 退出

语法:
  let x = 5;              # 变量声明
  x = 10;                 # 变量赋值
  x += 1;                 # 复合赋值

  # 算术运算
  5 + 3 * 2               # 11
  2 ** 10                 # 1024

  # 比较和逻辑
  x > 5 and x < 20        # true
  not false               # true

  # 字符串
  "hello" + " world"      # "hello world"

  # 数组
  let arr = [1, 2, 3];
  arr[0]                  # 1

  # 函数
  fn add(a, b) { return a + b; }
  add(1, 2)               # 3

  # 闭包
  fn makeCounter() {
    let count = 0;
    fn() { count += 1; return count; }
  }

  # 控制流
  if x > 5 { ... } elif x > 0 { ... } else { ... }
  while x > 0 { x -= 1; }
  for x in [1, 2, 3] { print(x); }

内置函数:
  print, println, input, str, number, bool, type
  len, upper, lower, trim, split, join, replace
  contains, starts_with, ends_with
  push, pop, sort, reverse, range
  abs, sqrt, floor, ceil, round, min, max
""")


def _show_env(interpreter: Interpreter):
    """显示环境中的变量"""
    keys = interpreter.global_env.all_keys()
    if not keys:
        print("(空)")
        return
    for key in keys:
        try:
            value = interpreter.global_env.get(key)
            print(f"  {key} = {value.inspect()}")
        except Exception:
            pass


def main():
    """主入口"""
    args = sys.argv[1:]

    if not args:
        repl()
        return

    if args[0] == "-e" or args[0] == "--eval":
        if len(args) < 2:
            print("错误: -e 选项需要表达式参数")
            sys.exit(1)
        run_expression(args[1])
        return

    if args[0] == "--ast":
        if len(args) < 2:
            print("错误: --ast 选项需要文件参数")
            sys.exit(1)
        run_file(args[1], show_ast=True)
        return

    if args[0] == "--version" or args[0] == "-v":
        print(f"Mini语言解释器 v{VERSION}")
        return

    if args[0] == "--help" or args[0] == "-h":
        print(__doc__)
        return

    # 执行脚本文件
    run_file(args[0])


if __name__ == "__main__":
    main()
