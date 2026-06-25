"""
TTL (Time-To-Live) 管理模块

实现数据过期和自动清理功能。
"""

import time
import threading
import logging
from typing import Dict, Optional, Callable, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class TTLConfig:
    """TTL 配置"""

    def __init__(self, metric: str, ttl_seconds: int):
        """
        初始化 TTL 配置

        Args:
            metric: 指标名称
            ttl_seconds: TTL 时间（秒）
        """
        self.metric = metric
        self.ttl_seconds = ttl_seconds
        self.created_at = int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'metric': self.metric,
            'ttl_seconds': self.ttl_seconds,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TTLConfig':
        """从字典创建"""
        config = cls(data['metric'], data['ttl_seconds'])
        config.created_at = data.get('created_at', int(time.time()))
        return config


class TTLManager:
    """
    TTL 管理器

    功能:
    - 设置全局默认 TTL
    - 设置 metric 级别 TTL
    - 后台自动清理过期数据
    - 手动触发清理
    """

    def __init__(
        self,
        storage_engine: Any,
        default_ttl: Optional[int] = None,
        cleanup_interval: int = 3600,
        config_file: Optional[str] = None
    ):
        """
        初始化 TTL 管理器

        Args:
            storage_engine: 存储引擎实例
            default_ttl: 默认 TTL（秒），None 表示不过期
            cleanup_interval: 清理间隔（秒）
            config_file: 配置文件路径
        """
        self.storage = storage_engine
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self.config_file = config_file

        # Metric 级别 TTL 配置
        self.ttl_configs: Dict[str, TTLConfig] = {}

        # 清理线程
        self.cleanup_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.Lock()

        # 回调函数
        self.on_cleanup: Optional[Callable] = None

        # 加载配置
        if config_file:
            self._load_config()

    def set_ttl(self, metric: str, ttl_seconds: int) -> None:
        """
        设置 metric 级别 TTL

        Args:
            metric: 指标名称
            ttl_seconds: TTL 时间（秒）
        """
        with self.lock:
            self.ttl_configs[metric] = TTLConfig(metric, ttl_seconds)
            self._save_config()
            logger.info(f"Set TTL for metric '{metric}': {ttl_seconds}s")

    def get_ttl(self, metric: str) -> Optional[int]:
        """
        获取 metric 的 TTL

        Args:
            metric: 指标名称

        Returns:
            Optional[int]: TTL 时间（秒），None 表示不过期
        """
        with self.lock:
            if metric in self.ttl_configs:
                return self.ttl_configs[metric].ttl_seconds
            return self.default_ttl

    def remove_ttl(self, metric: str) -> None:
        """
        移除 metric 级别 TTL

        Args:
            metric: 指标名称
        """
        with self.lock:
            if metric in self.ttl_configs:
                del self.ttl_configs[metric]
                self._save_config()
                logger.info(f"Removed TTL for metric '{metric}'")

    def list_configs(self) -> Dict[str, int]:
        """
        列出所有 TTL 配置

        Returns:
            Dict[str, int]: {metric: ttl_seconds}
        """
        with self.lock:
            configs = {}
            if self.default_ttl is not None:
                configs['__default__'] = self.default_ttl
            for metric, config in self.ttl_configs.items():
                configs[metric] = config.ttl_seconds
            return configs

    def start(self) -> None:
        """启动自动清理线程"""
        if self.running:
            return

        self.running = True
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True
        )
        self.cleanup_thread.start()
        logger.info(f"Started TTL cleanup thread, interval: {self.cleanup_interval}s")

    def stop(self) -> None:
        """停止自动清理线程"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
            self.cleanup_thread = None
        logger.info("Stopped TTL cleanup thread")

    def cleanup(self, metric: Optional[str] = None) -> int:
        """
        执行清理

        Args:
            metric: 指定 metric 清理，None 表示清理所有

        Returns:
            int: 清理的数据点数量
        """
        total_cleaned = 0
        current_time = int(time.time())

        with self.lock:
            metrics_to_clean = []

            if metric:
                # 清理指定 metric
                if metric in self.ttl_configs:
                    metrics_to_clean.append((metric, self.ttl_configs[metric].ttl_seconds))
                elif self.default_ttl is not None:
                    metrics_to_clean.append((metric, self.default_ttl))
            else:
                # 清理所有 metric
                for m, config in self.ttl_configs.items():
                    metrics_to_clean.append((m, config.ttl_seconds))

                # 如果有默认 TTL，清理所有没有单独配置的 metric
                if self.default_ttl is not None:
                    all_metrics = self._get_all_metrics()
                    for m in all_metrics:
                        if m not in self.ttl_configs:
                            metrics_to_clean.append((m, self.default_ttl))

        # 执行清理
        for m, ttl in metrics_to_clean:
            cutoff_time = current_time - ttl
            cleaned = self.storage.delete_before(m, cutoff_time)
            if cleaned > 0:
                logger.info(f"Cleaned {cleaned} expired points for metric '{m}'")
                total_cleaned += cleaned

        # 触发回调
        if self.on_cleanup and total_cleaned > 0:
            self.on_cleanup(total_cleaned)

        return total_cleaned

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'default_ttl': self.default_ttl,
            'metric_configs': len(self.ttl_configs),
            'cleanup_interval': self.cleanup_interval,
            'running': self.running,
            'configs': self.list_configs(),
        }

    def _cleanup_worker(self) -> None:
        """清理工作线程"""
        while self.running:
            try:
                self.cleanup()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

            # 等待下次清理
            for _ in range(self.cleanup_interval):
                if not self.running:
                    break
                time.sleep(1)

    def _get_all_metrics(self) -> list:
        """获取所有 metric 名称"""
        metrics = set()

        # 从 SSTable 元数据获取
        for metric in self.storage.sstables.keys():
            metrics.add(metric)

        # 从 MemTable 获取
        data = self.storage.memtable.get_all()
        for metric, _, _, _ in data:
            metrics.add(metric)

        return list(metrics)

    def _load_config(self) -> None:
        """加载配置文件"""
        if not self.config_file:
            return

        config_path = Path(self.config_file)
        if not config_path.exists():
            return

        try:
            with open(config_path, 'r') as f:
                data = json.load(f)

            self.default_ttl = data.get('default_ttl')
            for metric, config_data in data.get('metrics', {}).items():
                self.ttl_configs[metric] = TTLConfig.from_dict(config_data)

            logger.info(f"Loaded TTL config from {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load TTL config: {e}")

    def _save_config(self) -> None:
        """保存配置文件"""
        if not self.config_file:
            return

        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'default_ttl': self.default_ttl,
            'metrics': {
                metric: config.to_dict()
                for metric, config in self.ttl_configs.items()
            }
        }

        try:
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved TTL config to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save TTL config: {e}")


class RetentionPolicy:
    """
    数据保留策略

    支持多种保留策略:
    - 按时间保留
    - 按大小保留
    - 按条目数量保留
    """

    def __init__(
        self,
        max_age_seconds: Optional[int] = None,
        max_size_bytes: Optional[int] = None,
        max_entries: Optional[int] = None
    ):
        """
        初始化保留策略

        Args:
            max_age_seconds: 最大保留时间（秒）
            max_size_bytes: 最大存储大小（字节）
            max_entries: 最大条目数量
        """
        self.max_age_seconds = max_age_seconds
        self.max_size_bytes = max_size_bytes
        self.max_entries = max_entries

    def should_cleanup(self, stats: Dict[str, Any]) -> bool:
        """
        检查是否需要清理

        Args:
            stats: 当前统计信息

        Returns:
            bool: 是否需要清理
        """
        if self.max_age_seconds:
            # 检查是否有过期数据
            return True

        if self.max_size_bytes and stats.get('total_size', 0) > self.max_size_bytes:
            return True

        if self.max_entries and stats.get('total_entries', 0) > self.max_entries:
            return True

        return False

    def get_cleanup_params(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取清理参数

        Args:
            stats: 当前统计信息

        Returns:
            Dict[str, Any]: 清理参数
        """
        params = {}

        if self.max_age_seconds:
            params['before_timestamp'] = int(time.time()) - self.max_age_seconds

        if self.max_size_bytes:
            # 计算需要清理的大小
            excess = stats.get('total_size', 0) - self.max_size_bytes
            if excess > 0:
                params['target_size'] = self.max_size_bytes

        if self.max_entries:
            excess = stats.get('total_entries', 0) - self.max_entries
            if excess > 0:
                params['target_entries'] = self.max_entries

        return params
