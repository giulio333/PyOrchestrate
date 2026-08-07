# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed

- **Breaking:** `PyOrchestrate.settings` has been removed. `LOG_FOLDER` and
  `LOG_LEVEL` were read by nothing, and `LOG_FOLDER` pointed inside the
  installed package (`site-packages/PyOrchestrate/logs`), which is not a
  writable location. Configure logging through `LoggerFactory.set_defaults()`
  or the agent's `logger_config` instead.
- `PyOrchestrate/web_interface/static.js`, referenced by nothing and not
  shipped in the wheel.
- **Breaking:** `PyOrchestrate/core/utilities/scheduler.py` and its `Scheduler`
  class. Nothing in the package, the tests or the examples imported it, yet it
  was listed in `sphinx/utilities.rst` and therefore published in the API
  reference as if it were supported. Use `PeriodicAgent` for scheduled work, or
  `PyOrchestrate.utilities.periodic_timer.PeriodicTimer` for a bare timer.
- The `if __name__ == "__main__"` demo block in
  `PyOrchestrate/utilities/logguru.py`. Examples belong in `examples/`.
- `requirements-dev.txt` and `requirements-web.txt`, replaced by the `dev`
  dependency group and the `web` extra in `pyproject.toml`.
- `.devcontainer/`, which declared only `tasks` — no `image`, `build` or
  `dockerComposeFile` — and therefore never defined a usable environment. Use
  `uv sync --extra web && uv run pytest`.
- The Copilot guidance under `.github/` (`copilot-instructions.md`,
  `instructions/`, `context/`, `chatmodes/`). Nothing kept those 3,672 lines in
  sync with the code: they ended up offering copy-paste snippets importing
  `HeartbeatPlugin`, which does not exist, and importing
  `AgentTerminationStatus`, `OrchestratorEvent` and `RunMode` from
  `PyOrchestrate.core.utilities`, which exports none of them. `CLAUDE.md` and
  `.claude/skills/` are now the single place where the conventions live.

### Changed

- **Breaking:** `MessageRouter` takes an `OrchestratorEventBus` as its first
  argument instead of an `EventManager`, and exposes it as `router.event_bus`
  rather than `router.event_manager`. Framework integrations that build a
  router by hand must pass `orchestrator.event_bus`; passing the bare event
  manager still dispatches callbacks but records nothing in history.
- **Breaking:** `fastapi`, `uvicorn` and `pydantic` are no longer core
  dependencies. They are only used by the web interface and now live in the
  `web` extra: install with `pip install "PyOrchestrate[web]"` to keep
  `pyorchestrate-web` working.
- **Breaking:** `requests` is no longer a dependency. The package never
  imported it; only the examples do. Install it yourself to run those.
- **Breaking:** `EventManager` keys its listeners by the enum member instead of
  by `event.name`. `AgentEvent` and `OrchestratorEvent` overlap on
  `AGENT_READY`, `AGENT_TERMINATED`, `AGENT_ERROR` and `AGENT_HEARTBEAT`, and
  those members used to share a single listener list: a callback registered for
  `AgentEvent.AGENT_ERROR` was invoked when the orchestrator emitted
  `OrchestratorEvent.AGENT_ERROR`. Code that relied on that collision must now
  register the member the source actually emits.
- The version number has a single source of truth. It is declared only in
  `pyproject.toml` and exposed as `PyOrchestrate.__version__`, read from the
  distribution metadata. `CLIConstants.VERSION` and the FastAPI `version` now
  derive from it instead of repeating the literal.
- Dependencies upgraded to close the advisories reported against the
  repository, including `starlette` 1.3.1 (via `fastapi` 0.140.0) and
  `urllib3` 2.7.0.
- Docstrings, comments and error messages translated to English across
  `logguru.py`, `memory.py` and the Sphinx configuration.

### Fixed

