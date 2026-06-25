#!/usr/bin/env python3
"""
MVCC 基本使用示例。

演示 MVCC 引擎的核心功能:
    1. 创建事务和读写数据
    2. 快照隔离
    3. 写写冲突检测
    4. 版本链和垃圾回收
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mvcc.engine import MVCCEngine


def demo_basic_crud():
    """演示基本的增删改查操作。"""
    print("=" * 60)
    print("1. 基本 CRUD 操作")
    print("=" * 60)

    engine = MVCCEngine()

    # 写入数据
    txn = engine.begin()
    engine.txn_write(txn, "user:1", {"name": "Alice", "age": 30})
    engine.txn_write(txn, "user:2", {"name": "Bob", "age": 25})
    engine.txn_write(txn, "user:3", {"name": "Charlie", "age": 35})
    result = engine.commit(txn)
    print(f"写入 3 条数据: {result.message}")

    # 读取数据
    txn = engine.begin()
    user1 = engine.txn_read(txn, "user:1")
    user2 = engine.txn_read(txn, "user:2")
    print(f"读取 user:1 = {user1}")
    print(f"读取 user:2 = {user2}")
    engine.commit(txn)

    # 更新数据
    txn = engine.begin()
    engine.txn_write(txn, "user:1", {"name": "Alice", "age": 31})
    engine.commit(txn)
    print("更新 user:1 的 age 为 31")

    # 删除数据
    txn = engine.begin()
    engine.txn_delete(txn, "user:3")
    engine.commit(txn)
    print("删除 user:3")

    # 验证删除
    txn = engine.begin()
    user3 = engine.txn_read(txn, "user:3")
    print(f"读取已删除的 user:3 = {user3}")
    engine.commit(txn)


def demo_snapshot_isolation():
    """演示快照隔离。"""
    print("\n" + "=" * 60)
    print("2. 快照隔离")
    print("=" * 60)

    engine = MVCCEngine()

    # 写入初始数据
    txn = engine.begin()
    engine.txn_write(txn, "counter", 0)
    engine.commit(txn)

    # 事务 A 开始（快照时刻 counter=0）
    txn_a = engine.begin()
    val_a = engine.txn_read(txn_a, "counter")
    print(f"事务 A 读取 counter = {val_a}")

    # 事务 B 修改 counter 并提交
    txn_b = engine.begin()
    engine.txn_write(txn_b, "counter", 100)
    engine.commit(txn_b)
    print("事务 B 将 counter 修改为 100 并提交")

    # 事务 A 仍然看到旧值（快照隔离）
    val_a2 = engine.txn_read(txn_a, "counter")
    print(f"事务 A 再次读取 counter = {val_a2} (快照隔离，看到旧值)")
    engine.commit(txn_a)

    # 新事务可以看到最新值
    txn_c = engine.begin()
    val_c = engine.txn_read(txn_c, "counter")
    print(f"事务 C 读取 counter = {val_c} (看到最新值)")
    engine.commit(txn_c)


def demo_write_write_conflict():
    """演示写写冲突检测。"""
    print("\n" + "=" * 60)
    print("3. 写写冲突检测")
    print("=" * 60)

    engine = MVCCEngine()

    # 写入初始数据
    txn = engine.begin()
    engine.txn_write(txn, "account", 1000)
    engine.commit(txn)

    # 两个并发事务修改同一个 key
    txn1 = engine.begin()
    txn2 = engine.begin()

    engine.txn_write(txn1, "account", 900)   # 扣除 100
    engine.txn_write(txn2, "account", 800)   # 扣除 200

    # txn1 先提交 -> 成功
    result1 = engine.commit(txn1)
    print(f"事务 1 提交: {result1.message}")

    # txn2 后提交 -> 冲突
    result2 = engine.commit(txn2)
    print(f"事务 2 提交: {result2.message}")
    print(f"冲突类型: {result2.conflict_type}")
    print(f"冲突 key: {result2.conflicting_keys}")


def demo_version_chain():
    """演示版本链。"""
    print("\n" + "=" * 60)
    print("4. 版本链")
    print("=" * 60)

    engine = MVCCEngine(gc_threshold=3)

    # 写入多个版本
    for i in range(5):
        txn = engine.begin()
        engine.txn_write(txn, "data", f"version_{i}")
        engine.commit(txn)

    chain = engine.get_version_chain("data")
    print(f"版本链长度: {chain.length}")

    versions = chain.to_list()
    for i, v in enumerate(versions):
        print(f"  版本 {i}: data={v.data}, "
              f"create_ts={v.create_ts}, "
              f"txn_id={v.create_txn_id}")


def demo_garbage_collection():
    """演示垃圾回收。"""
    print("\n" + "=" * 60)
    print("5. 垃圾回收")
    print("=" * 60)

    engine = MVCCEngine(gc_threshold=3)

    # 写入多个版本
    for i in range(10):
        txn = engine.begin()
        engine.txn_write(txn, "data", f"version_{i}")
        engine.commit(txn)

    chain = engine.get_version_chain("data")
    print(f"GC 前版本链长度: {chain.length}")

    # 执行 GC
    collected, keys = engine.run_gc()
    print(f"清理了 {collected} 个版本，处理了 {keys} 个 key")

    chain = engine.get_version_chain("data")
    print(f"GC 后版本链长度: {chain.length}")

    # 统计信息
    stats = engine.get_stats()
    print(f"GC 统计: {stats['gc']}")


def demo_engine_stats():
    """演示引擎统计。"""
    print("\n" + "=" * 60)
    print("6. 引擎统计")
    print("=" * 60)

    engine = MVCCEngine()

    # 执行一些操作
    txn1 = engine.begin()
    engine.txn_write(txn1, "key1", 100)
    engine.txn_write(txn1, "key2", 200)
    engine.commit(txn1)

    txn2 = engine.begin()
    engine.txn_read(txn2, "key1")
    engine.txn_write(txn2, "key3", 300)

    stats = engine.get_stats()
    print(f"存储 key 数量: {stats['storage_keys']}")
    print(f"活跃事务数: {stats['active_txns']}")
    print(f"已提交事务数: {stats['committed_txns']}")
    print(f"当前时间戳: {stats['current_timestamp']}")

    engine.commit(txn2)


if __name__ == "__main__":
    demo_basic_crud()
    demo_snapshot_isolation()
    demo_write_write_conflict()
    demo_version_chain()
    demo_garbage_collection()
    demo_engine_stats()
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)
