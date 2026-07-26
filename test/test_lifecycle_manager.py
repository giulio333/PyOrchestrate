"""Focused tests for authoritative parent-process lifecycle management."""

import threading
import time
from unittest.mock import MagicMock

import pytest

from PyOrchestrate.core.agent.base_agent import BaseAgent
from PyOrchestrate.core.orchestrator.lifecycle_manager import (
    AgentLifecycleManager,
    LifecycleStartStatus,
)
from PyOrchestrate.core.orchestrator.memory import AgentLifecycleState, OMemory
from PyOrchestrate.core.orchestrator.worker_pool import (
    WorkerPoolScheduler,
    WorkerStartStatus,
)


class StubConfig:
    agent_start_timeout = 0.05


class StubAgent:
    a_type = "thread"
    acknowledge_start = True
    stop_succeeds = True

    def __init__(
        self,
        name=None,
        config=None,
        plugin=None,
        control_events=None,
        state_events=None,
        generation_id=0,
        **kwargs,
    ):
        self.name = name
        self.config = config
        self.plugin = plugin
        self.generation_id = generation_id
        self.control_events = control_events or BaseAgent.ControlEvents(
            setup_event=threading.Event(),
            execute_event=threading.Event(),
            stop_event=threading.Event(),
        )
        self.state_events = state_events or BaseAgent.StateEvents(
            start_event=threading.Event(),
            ready_event=threading.Event(),
            close_event=threading.Event(),
        )
        self._alive = False
        self.stop_calls = 0
        self.join_calls = 0

    def start(self):
        self._alive = True
        if self.acknowledge_start:
            self.state_events.start_event.set()

    def stop(self):
        self.stop_calls += 1
        self.control_events.stop_event.set()
        if self.stop_succeeds:
            self._alive = False

    def join(self, timeout=None):
        self.join_calls += 1
        return None

    def is_alive(self):
        return self._alive


class SilentAgent(StubAgent):
    acknowledge_start = False


class StubbornSilentAgent(SilentAgent):
    stop_succeeds = False


class PartialStartAgent(StubAgent):
    def start(self):
        self._alive = True
        raise RuntimeError("partial start")


class FailOnSecondInitializationAgent(StubAgent):
    initialization_count = 0

    def __init__(self, *args, **kwargs):
        type(self).initialization_count += 1
        if type(self).initialization_count == 2:
            raise RuntimeError("constructor failed")
        super().__init__(*args, **kwargs)


class BlockingConstructorAgent(StubAgent):
    constructor_entered = threading.Event()
    allow_constructor = threading.Event()

    def __init__(self, *args, **kwargs):
        type(self).constructor_entered.set()
        assert type(self).allow_constructor.wait(timeout=1)
        super().__init__(*args, **kwargs)


class BlockingClearEvent:
    """Event double that exposes attempts to clear startup cancellation."""

    def __init__(self):
        self._event = threading.Event()
        self.clear_entered = threading.Event()
        self.allow_clear = threading.Event()

    def clear(self):
        self.clear_entered.set()
        assert self.allow_clear.wait(timeout=1)
        self._event.clear()

    def set(self):
        self._event.set()

    def is_set(self):
        return self._event.is_set()


@pytest.fixture
def manager():
    result = AgentLifecycleManager(OMemory(), StubConfig(), MagicMock())
    result._FAILED_START_CLEANUP_TIMEOUT = 0.01
    return result


def test_timeout_is_a_clean_typed_failure(manager):
    entry = manager.register_agent(SilentAgent, "silent")

    result = manager.start_agent("silent")

    assert result.status is LifecycleStartStatus.FAILED_CLEAN
    assert entry.state_events is entry.instance.state_events
    assert entry.state is AgentLifecycleState.FAILED
    assert not entry.is_alive()


def test_stop_before_initialization_is_idempotent(manager):
    entry = manager.register_agent(StubAgent, "registered")

    manager.stop_agent("registered")
    manager.stop_agent("registered")

    assert not entry.is_initialized
    assert entry.state is AgentLifecycleState.TERMINATED


def test_duplicate_start_does_not_replace_live_instance(manager):
    entry = manager.register_agent(StubAgent, "worker")
    assert manager.start_agent("worker").started
    first_instance = entry.instance

    with pytest.raises(RuntimeError, match="cannot transition"):
        manager.start_agent("worker")

    assert entry.instance is first_instance
    assert entry.is_alive()


def test_unstoppable_failed_start_is_quarantined(manager):
    entry = manager.register_agent(StubbornSilentAgent, "stubborn")

    result = manager.start_agent("stubborn")

    assert result.status is LifecycleStartStatus.FAILED_LIVE
    assert entry.state is AgentLifecycleState.QUARANTINED
    assert entry.is_alive()


def test_partial_start_is_cleaned_and_typed(manager):
    entry = manager.register_agent(PartialStartAgent, "partial")

    result = manager.start_agent("partial")

    assert result.status is LifecycleStartStatus.FAILED_CLEAN
    assert "partial start" in result.reason
    assert entry.state is AgentLifecycleState.FAILED
    assert not entry.is_alive()


def test_restart_uses_hook_and_increments_generation(manager):
    before_start = MagicMock()
    manager.before_start = before_start
    entry = manager.register_agent(StubAgent, "restartable")

    assert manager.start_agent("restartable").started
    entry.instance._alive = False
    manager.mark_terminated("restartable")
    assert manager.restart_agent("restartable").started

    assert entry.generation_id == 2
    assert before_start.call_args_list[0].args == ("restartable", 1)
    assert before_start.call_args_list[1].args == ("restartable", 2)