- Asking the event store for zero events returned the whole ring buffer. Every
  `last()` implementation ended in `return items[-n:]`, and `items[-0:]` is
  `items[0:]`: `pyorchestrate history --last 0`, `GET /api/history?last=0` and
  `event_bus.get_history(limit=0)` all answered with up to `history_max_events`
  records — 5000 by default — pushed over ZeroMQ and rendered into the CLI
  table. A negative `n` was worse still, returning a slice counted from the
  front of the buffer. A non-positive `n` now returns an empty list, in
  `RingBufferStore`, `BucketRingStore` and `EventStore` alike.
- `history-stats` never counted heartbeats, and printed a total that
  contradicted its own breakdown. `EventStore.stats()` read only the default
  ring buffer, but `record()` routes each event to its configured policy store
  and every orchestrator installs a `BucketRingStore` for `agent_heartbeat`
  (`Orchestrator.__init__`), so those events were counted nowhere:
  `history-stats` reported `Total Events: 8` above a breakdown summing to 4.
  The root cause was `BucketRingStore.stats()`, which raised
  `NotImplementedError` — the framework's own policy did not satisfy the
  `StorePolicy` interface documented for custom ones. It now keeps the same
  counters as `RingBufferStore`, and `EventStore.stats()` sums every store,
  skipping a custom policy that still raises rather than failing the query.
  The CLI labels the two figures for what they measure, since they legitimately
  diverge once a buffer evicts: `Default buffer` and `Retained in all buffers`
  count what is still held, `Event Type Breakdown (recorded since start)` counts
  everything recorded.
- A `ChannelHandler` nobody stopped could abort the process at exit instead of
  letting it end. Its polling thread is a daemon, so nothing waits for it: when
  the interpreter closed the channel underneath it, `receive()` raised
  `OSError: handle is closed`, the loop logged the error, and writing to
  `stderr` while the runtime was finalizing hit
  `_enter_buffered_busy: could not acquire lock` and killed the process with
  `SIGABRT`. That is what turned four of the last twelve CI runs red with the
  whole suite already passed, and it reaches any application embedding an
  orchestrator. A closed channel now ends the loop instead of being logged once
  per poll, an `atexit` hook signals and joins the handlers still running, and
  nothing is written to the log while the interpreter is finalizing.
- Agent lifecycle events never reached the event store. `MessageRouter` was
  built on the bare `EventManager`, so routed `agent_started`, `agent_ready`,
  `agent_heartbeat`, `agent_error` and `agent_terminated` triggered the
  registered callbacks but bypassed `OrchestratorEventBus.emit()` and therefore
  `EventStore`: CLI `history`, `history-stats`, `get_agent_timeline()` and the
  web history endpoint saw none of them. The router now receives the bus.
- `status AGENT_NAME` and `dependencies` returned an internal error for any
  agent. Both handlers read `orchestrator.dependencies`, an attribute removed
  when dependency handling moved into `DependencyGraph`; they now read
  `orchestrator.dependency_graph.dependencies`. The web interface endpoints
  `/api/agents/{agent_name}` and `/api/orchestrator/dependencies`, which
  delegate to the same handlers, are fixed with them.
- The `shutdown` command left every agent running. It only set
  `_shutdown_requested`, which made `Orchestrator.join()` leave its loop and go
  straight to closing the message router and finalizing plugins: agents
  survived with their service channel already closed, and non-daemon threads
  kept the interpreter alive. `join()` now stops every agent, waits for them
  within `agent_stop_timeout`, force-terminates surviving process agents and
  reports any thread agent that cannot be terminated, all before the channel
  handlers and the plugins are shut down.
- `PoolAgentConfig` declared its class default as `agent_entry` while the rest
  of the class used `agents_entry`. A `PoolAgent` without an explicit
  `agents_entry` raised `AttributeError` inside `setup()` instead of emitting
  the documented validation warning.
- `ZeroMQPair.finalize()` had an empty body and never released its socket or
  context, unlike the other four ZeroMQ plugins. Each agent shutdown leaked a
  file descriptor and an I/O thread.
