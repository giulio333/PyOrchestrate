"""Readiness barrier between two process agents.

The dependency graph orders the start requests: `database` is submitted before
`api`. It does not wait for the database to become usable — `api` is started a
few milliseconds later, while the database is still loading — so the API waits
for it explicitly, on an event both agents received at registration.

Run it with:

    python examples/example_readiness_barrier.py
"""

import multiprocessing
import time

from PyOrchestrate.core.agent.periodic_agent import PeriodicProcessAgent
from PyOrchestrate.core.orchestrator import Orchestrator


class Database(PeriodicProcessAgent):
    """Agent that is not usable as soon as it starts."""

    class Config(PeriodicProcessAgent.Config):
        execution_interval = 0.5
        limit = 4

    config: Config

    def setup(self):
        super().setup()

        self.logger.info("loading, not usable yet")
        time.sleep(2)  # whatever makes the agent slow to become usable

        # Releases every agent waiting on the barrier.
        self.database_ready.set()
        self.logger.info("ready, other agents may proceed")

    def runner(self):
        self.logger.info("serving queries")


class Api(PeriodicProcessAgent):
    """Agent that must not run before the database is usable."""

    class Config(PeriodicProcessAgent.Config):
        execution_interval = 0.5
        limit = 3

    config: Config

    def setup(self):
        super().setup()

        # Blocking here is safe: the orchestrator waits for `start_event`, which
        # is set before setup() runs, so agent_start_timeout does not apply.
        self.logger.info("waiting for the database")
        if not self.database_ready.wait(timeout=30):
            raise RuntimeError("database did not become ready")

        self.logger.info("database is ready, starting to serve")

    def runner(self):
        self.logger.info("answering requests")


if __name__ == "__main__":
    # multiprocessing.Event, because both agents are process agents: a
    # threading.Event cannot be pickled into them and the start fails with
    # "cannot pickle '_thread.lock' object".
    database_ready = multiprocessing.Event()

    orchestrator = Orchestrator(
        config=Orchestrator.Config(enable_command_interface=False)
    )

    # The keyword argument reaches each agent as `self.database_ready`.
    orchestrator.register_agent(Database, "database", database_ready=database_ready)
    orchestrator.register_agent(Api, "api", database_ready=database_ready)

    # Orders the start requests; the barrier above is what makes the API wait.
    orchestrator.add_dependency("api", ["database"])

    orchestrator.start()
    orchestrator.join()
