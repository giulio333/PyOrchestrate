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

### Added

- `PyOrchestrate.core.utilities.messaging.is_local_only()`, which tells whether a
  socket bound to a ZeroMQ endpoint can be reached from another host. `tcp://`
  on loopback, `ipc://` and `inproc://` cannot; a wildcard, a routable address
  and a host name that cannot be resolved to loopback can. `CommandInterface`
  uses it to decide whether binding deserves a warning.

- `Orchestrator.shutdown()`, the complete teardown `join()` performs when its
  loop exits, callable on its own for an orchestrator nothing drives with
  `join()`. It stops and joins the agents, records the `SHUTDOWN` event, stops
  the channel handlers, finalizes the plugins and releases the event bus and the
  message channel, returning the names of any agents still alive. Calling it
  twice is a no-op.
- `Orchestrator.reap_terminated_agents()`, one pass of the bookkeeping the
  `join()` loop does per tick: an agent that has finished gives its worker slot
  back, which is what starts the next queued agent. Needed by any driver other
  than `join()`.
- `OrchestratorConfig` and `OrchestratorPlugin` are exported from
  `PyOrchestrate.core.orchestrator`. The package advertised twenty names,
  including internals such as `WorkerStartStatus`, but not the two classes
  needed to configure an orchestrator: they had to be imported from
  `PyOrchestrate.core.orchestrator.orchestrator`, which is what the
  documented examples were doing.
- `ZeroMQSocketPlugin`, the base the five socket plugins now derive from,
  exported from `PyOrchestrate.core.plugins`. It carries the `socket` property,
  `send()`, `recv()`, `setsockopt()` and `finalize()`; `initialize()` is its
  only abstract method. Subclass it to wrap a ZeroMQ socket type this module
  does not cover; the "Communication Plugins" page walks through one.
- `setsockopt()` on every socket plugin. It existed only on `ZeroMQPubSub`,
  although the underlying socket is the same on all of them.
- `PluginProtocol` is exported from `PyOrchestrate.core.plugins`, next to the
  plugins that implement it, instead of only from
  `PyOrchestrate.core.plugins.plugin_protocols`.

### Changed

- **Breaking:** `OrchestratorConfig.command_zmq_address` defaults to
  `"tcp://127.0.0.1:5555"` instead of `"tcp://*:5555"`. The command interface is
  enabled by default and authenticates nobody, so the old default put an
  unauthenticated control port on every network interface of every orchestrator:
  whoever reached port 5555 could `shutdown` it, `start` and `stop` its agents,
  and read the agent configurations `ps` serializes — user-defined `Config`
  fields included. Loopback is what the rest of the framework already assumed:
  the CLI connects to `tcp://127.0.0.1:5555`, `WebServerConfig.host` is
  `127.0.0.1`, and the documentation told readers to override the default in
  four different places. Deployments that need remote CLI or web clients must
  now set `command_zmq_address="tcp://*:5555"` explicitly, and should pair it
  with a restrictive `allowed_commands`.

- `CommandInterface` logs a warning when the address it binds is reachable from
  other hosts, naming the address and what an unauthenticated client can do with
  it. Deliberately a log line and not a `ValidationResult`: with the default
  `ValidationPolicy(ignore_warnings=True)` a WARNING result makes
  `BaseClassConfig._validate` raise `ConfigValidationWarning`, which would break
  every intentional wildcard bind rather than inform it.

- The `pyorchestrate create` scaffold (`CLIConstants.STARTER_TEMPLATE`) and
  `examples/cli/example_cli_interface.py` bind `tcp://127.0.0.1:5555`. The
  scaffold used to write out `tcp://*:5555` explicitly, so the first file a new
  user ran opened the port to the network.

- The README is a tour of the framework that links to the documentation site
  instead of a second copy of it: 424 lines down to 245. The `create`
  troubleshooting list, the "Modern Architecture" section that restated the
  `Config` and `Plugin` sections a second time, and the documentation build
  commands duplicated from `CONTRIBUTING.md` are gone. Both remaining snippets
  were executed before being committed. Links that pointed at `.mdx` files in
  the repository, which GitHub serves as plain text, now point at the rendered
  pages on https://pyorchestrate.mintlify.app.
- The README documents the runtime CLI commands (`ps`, `status`,
  `dependencies`, `start`, `stop`, `history`, `history-stats`, `stats`,
  `commands`, `shutdown`) and `pyorchestrate-web`. It described `create` alone,
  which is the only one of the eleven that does not talk to a running
  orchestrator.
- The documentation site links to GitHub once, from the navbar. The same link
  was also declared as a global anchor in `docs.json`, so it appeared a second
  time at the top of the sidebar on every page. The footer social link is
  unchanged.
