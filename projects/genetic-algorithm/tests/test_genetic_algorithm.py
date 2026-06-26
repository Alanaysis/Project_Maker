"""
遗传算法 - 单元测试
Genetic Algorithm - Unit Tests

Tests the additional modules implemented in this learning project:
- selection methods (tournament, roulette, rank, elitism)
- crossover operators (single-point, multi-point, uniform, arithmetic, order)
- mutation operators (bit-flip, swap, inversion, gaussian)
- convergence detection
- parameter configuration
- core engine (generational and steady-state modes)
- test function suites
"""

import sys
import os
import math
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# Use the pre-existing Individual/Population from src.core
from src.core.individual import Individual
from src.core.population import Population

# Test our additional modules
from src.selection import (
    TournamentSelection, RouletteWheelSelection,
    RankSelection, ElitismSelection, get_selection_method
)
from src.crossover import (
    SinglePointCrossover, MultiPointCrossover,
    UniformCrossover, ArithmeticCrossover, OrderCrossover, get_crossover_operator
)
from src.mutation import (
    BitFlipMutation, SwapMutation, InversionMutation,
    GaussianMutation, BoundaryMutation, UniformMutation, get_mutation_operator
)
from src.convergence import (
    DiversityConvergenceDetector, FitnessGainConvergenceDetector,
    CombinedConvergenceDetector, GenerationLimitDetector, get_convergence_detector
)
from src.config import GAParameters
from src.suites import (
    sphere_function, rosenbrock_function,
    rastrigin_function, ackley_function
)


def make_individual(chromosome, fitness=0.0):
    """Helper: create Individual with fitness set after construction."""
    ind = Individual(chromosome)
    ind.fitness = fitness
    return ind


# ============================================================
# Selection Tests
# ============================================================

class TestTournamentSelection:
    def test_select_returns_correct_count(self):
        individuals = [make_individual([i], float(i)) for i in range(10)]
        pop = Population()
        pop.initialize(10, lambda: [random.randint(0, 1) for _ in range(1)])
        pop.individuals = individuals

        selector = TournamentSelection(tournament_size=3)
        selected = selector.select(pop, 5)
        assert len(selected) == 5

    def test_select_biased_toward_fitter(self):
        random.seed(42)
        individuals = [make_individual([i], float(i)) for i in range(100)]
        pop = Population()
        pop.initialize(100, lambda: [random.randint(0, 1) for _ in range(1)])
        pop.individuals = individuals

        selector = TournamentSelection(tournament_size=5)
        selected_counts = [0] * 100
        for _ in range(1000):
            selected = selector.select(pop, 1)
            for ind in selected:
                val = ind.chromosome[0]
                selected_counts[int(val)] += 1

        high_sum = sum(selected_counts[80:])
        low_sum = sum(selected_counts[:20])
        assert high_sum > low_sum


class TestRouletteWheelSelection:
    def test_select_returns_correct_count(self):
        individuals = [make_individual([i], 10.0 + float(i)) for i in range(10)]
        pop = Population()
        pop.initialize(10, lambda: [random.randint(0, 1) for _ in range(1)])
        pop.individuals = individuals

        selector = RouletteWheelSelection()
        selected = selector.select(pop, 5)
        assert len(selected) == 5

    def test_with_negative_fitness(self):
        individuals = [make_individual([i], float(i - 5)) for i in range(10)]
        pop = Population()
        pop.initialize(10, lambda: [random.randint(0, 1) for _ in range(1)])
        pop.individuals = individuals

        selector = RouletteWheelSelection()
        selected = selector.select(pop, 5)
        assert len(selected) == 5


class TestRankSelection:
    def test_select(self):
        individuals = [make_individual([i], float(i)) for i in range(10)]
        pop = Population()
        pop.initialize(10, lambda: [random.randint(0, 1) for _ in range(1)])
        pop.individuals = individuals

        selector = RankSelection(min_prob=0.1, max_prob=0.9)
        selected = selector.select(pop, 5)
        assert len(selected) == 5


class TestElitismSelection:
    def test_select_elite(self):
        individuals = [make_individual([i], float(9 - i)) for i in range(10)]
        pop = Population()
        pop.initialize(10, lambda: [random.randint(0, 1) for _ in range(1)])
        pop.individuals = individuals

        selector = ElitismSelection(elite_count=3)
        selected = selector.select(pop, 5)
        assert len(selected) == 5


class TestGetSelectionMethod:
    def test_all_methods(self):
        assert get_selection_method('tournament', tournament_size=5).name == 'tournament'
        assert get_selection_method('roulette').name == 'roulette'
        assert get_selection_method('rank').name == 'rank'
        assert get_selection_method('elitism', elite_count=5).name == 'elitism'

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            get_selection_method('invalid')


# ============================================================
# Crossover Tests
# ============================================================

