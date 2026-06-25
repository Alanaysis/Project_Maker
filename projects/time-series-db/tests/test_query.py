"""查询模块测试"""

import pytest
import tempfile
import shutil
import os
from src.engine.storage import StorageEngine
from src.query.executor import QueryExecutor, QueryRequest
from src.query.aggregation import Aggregator
from src.query.downsampling import Downsampler


class TestAggregator:
    """聚合函数测试类"""

    def test_avg(self):
        """测试平均值"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert Aggregator.aggregate(values, 'avg') == 3.0

    def test_max(self):
        """测试最大值"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert Aggregator.aggregate(values, 'max') == 5.0

    def test_min(self):
        """测试最小值"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert Aggregator.aggregate(values, 'min') == 1.0

    def test_sum(self):
        """测试求和"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert Aggregator.aggregate(values, 'sum') == 15.0

    def test_count(self):
        """测试计数"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert Aggregator.aggregate(values, 'count') == 5.0

    def test_first(self):
        """测试第一个值"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert Aggregator.aggregate(values, 'first') == 1.0

    def test_last(self):
        """测试最后一个值"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert Aggregator.aggregate(values, 'last') == 5.0

    def test_stddev(self):
        """测试标准差"""
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        stddev = Aggregator.aggregate(values, 'stddev')
        assert abs(stddev - 2.0) < 0.01

    def test_median(self):
        """测试中位数"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert Aggregator.aggregate(values, 'median') == 3.0

    def test_empty_values(self):
        """测试空值列表"""
        assert Aggregator.aggregate([], 'avg') == 0.0
        assert Aggregator.aggregate([], 'max') == 0.0
        assert Aggregator.aggregate([], 'count') == 0.0


class TestDownsampler:
    """降采样测试类"""

    def test_downsample_1m(self):
        """测试 1 分钟降采样"""
        # 生成 10 分钟的数据，每秒一个点
        points = [(i, float(i)) for i in range(600)]

        downsampler = Downsampler('1m', 'avg')
        result = downsampler.downsample(points)

        assert len(result) == 10  # 10 分钟 / 1 分钟 = 10 个点

    def test_downsample_1h(self):
        """测试 1 小时降采样"""
        # 生成 2 小时的数据，每分钟一个点
        points = [(i * 60, float(i)) for i in range(120)]

        downsampler = Downsampler('1h', 'avg')
        result = downsampler.downsample(points)

        assert len(result) == 2

    def test_downsample_with_fill(self):
        """测试带填充的降采样"""
        points = [(0, 1.0), (120, 2.0)]  # 0秒和120秒

        downsampler = Downsampler('1m', 'avg', fill='0')
        result = downsampler.downsample(points)

        assert len(result) == 3  # 0, 60, 120
        assert result[1][1] == 0.0  # 填充 0

    def test_auto_interval(self):
        """测试自动间隔选择"""
        interval = Downsampler.auto_interval(0, 3600, 100)
        assert interval in ['30s', '1m']

    def test_parse_interval(self):
        """测试间隔解析"""
        assert Downsampler._parse_interval('1s') == 1
        assert Downsampler._parse_interval('1m') == 60
        assert Downsampler._parse_interval('1h') == 3600
        assert Downsampler._parse_interval('1d') == 86400


class TestQueryExecutor:
    """查询执行器测试类"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data')
        self.engine = StorageEngine(self.data_dir)
        self.executor = QueryExecutor(self.engine)

        # 写入测试数据
        for i in range(100):
            self.engine.write("cpu", {"host": "s1"}, i * 60, float(i))

    def teardown_method(self):
        """测试后清理"""
        self.engine.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_query(self):
        """测试基本查询"""
        request = QueryRequest(
            metric="cpu",
            start=0,
            end=6000,
            tags={"host": "s1"}
        )
        response = self.executor.execute(request)
        assert response.count == 100

    def test_query_with_aggregation(self):
        """测试聚合查询"""
        request = QueryRequest(
            metric="cpu",
            start=0,
            end=6000,
            aggregation="avg"
        )
        response = self.executor.execute(request)
        assert response.count == 1

    def test_query_with_downsample(self):
        """测试降采样查询"""
        request = QueryRequest(
            metric="cpu",
            start=0,
            end=6000,
            downsample="5m",
            aggregation="avg"
        )
        response = self.executor.execute(request)
        assert response.count == 20  # 100分钟 / 5分钟 = 20

    def test_latest(self):
        """测试最新值查询"""
        result = self.executor.latest("cpu", {"host": "s1"})
        assert result is not None
        assert result[0] == 99 * 60
        assert result[1] == 99.0

    def test_metrics(self):
        """测试指标列表"""
        metrics = self.executor.metrics()
        assert "cpu" in metrics


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
