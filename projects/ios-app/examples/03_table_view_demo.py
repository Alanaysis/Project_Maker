"""
示例 3: 表格视图演示
Table View Demo

演示 UITableView 的数据源和代理模式。
"""

import sys
sys.path.insert(0, "/home/siok/project_copyninja/projects/ios-app")

from src.ui import (
    UITableView, UITableViewStyle,
    UIView, UILabel, UIButton, UIImageView,
    UIViewController,
)


class MockDataSource:
    """模拟数据源 - 实现 UITableViewDataSource 协议"""

    def __init__(self, items):
        self.items = items

    def numberOfSections(self, tableView):
        return 1

    def numberOfRowsInSection(self, tableView, section):
        return len(self.items)

    def cellForRowAtIndexPath(self, tableView, indexPath):
        section, row = indexPath
        item = self.items[row]
        return self._create_cell(item, row)

    def _create_cell(self, item, row):
        """创建单元格"""
        cell = UIView(frame=(0, row * 44, 375, 44))
        cell._background_color = "#FFFFFF"

        # 标题标签
        title_label = UILabel(frame=(16, 10, 250, 24))
        title_label.text = item.get("title", "未知")
        title_label._font_size = 16
        title_label._text_color = "#000000"
        cell.add_subview(title_label)

        # 副标题标签
        subtitle_label = UILabel(frame=(16, 30, 250, 12))
        subtitle_label.text = item.get("subtitle", "")
        subtitle_label._font_size = 12
        subtitle_label._text_color = "#999999"
        cell.add_subview(subtitle_label)

        # 右侧箭头
        arrow = UILabel(frame=(340, 14, 20, 16))
        arrow.text = "›"
        arrow._font_size = 18
        arrow._text_color = "#CCCCCC"
        cell.add_subview(arrow)

        return cell


class GroupedDataSource:
    """分区数据源 - 模拟分组表格"""

    def __init__(self, sections_data):
        self.sections_data = sections_data

    def numberOfSections(self, tableView):
        return len(self.sections_data)

    def numberOfRowsInSection(self, tableView, section):
        return len(self.sections_data[section])

    def cellForRowAtIndexPath(self, tableView, indexPath):
        section, row = indexPath
        item = self.sections_data[section][row]
        return self._create_cell(item, section, row)

    def _create_cell(self, item, section, row):
        cell = UIView(frame=(0, row * 44, 375, 44))
        cell._background_color = "#FFFFFF"

        label = UILabel(frame=(16, 12, 300, 20))
        label.text = item
        label._font_size = 16
        cell.add_subview(label)

        return cell

    def sectionHeaderTitle(self, section):
        titles = ["个人设置", "通用设置", "关于"]
        return titles[section] if section < len(titles) else ""


class TableDelegate:
    """表格代理 - 实现 UITableViewDelegate 协议"""

    def tableView_didSelectRowAtIndexPath(self, tableView, indexPath):
        section, row = indexPath
        print(f"[TableDelegate] 选择行: section={section}, row={row}")

    def tableView_didChange(self, tableView, indexPath, value):
        print(f"[TableDelegate] 行变化: section={section}, row={row}, value={value}")


def demo_plain_table():
    """演示普通表格"""
    print("=" * 60)
    print("  表格视图演示 (Table View Demo)")
    print("=" * 60 + "\n")

    # 1. 创建表格
    table = UITableView(frame=(0, 0, 375, 667), style=UITableViewStyle.PLAIN)
    table.name = "MainTable"
    print(f"创建表格: style={table._style.value}")

    # 2. 准备数据
    items = [
        {"title": "账户设置", "subtitle": "管理你的账户信息"},
        {"title": "消息通知", "subtitle": "配置消息提醒方式"},
        {"title": "隐私与安全", "subtitle": "隐私政策和数据保护"},
        {"title": "主题与外观", "subtitle": "切换深色/浅色模式"},
        {"title": "帮助与反馈", "subtitle": "获取帮助或提交反馈"},
        {"title": "关于应用", "subtitle": "版本信息和许可证"},
    ]

    data_source = MockDataSource(items)
    delegate = TableDelegate()

    table.data_source = data_source
    table.delegate = delegate
    table.reload_data()

    # 3. 展示表格内容
    print(f"\n表格内容 ({table.number_of_sections()} 个分区):")
    for section in range(table.number_of_sections()):
        num_rows = table.number_of_rows_in_section(section)
        print(f"  分区 {section}: {num_rows} 行")
        for row in range(num_rows):
            cell = table.get_cell_at(section, row)
            if cell:
                title_label = cell.viewWithTag(0)
                print(f"    [{row}] {cell._subviews[0]._text if cell._subviews else 'N/A'}")

    # 4. 模拟选择行
    print("\n模拟交互:")
    table.select_row(0, 0)
    table.select_row(2, 3)
    table.select_row(5, 5)

    print(f"\n当前选中: {table.selected_row}")

    return table


def demo_grouped_table():
    """演示分组表格"""
    print("\n" + "=" * 60)
    print("  分组表格演示 (Grouped Table View)")
    print("=" * 60 + "\n")

    # 创建分组表格
    table = UITableView(frame=(0, 0, 375, 667), style=UITableViewStyle.GROUPED)
    table.name = "SettingsTable"

    # 准备分区数据
    sections_data = [
        ["账户设置", "头像修改", "密码修改"],
        ["通用设置", "语言", "字体大小", "夜间模式"],
        ["关于", "版本信息", "用户协议", "隐私政策"],
    ]

    data_source = GroupedDataSource(sections_data)
    table.data_source = data_source
    table.reload_data()

    # 展示分区内容
    print("分区内容:")
    for section in range(table.number_of_sections()):
        header = data_source.sectionHeaderTitle(section)
        print(f"\n  【{header}】")
        for row in range(table.number_of_rows_in_section(section)):
            cell = table.get_cell_at(section, row)
            if cell and cell._subviews:
                label = cell._subviews[0]
                print(f"    - {label._text}")

    return table


def demo_table_view_controller():
    """演示 UITableViewController"""
    print("\n" + "=" * 60)
    print("  UITableViewController 演示")
    print("=" * 60 + "\n")

    # 创建视图控制器
    class TableViewController(UIViewController):
        def __init__(self):
            super().__init__(title="用户列表")
            self.table = UITableView(frame=(0, 0, 375, 667))
            self.table.name = "UserTable"

        def view_did_load(self):
            super().view_did_load()

            # 模拟用户数据
            users = [
                {"title": "张三", "subtitle": "zhangsan@example.com"},
                {"title": "李四", "subtitle": "lisi@example.com"},
                {"title": "王五", "subtitle": "wangwu@example.com"},
                {"title": "赵六", "subtitle": "zhaoliu@example.com"},
                {"title": "孙七", "subtitle": "sunqi@example.com"},
            ]

            data_source = MockDataSource(users)
            self.table.data_source = data_source
            self.table.delegate = TableDelegate()
            self.table.reload_data()

            # 将表格添加到视图
            self.view.add_subview(self.table)
            print(f"[TableVC] 表格已创建: {len(users)} 行")

    vc = TableViewController()
    vc.load_view()
    vc.view_did_load()

    return vc


def main():
    """运行所有演示"""
    plain_table = demo_plain_table()
    grouped_table = demo_grouped_table()
    table_vc = demo_table_view_controller()

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("  Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
