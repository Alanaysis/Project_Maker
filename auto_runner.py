#!/usr/bin/env python3
"""
自动化项目生成器
端到端执行愿望单中的所有任务
"""

import re
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class Wish:
    """愿望单任务"""
    name: str
    description: str
    learning_goals: List[str]
    tech_stack: Dict[str, str]
    core_loop: str
    references: List[str]
    priority: str
    estimated_time: str
    status: str = "pending"  # pending, in_progress, completed, failed
    error_log: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

@dataclass
class ExecutionLog:
    """执行日志"""
    timestamp: str
    task_name: str
    status: str
    message: str
    details: Optional[Dict] = None

class WishlistParser:
    """愿望单解析器"""

    def __init__(self, wishlist_path: str):
        self.wishlist_path = wishlist_path

    def parse(self) -> List[Wish]:
        """解析愿望单文件"""
        with open(self.wishlist_path, 'r', encoding='utf-8') as f:
            content = f.read()

        wishes = []
        # 解析每个愿望块
        wish_blocks = re.split(r'\n---\n', content)

        for block in wish_blocks:
            if '### [' in block:
                wish = self._parse_wish_block(block)
                if wish:
                    wishes.append(wish)

        return wishes

    def _parse_wish_block(self, block: str) -> Optional[Wish]:
        """解析单个愿望块"""
        try:
            # 提取名称
            name_match = re.search(r'### \[(.+?)\]', block)
            if not name_match:
                return None
            name = name_match.group(1)

            # 提取一句话描述
            desc_match = re.search(r'\*\*一句话描述\*\*：(.+)', block)
            description = desc_match.group(1).strip() if desc_match else ""

            # 提取学习目标
            goals = []
            goals_section = re.search(r'\*\*学习目标\*\*：(.*?)(?=\*\*|\Z)', block, re.DOTALL)
            if goals_section:
                goals = [g.strip().lstrip('- 目标\d+：')
                        for g in goals_section.group(1).strip().split('\n')
                        if g.strip().startswith('-')]

            # 提取技术栈
            tech_stack = {}
            tech_section = re.search(r'\*\*技术栈\*\*：(.*?)(?=\*\*|\Z)', block, re.DOTALL)
            if tech_section:
                for line in tech_section.group(1).strip().split('\n'):
                    if '：' in line:
                        key, value = line.split('：', 1)
                        tech_stack[key.strip().lstrip('- ')] = value.strip()

            # 提取核心循环
            loop_match = re.search(r'\*\*核心循环\*\*：\s*\n```\n(.*?)\n```', block, re.DOTALL)
            core_loop = loop_match.group(1).strip() if loop_match else ""

            # 提取参考项目
            references = []
            ref_section = re.search(r'\*\*参考项目\*\*：(.*?)(?=\*\*|\Z)', block, re.DOTALL)
            if ref_section:
                references = [r.strip() for r in ref_section.group(1).strip().split('\n') if r.strip().startswith('-')]

            # 提取优先级
            priority_match = re.search(r'\*\*优先级\*\*：(P\d)', block)
            priority = priority_match.group(1) if priority_match else "P2"

            # 提取预估时长
            time_match = re.search(r'\*\*预估时长\*\*：(.+)', block)
            estimated_time = time_match.group(1).strip() if time_match else ""

            return Wish(
                name=name,
                description=description,
                learning_goals=goals,
                tech_stack=tech_stack,
                core_loop=core_loop,
                references=references,
                priority=priority,
                estimated_time=estimated_time
            )
        except Exception as e:
            print(f"解析愿望块失败: {e}")
            return None

