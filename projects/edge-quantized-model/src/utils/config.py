"""
配置管理模块

提供配置文件的加载和保存功能
"""

import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_config(
    config_path: str,
    config_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径
        config_type: 配置类型（'json' 或 'yaml'），如果为 None 则自动检测

    Returns:
        配置字典
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    # 自动检测类型
    if config_type is None:
        if path.suffix in ['.yaml', '.yml']:
            config_type = 'yaml'
        elif path.suffix == '.json':
            config_type = 'json'
        else:
            raise ValueError(f"无法识别配置文件类型: {path.suffix}")

    # 加载配置
    with open(path, 'r', encoding='utf-8') as f:
        if config_type == 'yaml':
            config = yaml.safe_load(f)
        elif config_type == 'json':
            config = json.load(f)
        else:
            raise ValueError(f"不支持的配置类型: {config_type}")

    logger.info(f"加载配置: {config_path}")
    return config


def save_config(
    config: Dict[str, Any],
    config_path: str,
    config_type: Optional[str] = None,
):
    """
    保存配置文件

    Args:
        config: 配置字典
        config_path: 配置文件路径
        config_type: 配置类型（'json' 或 'yaml'），如果为 None 则自动检测
    """
    path = Path(config_path)

    # 自动检测类型
    if config_type is None:
        if path.suffix in ['.yaml', '.yml']:
            config_type = 'yaml'
        elif path.suffix == '.json':
            config_type = 'json'
        else:
            raise ValueError(f"无法识别配置文件类型: {path.suffix}")

    # 创建目录
    path.parent.mkdir(parents=True, exist_ok=True)

    # 保存配置
    with open(path, 'w', encoding='utf-8') as f:
        if config_type == 'yaml':
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        elif config_type == 'json':
            json.dump(config, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的配置类型: {config_type}")

    logger.info(f"保存配置: {config_path}")


def merge_configs(
    base_config: Dict[str, Any],
    override_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    合并配置

    Args:
        base_config: 基础配置
        override_config: 覆盖配置

    Returns:
        合并后的配置
    """
    merged = base_config.copy()

    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value

    return merged


def validate_config(
    config: Dict[str, Any],
    schema: Dict[str, Any],
) -> list:
    """
    验证配置

    Args:
        config: 配置字典
        schema: 配置模式

    Returns:
        错误列表
    """
    errors = []

    for key, expected_type in schema.items():
        if key not in config:
            errors.append(f"缺少必填字段: {key}")
        elif not isinstance(config[key], expected_type):
            errors.append(f"字段 {key} 类型错误: 期望 {expected_type.__name__}，实际 {type(config[key]).__name__}")

    return errors