- The Weather Collector example callouts now show their headings and render the
  `requests` installation command as a separate code block.
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
- `ZeroMQPubSub`, `ZeroMQReqRep`, `ZeroMQPushPull`, `ZeroMQRouterDealer` and
  `ZeroMQPair` derive from `ZeroMQSocketPlugin` and implement only
  `initialize()` plus what is genuinely theirs — PubSub's topic frame,
  PushPull's direction guards, RouterDealer's multipart pair, Pair's `bind`.
  339 of `com.py`'s 912 lines sat in methods with a byte-identical twin
  elsewhere in the same file: `finalize()` in five copies, the `socket`
  property in five, `send()` and `recv()` in three each. No behaviour change,
  and the constructors keep their signatures.
- `PluginProtocol.set_owner` is no longer abstract. Its body was already `pass`,
  so every plugin that ignores the owner had to write
  `return super().set_owner(owner)` to become instantiable — six copies in
  `com.py` alone. Plugins that override it are unaffected.
- `ZeroMQPubSub` raises the same "Socket not initialized. Did you forget to
  call initialize?" message as the other four when the socket is used before
  `initialize()`. Its copy of the guard said "call initialize method?".
- The `com` module's API reference entry is generated with
  `:inherited-members:`. Without it, autodoc would list each plugin with only
  its constructor and `initialize()`, dropping the `send()`/`recv()`/
  `finalize()` users actually call now that they live on the base.
- CI's blocking `flake8` run also selects `F401`, `F811` and `F841`. The
  previous `E9,F63,F7,F82` let dead code through: fourteen unused imports
  across six modules, `heartbeat.py` importing `Optional` twice in one
  statement and `core.utilities.event` twice in two, and a discarded local in
  the web interface all passed a green build.
- `PyOrchestrate.core.plugins` declares an `__all__` and imports
  `PyOrchestrate.core.plugins.heartbeat` once instead of in two consecutive
  statements, matching the other packages' layout.

### Removed (internal)

- Dead code that the narrower `flake8` select never reported: the unused
  imports above, the `if unknown_commands:` block in
  `CommandPermissions.validate_commands` whose whole body was `pass`, six
  f-strings with no placeholders, and four `except Exception as e` clauses in
  the tests that never read `e`. No behaviour change.
- The web interface's `create_pretty_json_response` is now
  `create_json_response`. It built a `pretty_json` string, discarded it and
  returned the compact `JSONResponse` its name denied — the responses are
  unchanged, the name now matches them. The helper is internal to
  `web_interface/server.py`.

### Fixed

- The three ways a runtime command can report why it failed all threw the
  reason away, each in its own place. `pyorchestrate stats` printed
  `Error: Unknown error` for every failure: it read the reason from `message`,
  while `ServiceMessage.create_command_response()` carries it under `error`, so
  a `stats` left out of `allowed_commands` never told the user which commands
  were allowed. `status AGENT_NAME` answered `500 Failed to get status for X:
  Agent X not found` for an unregistered agent, because the `404` it raises is
  caught by its own `except Exception`; `start` and `stop` re-raise
  `CommandException` and report `404` as they should. And the web interface
  answered `500 Communication error: 503: Cannot connect to orchestrator at
  ...` when the orchestrator was not running, its `503` being raised inside the
  `try` that turns anything into a `500`: an orchestrator that is simply down
  looked like a fault of the web server. The reason now survives all three
  paths, and `OutputFormatter.format_error()` is the single place the CLI
  renders it.
- The API Reference workflow could not publish anything. It committed the
  regenerated Sphinx artifact straight to `main`, which no longer accepts a
  direct push: every attempt ended in
  `GH013: Repository rule violations found for refs/heads/main`. The breakage
  was silent for weeks because a run with nothing to commit never reaches the
  push and passes, so it only surfaced once a change finally left the artifact
  stale — meaning the published API reference had been frozen at the last
  successful run. The artifact now arrives as a pull request, which is what the
  rule asks for, on a branch the job owns and force-pushes so an open pull
  request is updated in place instead of one piling up per docstring change.
- A ZeroMQ plugin terminated a context it did not own. `finalize()` called
  `zmq.Context.term()` unconditionally, but `term()` blocks until every socket
  in the context is closed: an agent whose `Plugin` class declared two socket
  plugins over one shared context — the single context per process the
  plugins' own warning asks for — hung forever in the first `finalize()`, on
  the socket its sibling still held. `PluginManager.finalize_plugins()` runs
  from the `finally` of `BaseAgent.run()`, so the agent never reached
  `close_event`: a process agent had to be force-terminated at shutdown, a
  thread agent could not be terminated at all. Terminating the context also
  poisoned it for the siblings still using it, which failed with
  `ZMQError: Context was terminated`. `finalize()` now closes its socket and
  terminates only a context the plugin itself created; one received from the
  caller belongs to the caller.
