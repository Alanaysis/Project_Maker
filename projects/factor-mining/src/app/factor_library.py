"""
因子库管理模块

管理因子的注册、存储、查询和版本控制。
"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List


class FactorLibrary:
    """
    因子库管理器

    管理因子的元数据、存储和查询。

    使用示例:
        >>> library = FactorLibrary("./factor_library")
        >>> library.register("momentum_20d", category="technical", description="20日动量")
        >>> library.save("momentum_20d", factor_data)
        >>> factor = library.load("momentum_20d")
    """

    def __init__(self, library_path: str = "./factor_library"):
        """
        初始化因子库

        参数:
            library_path: 因子库存储路径
        """
        self.library_path = library_path
        self.metadata_file = os.path.join(library_path, "metadata.json")
        os.makedirs(library_path, exist_ok=True)
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """加载因子库元数据"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {"factors": {}, "version": "1.0"}

    def _save_metadata(self):
        """保存因子库元数据"""
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2, default=str)

    def register(self, name: str, category: str = "custom",
                 description: str = "", author: str = "",
                 tags: Optional[List[str]] = None) -> Dict:
        """
        注册新因子

        参数:
            name: 因子名称 (唯一标识)
            category: 因子类别 ("technical", "fundamental", "alternative", "custom")
            description: 因子描述
            author: 作者
            tags: 标签列表

        返回:
            因子注册信息
        """
        if name in self.metadata["factors"]:
            print(f"Warning: Factor '{name}' already exists. Updating metadata.")

        factor_info = {
            "name": name,
            "category": category,
            "description": description,
            "author": author,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "status": "registered",
        }

        self.metadata["factors"][name] = factor_info
        self._save_metadata()
        return factor_info

    def save(self, name: str, data: pd.DataFrame,
             overwrite: bool = False):
        """
        保存因子数据

        参数:
            name: 因子名称
            data: 因子数据 DataFrame
            overwrite: 是否覆盖已有数据
        """
        filepath = os.path.join(self.library_path, f"{name}.parquet")

        if os.path.exists(filepath) and not overwrite:
            raise FileExistsError(f"Factor '{name}' already exists. Use overwrite=True.")

        data.to_parquet(filepath)

        if name in self.metadata["factors"]:
            self.metadata["factors"][name]["updated_at"] = datetime.now().isoformat()
            self.metadata["factors"][name]["version"] += 1
            self.metadata["factors"][name]["rows"] = len(data)
            self.metadata["factors"][name]["columns"] = list(data.columns)
            self.metadata["factors"][name]["status"] = "active"
            self._save_metadata()

    def load(self, name: str) -> pd.DataFrame:
        """
        加载因子数据

        参数:
            name: 因子名称

        返回:
            因子数据 DataFrame
        """
        filepath = os.path.join(self.library_path, f"{name}.parquet")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Factor '{name}' not found.")
        return pd.read_parquet(filepath)

    def list_factors(self, category: Optional[str] = None,
                      status: Optional[str] = None) -> pd.DataFrame:
        """
        列出所有因子

        参数:
            category: 按类别筛选
            status: 按状态筛选

        返回:
            因子信息 DataFrame
        """
        factors = list(self.metadata["factors"].values())
        df = pd.DataFrame(factors)

        if df.empty:
            return df

        if category:
            df = df[df["category"] == category]
        if status:
            df = df[df["status"] == status]

        return df

    def get_info(self, name: str) -> Dict:
        """
        获取因子信息

        参数:
            name: 因子名称

        返回:
            因子元数据字典
        """
        if name not in self.metadata["factors"]:
            raise KeyError(f"Factor '{name}' not found in library.")
        return self.metadata["factors"][name]

    def delete(self, name: str):
        """
        删除因子

        参数:
            name: 因子名称
        """
        filepath = os.path.join(self.library_path, f"{name}.parquet")
        if os.path.exists(filepath):
            os.remove(filepath)

        if name in self.metadata["factors"]:
            del self.metadata["factors"][name]
            self._save_metadata()

    def search(self, keyword: str) -> pd.DataFrame:
        """
        搜索因子

        参数:
            keyword: 搜索关键词

        返回:
            匹配的因子信息 DataFrame
        """
        factors = list(self.metadata["factors"].values())
        results = []
        for f in factors:
            if (keyword.lower() in f["name"].lower() or
                keyword.lower() in f["description"].lower() or
                keyword.lower() in " ".join(f["tags"]).lower()):
                results.append(f)
        return pd.DataFrame(results)
