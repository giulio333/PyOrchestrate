---
title: Orchestrator Heartbeat Plugin
---

# Orchestrator Heartbeat Plugin

This example demonstrates how the orchestrator heartbeat plugin can be used to send periodic
heartbeat STATUS messages and collect simple stats.

## Overview

This example shows the minimal steps required to wire the framework's heartbeat support into an
Orchestrator and an agent. It focuses on the high-level flow used in other examples in this
directory:

1. Implement an agent that performs work and exposes lifecycle hooks (here: `CriticalAgent`).
2. Add the heartbeat plugin to the orchestrator via the `Plugin` subclass.
3. Register the agent with the orchestrator and start the orchestrator.
4. The heartbeat plugin emits periodic STATUS messages and provides a small API for collecting
	 runtime statistics (used in `on_close` in the example).

## Agent implementation

The `CriticalAgent` in the example is a tiny `PeriodicProcessAgent` used to demonstrate
heartbeat lifecycle integration. Key points:

1) Initialization (`setup`) — use `setup` to prepare state and log startup:

```python
def setup(self):
	super().setup()
	self.logger.info("CriticalAgent setup complete")
```

2) Periodic work (`runner`) — the agent's main loop logs activity to show it's alive:

```python
def runner(self):
	super().runner()
	# Simulate work
	self.logger.info("CriticalAgent working...")
```

3) Shutdown hook (`on_close`) — query the heartbeat plugin for final stats:

```python
def on_close(self):
	super().on_close()
	if self.plugin.heartbeat:
		stats = self.plugin.heartbeat.get_status()
		self.logger.info(f"Final Heartbeat Stats: {stats}")
```

## Orchestrator configuration

The orchestrator configures the heartbeat plugin by exposing it on the `Plugin` inner class:


Add the plugin to the orchestrator's `Plugin` inner class. This small snippet shows the
assignment used in the example:

```python
class Plugin(OrchestratorPlugin):
	heartbeat = OrchestratorHeartbeatPlugin(agent_send_interval=2)
```

Control how the orchestrator runs via its `Config` class:

```python
class Config(Orchestrator.Config):
	run_mode = RunMode.DAEMON
```

## How to run this example

To run the example follow the usual steps found in other examples:

1. Create an instance of `MyOrchestrator`.
2. Register one or more agents with `orchestrator.register_agent(...)`.
3. Call `orchestrator.start()` and then `orchestrator.join()` to wait for termination.

Concretely, the bottom of the full example performs these steps:

```python
orchestrator = MyOrchestrator()
orchestrator.register_agent(CriticalAgent, "CriticalAgent")
orchestrator.start()
orchestrator.join()
```

## When to use

Use this example when you want to validate or document how the heartbeat plugin integrates with
the orchestrator and agents. It's a small, self-contained reference that shows lifecycle
interactions and how to collect final heartbeat statistics.

```python
"""
Example demonstrating the OrchestratorHeartbeatPlugin.

This example shows how to use the heartbeat plugin to send periodic
heartbeat messages to the orchestrator for monitoring purposes.
"""

from PyOrchestrate.core.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.orchestrator.orchestrator import OrchestratorPlugin
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins.heartbeat import (
	OrchestratorHeartbeatPlugin,
)


class CriticalAgent(PeriodicProcessAgent):
	"""Agent that demonstrates heartbeat functionality."""

	class Config(PeriodicProcessAgent.Config):
		"""Configuration for the CriticalAgent."""

		limit = 10
		execution_interval = 3.0  # Execute every 3 seconds

	config: Config

	def setup(self):
		"""Setup method called when agent starts."""
		super().setup()
		self.logger.info("CriticalAgent setup complete")

	def runner(self):
		"""Main agent logic."""
		super().runner()

		# Simulate some work
		self.logger.info("CriticalAgent working...")

	def on_close(self):
		super().on_close()

		if self.plugin.heartbeat:
			stats = self.plugin.heartbeat.get_status()
			self.logger.info(f"Final Heartbeat Stats: {stats}")



class MyOrchestrator(Orchestrator):
	class Plugin(OrchestratorPlugin):
		"""Plugins for the orchestrator."""

		heartbeat = OrchestratorHeartbeatPlugin(agent_send_interval=2)

	class Config(Orchestrator.Config):
		"""Configuration for the MyOrchestrator."""

		run_mode = RunMode.DAEMON


if __name__ == "__main__":

	# Create orchestrator with heartbeat plugin
	orchestrator = MyOrchestrator()

	# Register heartbeat agent
	orchestrator.register_agent(CriticalAgent, "CriticalAgent")

	orchestrator.start()
	orchestrator.join()

```
