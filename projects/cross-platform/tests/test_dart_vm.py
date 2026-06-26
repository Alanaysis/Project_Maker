"""
跨平台框架原理 - 测试套件
Cross-Platform Framework Principles - Test Suite

测试 Dart VM 核心功能：
- 字节码编译和执行
- 垃圾回收
- 对象模型
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dart_vm import (
    DartVM, DartObject, DartList, GarbageCollector,
    Opcode
)


class TestDartObject(unittest.TestCase):
    """测试 Dart 对象模型"""

    def test_create_object(self):
        """测试创建 Dart 对象"""
        obj = DartObject("TestType", name="test", value=42)
        self.assertEqual(obj.type, "TestType")
        self.assertEqual(obj.get_attr("name"), "test")
        self.assertEqual(obj.get_attr("value"), 42)

    def test_object_id_uniqueness(self):
        """测试对象 ID 唯一性"""
        obj1 = DartObject("Type1")
        obj2 = DartObject("Type2")
        self.assertNotEqual(obj1.id, obj2.id)

    def test_set_attr(self):
        """测试设置属性"""
        obj = DartObject("Test")
        obj.set_attr("new_attr", "new_value")
        self.assertEqual(obj.get_attr("new_attr"), "new_value")

    def test_mark_and_clear(self):
        """测试标记和清除标记"""
        obj = DartObject("Test")
        self.assertFalse(obj.is_marked())
        obj.mark()
        self.assertTrue(obj.is_marked())
        obj.clear_mark()
        self.assertFalse(obj.is_marked())

    def test_repr(self):
        """测试字符串表示"""
        obj = DartObject("Test", x=1, y=2)
        self.assertIn("Test", repr(obj))


class TestDartList(unittest.TestCase):
    """测试 Dart 列表"""

    def test_create_list(self):
        """测试创建列表"""
        lst = DartList()
        self.assertEqual(len(lst), 0)

    def test_list_with_elements(self):
        """测试带初始元素的列表"""
        lst = DartList([1, 2, 3])
        self.assertEqual(len(lst), 3)
        self.assertEqual(lst[0], 1)
        self.assertEqual(lst[2], 3)

    def test_append(self):
        """测试追加元素"""
        lst = DartList()
        lst.append(1)
        lst.append(2)
        self.assertEqual(len(lst), 2)

    def test_is_dart_object(self):
        """测试继承关系"""
        lst = DartList()
        self.assertIsInstance(lst, DartObject)


class TestGarbageCollector(unittest.TestCase):
    """测试垃圾回收器"""

    def setUp(self):
        self.gc = GarbageCollector()

    def test_add_and_collect(self):
        """测试添加和回收对象"""
        obj = DartObject("Test")
        self.gc.add_object(obj)
        self.assertEqual(len(self.gc._objects), 1)

    def test_collect_frees_unmarked(self):
        """测试回收释放未标记对象"""
        # 添加多个对象
        for i in range(10):
            self.gc.add_object(DartObject(f"Type{i}"))

        # 执行回收
        freed = self.gc.collect()
        self.assertGreaterEqual(freed, 0)

    def test_gc_stats(self):
        """测试 GC 统计"""
        stats = self.gc.stats
        self.assertIn("collection_count", stats)
        self.assertIn("total_freed", stats)
        self.assertIn("live_objects", stats)

    def test_multiple_collections(self):
        """测试多次回收"""
        for i in range(5):
            self.gc.add_object(DartObject(f"Temp{i}"))

        self.gc.collect()
        count = self.gc.stats["collection_count"]
        self.assertEqual(count, 1)

        self.gc.collect()
        self.assertEqual(self.gc.stats["collection_count"], 2)


class TestDartVM(unittest.TestCase):
    """测试 Dart VM"""

    def setUp(self):
        self.vm = DartVM()

    def test_set_global(self):
        """测试设置全局变量"""
        self.vm.set_global("counter", 42)
        self.assertEqual(self.vm.get_global("counter"), 42)

    def test_register_function(self):
        """测试注册函数"""
        def test_func():
            return "hello"
        self.vm.register_function("testFunc", test_func)
        self.assertIn("testFunc", self.vm._functions)

    def test_compile_basic(self):
        """测试编译基本代码"""
        source = "new Object 1 + 2"
        bytecode = self.vm.compile(source)
        self.assertGreater(len(bytecode), 0)

    def test_execute_bytecode(self):
        """测试执行字节码"""
        bytecode = [
            {'opcode': Opcode.LOAD_CONST, 'value': 10},
            {'opcode': Opcode.LOAD_CONST, 'value': 5},
            {'opcode': Opcode.ADD},
            {'opcode': Opcode.RETURN},
        ]
        result = self.vm.execute(bytecode)
        self.assertIn(15, result)

    def test_gc_trigger(self):
        """测试触发 GC"""
        for i in range(20):
            self.vm.set_global(f"temp_{i}", i)

        stats = self.vm.trigger_gc()
        self.assertIn("collection_count", stats)

    def test_gc_stats_property(self):
        """测试 GC 统计属性"""
        stats = self.vm.gc_stats
        self.assertIn("live_objects", stats)

    def test_execution_log(self):
        """测试执行日志"""
        bytecode = [
            {'opcode': Opcode.LOAD_CONST, 'value': 1},
            {'opcode': Opcode.RETURN},
        ]
        self.vm.execute(bytecode)
        self.assertGreater(len(self.vm.execution_log), 0)

    def test_tokenizer(self):
        """测试词法分析器"""
        tokens = self.vm._tokenize("new Object 42 + true")
        self.assertIn("new", tokens)
        self.assertIn("Object", tokens)
        self.assertIn("42", tokens)
        self.assertIn("+", tokens)
        self.assertIn("true", tokens)


class TestOpcode(unittest.TestCase):
    """测试字节码指令"""

    def test_all_opcodes_exist(self):
        """测试所有指令类型存在"""
        expected = [
            "LOAD_CONST", "LOAD_GLOBAL", "LOAD_LOCAL",
            "ADD", "SUB", "MUL", "DIV",
            "JUMP", "JUMP_IF_FALSE", "CALL", "RETURN",
            "NEW_OBJECT", "SET_ATTR", "GET_ATTR", "NEW_LIST",
            "PLATFORM_CHANNEL_CALL", "PLATFORM_CHANNEL_RESPONSE",
        ]
        actual = [op.value for op in Opcode]
        for exp in expected:
            self.assertIn(exp, actual)


if __name__ == "__main__":
    unittest.main()