- No `PoolAgent` could run under an orchestrator with the command interface
  enabled, which is the default. `setup()` built its inner `Orchestrator` with
  the default configuration, so every pool tried to bind the parent's
  `tcp://*:5555` and died with `Address already in use` before registering any
  child. The inner orchestrator is now built from
  `PoolAgentConfig.orchestrator_config`, and without one its command interface
  is disabled.
- `DependencyGraph.topological_sort()` wrote an empty list into
  `self.dependencies` for every agent it was asked to order. Since
  `Orchestrator.start()` sorts, from that point on the `dependencies` command
  (and `/api/orchestrator/dependencies`) reported every registered agent,
  against the documented payload, and `has_dependencies()` answered `True` for
  a graph holding no edge at all. Sorting now reads the graph through a local
  view, and `add_dependency()` with an empty list adds no node.
- `PoolAgent.setup()` passed its entries to `register_agent()` positionally, so
  each child's `ControlEvents` arrived as `custom_plugin`, its `StateEvents` as
  `control_events`, the real `state_events` was dropped and `AgentEntry.plugin`
  was never forwarded. The arguments are now passed by keyword.
- An agent killed by an invalid configuration left no trace beyond a log line.
  `BaseAgent.run()` caught `ConfigValidationError` without sending the
  `AGENT_ERROR` status its generic error branch sends, so the failure produced
  no `agent_error` record in the event store, no `OrchestratorEvent.AGENT_ERROR`
  callback and nothing in `history`. The validation message is now reported as
  `error_message`, and the log line finally includes it instead of dropping the
  exception.
- `ZeroMQPubSub`, `ZeroMQReqRep`, `ZeroMQPushPull` and `ZeroMQRouterDealer`
  raised `RuntimeError` from `finalize()` when `initialize()` had never run or
  had failed, since the `socket` property rejects an uninitialized socket. They
  now return early like `ZeroMQPair`. `PluginManager.finalize_plugins()` logs
  and swallows plugin exceptions, so the visible effect was log noise on
  shutdown rather than a crash.
- The two comments in `PeriodicTimer.wait()` described each other's branch:
  resetting the timer is what *drops* the accumulated delay, and keeping the
  absolute schedule is what compensates for it. The behaviour was always
  correct and is now covered by `test/test_periodic_timer.py`.

### Added

- `PoolAgentConfig.orchestrator_config`, the configuration of the orchestrator
  a pool creates for its children — use it to give the inner orchestrator a
  command port of its own.
- `examples/example_readiness_barrier.py`, the runnable version of the
  readiness barrier documented under "Ordering Is Not Readiness": a dependent
  agent waiting on an event its dependency sets. The page previously showed a
  single class, without the registration that shares the event.

- `Orchestrator.Config.agent_stop_timeout` (default `10.0`), the budget shared
  by all agents while shutdown waits for them to terminate.
- `WorkerPoolScheduler.shutdown_all()` and `AgentLifecycleManager.shutdown_all()`,
  the blocking counterparts of `stop_all()` used by the shutdown path. They
  return the names of the agents that are still alive afterwards.
- Documentation for `PoolAgent` (`PoolProcessAgent`, `PoolThreadAgent`) and for
  the four previously undocumented ZeroMQ plugins: `ZeroMQPushPull`,
  `ZeroMQRouterDealer`, `ZeroMQPair` and `ZeroMQPoller`.
- `PyOrchestrate.cli` and `PyOrchestrate.web_interface.server` in the generated
  API reference.
- `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md` and issue/pull request
  templates.

## [0.2.0]

First versions tracked before this changelog existed. See the
[commit history](https://github.com/giulio333/PyOrchestrate/commits/main) for
details.

[Unreleased]: https://github.com/giulio333/PyOrchestrate/compare/main...HEAD
[0.2.0]: https://github.com/giulio333/PyOrchestrate/releases/tag/v0.2.0