class ProjectGenerator:
    """项目生成器"""

    def __init__(self, base_dir: str, template_dir: str):
        self.base_dir = Path(base_dir)
        self.template_dir = Path(template_dir)
        self.log_file = self.base_dir / "execution_log.json"
        self.logs: List[ExecutionLog] = []

    def generate_project(self, wish: Wish) -> bool:
        """生成单个项目"""
        try:
            # 创建项目目录
            project_dir = self.base_dir / "projects" / self._to_kebab_case(wish.name)
            project_dir.mkdir(parents=True, exist_ok=True)

            # 复制并填充模板
            self._fill_template(project_dir, wish)

            # 记录成功
            self._log(wish.name, "completed", f"项目 {wish.name} 生成成功")
            return True

        except Exception as e:
            # 记录失败
            self._log(wish.name, "failed", f"项目 {wish.name} 生成失败: {str(e)}")
            return False

    def _to_kebab_case(self, name: str) -> str:
        """转换为 kebab-case"""
        # 移除特殊字符，转换为小写
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '-', name)
        return name.lower().strip('-')

    def _fill_template(self, project_dir: Path, wish: Wish):
        """填充模板"""
        # 这里会调用子代理来实际实现项目
        # 目前只是创建占位文件
        readme_content = f"""# {wish.name}

{wish.description}

## 学习目标
{chr(10).join(f'- {goal}' for goal in wish.learning_goals)}

## 技术栈
{chr(10).join(f'- {k}: {v}' for k, v in wish.tech_stack.items())}

## 核心循环
```
{wish.core_loop}
```

## 参考项目
{chr(10).join(wish.references)}

---
*此项目由自动化生成器创建，等待子代理实现*
"""
        (project_dir / "README.md").write_text(readme_content, encoding='utf-8')

        # 创建其他必要目录
        (project_dir / "docs").mkdir(exist_ok=True)
        (project_dir / "src").mkdir(exist_ok=True)
        (project_dir / "tests").mkdir(exist_ok=True)
        (project_dir / "examples").mkdir(exist_ok=True)

    def _log(self, task_name: str, status: str, message: str, details: Dict = None):
        """记录日志"""
        log = ExecutionLog(
            timestamp=datetime.now().isoformat(),
            task_name=task_name,
            status=status,
            message=message,
            details=details
        )
        self.logs.append(asdict(log))
        self._save_logs()

    def _save_logs(self):
        """保存日志到文件"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)

class AutoRunner:
    """自动化运行器"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.wishlist_path = self.base_dir / "WISHLIST.md"
        self.template_dir = self.base_dir / "_template"
        self.parser = WishlistParser(str(self.wishlist_path))
        self.generator = ProjectGenerator(str(self.base_dir), str(self.template_dir))
        self.state_file = self.base_dir / "runner_state.json"

    def run(self, max_rounds: int = 2):
        """运行自动化流程"""
        print(f"🚀 启动自动化项目生成器")
        print(f"📁 基础目录: {self.base_dir}")
        print(f"📋 愿望单: {self.wishlist_path}")
        print(f"🔄 最大轮数: {max_rounds}")
        print("=" * 50)

        for round_num in range(1, max_rounds + 1):
            print(f"\n{'='*50}")
            print(f"🔄 第 {round_num} 轮开始")
            print(f"{'='*50}")

            # 解析愿望单
            wishes = self.parser.parse()
            print(f"📋 解析到 {len(wishes)} 个任务")

            # 按优先级排序
            wishes.sort(key=lambda w: w.priority)

            # 执行任务
            completed = 0
            failed = 0

            for i, wish in enumerate(wishes, 1):
                print(f"\n[{i}/{len(wishes)}] 🎯 处理任务: {wish.name}")
                print(f"  优先级: {wish.priority}")
                print(f"  预估时长: {wish.estimated_time}")

                # 更新状态
                wish.status = "in_progress"
                wish.start_time = datetime.now().isoformat()

                # 生成项目
                success = self.generator.generate_project(wish)

                if success:
                    wish.status = "completed"
                    wish.end_time = datetime.now().isoformat()
                    completed += 1
                    print(f"  ✅ 完成")
                else:
                    wish.status = "failed"
                    wish.end_time = datetime.now().isoformat()
                    failed += 1
                    print(f"  ❌ 失败")

            # 本轮统计
            print(f"\n{'='*50}")
            print(f"📊 第 {round_num} 轮统计")
            print(f"{'='*50}")
            print(f"  成功: {completed}")
            print(f"  失败: {failed}")
            print(f"  总计: {len(wishes)}")

            # 保存本轮状态
            self._save_round_state(round_num, wishes)

            # 如果不是最后一轮，准备下一轮
            if round_num < max_rounds:
                print(f"\n⏳ 准备第 {round_num + 1} 轮...")
                print("  提示: 下一轮将重新调研，抛弃旧选型")

        print(f"\n{'='*50}")
        print("🎉 所有轮次完成!")
        print(f"{'='*50}")

    def _save_round_state(self, round_num: int, wishes: List[Wish]):
        """保存轮次状态"""
        state = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "tasks": [
                {
                    "name": w.name,
                    "status": w.status,
                    "priority": w.priority,
                    "start_time": w.start_time,
                    "end_time": w.end_time,
                    "error_log": w.error_log
                }
                for w in wishes
            ]
        }

        state_file = self.base_dir / f"round_{round_num}_state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    base_dir = Path(__file__).parent
    runner = AutoRunner(str(base_dir))
    runner.run(max_rounds=2)

if __name__ == "__main__":
    main()
