"""
信号追踪模块

实现信号追踪和波形显示。
"""

from typing import Dict, List, Optional
import io


class SignalTrace:
    """信号追踪器

    记录和显示信号波形。

    Examples:
        >>> trace = SignalTrace()
        >>> trace.add_signal("CLK", [0, 1, 0, 1, 0, 1, 0, 1])
        >>> trace.add_signal("DATA", [0, 0, 1, 1, 0, 0, 1, 1])
        >>> print(trace.to_waveform())
        CLK:  _-_-_-_
        DATA: __--__--
    """

    def __init__(self):
        """初始化信号追踪器"""
        self._signals: Dict[str, List[int]] = {}
        self._time_range: Optional[tuple] = None

    def add_signal(self, name: str, values: List[int]):
        """添加信号

        Args:
            name: 信号名称
            values: 信号值列表
        """
        self._signals[name] = values

    def set_time_range(self, start: int, end: int):
        """设置时间范围

        Args:
            start: 开始时间
            end: 结束时间
        """
        self._time_range = (start, end)

    def to_waveform(self, width: int = 80) -> str:
        """生成波形图

        Args:
            width: 显示宽度

        Returns:
            str: 波形图字符串
        """
        if not self._signals:
            return ""

        # 确定时间范围
        max_length = max(len(values) for values in self._signals.values())
        if self._time_range:
            start, end = self._time_range
        else:
            start, end = 0, max_length

        # 计算缩放比例
        time_range = end - start
        if time_range == 0:
            return ""

        scale = width / time_range

        # 生成波形
        output = io.StringIO()

        # 时间刻度
        time_line = "Time: "
        for t in range(start, end, max(1, time_range // 10)):
            pos = int((t - start) * scale)
            time_line += f"{t:^5}"
        output.write(time_line + "\n")
        output.write("-" * (len(time_line) + 10) + "\n")

        # 每个信号的波形
        for name, values in self._signals.items():
            # 信号名称
            line = f"{name:>8}: "

            # 生成波形
            prev_value = 0
            for t in range(start, end):
                if t < len(values):
                    value = values[t]
                else:
                    value = prev_value

                # 绘制波形
                if value == 1:
                    if prev_value == 0:
                        line += "/"  # 上升沿
                    else:
                        line += "-"  # 高电平
                else:
                    if prev_value == 1:
                        line += "\\"  # 下降沿
                    else:
                        line += "_"  # 低电平

                prev_value = value

            output.write(line + "\n")

        return output.getvalue()

    def to_ascii_art(self, width: int = 80, height: int = 20) -> str:
        """生成ASCII艺术波形图

        Args:
            width: 显示宽度
            height: 显示高度

        Returns:
            str: ASCII艺术波形图
        """
        if not self._signals:
            return ""

        # 确定时间范围
        max_length = max(len(values) for values in self._signals.values())
        if self._time_range:
            start, end = self._time_range
        else:
            start, end = 0, max_length

        # 计算缩放比例
        time_range = end - start
        if time_range == 0:
            return ""

        scale_x = width / time_range
        scale_y = height / len(self._signals)

        # 创建画布
        canvas = [[' ' for _ in range(width)] for _ in range(height)]

        # 绘制每个信号
        for sig_idx, (name, values) in enumerate(self._signals.items()):
            y_pos = int(sig_idx * scale_y)

            prev_value = 0
            for t in range(start, end):
                if t < len(values):
                    value = values[t]
                else:
                    value = prev_value

                x_pos = int((t - start) * scale_x)
                if x_pos < width:
                    if value == 1:
                        canvas[y_pos][x_pos] = '-'
                        if y_pos + 1 < height:
                            canvas[y_pos + 1][x_pos] = '|'
                    else:
                        canvas[y_pos][x_pos] = '_'

                prev_value = value

        # 转换为字符串
        output = io.StringIO()
        for row in canvas:
            output.write(''.join(row) + '\n')

        return output.getvalue()

    def get_signal(self, name: str) -> List[int]:
        """获取信号值

        Args:
            name: 信号名称

        Returns:
            List[int]: 信号值列表
        """
        return self._signals.get(name, [])

    def get_value_at_time(self, name: str, time: int) -> int:
        """获取指定时间的信号值

        Args:
            name: 信号名称
            time: 时间

        Returns:
            int: 信号值
        """
        values = self._signals.get(name, [])
        if time < len(values):
            return values[time]
        return 0

    def get_transitions(self, name: str) -> List[tuple]:
        """获取信号转换

        Args:
            name: 信号名称

        Returns:
            List[tuple]: [(时间, 旧值, 新值), ...]
        """
        values = self._signals.get(name, [])
        transitions = []

        for i in range(1, len(values)):
            if values[i] != values[i - 1]:
                transitions.append((i, values[i - 1], values[i]))

        return transitions

    def clear(self):
        """清除所有信号"""
        self._signals.clear()
        self._time_range = None

    def export_csv(self) -> str:
        """导出为CSV格式

        Returns:
            str: CSV字符串
        """
        if not self._signals:
            return ""

        # 获取最大长度
        max_length = max(len(values) for values in self._signals.values())

        # 生成CSV
        output = io.StringIO()

        # 表头
        headers = ["Time"] + list(self._signals.keys())
        output.write(",".join(headers) + "\n")

        # 数据行
        for t in range(max_length):
            row = [str(t)]
            for name in self._signals:
                values = self._signals[name]
                if t < len(values):
                    row.append(str(values[t]))
                else:
                    row.append("")
            output.write(",".join(row) + "\n")

        return output.getvalue()

    def export_vcd(self) -> str:
        """导出为VCD (Value Change Dump) 格式

        Returns:
            str: VCD字符串
        """
        if not self._signals:
            return ""

        output = io.StringIO()

        # VCD 头
        output.write("$date\n")
        output.write("    Generated by Logic Gates Simulator\n")
        output.write("$end\n")
        output.write("$version\n")
        output.write("    1.0.0\n")
        output.write("$end\n")
        output.write("$timescale 1ns $end\n")
        output.write("$scope module top $end\n")

        # 信号定义
        for i, name in enumerate(self._signals.keys()):
            output.write(f"$var wire 1 {chr(65 + i)} {name} $end\n")

        output.write("$upscope $end\n")
        output.write("$enddefinitions $end\n")
        output.write("$dumpvars\n")

        # 初始值
        for i, (name, values) in enumerate(self._signals.items()):
            if values:
                output.write(f"{values[0]}{chr(65 + i)}\n")

        output.write("$end\n")

        # 值变化
        max_length = max(len(values) for values in self._signals.values())
        for t in range(max_length):
            changes = []
            for i, (name, values) in enumerate(self._signals.items()):
                if t < len(values):
                    if t == 0 or values[t] != values[t - 1]:
                        changes.append(f"{values[t]}{chr(65 + i)}")

            if changes:
                output.write(f"#{t}\n")
                for change in changes:
                    output.write(change + "\n")

        return output.getvalue()
