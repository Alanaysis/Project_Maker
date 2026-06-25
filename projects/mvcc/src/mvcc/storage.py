"""
存储引擎 - MVCC 的底层数据存储。

存储引擎负责:
    1. 管理所有数据记录的版本链
    2. 提供事务感知的读写接口
    3. 支持写缓冲（事务本地缓存）
    4. 在提交时将写缓冲批量应用到主存储

数据组织:
    主存储: Dict[key, VersionChain]
    每个 key 对应一条版本链，存储该 key 的所有历史版本

读写流程:
    READ:
        1. 先检查事务的写缓冲
        2. 写缓冲中有 -> 返回缓冲值（支持 Write-Read 自依赖）
        3. 写缓冲中无 -> 从版本链中按快照查找可见版本

    WRITE:
        1. 写入事务的写缓冲（不立即修改主存储）
        2. 提交时批量应用到主存储

    DELETE:
        1. 标记到事务的删除集合
        2. 提交时在版本链上标记删除
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Set

from .version import Version, VersionChain
from .transaction import Transaction


class Storage:
    """
    存储引擎 - 基于版本链的键值存储。

    属性:
        data: 主存储，key -> VersionChain 映射
    """

    def __init__(self):
        self.data: Dict[str, VersionChain] = {}

    def read(self, key: str, txn: Transaction) -> Optional[Any]:
        """
        事务读取一个 key。

        读取顺序:
            1. 检查事务的写缓冲（包括删除集合）
            2. 从版本链中按快照查找可见版本

        Args:
            key: 要读取的键
            txn: 当前事务

        Returns:
            读取的值，如果 key 不存在或不可见则返回 None

        Raises:
            RuntimeError: 如果 key 已被当前事务标记删除
        """
        # 记录读操作
        txn.add_read(key)

        # 1. 先检查写缓冲
        if key in txn.delete_set:
            return None
        if key in txn.write_buffer:
            return txn.write_buffer[key]

        # 2. 从版本链中查找可见版本
        chain = self.data.get(key)
        if chain is None:
            return None

        visible = chain.find_visible(
            snapshot_ts=txn.snapshot.timestamp,
            active_txns=txn.snapshot.active_txns,
            read_own=True,
            txn_id=txn.txn_id,
        )

        if visible is None:
            return None

        return visible.data.get("value")

    def write(self, key: str, value: Any, txn: Transaction) -> None:
        """
        事务写入一个 key（写入缓冲区）。

        Args:
            key: 要写入的键
            value: 要写入的值
            txn: 当前事务
        """
        txn.add_write(key, value)

    def delete(self, key: str, txn: Transaction) -> bool:
        """
        事务删除一个 key（标记到删除集合）。

        Args:
            key: 要删除的键
            txn: 当前事务

        Returns:
            是否成功标记删除（key 存在且可见时返回 True）
        """
        # 先检查 key 是否存在且可见
        chain = self.data.get(key)
        key_exists = False

        if chain is not None:
            visible = chain.find_visible(
                snapshot_ts=txn.snapshot.timestamp,
                active_txns=txn.snapshot.active_txns,
                read_own=True,
                txn_id=txn.txn_id,
            )
            key_exists = visible is not None

        # 也检查写缓冲中是否有该 key
        if key in txn.write_buffer:
            key_exists = True

        if key_exists:
            txn.add_delete(key)
            return True
        return False

    def apply_commit(
        self,
        txn: Transaction,
        commit_ts: int,
    ) -> int:
        """
        将事务的写缓冲应用到主存储（提交时调用）。

        处理逻辑:
            1. 遍历写缓冲，为每个写入创建新版本
            2. 遍历删除集合，标记已有版本为删除
            3. 返回应用的操作数量

        Args:
            txn: 要提交的事务
            commit_ts: 提交时间戳

        Returns:
            应用的操作数量
        """
        ops = 0

        # 1. 处理写入
        for key, value in txn.write_buffer.items():
            if key not in self.data:
                self.data[key] = VersionChain()

            version = Version(
                data={"value": value},
                create_txn_id=txn.txn_id,
                create_ts=commit_ts,
            )
            self.data[key].append(version)
            ops += 1

        # 2. 处理删除
        for key in txn.delete_set:
            chain = self.data.get(key)
            if chain is None:
                continue

            # 找到要删除的版本
            # 可能是自己刚写入的版本（在 write_buffer 中也有的情况）
            # 也可能是已存在的版本
            target = chain.head
            while target is not None:
                if target.create_txn_id == txn.txn_id:
                    # 自己刚创建的版本，直接标记删除
                    target.mark_deleted(txn.txn_id, commit_ts)
                    ops += 1
                    break
                elif target.create_txn_id != txn.txn_id and not target.is_deleted:
                    # 已存在的版本，标记删除
                    target.mark_deleted(txn.txn_id, commit_ts)
                    ops += 1
                    break
                target = target.prev

        return ops

    def get_version_chain(self, key: str) -> Optional[VersionChain]:
        """获取 key 的版本链（调试/测试用）。"""
        return self.data.get(key)

    def get_all_keys(self) -> Set[str]:
        """获取所有 key。"""
        return set(self.data.keys())

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"Storage(keys={len(self.data)})"
