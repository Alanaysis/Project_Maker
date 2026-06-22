"""Tests for the Grid World environment."""

import pytest
import numpy as np

from src.grid_world import GridWorld, Action, State


class TestState:
    """Tests for the State class."""

    def test_state_creation(self):
        state = State(2, 3)
        assert state.row == 2
        assert state.col == 3

    def test_state_equality(self):
        s1 = State(1, 2)
        s2 = State(1, 2)
        s3 = State(2, 1)
        assert s1 == s2
        assert s1 != s3

    def test_state_hash(self):
        s1 = State(1, 2)
        s2 = State(1, 2)
        assert hash(s1) == hash(s2)

    def test_state_to_tuple(self):
        state = State(3, 4)
        assert state.to_tuple() == (3, 4)


class TestGridWorld:
    """Tests for the GridWorld class."""

    def test_initialization(self):
        env = GridWorld(rows=5, cols=5, start=(0, 0), goal=(4, 4))
        assert env.rows == 5
        assert env.cols == 5
        assert env.start == State(0, 0)
        assert env.goal == State(4, 4)

    def test_grid_with_walls(self):
        walls = [(1, 1), (2, 2)]
        env = GridWorld(rows=5, cols=5, walls=walls)
        assert env.grid[1, 1] == 1
        assert env.grid[2, 2] == 1

    def test_grid_with_traps(self):
        traps = [(3, 3)]
        env = GridWorld(rows=5, cols=5, traps=traps)
        assert env.grid[3, 3] == 3

    def test_goal_is_set(self):
        env = GridWorld(rows=5, cols=5, goal=(4, 4))
        assert env.grid[4, 4] == 2

    def test_reset(self):
        env = GridWorld(rows=5, cols=5, start=(0, 0), goal=(4, 4))
        env.agent_pos = State(3, 3)
        state = env.reset()
        assert state == (0, 0)
        assert env.agent_pos == State(0, 0)

    def test_step_valid_move(self):
        env = GridWorld(rows=5, cols=5, start=(2, 2), goal=(4, 4))
        env.reset()

        # Move right
        next_state, reward, done, info = env.step(Action.RIGHT)
        assert next_state == (2, 3)
        assert reward == GridWorld.REWARD_STEP
        assert not done

    def test_step_into_wall(self):
        walls = [(1, 1)]
        env = GridWorld(rows=5, cols=5, start=(1, 0), goal=(4, 4), walls=walls)
        env.reset()

        # Try to move into wall
        next_state, reward, done, info = env.step(Action.RIGHT)
        assert next_state == (1, 0)  # Stay in place
        assert reward == GridWorld.REWARD_WALL
        assert info.get("hit_wall") is True

    def test_step_into_boundary(self):
        env = GridWorld(rows=5, cols=5, start=(0, 0), goal=(4, 4))
        env.reset()

        # Try to move up from top-left corner
        next_state, reward, done, info = env.step(Action.UP)
        assert next_state == (0, 0)  # Stay in place
        assert reward == GridWorld.REWARD_WALL

    def test_step_reach_goal(self):
        env = GridWorld(rows=5, cols=5, start=(3, 4), goal=(4, 4))
        env.reset()

        # Move down to goal
        next_state, reward, done, info = env.step(Action.DOWN)
        assert next_state == (4, 4)
        assert reward == GridWorld.REWARD_GOAL
        assert done is True
        assert info.get("reached_goal") is True

    def test_step_into_trap(self):
        traps = [(2, 2)]
        env = GridWorld(rows=5, cols=5, start=(1, 2), goal=(4, 4), traps=traps)
        env.reset()

        # Move down into trap
        next_state, reward, done, info = env.step(Action.DOWN)
        assert next_state == (2, 2)
        assert reward == GridWorld.REWARD_TRAP
        assert done is True
        assert info.get("fell_in_trap") is True

    def test_is_terminal(self):
        env = GridWorld(rows=5, cols=5, start=(0, 0), goal=(4, 4), traps=[(2, 2)])
        assert env.is_terminal(4, 4) is True
        assert env.is_terminal(2, 2) is True
        assert env.is_terminal(0, 0) is False

    def test_render(self):
        env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2))
        env.reset()
        rendered = env.render()
        assert "A" in rendered  # Agent
        assert "G" in rendered  # Goal

    def test_get_all_states(self):
        walls = [(1, 1)]
        env = GridWorld(rows=3, cols=3, start=(0, 0), goal=(2, 2), walls=walls)
        states = env.get_all_states()
        assert (1, 1) not in states
        assert len(states) == 8  # 9 - 1 wall

    def test_state_index_conversion(self):
        env = GridWorld(rows=5, cols=5)
        assert env.get_state_index(0, 0) == 0
        assert env.get_state_index(0, 4) == 4
        assert env.get_state_index(1, 0) == 5
        assert env.index_to_state(0) == (0, 0)
        assert env.index_to_state(4) == (0, 4)
        assert env.index_to_state(5) == (1, 0)

    def test_n_states(self):
        env = GridWorld(rows=5, cols=5)
        assert env.n_states == 25

    def test_n_actions(self):
        env = GridWorld(rows=5, cols=5)
        assert env.n_actions == 4
