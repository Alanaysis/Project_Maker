"""
因子报告模块

生成因子研究报告，包括因子分析结果、图表数据和投资建议。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime


class FactorReport:
    """
    因子报告生成器

    生成结构化的因子分析报告。

    使用示例:
        >>> report = FactorReport()
        >>> report.add_section("IC分析", ic_results)
        >>> report.generate("output/report.md")
    """

    def __init__(self, title: str = "因子分析报告"):
        """
        初始化报告生成器

        参数:
            title: 报告标题
        """
        self.title = title
        self.sections = []
        self.created_at = datetime.now()

    def add_section(self, title: str, content: Dict):
        """
        添加报告章节

        参数:
            title: 章节标题
            content: 章节内容 (字典)
        """
        self.sections.append({"title": title, "content": content})

    def add_factor_overview(self, factor_name: str,
                             category: str,
                             description: str,
                             metrics: Dict):
        """
        添加因子概览

        参数:
            factor_name: 因子名称
            category: 因子类别
            description: 因子描述
            metrics: 因子指标
        """
        self.add_section(f"因子概览: {factor_name}", {
            "category": category,
            "description": description,
            "metrics": metrics,
        })

    def add_ic_analysis(self, ic_summary: Dict):
        """
        添加 IC 分析结果

        参数:
            ic_summary: IC 分析摘要
        """
        self.add_section("IC 分析", ic_summary)

    def add_group_backtest(self, group_stats: pd.DataFrame,
                            monotonicity: float):
        """
        添加分组回测结果

        参数:
            group_stats: 分组统计
            monotonicity: 单调性指标
        """
        self.add_section("分组回测", {
            "group_stats": group_stats.to_dict(),
            "monotonicity": monotonicity,
        })

    def add_comparison(self, comparison_df: pd.DataFrame):
        """
        添加多因子对比

        参数:
            comparison_df: 因子对比 DataFrame
        """
        self.add_section("多因子对比", {
            "comparison": comparison_df.to_dict(),
        })

    def generate_text(self) -> str:
        """
        生成文本格式报告

        返回:
            报告文本
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"  {self.title}")
        lines.append(f"  生成时间: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)

        for i, section in enumerate(self.sections, 1):
            lines.append(f"\n{'─' * 60}")
            lines.append(f"  {i}. {section['title']}")
            lines.append(f"{'─' * 60}")

            content = section["content"]
            if isinstance(content, dict):
                for key, value in content.items():
                    if isinstance(value, dict):
                        lines.append(f"\n  {key}:")
                        for k, v in value.items():
                            if isinstance(v, float):
                                lines.append(f"    {k}: {v:.4f}")
                            else:
                                lines.append(f"    {k}: {v}")
                    elif isinstance(value, float):
                        lines.append(f"  {key}: {value:.4f}")
                    else:
                        lines.append(f"  {key}: {value}")

        lines.append(f"\n{'=' * 60}")
        lines.append("  报告结束")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_markdown(self) -> str:
        """
        生成 Markdown 格式报告

        返回:
            Markdown 格式报告文本
        """
        lines = []
        lines.append(f"# {self.title}")
        lines.append(f"\n*生成时间: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}*\n")

        for i, section in enumerate(self.sections, 1):
            lines.append(f"## {i}. {section['title']}\n")
            content = section["content"]

            if isinstance(content, dict):
                lines.append("| 指标 | 值 |")
                lines.append("|------|-----|")
                for key, value in content.items():
                    if isinstance(value, dict):
                        lines.append(f"\n### {key}\n")
                        lines.append("| 指标 | 值 |")
                        lines.append("|------|-----|")
                        for k, v in value.items():
                            if isinstance(v, float):
                                lines.append(f"| {k} | {v:.4f} |")
                            else:
                                lines.append(f"| {k} | {v} |")
                    elif isinstance(value, float):
                        lines.append(f"| {key} | {value:.4f} |")
                    else:
                        lines.append(f"| {key} | {value} |")
                lines.append("")

        return "\n".join(lines)

    def generate(self, filepath: str, format: str = "text"):
        """
        生成并保存报告

        参数:
            filepath: 输出文件路径
            format: 输出格式 ("text" 或 "markdown")
        """
        if format == "markdown":
            content = self.generate_markdown()
        else:
            content = self.generate_text()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"报告已保存到: {filepath}")

    @staticmethod
    def generate_factor_card(factor_name: str,
                              metrics: Dict) -> str:
        """
        生成因子卡片 (简短摘要)

        参数:
            factor_name: 因子名称
            metrics: 因子指标

        返回:
            因子卡片文本
        """
        grade = metrics.get("overall_score", {}).get("grade", "N/A")
        ic_mean = metrics.get("ic_summary", {}).get("ic_mean", 0)
        ir = metrics.get("ir", 0)
        monotonicity = metrics.get("monotonicity", 0)

        card = f"""
┌─────────────────────────────────────┐
│  因子: {factor_name:<29}│
│  评级: {grade:<29}│
│  IC:   {ic_mean:<29.4f}│
│  IR:   {ir:<29.4f}│
│  单调: {monotonicity:<29.4f}│
└─────────────────────────────────────┘"""
        return card
