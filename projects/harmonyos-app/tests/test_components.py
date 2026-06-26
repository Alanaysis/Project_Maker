"""
组件单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.component.base import BaseComponent, ComponentStyle, LifecyclePhase
from src.component.text import Text
from src.component.button import Button
from src.component.image import Image
from src.component.input import TextInput
from src.component.container import Column, Row, Stack, Flex, Grid


class TestBaseComponent:
    """测试组件基类"""

    def test_create_component(self):
        comp = BaseComponent(name='TestComp')
        assert comp.name == 'TestComp'
        assert comp.id.startswith('TestComp_')
        assert comp.children == []
        assert comp.is_rendered is False

    def test_add_child(self):
        parent = BaseComponent(name='Parent')
        child = BaseComponent(name='Child')
        result = parent.add_child(child)
        assert result is parent  # 返回自身支持链式调用
        assert len(parent.children) == 1
        assert child.parent is parent

    def test_set_property(self):
        comp = BaseComponent(name='Test')
        result = comp.set_property('key', 'value')
        assert result is comp
        assert comp.properties['key'] == 'value'

    def test_event_handler(self):
        comp = BaseComponent(name='Test')
        calls = []
        comp.on('click', lambda: calls.append(1))
        comp.trigger_event('click')
        assert len(calls) == 1

    def test_lifecycle_callback(self):
        comp = BaseComponent(name='Test')
        calls = []
        comp.on_lifecycle(LifecyclePhase.ABOUT_TO_APPEAR, lambda: calls.append('appear'))
        comp.trigger_lifecycle(LifecyclePhase.ABOUT_TO_APPEAR)
        assert len(calls) == 1

    def test_get_component_by_id(self):
        parent = BaseComponent(name='Parent')
        child = BaseComponent(name='Child')
        parent.add_child(child)
        found = parent.get_component_by_id(child.id)
        assert found is child

    def test_find_children(self):
        parent = BaseComponent(name='Parent')
        for _ in range(3):
            parent.add_child(BaseComponent(name='Target'))
        results = parent.find_children('Target')
        assert len(results) == 3

    def test_count_components(self):
        parent = BaseComponent(name='Parent')
        child1 = BaseComponent(name='Child1')
        child2 = BaseComponent(name='Child2')
        grandchild = BaseComponent(name='GrandChild')
        parent.add_child(child1)
        parent.add_child(child2)
        child1.add_child(grandchild)
        assert parent.count_components() == 4

    def test_render(self):
        comp = BaseComponent(name='Test')
        output = comp.render()
        assert '[Test]' in output


class TestComponentStyle:
    """测试样式系统"""

    def test_default_styles(self):
        style = ComponentStyle()
        assert style.get('width') is None
        assert style.get('opacity') == 1.0

    def test_chain_apply(self):
        style = ComponentStyle()
        result = style.apply('width', 100).apply('height', 50)
        assert result.get('width') == 100
        assert result.get('height') == 50

    def test_to_dict(self):
        style = ComponentStyle()
        style.apply('width', 100)
        d = style.to_dict()
        assert d['width'] == 100


class TestText:
    """测试 Text 组件"""

    def test_create_text(self):
        text = Text('Hello')
        assert text.properties['content'] == 'Hello'

    def test_font_style(self):
        text = Text('Test')
        text.font_size(24).font_weight('bold').font_color('#FF0000')
        assert text.text_style['fontSize'] == 24
        assert text.text_style['fontWeight'] == 'bold'
        assert text.text_style['fontColor'] == '#FF0000'

    def test_text_overflow(self):
        text = Text('Long content')
        text.text_overflow('ellipsis').max_lines(2)
        assert text.text_style['textOverflow'] == 'ellipsis'
        assert text.text_style['maxLines'] == 2

    def test_rich_text(self):
        text = Text()
        text.append_text('Hello ').append_text('World', fontColor='#FF0000')
        assert len(text.rich_text_segments) == 2
        assert text.get_display_content() == 'Hello World'

    def test_render(self):
        text = Text('Hello HarmonyOS')
        output = text.render()
        assert '[Text]' in output
        assert 'Hello' in output


class TestButton:
    """测试 Button 组件"""

    def test_create_button(self):
        btn = Button('Submit')
        assert btn.properties['content'] == 'Submit'

    def test_button_type(self):
        btn = Button('Test')
        btn.button_type('Capsule')
        assert btn.button_style['type'] == 'Capsule'

    def test_disabled_state(self):
        btn = Button('Test')
        btn.set_disabled(True)
        assert btn.state == 'disabled'
        btn.set_disabled(False)
        assert btn.state == 'normal'

    def test_click_event(self):
        btn = Button('Click')
        clicked = []
        btn.on_click(lambda: clicked.append(True))
        btn.trigger_click()
        assert len(clicked) == 1

    def test_disabled_click(self):
        btn = Button('Click')
        btn.set_disabled(True)
        result = btn.trigger_click()
        assert len(result) == 0


class TestImage:
    """测试 Image 组件"""

    def test_create_image(self):
        img = Image('photo.jpg')
        assert img.properties['source'] == 'photo.jpg'

    def test_image_fit(self):
        img = Image()
        img.image_fit('Cover')
        assert img.image_style['objectFit'] == 'Cover'

    def test_border_radius(self):
        img = Image()
        img.border_radius(50)
        assert img.image_style['borderRadius'] == 50

    def test_load_state(self):
        img = Image()
        img.set_load_state('loading')
        assert img.load_state == 'loading'
        img.set_load_state('success')
        assert img.load_state == 'success'


class TestTextInput:
    """测试 TextInput 组件"""

    def test_create_input(self):
        inp = TextInput('请输入')
        assert inp.properties['placeholder'] == '请输入'

    def test_input_type(self):
        inp = TextInput()
        inp.input_type('PASSWORD')
        assert inp.input_config['type'] == 'PASSWORD'

    def test_max_length(self):
        inp = TextInput()
        inp.max_length(20)
        assert inp.input_config['maxLength'] == 20

    def test_update_value(self):
        inp = TextInput()
        inp.max_length(5)
        inp.update_value('Hello')
        assert inp.properties['value'] == 'Hello'

    def test_max_length_enforcement(self):
        inp = TextInput()
        inp.max_length(3)
        inp.update_value('Hello')
        assert inp.properties['value'] == 'Hel'

    def test_validate(self):
        inp = TextInput()
        inp.properties['value'] = 'test@test.com'
        is_valid = inp.validate(lambda v: (True, '') if '@' in v else (False, 'Invalid email'))
        assert is_valid is True


class TestColumn:
    """测试 Column 容器"""

    def test_create_column(self):
        col = Column()
        assert col.name == 'Column'

    def test_gap(self):
        col = Column()
        col.gap(10)
        assert col.layout_config['gap'] == 10

    def test_align_items(self):
        col = Column()
        col.align_items('Center')
        assert col.layout_config['alignItems'] == 'Center'

    def test_add_children(self):
        col = Column()
        col.add_child(Text('A')).add_child(Text('B'))
        assert len(col.children) == 2


class TestRow:
    """测试 Row 容器"""

    def test_create_row(self):
        row = Row()
        assert row.name == 'Row'

    def test_gap(self):
        row = Row()
        row.gap(8)
        assert row.layout_config['gap'] == 8


class TestStack:
    """测试 Stack 容器"""

    def test_create_stack(self):
        stack = Stack()
        assert stack.name == 'Stack'

    def test_stack_order(self):
        stack = Stack()
        stack.add_child(Text('Bottom'))
        stack.add_child(Text('Top'))
        assert len(stack.children) == 2
        assert stack.children[1].properties['content'] == 'Top'


class TestFlex:
    """测试 Flex 容器"""

    def test_create_flex(self):
        flex = Flex('Row')
        assert flex.name == 'Flex'

    def test_flex_direction(self):
        flex = Flex()
        flex.flex_direction('Column')
        assert flex.layout_config['direction'] == 'Column'

    def test_flex_wrap(self):
        flex = Flex()
        flex.flex_wrap('Wrap')
        assert flex.layout_config['flexWrap'] == 'Wrap'

    def test_flex_grow(self):
        flex = Flex()
        flex.flex_grow(0, 1)
        assert flex._flex_grow[0] == 1


class TestGrid:
    """测试 Grid 容器"""

    def test_create_grid(self):
        grid = Grid(3)
        assert grid.name == 'Grid'
        assert grid.layout_config['columns'] == 3

    def test_grid_columns(self):
        grid = Grid(3)
        grid.grid_columns(4)
        assert grid.layout_config['columns'] == 4

    def test_grid_gap(self):
        grid = Grid(3)
        grid.grid_gap(row=10, column=5)
        assert grid.layout_config['gap'] == {'row': 10, 'column': 5}


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
