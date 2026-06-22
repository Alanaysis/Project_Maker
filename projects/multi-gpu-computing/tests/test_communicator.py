"""
Tests for Communication module.
"""

import pytest
import numpy as np
from src.core.tensor import GPUTensor, get_device
from src.core.communicator import (
    SimulationCommunicator,
    NCCLCommunicator,
    create_communicator,
)


class TestSimulationCommunicator:
    """Test SimulationCommunicator."""

    def test_init(self):
        comm = SimulationCommunicator(world_size=4, rank=0)
        comm.init()
        assert comm._initialized

    def test_allreduce_sum(self):
        comm = SimulationCommunicator(world_size=2, rank=0)
        comm.init()

        t = GPUTensor(np.array([1.0, 2.0, 3.0]), get_device(0))
        result = comm.allreduce(t, op="sum")

        # In simulation, this returns sum of all registered tensors
        assert result.shape == (3,)

    def test_allreduce_mean(self):
        comm = SimulationCommunicator(world_size=2, rank=0)
        comm.init()

        t = GPUTensor(np.array([2.0, 4.0, 6.0]), get_device(0))
        result = comm.allreduce(t, op="mean")

        assert result.shape == (3,)

    def test_broadcast(self):
        comm = SimulationCommunicator(world_size=2, rank=0)
        comm.init()

        t = GPUTensor(np.array([1.0, 2.0, 3.0]), get_device(0))
        result = comm.broadcast(t, root=0)

        np.testing.assert_array_almost_equal(result.data, [1.0, 2.0, 3.0])

    def test_allgather(self):
        comm = SimulationCommunicator(world_size=2, rank=0)
        comm.init()

        t = GPUTensor(np.array([1.0, 2.0]), get_device(0))
        results = comm.allgather(t)

        assert len(results) == 2

    def test_not_initialized_raises(self):
        comm = SimulationCommunicator(world_size=2, rank=0)
        t = GPUTensor(np.array([1.0]), get_device(0))

        with pytest.raises(RuntimeError):
            comm.allreduce(t)

    def test_comm_time_tracking(self):
        comm = SimulationCommunicator(world_size=4, rank=0)
        comm.init()

        t = GPUTensor(np.ones(100), get_device(0))
        comm.allreduce(t)
        comm.allreduce(t)

        assert comm.comm_time > 0

    def test_reset_comm_time(self):
        comm = SimulationCommunicator(world_size=2, rank=0)
        comm.init()

        t = GPUTensor(np.ones(100), get_device(0))
        comm.allreduce(t)

        assert comm.comm_time > 0
        comm.reset_comm_time()
        assert comm.comm_time == 0


class TestNCCLCommunicator:
    """Test NCCLCommunicator."""

    def test_init(self):
        comm = NCCLCommunicator(world_size=2, rank=0)
        comm.init()
        assert comm._initialized

    def test_allreduce_not_implemented(self):
        comm = NCCLCommunicator(world_size=2, rank=0)
        comm.init()
        t = GPUTensor(np.array([1.0]), get_device(0))

        with pytest.raises(NotImplementedError):
            comm.allreduce(t)


class TestFactory:
    """Test communicator factory."""

    def test_create_simulation(self):
        comm = create_communicator(4, 0, "simulation")
        assert isinstance(comm, SimulationCommunicator)
        assert comm._initialized

    def test_create_nccl(self):
        comm = create_communicator(2, 0, "nccl")
        assert isinstance(comm, NCCLCommunicator)

    def test_create_invalid(self):
        with pytest.raises(ValueError):
            create_communicator(2, 0, "invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
