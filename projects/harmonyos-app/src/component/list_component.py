"""
List/ListItem 列表组件 - List Component

鸿蒙 ArkUI 中的 List 组件用于显示列表数据。

ArkTS 示例：
```
List() {
  ForEach(items, (item) => {
    ListItem() {
      Text(item.name)
        .fontSize(18)
    }
  })
}
.listStyle(ListStyle.None)
.divider({ strokeWidth: 1, startMargin: 16, endMargin: 16 })
```

支持：
- ForEach 循环渲染
- 列表样式
- 分隔线
- 滑动操作
- 滚动事件
"""

from typing import Any, Callable, List, Optional
from .base import BaseComponent, LifecyclePhase


class ListItem(BaseComponent):
    """
    列表项组件 - 模拟 ArkUI 的 ListItem 组件

    ListItem 是 List 中的子项容器。
    """

    def __init__(self, data: Any = None, parent=None):
        super().__init__(name='ListItem', parent=parent)
        self.set_property('data', data)
        self.swipe_action = None

    def swipe_action(self, action: dict) -> 'ListItem':
        """设置滑动操作"""
        self.swipe_action = action
        return self

    def render(self, depth: int = 0) -> str:
        indent = '  ' * depth
        data = self.properties.get('data')
        data_str = str(data)[:30] if data else 'None'
        lines = [f'{indent}[ListItem] data={data_str}']
        if self.swipe_action:
            lines.append(f'{indent}  swipe_action={self.swipe_action}')
        return '\n'.join(lines)


class List(BaseComponent):
    """
    列表组件 - 模拟 ArkUI 的 List 组件

    鸿蒙 List 特性：
    1. 支持 ForEach 循环渲染
    2. 支持多种列表样式
    3. 支持分隔线配置
    4. 支持滑动删除/操作
    5. 支持滚动事件
    """

    LIST_STYLES = ['None', 'Line', 'Card', 'Default']

    def __init__(self, data: Optional[List[Any]] = None, parent=None):
        super().__init__(name='List', parent=parent)
        self._data = data or []

        # 列表配置
        self.list_config = {
            'style': 'None',
            'divider': {
                'strokeWidth': 1,
                'startMargin': 0,
                'endMargin': 0,
                'color': '#E1E1E1',
            },
            'scrollBar': 'off',  # 'on', 'off', 'auto'
            'edgeEffect': 'none',  # 'none', 'always', 'auto'
        }

        # 索引到 ListItem 的映射
        self._index_map: dict = {}

    def list_style(self, style: str) -> 'List':
        """设置列表样式"""
        if style in self.LIST_STYLES:
            self.list_config['style'] = style
        return self

    def divider(self, **kwargs) -> 'List':
        """配置分隔线样式"""
        self.list_config['divider'].update(kwargs)
        return self

    def scroll_bar(self, bar: str) -> 'List':
        """设置滚动条显示模式"""
        self.list_config['scrollBar'] = bar
        return self

    def set_data(self, data: List[Any]) -> 'List':
        """
        设置列表数据并重建子组件

        模拟 ForEach 渲染：
        ForEach(items, (item) => ListItem() { ... })
        """
        self._data = data
        # 重建子组件
        self.children = []
        self._index_map = {}
        for i, item in enumerate(data):
            item_component = ListItem(data=item, parent=self)
            self.children.append(item_component)
            self._index_map[i] = item_component
        return self

    def get_item(self, index: int) -> Optional[ListItem]:
        """获取指定索引的列表项"""
        return self._index_map.get(index)

    def append_item(self, data: Any) -> 'List':
        """追加列表项"""
        self._data.append(data)
        item_component = ListItem(data=data, parent=self)
        self.children.append(item_component)
        self._index_map[len(self._data) - 1] = item_component
        return self

    def remove_item(self, index: int) -> Optional[Any]:
        """移除指定索引的列表项"""
        if 0 <= index < len(self._data):
            removed_data = self._data.pop(index)
            self.children.pop(index)
            self._index_map.pop(index, None)
            # 重新映射索引
            for i, item in enumerate(self.children):
                self._index_map[i] = item
            return removed_data
        return None

    def on_scroll(self, handler: Callable) -> 'List':
        """绑定滚动事件"""
        return self.on(LifecyclePhase.ON_AREA_CHANGE, handler)

    def render(self, depth: int = 0) -> str:
        indent = '  ' * depth
        lines = [f'{indent}[List] itemCount={len(self._data)} style={self.list_config["style"]}']
        lines.append(f'{indent}  scrollBar={self.list_config["scrollBar"]} edgeEffect={self.list_config["edgeEffect"]}')
        divider = self.list_config['divider']
        if divider['strokeWidth'] > 0:
            lines.append(f'{indent}  divider: w={divider["strokeWidth"]} margin=[{divider["startMargin"]}, {divider["endMargin"]}]')
        return '\n'.join(lines)
