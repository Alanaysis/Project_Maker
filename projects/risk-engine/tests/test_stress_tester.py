"""测试压力测试模块"""

import pytest
import numpy as np
from src.stress_tester import StressTester, StressScenario, StressTestResult


@pytest.fixture
def tester():
    """压力测试器"""
    return StressTester(portfolio_value=1000000)


@pytest.fixture
def sample_weights():
    """示例权重"""
    return {
        "equity": 0.60,
        "bond": 0.30,
        "commodity": 0.10
    }


class TestStressTester:
    """StressTester 类测试"""

    def test_historical_stress_test(self, tester, sample_weights):
        """测试历史情景压力测试"""
        result = tester.historical_stress_test("2008_financial_crisis", sample_weights)

        assert isinstance(result, StressTestResult)
        assert result.portfolio_loss < 0  # 应该是负数（损失）
        assert result.portfolio_loss_amount < 0
        assert len(result.position_losses) > 0

    def test_historical_stress_test_invalid_scenario(self, tester, sample_weights):
        """测试无效的历史情景"""
        with pytest.raises(ValueError, match="Unknown scenario"):
            tester.historical_stress_test("invalid_scenario", sample_weights)

    def test_hypothetical_stress_test(self, tester, sample_weights):
        """测试假设情景压力测试"""
        scenario = StressScenario(
            name="Test Scenario",
            description="测试情景",
            shocks={"equity": -0.20, "bond": 0.05, "commodity": -0.10}
        )

        result = tester.hypothetical_stress_test(scenario, sample_weights)

        assert isinstance(result, StressTestResult)
        assert result.scenario.name == "Test Scenario"

    def test_reverse_stress_test(self, tester, sample_weights):
        """测试反向压力测试"""
        scenario = tester.reverse_stress_test(
            target_loss=-0.20,
            weights=sample_weights,
            risk_factor="equity"
        )

        assert isinstance(scenario, StressScenario)
        assert "equity" in scenario.shocks
        assert scenario.shocks["equity"] < 0  # 应该是负冲击

    def test_reverse_stress_test_invalid_factor(self, tester, sample_weights):
        """测试反向压力测试无效风险因子"""
        with pytest.raises(ValueError, match="not in weights"):
            tester.reverse_stress_test(
                target_loss=-0.20,
                weights=sample_weights,
                risk_factor="invalid"
            )

    def test_run_multiple_scenarios(self, tester, sample_weights):
        """测试运行多个情景"""
        scenarios = [
            StressScenario("S1", "Scenario 1", {"equity": -0.10}),
            StressScenario("S2", "Scenario 2", {"equity": -0.20}),
            StressScenario("S3", "Scenario 3", {"equity": -0.30})
        ]

        results = tester.run_multiple_scenarios(scenarios, sample_weights)

        assert len(results) == 3
        assert all(isinstance(r, StressTestResult) for r in results)

    def test_sensitivity_analysis(self, tester, sample_weights):
        """测试敏感性分析"""
        results = tester.sensitivity_analysis(
            sample_weights,
            "equity",
            shock_range=(-0.30, 0.10),
            num_steps=5
        )

        assert len(results) == 5
        # 结果应该是 (冲击水平, 损失) 的元组
        for shock, loss in results:
            assert isinstance(shock, float)
            assert isinstance(loss, float)

    def test_sensitivity_analysis_invalid_factor(self, tester, sample_weights):
        """测试敏感性分析无效风险因子"""
        with pytest.raises(ValueError, match="not in weights"):
            tester.sensitivity_analysis(sample_weights, "invalid")


class TestStressScenario:
    """StressScenario 类测试"""

    def test_scenario_creation(self):
        """测试情景创建"""
        scenario = StressScenario(
            name="Test",
            description="Test scenario",
            shocks={"equity": -0.20, "bond": 0.05}
        )

        assert scenario.name == "Test"
        assert scenario.description == "Test scenario"
        assert scenario.shocks["equity"] == -0.20
        assert scenario.shocks["bond"] == 0.05

    def test_scenario_to_dict(self):
        """测试情景转换为字典"""
        scenario = StressScenario(
            name="Test",
            description="Test scenario",
            shocks={"equity": -0.20},
            probability=0.1
        )

        data = scenario.to_dict()
        assert data["name"] == "Test"
        assert data["description"] == "Test scenario"
        assert data["shocks"] == {"equity": -0.20}
        assert data["probability"] == 0.1


class TestStressTestResult:
    """StressTestResult 类测试"""

    def test_result_creation(self):
        """测试结果创建"""
        scenario = StressScenario("Test", "Test scenario", {"equity": -0.20})
        result = StressTestResult(
            scenario=scenario,
            portfolio_loss=-0.15,
            portfolio_loss_amount=-150000,
            position_losses={"equity": -0.15},
            var_before=20000,
            var_after=100000
        )

        assert result.scenario.name == "Test"
        assert result.portfolio_loss == -0.15
        assert result.portfolio_loss_amount == -150000
        assert result.position_losses["equity"] == -0.15

    def test_result_to_dict(self):
        """测试结果转换为字典"""
        scenario = StressScenario("Test", "Test scenario", {"equity": -0.20})
        result = StressTestResult(
            scenario=scenario,
            portfolio_loss=-0.15,
            portfolio_loss_amount=-150000,
            position_losses={"equity": -0.15},
            var_before=20000,
            var_after=100000
        )

        data = result.to_dict()
        assert "scenario" in data
        assert "portfolio_loss" in data
        assert "position_losses" in data


class TestHistoricalScenarios:
    """历史情景测试"""

    def test_all_scenarios_exist(self):
        """测试所有历史情景都存在"""
        expected_scenarios = [
            "2008_financial_crisis",
            "2020_covid",
            "2000_dotcom",
            "black_monday"
        ]

        for scenario in expected_scenarios:
            assert scenario in StressTester.HISTORICAL_SCENARIOS

    def test_scenario_properties(self):
        """测试情景属性"""
        for name, scenario in StressTester.HISTORICAL_SCENARIOS.items():
            assert scenario.name
            assert scenario.description
            assert len(scenario.shocks) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
