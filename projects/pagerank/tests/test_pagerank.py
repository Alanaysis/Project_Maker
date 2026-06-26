"""
PageRank 算法单元测试

测试覆盖：
- 图创建和验证
- PageRank 计算正确性
- 收敛性
- 边界情况
- 个性化 PageRank
- HITS 算法
- 稀疏矩阵优化
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph import Graph, create_web_graph, create_random_graph, create_scale_free_graph
from src.pagerank import (
    compute_pagerank,
    compute_pagerank_with_personalization,
    get_top_pages,
    normalize_pagerank,
    expected_iterations,
)
from src.hits import compute_hits, compute_hits_for_subgraph
from src.sparse_utils import (
    dense_to_csr,
    csr_to_dense,
    compute_sparsity,
    analyze_memory_usage,
)


class TestGraph(unittest.TestCase):
    """测试图数据结构"""

    def test_create_graph(self):
        """测试图创建"""
        graph = Graph(5)
        self.assertEqual(graph.num_nodes, 5)
        self.assertEqual(graph.edge_count, 0)

    def test_add_edge(self):
        """测试添加边"""
        graph = Graph(3)
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        self.assertEqual(graph.edge_count, 2)
        self.assertEqual(graph.get_out_degree(0), 1)
        self.assertEqual(graph.get_out_degree(1), 1)
        self.assertEqual(graph.get_in_degree(1), 1)

    def test_remove_edge(self):
        """测试移除边"""
        graph = Graph(3)
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        graph.remove_edge(0, 1)
        self.assertEqual(graph.edge_count, 1)
        self.assertEqual(graph.get_out_degree(0), 0)

    def test_add_edge_invalid(self):
        """测试添加无效边"""
        graph = Graph(3)
        with self.assertRaises(ValueError):
            graph.add_edge(-1, 0)
        with self.assertRaises(ValueError):
            graph.add_edge(0, 3)

    def test_get_neighbors(self):
        """测试获取邻居"""
        graph = Graph(4)
        graph.add_edge(0, 1)
        graph.add_edge(0, 2)
        graph.add_edge(3, 0)

        out_neighbors = graph.get_neighbors(0, "out")
        self.assertIn(1, out_neighbors)
        self.assertIn(2, out_neighbors)

        in_neighbors = graph.get_neighbors(0, "in")
        self.assertIn(3, in_neighbors)

    def test_transition_matrix(self):
        """测试转移矩阵计算"""
        graph = Graph(3)
        graph.add_edge(0, 1)
        graph.add_edge(0, 2)
        graph.add_edge(1, 2)

        M = graph.to_transition_matrix()

        # 第 0 列：从节点 0 出发，均匀分配到 1 和 2
        self.assertAlmostEqual(M[1, 0], 0.5)
        self.assertAlmostEqual(M[2, 0], 0.5)
        self.assertAlmostEqual(M[0, 0], 0.0)

        # 第 1 列：从节点 1 出发，到节点 2
        self.assertAlmostEqual(M[2, 1], 1.0)

        # 第 2 列：节点 2 是悬垂节点
        self.assertAlmostEqual(M[0, 2], 1.0 / 3)
        self.assertAlmostEqual(M[1, 2], 1.0 / 3)
        self.assertAlmostEqual(M[2, 2], 1.0 / 3)

    def test_dangling_nodes(self):
        """测试悬垂节点检测"""
        graph = Graph(3)
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        dangling = graph.get_dangling_nodes()
        self.assertIn(2, dangling)
        self.assertEqual(len(dangling), 1)

    def test_density(self):
        """测试密度计算"""
        graph = Graph(4)
        graph.add_edge(0, 1)
        graph.add_edge(2, 3)
        self.assertAlmostEqual(graph.get_density(), 2.0 / 12)

    def test_create_web_graph(self):
        """测试示例图创建"""
        graph = create_web_graph()
        self.assertEqual(graph.num_nodes, 6)
        self.assertGreater(graph.edge_count, 0)

    def test_create_random_graph(self):
        """测试随机图创建"""
        graph = create_random_graph(10, 20, seed=42)
        self.assertEqual(graph.num_nodes, 10)
        self.assertGreater(graph.edge_count, 0)

    def test_create_scale_free_graph(self):
        """测试无标度图创建"""
        graph = create_scale_free_graph(20, m_per_node=3, seed=42)
        self.assertEqual(graph.num_nodes, 20)
        self.assertGreater(graph.edge_count, 0)


class TestPageRank(unittest.TestCase):
    """测试 PageRank 算法"""

    def test_pagerank_basic(self):
        """测试基本 PageRank 计算"""
        graph = create_web_graph()
        pr, history, iterations = compute_pagerank(graph)

        # PageRank 值应为正数
        self.assertTrue(np.all(pr >= 0))

        # PageRank 值之和应为 1
        self.assertAlmostEqual(pr.sum(), 1.0, places=5)

        # 应返回收敛历史
        self.assertGreater(len(history), 0)

        # 应返回迭代次数
        self.assertGreater(iterations, 0)

    def test_pagerank_convergence(self):
        """测试 PageRank 收敛"""
        graph = create_web_graph()
        pr, history, iterations = compute_pagerank(graph)

        # 最后一步变化应小于容差
        self.assertLess(history[-1], 1e-6)

        # 应在最大迭代次数内收敛
        self.assertLess(iterations, 100)

    def test_pagerank_dangling_nodes(self):
        """测试悬垂节点处理"""
        graph = Graph(3)
        graph.add_edge(0, 1)
        # 节点 2 是悬垂节点

        pr, _, iterations = compute_pagerank(graph)

        # 所有节点应有正 PageRank
        self.assertTrue(np.all(pr > 0))
        self.assertAlmostEqual(pr.sum(), 1.0, places=5)

    def test_pagerank_damping_factor(self):
        """测试阻尼因子影响"""
        # 使用不对称图
        graph = Graph(4)
        graph.add_edge(0, 1)
        graph.add_edge(0, 2)
        graph.add_edge(1, 2)
        graph.add_edge(2, 3)
        # 节点 3 是悬垂节点

        pr_085, hist_085, _ = compute_pagerank(graph, damping=0.85)
        pr_05, hist_05, _ = compute_pagerank(graph, damping=0.5)
        pr_095, hist_095, _ = compute_pagerank(graph, damping=0.95)

        # 收敛历史应非空
        self.assertGreater(len(hist_085), 0)
        self.assertGreater(len(hist_05), 0)
        self.assertGreater(len(hist_095), 0)
        # 所有结果应归一化
        self.assertAlmostEqual(pr_085.sum(), 1.0, places=5)
        self.assertAlmostEqual(pr_05.sum(), 1.0, places=5)
        self.assertAlmostEqual(pr_095.sum(), 1.0, places=5)

        # 所有结果都应归一化
        self.assertAlmostEqual(pr_085.sum(), 1.0, places=5)
        self.assertAlmostEqual(pr_05.sum(), 1.0, places=5)
        self.assertAlmostEqual(pr_095.sum(), 1.0, places=5)

    def test_pagerank_top_pages(self):
        """测试获取 Top 页面"""
        graph = create_web_graph()
        pr, _, _ = compute_pagerank(graph)

        top3 = get_top_pages(pr, 3)
        self.assertEqual(len(top3), 3)

        # Top 3 应按降序排列
        for i in range(2):
            self.assertGreaterEqual(pr[top3[i]], pr[top3[i + 1]])

    def test_pagerank_normalize(self):
        """测试归一化"""
        pr = np.array([1.0, 2.0, 3.0, 4.0])
        normalized = normalize_pagerank(pr)
        self.assertAlmostEqual(normalized.sum(), 1.0, places=10)

    def test_pagerank_sparse_vs_dense(self):
        """测试稀疏矩阵和稠密矩阵结果一致性"""
        graph = create_web_graph()

        pr_dense, _, _ = compute_pagerank(graph, use_sparse=False)
        pr_sparse, _, _ = compute_pagerank(graph, use_sparse=True)

        self.assertAlmostEqual(np.abs(pr_dense - pr_sparse).max(), 0.0, places=10)

    def test_pagerank_large_graph(self):
        """测试大规模图"""
        graph = create_random_graph(100, 300, seed=42)
        pr, history, iterations = compute_pagerank(graph)

        self.assertTrue(np.all(pr >= 0))
        self.assertAlmostEqual(pr.sum(), 1.0, places=5)
        self.assertLess(len(history), 100)


class TestPersonalizedPageRank(unittest.TestCase):
    """测试个性化 PageRank"""

    def test_personalized_basic(self):
        """测试基本个性化 PageRank"""
        graph = create_web_graph()

        # 从节点 0 开始
        personalization = [0.0] * graph.num_nodes
        personalization[0] = 1.0

        pr, history, iterations = compute_pagerank_with_personalization(
            graph, personalization=personalization
        )

        # 结果应归一化
        self.assertAlmostEqual(pr.sum(), 1.0, places=5)

        # 应返回收敛历史
        self.assertGreater(len(history), 0)

    def test_personalized_different_seeds(self):
        """测试不同种子节点产生不同结果"""
        graph = create_web_graph()

        personalization_0 = [0.0] * graph.num_nodes
        personalization_0[0] = 1.0

        personalization_1 = [0.0] * graph.num_nodes
        personalization_1[1] = 1.0

        pr_0, _, _ = compute_pagerank_with_personalization(
            graph, personalization=personalization_0
        )
        pr_1, _, _ = compute_pagerank_with_personalization(
            graph, personalization=personalization_1
        )

        # 不同种子应产生不同结果
        self.assertFalse(np.allclose(pr_0, pr_1))

    def test_personalized_none(self):
        """测试 None 个人化向量 (应退化为标准 PageRank)"""
        graph = create_web_graph()

        pr_none, _, _ = compute_pagerank_with_personalization(
            graph, personalization=None
        )
        pr_standard, _, _ = compute_pagerank(graph)

        # 两者应非常接近
        self.assertAlmostEqual(np.abs(pr_none - pr_standard).max(), 0.0, places=5)


class TestHITS(unittest.TestCase):
    """测试 HITS 算法"""

    def test_hits_basic(self):
        """测试基本 HITS 计算"""
        graph = create_web_graph()
        authority, hub, history, iterations = compute_hits(graph)

        # Authority 和 Hub 值应为正数
        self.assertTrue(np.all(authority >= 0))
        self.assertTrue(np.all(hub >= 0))

        # 归一化
        self.assertAlmostEqual(np.linalg.norm(authority), 1.0, places=5)
        self.assertAlmostEqual(np.linalg.norm(hub), 1.0, places=5)

    def test_hits_convergence(self):
        """测试 HITS 收敛"""
        graph = create_web_graph()
        authority, hub, history, iterations = compute_hits(graph)

        self.assertLess(history[-1], 1e-6)

    def test_hits_authority_hub_relationship(self):
        """测试 authority 和 hub 的相互关系"""
        graph = Graph(4)
        graph.add_edge(0, 1)
        graph.add_edge(0, 2)
        graph.add_edge(1, 3)
        graph.add_edge(2, 3)

        authority, hub, _, _ = compute_hits(graph)

        # 节点 3 有最高的 authority (被 1 和 2 指向)
        self.assertGreater(authority[3], authority[0])

        # 节点 0 有最高的 hub (指向 1 和 2)
        self.assertGreater(hub[0], hub[3])

    def test_hits_for_subgraph(self):
        """测试子图 HITS"""
        graph = create_web_graph()
        authority, hub, subgraph_nodes = compute_hits_for_subgraph(
            graph, seed_nodes=[0]
        )

        # 子图节点数应大于种子节点数
        self.assertGreater(len(subgraph_nodes), len([0]))

        # 种子节点 hub 值应非零
        self.assertGreater(hub[0], 0)


class TestSparseUtils(unittest.TestCase):
    """测试稀疏矩阵工具"""

    def test_dense_to_csr(self):
        """测试稠密到稀疏转换"""
        adj = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]])
        csr = dense_to_csr(adj)
        dense_back = csr_to_dense(csr)

        np.testing.assert_array_equal(adj, dense_back)

    def test_compute_sparsity(self):
        """测试稀疏度计算"""
        dense = np.zeros((100, 100))
        dense[0, 0] = 1.0
        sparsity = compute_sparsity(dense)
        self.assertAlmostEqual(sparsity, 9999.0 / 10000.0)

    def test_analyze_memory(self):
        """测试内存分析"""
        graph = create_web_graph()
        memory = analyze_memory_usage(graph.adj_matrix, graph.adj_list)

        self.assertIn('dense_bytes', memory)
        self.assertIn('sparse_bytes', memory)
        self.assertIn('density', memory)
        self.assertIn('compression_ratio', memory)
        self.assertGreater(memory['dense_bytes'], 0)
        self.assertGreater(memory['density'], 0)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def test_single_node(self):
        """测试单节点图"""
        graph = Graph(1)
        pr, _, _ = compute_pagerank(graph)
        self.assertAlmostEqual(pr[0], 1.0)

    def test_two_nodes(self):
        """测试两节点图"""
        graph = Graph(2)
        graph.add_edge(0, 1)
        graph.add_edge(1, 0)

        pr, _, _ = compute_pagerank(graph)
        self.assertAlmostEqual(pr[0], 0.5, places=5)
        self.assertAlmostEqual(pr[1], 0.5, places=5)

    def test_chain_graph(self):
        """测试链式图"""
        graph = Graph(5)
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        graph.add_edge(2, 3)
        graph.add_edge(3, 4)

        pr, _, _ = compute_pagerank(graph)

        # 所有节点应有正 PageRank
        self.assertTrue(np.all(pr > 0))
        self.assertAlmostEqual(pr.sum(), 1.0, places=5)

    def test_complete_graph(self):
        """测试完全图"""
        graph = Graph(4)
        for i in range(4):
            for j in range(4):
                if i != j:
                    graph.add_edge(i, j)

        pr, _, _ = compute_pagerank(graph)

        # 完全图中所有节点应有相等的 PageRank
        for i in range(1, 4):
            self.assertAlmostEqual(pr[i], pr[0], places=5)

    def test_expected_iterations(self):
        """测试迭代次数估算"""
        n = 100
        expected = expected_iterations(n)
        self.assertGreater(expected, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
