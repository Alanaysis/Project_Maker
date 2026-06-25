"""文档检索示例 - Document Retrieval Example

演示高级文档检索功能，包括短语查询、模糊查询等。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.search_engine import SearchEngine
from src.index import PositionalIndex, CompressedIndex


def phrase_search_demo():
    """短语查询演示"""
    print("=== 短语查询演示 ===\n")

    engine = SearchEngine('positional')

    documents = [
        {"doc_id": "1", "title": "Python教程",
         "content": "Python programming language is easy to learn"},
        {"doc_id": "2", "title": "编程入门",
         "content": "Learning programming is fun with Python"},
        {"doc_id": "3", "title": "高级Python",
         "content": "Advanced Python programming techniques"},
    ]

    engine.add_documents(documents)

    # 短语查询
    phrase = '"python programming"'
    print(f"短语查询: {phrase}")
    results = engine.search(phrase)
    for r in results:
        print(f"  - {r.title}: {r.snippet}")
    print()


def wildcard_search_demo():
    """通配符查询演示"""
    print("=== 通配符查询演示 ===\n")

    engine = SearchEngine()

    documents = [
        {"doc_id": "1", "title": "Python", "content": "Python programming"},
        {"doc_id": "2", "title": "JavaScript", "content": "JavaScript web development"},
        {"doc_id": "3", "title": "TypeScript", "content": "TypeScript typed JavaScript"},
    ]

    engine.add_documents(documents)

    # 通配符查询
    queries = ["*script", "java*", "py*"]
    for query in queries:
        print(f"通配符查询: {query}")
        results = engine.search(query)
        for r in results:
            print(f"  - {r.title}")
    print()


def fuzzy_search_demo():
    """模糊查询演示"""
    print("=== 模糊查询演示 ===\n")

    engine = SearchEngine()

    documents = [
        {"doc_id": "1", "title": "Python Programming",
         "content": "Learn Python programming language"},
        {"doc_id": "2", "title": "Machine Learning",
         "content": "Introduction to machine learning"},
    ]

    engine.add_documents(documents)

    # 模糊查询（拼写错误）
    queries = ["pythn~", "programing~", "machne~"]
    for query in queries:
        print(f"模糊查询: {query}")
        results = engine.search(query)
        for r in results:
            print(f"  - {r.title}")
    print()


def boolean_search_demo():
    """布尔查询演示"""
    print("=== 布尔查询演示 ===\n")

    engine = SearchEngine()

    documents = [
        {"doc_id": "1", "title": "Python Data Science",
         "content": "Python is widely used in data science and machine learning"},
        {"doc_id": "2", "title": "Java Enterprise",
         "content": "Java is popular for enterprise applications"},
        {"doc_id": "3", "title": "Web Development",
         "content": "Python and JavaScript are used for web development"},
        {"doc_id": "4", "title": "Data Analysis",
         "content": "R and Python are tools for data analysis"},
    ]

    engine.add_documents(documents)

    queries = [
        "python AND data",
        "python OR java",
        "python NOT java",
        "data science",
    ]

    for query in queries:
        print(f"布尔查询: {query}")
        results = engine.search(query)
        for r in results:
            print(f"  - {r.title}")
    print()


def compression_demo():
    """压缩索引演示"""
    print("=== 压缩索引演示 ===\n")

    engine = SearchEngine('compressed')

    documents = [
        {"doc_id": "1", "title": "Python Programming",
         "content": "Python is a popular programming language"},
        {"doc_id": "2", "title": "Java Programming",
         "content": "Java is a programming language for enterprise"},
    ]

    engine.add_documents(documents)

    # 压缩索引
    if isinstance(engine.index, CompressedIndex):
        engine.index.compress()
        ratio = engine.index.get_compression_ratio()
        print(f"压缩比: {ratio:.2%}")

    # 保存和加载
    filepath = "/tmp/compressed_index.gz"
    engine.save_index(filepath)
    print(f"索引已保存到: {filepath}")

    # 搜索测试
    results = engine.search("python")
    print(f"搜索结果: {len(results)} 个文档")


if __name__ == "__main__":
    phrase_search_demo()
    wildcard_search_demo()
    fuzzy_search_demo()
    boolean_search_demo()
    compression_demo()
