"""
Example demonstrating ZeroMQ Push/Pull pattern for distributed task processing.

This example shows how to use the ZeroMQPushPull class to create a distributed
processing pipeline with multiple workers.

The Push/Pull pattern is useful for:
- Distributing tasks to workers (load balancing)
- Creating data processing pipelines
- Asynchronous task distribution

Run multiple instances of this script with --worker to create multiple workers.
"""

import argparse
import random
import time
from threading import Thread

from PyOrchestrate.core.plugins.com import ZeroMQPushPull, SocketType
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent import PeriodicProcessAgent, LoopingProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQPushPull, SocketType


class PushAgent(PeriodicProcessAgent):
    """Agent that pushes tasks to workers using ZeroMQ PUSH socket."""

    class Config(PeriodicProcessAgent.Config):
        """Configuration for the PushAgent."""

        limit = 40
        execution_interval = 0.05  # 1 second between tasks
        counter: int = 1
        num_workers: int = 3  # Numero di worker da terminare

    class Plugin(PeriodicProcessAgent.Plugin):
        """Plugin for the PushAgent."""

        zmq = ZeroMQPushPull("tcp://*:5555", SocketType.PUSH, hwm=1)

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()

        task = f"Task {self.config.counter}"
        self.logger.info(f"Pushing task: {task}")
        self.plugin.zmq.send(task.encode(), blocking=True)
        self.config.counter += 1

    def on_close(self):
        super().on_close()

        # Invia un messaggio END per ogni worker
        self.logger.info(
            f"Sending termination signal to {self.config.num_workers} workers"
        )
        for i in range(self.config.num_workers):
            self.logger.debug(f"Sending END signal {i+1}/{self.config.num_workers}")
            self.plugin.zmq.send(b"END")


class PullAgent(LoopingProcessAgent):
    """Agent that pulls and processes tasks using ZeroMQ PULL socket."""

    class Config(LoopingProcessAgent.Config):
        """Configuration for the PullAgent."""

        worker_id: int = 1
        processing_weight: float = 1  # Simulated processing time

    class Plugin(LoopingProcessAgent.Plugin):
        """Plugin for the PullAgent."""

        zmq = ZeroMQPushPull("tcp://localhost:5555", SocketType.PULL, hwm=1)

    config: Config
    plugin: Plugin

    def cycle(self):
        super().cycle()

        # Receive a task
        task = self.plugin.zmq.recv().decode()
        self.logger.info(f"Worker {self.config.worker_id} received: {task}")

        if task == "END":
            self.logger.info(
                f"Worker {self.config.worker_id} received termination signal"
            )
            self.stop()

        time.sleep(self.config.processing_weight)


if __name__ == "__main__":
    orchestrator = Orchestrator()

    # Register push agent (producer)
    orchestrator.register_agent(PushAgent, "PushAgent")

    # Register multiple pull agents (workers)
    for worker_id in range(1, 4):  # Create 3 workers
        orchestrator.register_agent(
            PullAgent,
            f"PullAgent_{worker_id}",
            custom_config=PullAgent.Config(
                worker_id=worker_id, processing_weight=worker_id
            ),
        )

    # Start all agents
    orchestrator.start()

    # Wait for agents to complete
    orchestrator.join()
