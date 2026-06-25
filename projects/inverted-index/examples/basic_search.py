"""基本搜索示例 - Basic Search Example

演示搜索引擎的基本功能。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.search_engine import SearchEngine, SimpleSearchEngine
from src.index import Document


def basic_search_demo():
    """基本搜索演示"""
    print("=== 基本搜索演示 ===\n")

    # 创建搜索引擎
    engine = SearchEngine()

    # 添加文档
    documents = [
        {"doc_id": "1", "title": "Python Programming",
         "content": "Python is a popular programming language for data science and machine learning"},
        {"doc_id": "2", "title": "Java Programming",
         "content": "Java is a programming language widely used in enterprise applications"},
        {"doc_id": "3", "title": "Data Science",
         "content": "Data science involves using Python and R for data analysis and visualization"},
        {"doc_id": "4", "title": "Machine Learning",
         "content": "Machine learning algorithms can be implemented in Python using libraries like scikit-learn"},
        {"doc_id": "5", "title": "Web Development",
         "content": "Python frameworks like Django and Flask are used for web development"},
    ]

    engine.add_documents(documents)
    print(f"已索引 {len(documents)} 个文档")
    print(f"统计信息: {engine.get_statistics()}\n")

    # 执行搜索
    queries = [
        "python",
        "programming language",
        "data science",
        "python AND machine",
        "web OR enterprise",
        "python NOT java",
    ]

    for query in queries:
        print(f"查询: {query}")
        results = engine.search(query, top_k=3)
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.title} (得分: {result.score:.4f})")
            print(f"     {result.snippet}")
        print()


def simple_search_demo():
    """简单搜索演示"""
    print("=== 简单搜索演示 ===\n")

    engine = SimpleSearchEngine()

    documents = [
        {"title": "Python教程", "content": "Python是一种简单易学的编程语言"},
        {"title": "机器学习入门", "content": "机器学习是人工智能的一个分支"},
        {"title": "数据分析", "content": "Python常用于数据分析和可视化"},
    ]

    engine.index_documents(documents)

    results = engine.search("Python", top_k=2)
    print("搜索 'Python':")
    for r in results:
        print(f"  - {r['title']}: {r['score']}")


if __name__ == "__main__":
    basic_search_demo()
    print("\n" + "=" * 50 + "\n")
    simple_search_demo()