class TestCrossover:
    def test_single_point(self):
        p1 = Individual([1, 0, 1, 0, 1])
        p2 = Individual([0, 1, 0, 1, 0])
        cx = SinglePointCrossover()
        c1, c2 = cx.crossover(p1, p2)
        assert len(c1.chromosome) == 5
        assert len(c2.chromosome) == 5

    def test_multi_point(self):
        p1 = Individual([1, 0, 1, 0, 1, 0])
        p2 = Individual([0, 1, 0, 1, 0, 1])
        cx = MultiPointCrossover(num_points=2)
        c1, c2 = cx.crossover(p1, p2)
        assert len(c1.chromosome) == 6

    def test_uniform(self):
        p1 = Individual([1, 0, 1, 0, 1])
        p2 = Individual([0, 1, 0, 1, 0])
        cx = UniformCrossover(crossover_rate=1.0)
        c1, c2 = cx.crossover(p1, p2)
        assert len(c1.chromosome) == 5

    def test_arithmetic(self):
        p1 = Individual([1.0, 2.0, 3.0])
        p2 = Individual([4.0, 5.0, 6.0])
        cx = ArithmeticCrossover(alpha=0.5)
        c1, c2 = cx.crossover(p1, p2)
        for i in range(3):
            lo = min(p1.chromosome[i], p2.chromosome[i])
            hi = max(p1.chromosome[i], p2.chromosome[i])
            assert lo <= c1.chromosome[i] <= hi

    def test_order_crossover_valid_permutation(self):
        p1 = Individual([0, 1, 2, 3, 4])
        p2 = Individual([4, 3, 2, 1, 0])
        cx = OrderCrossover()
        c1, c2 = cx.crossover(p1, p2)
        assert sorted(c1.chromosome) == [0, 1, 2, 3, 4]
        assert sorted(c2.chromosome) == [0, 1, 2, 3, 4]

    def test_get_operator(self):
        assert get_crossover_operator('single_point').name == 'single_point'
        assert get_crossover_operator('arithmetic').name == 'arithmetic'
        assert get_crossover_operator('order').name == 'order'
        with pytest.raises(ValueError):
            get_crossover_operator('invalid')


# ============================================================
# Mutation Tests
# ============================================================

class TestMutation:
    def test_bit_flip(self):
        ind = Individual([0, 0, 0, 0, 0])
        mut = BitFlipMutation(mutation_rate=1.0)
        mutated = mut.mutate(ind)
        assert all(g == 1 for g in mutated.chromosome)

    def test_swap_valid_permutation(self):
        ind = Individual([0, 1, 2, 3, 4])
        mut = SwapMutation(mutation_rate=1.0)
        mutated = mut.mutate(ind)
        assert sorted(mutated.chromosome) == [0, 1, 2, 3, 4]

    def test_inversion_valid_permutation(self):
        ind = Individual([0, 1, 2, 3, 4])
        mut = InversionMutation(mutation_rate=1.0)
        mutated = mut.mutate(ind)
        assert sorted(mutated.chromosome) == [0, 1, 2, 3, 4]

    def test_gaussian_close_to_original(self):
        ind = Individual([1.0, 2.0, 3.0])
        mut = GaussianMutation(mutation_rate=1.0, sigma=0.1)
        mutated = mut.mutate(ind)
        for i in range(3):
            assert abs(mutated.chromosome[i] - ind.chromosome[i]) < 1.0

    def test_boundary_in_range(self):
        ind = Individual([5.0, 5.0, 5.0])
        mut = BoundaryMutation(lower_bound=-10.0, upper_bound=10.0, mutation_rate=1.0)
        mutated = mut.mutate(ind)
        for g in mutated.chromosome:
            assert -10.0 <= g <= 10.0

    def test_get_operator(self):
        assert get_mutation_operator('bit_flip').name == 'bit_flip'
        assert get_mutation_operator('gaussian').name == 'gaussian'
        with pytest.raises(ValueError):
            get_mutation_operator('invalid')


# ============================================================
# Convergence Tests
# ============================================================

class TestConvergence:
    def test_generation_limit(self):
        detector = GenerationLimitDetector(max_generations=10)
        pop = Population()
        pop.initialize(10, lambda: [0])
        assert not detector.check_convergence(pop, 5)
        assert detector.check_convergence(pop, 10)

    def test_fitness_gain_convergence(self):
        detector = FitnessGainConvergenceDetector(threshold=1e-6, patience=5)
        pop = Population()
        pop.initialize(10, lambda: [0])
        for ind in pop.individuals:
            ind.fitness = 5.0
        history = []
        converged = False
        for gen in range(10):
            if detector.check_convergence(pop, gen, history):
                converged = True
                break
            history.append(5.0)
        assert converged

    def test_diversity_convergence(self):
        detector = DiversityConvergenceDetector(threshold=1e-6, window_size=5)
        pop = Population()
        pop.initialize(10, lambda: [1, 0, 1])
        history = []
        for gen in range(15):
            if detector.check_convergence(pop, gen, history):
                break
            history.append(0.0)

    def test_get_detector(self):
        assert get_convergence_detector('diversity') is not None
        assert get_convergence_detector('fitness_gain') is not None
        assert get_convergence_detector('combined') is not None
        assert get_convergence_detector('generation_limit', max_generations=100) is not None
        with pytest.raises(ValueError):
            get_convergence_detector('invalid')


# ============================================================
# Config Tests
# ============================================================

class TestConfig:
    def test_default_params(self):
        params = GAParameters()
        assert params.population_size == 100
        assert params.crossover_rate == 0.8
        assert params.mutation_rate == 0.01

    def test_validation(self):
        with pytest.raises(ValueError):
            GAParameters(population_size=5)
        with pytest.raises(ValueError):
            GAParameters(crossover_rate=1.5)
        with pytest.raises(ValueError):
            GAParameters(mutation_rate=-0.1)

    def test_to_dict(self):
        params = GAParameters()
        d = params.to_dict()
        assert 'population_size' in d
        assert 'crossover_rate' in d


# ============================================================
# Suites (Test Functions) Tests
# ============================================================

class TestSuites:
    def test_sphere_global_optimum(self):
        assert sphere_function([0.0, 0.0, 0.0]) == 0.0

    def test_sphere_positive(self):
        assert sphere_function([1.0, 2.0]) > 0

    def test_rosenbrock_global_optimum(self):
        assert rosenbrock_function([1.0, 1.0]) == 0.0

    def test_rastrigin_global_optimum(self):
        assert rastrigin_function([0.0, 0.0]) == 0.0

    def test_ackley_global_optimum(self):
        val = ackley_function([0.0, 0.0])
        assert abs(val) < 1e-10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