- **Breaking:** `ZeroMQPoller` allocated a `zmq.Context` nothing ever used.
  `initialize()` only builds a `zmq.Poller`, which takes no context, and
  `finalize()` never terminated the one the constructor had created, so every
  poller built without an explicit `context` left a live context — and the
  file descriptor it opens — behind for as long as the poller was referenced:
  for a poller declared in a `Plugin` class, the lifetime of the process. The
  constructor now stores the context it is given and creates none, which is
  the breaking part: `poller.context` is `None` when the argument is omitted,
  where it used to be a fresh context. The argument itself stays, so a poller
  can still be declared next to the socket plugins from the one context they
  share, and the ownership rule holds for it as it does for them — a context
  passed to the poller is never terminated by it and remains the caller's.
- The README's ZeroMQ example never delivered a message. It bound the publisher
  to `tcp://*:5555`, which is the orchestrator's own default
  `command_zmq_address`, so the socket collided with `CommandInterface` and the
  subscriber received nothing — for 50 seconds of runtime, 2 messages published
  and 0 received. Both `except:` clauses in the snippet were bare, so the
  `zmq.Again` this raised on every cycle was reported as "No weather data
  available" and read as normal operation. The README now shows the pattern
  from `examples/communication/example_zmq_pubsub.py`, which runs to
  completion, and states explicitly that port 5555 is reserved.
- Asking the event store for the history of an agent that had never sent a
  heartbeat allocated a bucket for it, permanently. `BucketRingStore.last()`
  indexed its `defaultdict`, and the agent name arrives straight from the
  request — `pyorchestrate history --agent NAME --type agent_heartbeat`, or the
  same query over HTTP — so the one component whose premise is constant memory
  had an unbounded growth path reachable from the command interface, and
  `capacity_info()` counted the phantom agents in `agents_known`. Only
  `append()` creates a bucket now.
- `Config.to_dict()` reported only the settings defined on the leaf class. It
  read `self.__class__.__dict__` instead of the MRO, so every inherited default
  was missing, and it skipped underscore keys, so the user-defined values in
  `_custom_attr` were missing too — a `PeriodicAgent` config subclass reported
  `execution_interval` and nothing else. This is what `pyorchestrate ps` and
  `GET /api/agents` print as the agent's configuration. Values are now also
  rendered JSON-encodable: an agent registered with an explicit `logger_config`
  used to fail the whole `ps` response with
  `TypeError: Object of type LoggerConfig is not JSON serializable`.
- `AgentEntry.instance` guarded with `assert`, which `python -O` strips: the
  property then returned `None` and the failure surfaced later as an
  `AttributeError`. It raises `RuntimeError` now. `OMemory.get_group_agents()`
  went through it for every member of a group and therefore raised for any
  agent that was registered but not started; it skips them instead.
- A `PoolAgent` abandoned its inner orchestrator. `setup()` builds one,
  registers the pool's agents and starts it, and nothing ever stopped it: a
  pool that reached its limit or was stopped from the outside left its children
  running. For a `PoolThreadAgent` those are non-daemon threads in the same
  process, so they outlived the whole application. `on_close()` now shuts the
  inner orchestrator down.
- A `PoolAgent` holding more agents than the inner `max_workers` never started
  the ones beyond the limit. Reclaiming the slot of a finished agent — which is
  what starts the next queued one — happens in the `Orchestrator.join()` loop,
  and the pool never calls `join()` on its inner orchestrator. That pass is now
  `Orchestrator.reap_terminated_agents()` and `PoolAgent.runner()` calls it on
  every supervision cycle. The liveness check that ends the pool also went
  through `AgentEntry.instance`, which raises `AssertionError` for an agent
  still waiting in the queue.
- `Orchestrator.stop()` could not end a `RunMode.DAEMON` `join()`, although the
  `RunMode.DAEMON` documentation offers it as one of the two ways to shut the
  orchestrator down. The loop runs until `_shutdown_requested` is set, and only
  the CLI `shutdown` command set it, so a program that called `stop()` and
  waited on `join()` hung until someone poked a private attribute. `stop()` now
  raises the flag.
- Nothing released the resources the orchestrator itself owns.
  `OrchestratorEventBus.shutdown()` existed, documented as "call this method
  during orchestrator shutdown", and had no caller anywhere in the package, so
  the `EventManager`'s `ThreadPoolExecutor` stayed up after `join()` returned;
  the agent `MessageChannel` was never closed either, keeping a queue feeder
  thread and a pipe per orchestrator. Both are now released, and
  `EventManager` registers its `atexit` backstop through a `weakref` instead of
  a bound method, which used to keep every manager — and through its listeners
  the whole orchestrator — reachable until the process exited.