def test_starting_agent_can_be_cancelled_without_waiting_for_timeout(manager):
    entry = manager.register_agent(SilentAgent, "cancel")
    results = []
    startup = threading.Thread(
        target=lambda: results.append(manager.start_agent("cancel"))
    )
    startup.start()

    deadline = time.monotonic() + 1
    while not entry.is_alive() and time.monotonic() < deadline:
        time.sleep(0.001)

    started = time.monotonic()
    manager.stop_agent("cancel")
    elapsed = time.monotonic() - started
    startup.join(timeout=1)

    assert elapsed < StubConfig.agent_start_timeout
    assert not startup.is_alive()
    assert results[0].status is LifecycleStartStatus.CANCELLED
    assert entry.state is AgentLifecycleState.TERMINATED


def test_start_transition_and_cancellation_reset_are_atomic(manager):
    entry = manager.register_agent(SilentAgent, "atomic-cancel")
    cancellation = BlockingClearEvent()
    entry._start_cancel_requested = cancellation
    execute_entered = threading.Event()
    stop_called = threading.Event()
    stop_finished = threading.Event()
    original_execute = manager.execute_start

    def execute_after_stop(agent_name, attempt):
        execute_entered.set()
        assert stop_finished.wait(timeout=1)
        return original_execute(agent_name, attempt)

    def stop_during_begin_start():
        stop_called.set()
        manager.stop_agent("atomic-cancel")
        stop_finished.set()

    manager.execute_start = execute_after_stop
    results = []
    startup = threading.Thread(
        target=lambda: results.append(manager.start_agent("atomic-cancel"))
    )
    startup.start()
    assert cancellation.clear_entered.wait(timeout=1)

    stopper = threading.Thread(target=stop_during_begin_start)
    stopper.start()
    assert stop_called.wait(timeout=1)
    assert stopper.is_alive()

    cancellation.allow_clear.set()
    assert execute_entered.wait(timeout=1)
    stopper.join(timeout=1)
    startup.join(timeout=1)

    assert not stopper.is_alive()
    assert not startup.is_alive()
    assert results[0].status is LifecycleStartStatus.CANCELLED
    assert entry.state is AgentLifecycleState.TERMINATED


def test_pool_stop_cancels_attempt_reserved_before_blocking_startup(manager):
    entry = manager.register_agent(StubAgent, "reserved")
    scheduler = WorkerPoolScheduler(1, manager, MagicMock())
    entered = threading.Event()
    release = threading.Event()
    original_start_reserved = scheduler._start_reserved_agent
    results = []

    def delayed_start_reserved(*args):
        entered.set()
        assert release.wait(timeout=1)
        return original_start_reserved(*args)

    scheduler._start_reserved_agent = delayed_start_reserved
    startup = threading.Thread(
        target=lambda: results.append(scheduler.start_agent("reserved"))
    )
    startup.start()
    assert entered.wait(timeout=1)

    scheduler.stop_agent("reserved")
    release.set()
    startup.join(timeout=1)

    assert not startup.is_alive()
    assert results[0].status is WorkerStartStatus.CANCELLED
    assert entry.state is AgentLifecycleState.TERMINATED
    assert not entry.is_alive()


def test_cancelling_started_instance_requests_stop_once(manager):
    entry = manager.register_agent(SilentAgent, "stop-once")
    results = []
    startup = threading.Thread(
        target=lambda: results.append(manager.start_agent("stop-once"))
    )
    startup.start()

    deadline = time.monotonic() + 1
    while not entry.is_alive() and time.monotonic() < deadline:
        time.sleep(0.001)

    manager.stop_agent("stop-once")
    startup.join(timeout=1)

    assert results[0].status is LifecycleStartStatus.CANCELLED
    assert entry.instance.stop_calls == 1


def test_failed_restart_constructor_does_not_cleanup_old_generation(manager):
    FailOnSecondInitializationAgent.initialization_count = 0
    entry = manager.register_agent(FailOnSecondInitializationAgent, "constructor")
    assert manager.start_agent("constructor").started
    old_instance = entry.instance
    old_instance._alive = False
    manager.mark_terminated("constructor")

    result = manager.restart_agent("constructor")

    assert result.status is LifecycleStartStatus.FAILED_CLEAN
    assert entry.generation_id == 2
    assert not entry.is_initialized
    assert old_instance.stop_calls == 0
    assert old_instance.join_calls == 0


def test_stop_does_not_wait_for_blocking_agent_constructor(manager):
    BlockingConstructorAgent.constructor_entered = threading.Event()
    BlockingConstructorAgent.allow_constructor = threading.Event()
    entry = manager.register_agent(BlockingConstructorAgent, "blocking-constructor")
    results = []
    startup = threading.Thread(
        target=lambda: results.append(manager.start_agent("blocking-constructor"))
    )
    startup.start()
    assert BlockingConstructorAgent.constructor_entered.wait(timeout=1)

    stop_finished = threading.Event()
    stopper = threading.Thread(
        target=lambda: (
            manager.stop_agent("blocking-constructor"),
            stop_finished.set(),
        )
    )
    stopper.start()

    assert stop_finished.wait(timeout=0.2)
    assert startup.is_alive()

    BlockingConstructorAgent.allow_constructor.set()
    stopper.join(timeout=1)
    startup.join(timeout=1)

    assert not stopper.is_alive()
    assert not startup.is_alive()
    assert results[0].status is LifecycleStartStatus.CANCELLED
    assert entry.state is AgentLifecycleState.TERMINATED
    assert not entry.is_alive()
