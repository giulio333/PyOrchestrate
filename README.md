# PyOrchestrate Framework

[![PyOrchestrate Test](https://github.com/giulio333/PyOrchestrate/actions/workflows/python-app.yml/badge.svg)](https://github.com/giulio333/PyOrchestrate/actions/workflows/python-app.yml)

**PyOrchestrate** is a Python framework designed to simplify the creation and management of multi-process and
multi-thread architectures. It provides a structured approach to orchestrating tasks, allowing developers to focus on
logic while the framework handles complexities like process and thread management.

📚 **[Read the documentation →](https://pyorchestrate.mintlify.app)**

This README is a tour of the framework. The documentation site covers every
class, option and command in depth, and the
[API Reference](https://pyorchestrate.mintlify.app/api/agent) is generated from
the docstrings, so it never drifts from the code.

## Features

- **Centralized Management**: the **Orchestrator** provides unified control over all agents
- **Flexible Execution Models**: every agent comes in a process and a thread flavour
- **Multiple Agent Types**: base, looping, periodic and pool agents for different execution patterns
- **Configuration-First Design**: inner `Config` classes with type hints and validation
- **Plugin System**: inner `Plugin` classes extend an agent without subclassing it
- **Inter-Agent Communication**: ZeroMQ plugins (Pair, PubSub, PushPull, ReqRep, RouterDealer) plus a Poller for watching several sockets at once
- **Lifecycle Management**: automated setup, execution and cleanup of agent resources
- **Structured Logging**: Loguru-based logging with per-agent log files
- **CLI and Web Interface**: inspect and drive a running orchestrator from outside

* * *

## Installation

Python 3.11+ is required.

``` bash
git clone https://github.com/giulio333/PyOrchestrate.git
cd PyOrchestrate
pip install .
```

This also installs the `pyorchestrate` CLI. The web interface is an optional
extra, since `fastapi`, `uvicorn` and `pydantic` are only needed by it:

``` bash
pip install ".[web]"
```

For development, [`uv`](https://docs.astral.sh/uv/) reproduces the exact locked
environment, dev tools included — see [CONTRIBUTING.md](CONTRIBUTING.md):

``` bash
uv sync --extra web
uv run pytest
```

* * *

## Quick Start

Define an agent by inheriting from one of the built-in classes, then hand it to
an `Orchestrator`. Here is a `FileWriter` that logs a message every second and
stops after five cycles ([`examples/example_periodic_agent.py`](examples/example_periodic_agent.py)):

``` python
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.agent.periodic_agent import PeriodicProcessAgent


class FileWriter(PeriodicProcessAgent):
    """Agent Class that logs a message periodically."""

    class Config(PeriodicProcessAgent.Config):
        """Process agent configuration class."""

        limit = 5
        execution_interval = 1
        directory = "/tmp"

    config: Config

    def setup(self):
        super().setup()
        self.logger.info(f"FileWriter {self.name} initialized. pid={self.pid}")
        self.logger.info(f"Working with directory: {self.config.directory}")

    def runner(self):
        self.logger.info("Doing some work")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    # register agents
    orchestrator.register_agent(FileWriter, "FileWriter")
    orchestrator.register_agent(
        FileWriter,
        "FileWriter2",
        custom_config=FileWriter.Config(execution_interval=0.2, directory="/tmp2"),
    )

    # start agent
    orchestrator.start()

    # wait for agent to complete
    orchestrator.join()
```

Agents log to `logs/<AgentName>.log`, one file per agent.

Two conventions are worth learning early:

- **Call `super()` first in every lifecycle hook.** `setup`, `execute` and
  `runner` do bookkeeping in the base class — counters, limits, plugin wiring.
- **Re-declare the annotation** (`config: Config`, `plugin: Plugin`) below the
  inner class. The framework finds the inner class without it, but the
  annotation is what gives type checkers and editors your own settings on
  `self.config` instead of the base class's.

→ [Getting started](https://pyorchestrate.mintlify.app/learn/agents/index) ·
[Configuration and validation](https://pyorchestrate.mintlify.app/learn/config_and_validation)

* * *

## Agent Types

Each type exists in a `Process` and a `Thread` flavour: pick a process for
CPU-bound, isolated work, a thread for I/O-bound work that shares memory.

| Type | Hook to implement | Use it for |
| --- | --- | --- |
| [`BaseAgent`](https://pyorchestrate.mintlify.app/learn/agents/built-in-agents/baseagent) | `execute` | a task that runs once |
| [`LoopingAgent`](https://pyorchestrate.mintlify.app/learn/agents/built-in-agents/loopingagent) | `cycle` | continuous processing, as fast as it can go |
| [`PeriodicAgent`](https://pyorchestrate.mintlify.app/learn/agents/built-in-agents/periodicagent) | `runner` | work on a schedule, with delay compensation |
| [`PoolAgent`](https://pyorchestrate.mintlify.app/learn/agents/built-in-agents/poolagent) | `setup` | a *group* of collaborating agents supervised by an inner orchestrator |

Every type drives your hook from a `@final` method you must not override —
`LoopingAgent.execute`, `PeriodicAgent.cycle`, `PoolAgent.runner` — so
implement the one named in the table. A `PoolAgent` registers its children in
`setup` and can observe each supervision pass through `pre_runner` and
`post_runner`.

* * *

## Plugins

Plugins extend an agent through the inner `Plugin` class. The communication
plugins wrap the ZeroMQ patterns — `ZeroMQPair`, `ZeroMQPubSub`,
`ZeroMQPushPull`, `ZeroMQReqRep`, `ZeroMQRouterDealer` — with `ZeroMQPoller`
for serving several sockets at once.

``` python
from PyOrchestrate.core.agent import PeriodicProcessAgent, LoopingProcessAgent
from PyOrchestrate.core.plugins.com import ZeroMQPubSub, SocketType


class Publisher(PeriodicProcessAgent):

    class Config(PeriodicProcessAgent.Config):
        limit = 100
        execution_interval = 0.05
        counter: int = 1

    class Plugin(PeriodicProcessAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://*:5556", SocketType.PUB)

    config: Config
    plugin: Plugin

    def runner(self):
        super().runner()

        self.plugin.zmq.send(f"Message {self.config.counter}".encode())
        self.config.counter += 1

    def on_close(self):
        super().on_close()

        self.plugin.zmq.send(b"END")


class Subscriber(LoopingProcessAgent):

    class Plugin(LoopingProcessAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://localhost:5556", SocketType.SUB)

    plugin: Plugin

    def cycle(self):
        super().cycle()

        message = self.plugin.zmq.recv().decode()
        self.logger.info(f"Received: {message}")

        if message == "END":
            self.stop()
```

Plugins are initialized after the configuration is validated and before
`setup()`, and are reachable as `self.plugin.<name>`.

> [!WARNING]
> Do not bind an agent socket to port **5555**. That is the orchestrator's own
> default `command_zmq_address`: an agent binding it collides with the
> `CommandInterface` and silently never delivers a message. Use another port,
> as the examples do.

→ [Communication plugins](https://pyorchestrate.mintlify.app/learn/agents/plugins/communication-plugins) ·
runnable examples in [`examples/communication/`](examples/communication/)

* * *

## Command Line Interface

`pyorchestrate create <app_name>` scaffolds a project (`models/`,
`configurations/` and a `starter.py`). The remaining commands talk to a running
orchestrator over ZeroMQ:

| Command | Description |
| --- | --- |
| `ps` | list all agents and their status |
| `status` | orchestrator or single-agent status |
| `dependencies` | show the declared agent dependencies |
| `start` / `stop` | drive a single agent |
| `history` / `history-stats` | event history and aggregated statistics |
| `stats` | live resource usage, like `docker stats` |
| `commands` | list the commands this orchestrator allows |
| `shutdown` | shut the orchestrator down gracefully |

`pyorchestrate-web` serves the same information as a FastAPI web interface
(requires the `web` extra).

→ [CLI reference](https://pyorchestrate.mintlify.app/cli/index) ·
[Web interface](https://pyorchestrate.mintlify.app/cli/web-interface)

* * *

## Contributing

Bug reports, feature requests and pull requests are welcome. Read
[CONTRIBUTING.md](CONTRIBUTING.md) first: it covers the development
environment, the checks CI runs and how the documentation is built. Everything
in this repository is written in English.

## License

PyOrchestrate is released under the [MIT License](LICENSE).
