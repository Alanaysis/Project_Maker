"""
分布式训练工具模块

⭐ 分布式训练基础:
    1. 数据并行 (Data Parallelism):
       - 每个 GPU 持有完整的模型副本
       - 数据被分成多个部分，每个 GPU 处理一部分
       - 梯度在所有 GPU 之间同步

    2. 模型并行 (Model Parallelism):
       - 模型被分割到多个 GPU 上
       - 适用于单个 GPU 放不下整个模型的情况

    3. DeepSpeed ZeRO:
       - ZeRO-1: 分片优化器状态
       - ZeRO-2: 分片优化器状态 + 梯度
       - ZeRO-3: 分片优化器状态 + 梯度 + 参数

💡 本模块提供分布式训练的基本工具函数
"""

import os
from typing import Optional

import torch
import torch.distributed as dist


def setup_distributed(backend: str = "nccl") -> bool:
    """
    设置分布式训练环境

    ⭐ 关键步骤:
    1. 检测分布式环境变量
    2. 初始化进程组
    3. 设置当前设备

    Args:
        backend: 通信后端 ("nccl" 用于 GPU, "gloo" 用于 CPU)

    Returns:
        是否成功设置分布式环境
    """
    # 检查是否在分布式环境中
    if not is_distributed_available():
        return False

    # 获取环境变量
    rank = int(os.environ.get("RANK", 0))
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    local_rank = int(os.environ.get("LOCAL_RANK", 0))

    # 初始化进程组
    if not dist.is_initialized():
        dist.init_process_group(
            backend=backend,
            rank=rank,
            world_size=world_size,
        )

    # 设置当前设备
    if torch.cuda.is_available():
        torch.cuda.set_device(local_rank)

    print(f"分布式训练已初始化: rank={rank}, world_size={world_size}, local_rank={local_rank}")

    return True


def cleanup_distributed():
    """
    清理分布式训练环境

    在训练结束后调用，释放资源
    """
    if dist.is_initialized():
        dist.destroy_process_group()
        print("分布式训练环境已清理")


def is_distributed_available() -> bool:
    """
    检查是否可用分布式训练

    Returns:
        是否可用分布式训练
    """
    return (
        "RANK" in os.environ
        and "WORLD_SIZE" in os.environ
        and "LOCAL_RANK" in os.environ
    )


def is_main_process() -> bool:
    """
    检查当前进程是否是主进程

    ⭐ 主进程负责:
    - 日志记录
    - 模型保存
    - 评估

    Returns:
        是否是主进程
    """
    if not dist.is_initialized():
        return True

    return dist.get_rank() == 0


def get_rank() -> int:
    """获取当前进程的 rank"""
    if not dist.is_initialized():
        return 0
    return dist.get_rank()


def get_world_size() -> int:
    """获取总进程数"""
    if not dist.is_initialized():
        return 1
    return dist.get_world_size()


def get_local_rank() -> int:
    """获取本地 rank（同一节点内的 rank）"""
    return int(os.environ.get("LOCAL_RANK", 0))


def barrier():
    """
    同步所有进程

    ⭐ 用于确保所有进程都到达某个点后再继续
    """
    if dist.is_initialized():
        dist.barrier()


def all_reduce(
    tensor: torch.Tensor,
    op: str = "mean",
) -> torch.Tensor:
    """
    AllReduce 操作

    ⭐ AllReduce 是分布式训练的核心操作:
    - 将所有进程的 tensor 进行归约
    - 将结果广播到所有进程

    Args:
        tensor: 要归约的 tensor
        op: 归约操作 ("mean", "sum", "max", "min")

    Returns:
        归约后的 tensor
    """
    if not dist.is_initialized():
        return tensor

    # 选择归约操作
    if op == "mean":
        dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
        tensor /= get_world_size()
    elif op == "sum":
        dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
    elif op == "max":
        dist.all_reduce(tensor, op=dist.ReduceOp.MAX)
    elif op == "min":
        dist.all_reduce(tensor, op=dist.ReduceOp.MIN)
    else:
        raise ValueError(f"不支持的归约操作: {op}")

    return tensor


def broadcast(
    tensor: torch.Tensor,
    src: int = 0,
) -> torch.Tensor:
    """
    广播操作

    ⭐ 将 src 进程的 tensor 广播到所有进程

    Args:
        tensor: 要广播的 tensor
        src: 源进程 rank

    Returns:
        广播后的 tensor
    """
    if not dist.is_initialized():
        return tensor

    dist.broadcast(tensor, src=src)
    return tensor


def all_gather(
    tensor: torch.Tensor,
) -> list:
    """
    AllGather 操作

    ⭐ 收集所有进程的 tensor

    Args:
        tensor: 要收集的 tensor

    Returns:
        收集到的 tensor 列表
    """
    if not dist.is_initialized():
        return [tensor]

    world_size = get_world_size()
    gathered = [torch.zeros_like(tensor) for _ in range(world_size)]
    dist.all_gather(gathered, tensor)

    return gathered


def reduce_dict(
    data: dict,
    op: str = "mean",
) -> dict:
    """
    对字典中的所有 tensor 进行归约

    Args:
        data: 包含 tensor 的字典
        op: 归约操作

    Returns:
        归约后的字典
    """
    if not dist.is_initialized():
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, torch.Tensor):
            result[key] = all_reduce(value.clone(), op)
        else:
            result[key] = value

    return result
