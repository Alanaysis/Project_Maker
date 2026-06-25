#!/usr/bin/env python3
"""
MVCC 并发访问模拟示例。

使用线程模拟多个事务并发执行，展示:
    1. 并发读写
    2. 冲突检测和自动中止
    3. 重试机制
"""

import sys
import os
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mvcc.engine import MVCCEngine


class BankAccount:
    """银行账户 - 基于 MVCC 的简单账户系统。"""

    def __init__(self, engine: MVCCEngine):
        self.engine = engine
        self._lock = threading.Lock()

    def create_account(self, name: str, balance: float):
        """创建账户。"""
        txn = self.engine.begin()
        self.engine.txn_write(txn, f"account:{name}", balance)
        self.engine.commit(txn, check_conflicts=False)

    def transfer(self, from_acc: str, to_acc: str, amount: float, max_retries: int = 3):
        """
        转账操作（带重试机制）。

        Args:
            from_acc: 转出账户
            to_acc: 转入账户
            amount: 转账金额
            max_retries: 最大重试次数

        Returns:
            是否成功
        """
        for attempt in range(max_retries):
            txn = self.engine.begin()

            # 读取余额
            from_balance = self.engine.txn_read(txn, f"account:{from_acc}")
            to_balance = self.engine.txn_read(txn, f"account:{to_acc}")

            if from_balance is None or to_balance is None:
                self.engine.abort(txn)
                return False

            if from_balance < amount:
                self.engine.abort(txn)
                return False

            # 写入新余额
            self.engine.txn_write(txn, f"account:{from_acc}", from_balance - amount)
            self.engine.txn_write(txn, f"account:{to_acc}", to_balance + amount)

            # 提交
            result = self.engine.commit(txn)
            if not result.has_conflict:
                return True

            # 冲突，重试
            print(f"  [重试 {attempt + 1}/{max_retries}] "
                  f"转账 {from_acc} -> {to_acc} 冲突，重新尝试...")
            time.sleep(0.01)

        return False

    def get_balance(self, name: str) -> float:
        """查询余额。"""
        txn = self.engine.begin()
        balance = self.engine.txn_read(txn, f"account:{name}")
        self.engine.commit(txn, check_conflicts=False)
        return balance or 0


def demo_concurrent_transfers():
    """演示并发转账。"""
    print("=" * 60)
    print("并发转账模拟")
    print("=" * 60)

    engine = MVCCEngine()
    bank = BankAccount(engine)

    # 创建账户
    bank.create_account("Alice", 1000)
    bank.create_account("Bob", 1000)
    bank.create_account("Charlie", 1000)

    print(f"Alice:   {bank.get_balance('Alice')}")
    print(f"Bob:     {bank.get_balance('Bob')}")
    print(f"Charlie: {bank.get_balance('Charlie')}")

    results = []

    def do_transfer(from_acc, to_acc, amount):
        success = bank.transfer(from_acc, to_acc, amount)
        results.append((from_acc, to_acc, amount, success))

    # 创建多个并发转账
    threads = [
        threading.Thread(target=do_transfer, args=("Alice", "Bob", 100)),
        threading.Thread(target=do_transfer, args=("Bob", "Charlie", 200)),
        threading.Thread(target=do_transfer, args=("Charlie", "Alice", 150)),
        threading.Thread(target=do_transfer, args=("Alice", "Charlie", 50)),
    ]

    # 启动所有线程
    for t in threads:
        t.start()

    # 等待完成
    for t in threads:
        t.join()

    # 打印结果
    print("\n转账结果:")
    for from_acc, to_acc, amount, success in results:
        status = "成功" if success else "失败(冲突)"
        print(f"  {from_acc} -> {to_acc}: {amount} [{status}]")

    print(f"\n最终余额:")
    print(f"  Alice:   {bank.get_balance('Alice')}")
    print(f"  Bob:     {bank.get_balance('Bob')}")
    print(f"  Charlie: {bank.get_balance('Charlie')}")

    total = (bank.get_balance("Alice")
             + bank.get_balance("Bob")
             + bank.get_balance("Charlie"))
    print(f"  总计:    {total} (应为 3000)")


def demo_read_heavy_workload():
    """演示读密集型工作负载。"""
    print("\n" + "=" * 60)
    print("读密集型工作负载")
    print("=" * 60)

    engine = MVCCEngine()

    # 写入初始数据
    txn = engine.begin()
    for i in range(10):
        engine.txn_write(txn, f"key:{i}", f"value:{i}")
    engine.commit(txn, check_conflicts=False)

    read_results = []
    write_results = []

    def reader(thread_id):
        """读取线程。"""
        for _ in range(5):
            txn = engine.begin()
            for i in range(10):
                val = engine.txn_read(txn, f"key:{i}")
                read_results.append((thread_id, f"key:{i}", val))
            engine.commit(txn, check_conflicts=False)

    def writer(thread_id):
        """写入线程。"""
        for i in range(3):
            txn = engine.begin()
            engine.txn_write(txn, f"key:{thread_id * 100 + i}", f"new_value")
            result = engine.commit(txn)
            write_results.append((thread_id, result.has_conflict))

    # 启动读写线程
    threads = []
    for i in range(3):
        threads.append(threading.Thread(target=reader, args=(i,)))
    for i in range(2):
        threads.append(threading.Thread(target=writer, args=(i,)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"读操作总数: {len(read_results)}")
    print(f"写操作总数: {len(write_results)}")
    print(f"写入冲突数: {sum(1 for _, c in write_results if c)}")

    stats = engine.get_stats()
    print(f"引擎状态: {stats}")


if __name__ == "__main__":
    demo_concurrent_transfers()
    demo_read_heavy_workload()
    print("\n所有并发示例执行完成!")
