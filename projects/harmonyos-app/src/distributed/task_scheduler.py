"""
任务调度 - Task Scheduler

模拟鸿蒙的分布式任务调度能力：
- 跨设备任务分发
- 设备能力评估
- 任务迁移
- 负载均衡
"""

import time
import random
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from .device_manager import DeviceInfo


@dataclass
class Task:
    """
    分布式任务

    鸿蒙分布式任务调度：
    - 任务定义（名称、类型、资源需求）
    - 任务状态（pending, running, completed, failed）
    - 任务迁移记录
    """
    task_id: str
    name: str
    task_type: str = 'compute'  # compute, io, display, audio, video
    required_capabilities: Dict[str, Any] = field(default_factory=dict)
    status: str = 'pending'
    assigned_device: Optional[str] = None
    result: Any = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    migration_count: int = 0

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'task_type': self.task_type,
            'status': self.status,
            'assigned_device': self.assigned_device,
            'migration_count': self.migration_count,
        }


class DistributedTaskScheduler:
    """
    分布式任务调度器

    模拟鸿蒙分布式任务调度核心：
    1. 设备能力发现
    2. 任务匹配
    3. 任务分发
    4. 任务迁移
    5. 负载均衡
    """

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._task_counter = 0

    def create_task(self, name: str, task_type: str = 'compute',
                    requirements: Optional[Dict] = None) -> Task:
        """创建新任务"""
        self._task_counter += 1
        task = Task(
            task_id=f'task_{self._task_counter:04d}',
            name=name,
            task_type=task_type,
            required_capabilities=requirements or {},
        )
        self._tasks[task.task_id] = task
        return task

    def schedule_task(self, task_id: str, available_devices: List[DeviceInfo]) -> Optional[str]:
        """
        调度任务到合适的设备

        调度策略：
        1. 检查设备能力是否满足任务需求
        2. 选择负载最低的设备
        3. 记录调度结果
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        # 过滤符合条件的设备
        suitable_devices = []
        for device in available_devices:
            if not device.is_online:
                continue

            # 检查设备能力
            if task.required_capabilities:
                capable = True
                for cap, min_val in task.required_capabilities.items():
                    device_val = device.capabilities.get(cap, 0)
                    if device_val < min_val:
                        capable = False
                        break
                if not capable:
                    continue

            # 计算设备负载（基于已分配任务数）
            load = sum(1 for t in self._tasks.values()
                       if t.assigned_device == device.device_id and t.status == 'running')
            suitable_devices.append((device, load))

        if not suitable_devices:
            return None

        # 选择负载最低的设备
        suitable_devices.sort(key=lambda x: x[1])
        chosen_device = suitable_devices[0][0]

        # 分配任务
        task.status = 'running'
        task.assigned_device = chosen_device.device_id
        return chosen_device.device_id

    def migrate_task(self, task_id: str, target_device: DeviceInfo) -> bool:
        """
        迁移任务到目标设备

        模拟鸿蒙应用迁移：
        1. 保存当前状态
        2. 传输状态到目标设备
        3. 在目标设备恢复
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.assigned_device == target_device.device_id:
            return True

        old_device = task.assigned_device
        task.assigned_device = target_device.device_id
        task.migration_count += 1

        return True

    def complete_task(self, task_id: str, result: Any = None) -> bool:
        """完成任务"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        task.status = 'completed'
        task.result = result
        task.completed_at = time.time()
        return True

    def fail_task(self, task_id: str, error: str = '') -> bool:
        """任务失败"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        task.status = 'failed'
        task.completed_at = time.time()
        return True

    def get_task_stats(self) -> Dict[str, int]:
        """获取任务统计"""
        stats = {'pending': 0, 'running': 0, 'completed': 0, 'failed': 0}
        for task in self._tasks.values():
            if task.status in stats:
                stats[task.status] += 1
        return stats

    def get_device_load(self, device_id: str) -> int:
        """获取设备负载（运行中的任务数）"""
        return sum(1 for t in self._tasks.values()
                   if t.assigned_device == device_id and t.status == 'running')

    def get_all_tasks(self) -> List[Task]:
        return list(self._tasks.values())

    def __repr__(self):
        stats = self.get_task_stats()
        return f'DistributedTaskScheduler(tasks={len(self._tasks)} {stats})'