- `Orchestrator.join()` and `simple_join()` raised
  `AttributeError: 'Orchestrator' object has no attribute 'start_time'` when
  called without `start()`, after the shutdown had already run: `start_time`
  was only assigned in `start()`. It is now initialized in `__init__`.
- Enabling heartbeat monitoring silently deleted every plugin an agent
  declared. `OrchestratorHeartbeatPlugin.inject_agent_heartbeat_plugin()` did
  not inject: it built a fresh `AgentPlugin(heartbeat=...)` and returned that,
  discarding whatever it was given. Because `register_agent` passes the result
  to the agent constructor as `plugin=`, which takes precedence over the
  agent's own inner `Plugin` class, an agent declaring a `ZeroMQPubSub` started
  with no socket at all as soon as an `OrchestratorHeartbeatPlugin` was added
  to the orchestrator — and the warning it logged only fired when
  `custom_plugin` had been passed explicitly, so the usual case was silent. The
  heartbeat is now attached to the container the agent would have used, and an
  agent that declares its own `heartbeat` keeps that instance.
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
- Documented examples that raised `TypeError` when copied off the site. The
  `LogMonitorAgent` of `loopingagent.mdx` overrode `execute()`, which is
  `@final` on `LoopingAgent`, and never implemented the abstract `cycle()`, so
  it could not be instantiated; it now implements `cycle()`. The
  `WeatherCollector` of `project-initialization.mdx` subclassed
  `PeriodicProcessAgent[WCConfig]`, but the agent classes are not generic, and
  bound its configuration with `config = WCConfig`, which `__init__` overwrites
  — the custom config was silently ignored. It now uses `Config = WCConfig`.
  The manual `MyAgent` of `communication-plugins.mdx` declared
  `def __init__(self)`, which rejects every keyword `register_agent` passes;
  it now forwards `**kwargs`. `test/test_documented_examples.py` covers all
  three, and asserts the broken forms still fail.
- `project-initialization.mdx` told the reader to scaffold with
  `PyOrchestrate.cli start weather_collector`. `start` is a runtime command
  against a running orchestrator; the scaffolding command is
  `pyorchestrate create`. The page also showed a `config/` directory that the
  CLI never creates — it creates `models/` and `configurations/` — and placed
  `WCConfig` in `models/` while importing it from `configurations`.
- The `LoopingAgent` class diagram derived `BaseProcessAgent` and
  `BaseThreadAgent` from `LoopingAgent`. They derive from `BaseAgent`; the
  subclasses of `LoopingAgent` are `LoopingProcessAgent` and
  `LoopingThreadAgent`.
- `periodicagent.mdx` documented `execute` as `@abstractmethod` "to be
  overridden by the derived class", contradicting the section below it and the
  `@final` on `LoopingAgent.execute()`. `runner` is the method to implement.
- The `OrchestratorEvent.AGENT_HEARTBEAT` docstring said the event takes no
  arguments. `MessageRouter` emits it with `agent_name`, as the narrative pages
  already documented. `AgentEvent.AGENT_HEARTBEAT`, the agent-side event, does
  take no arguments and is unchanged.
- Two `#validation` links pointed at `/learn/agents/index#validation`, a
  heading that does not exist on that page. They now point at
  `/learn/config_and_validation#validation`.
- `README.md` described `PoolProcessAgent` and `PoolThreadAgent` as pools of
  worker processes and threads, and recommended `PoolProcessAgent` for
  distributing computation across processes — the opposite of what
  `poolagent.mdx` says. A `PoolAgent` supervises a declared group of child
  agents through an inner orchestrator; `process`/`thread` describes how the
  pool itself runs, not its children.
- The CLI pages still warned that `status AGENT_NAME` and `dependencies`
  "reference a removed source attribute and can return an internal error", and
  that routed lifecycle callbacks are missing from the event history. Both were
  fixed in 385e4db and 917cee1; `runtime-commands.mdx` had already been
  updated, `cli/index.mdx` and `cli/examples.mdx` had not.
- `validation.mdx` claimed the orchestrator starts only the agents that pass
  validation. All of them are started; the invalid one fails inside
  `BaseAgent.run()`, with its process already up, and terminates with
  `AgentTerminationStatus.ERROR`.
- `standalone-agent.mdx` ended by describing how the page registers a
  `WeatherCollector` with an orchestrator. The page defines a
  `SimpleCounterAgent` and demonstrates running without an orchestrator.
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
