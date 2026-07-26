"""Tests for worker-slot reservation, queueing, and quarantine."""

import threading
from itertools import count
from unittest.mock import MagicMock

from PyOrchestrate.core.orchestrator.lifecycle_manager import (
    LifecycleStartResult,
    LifecycleStartStatus,
)
from PyOrchestrate.core.orchestrator.memory import AgentStartAttempt
from PyOrchestrate.core.orchestrator.worker_pool import (
    WorkerPoolScheduler,
    WorkerStartStatus,
)
from PyOrchestrate.core.utilities.command_handler import (
    CommandException,
    CommandHandler,
)


def outcome(status, reason=None):
    return LifecycleStartResult(status, reason)


def make_scheduler(max_workers=3):
    lifecycle = MagicMock()
    generations = count(1)
    lifecycle.prepare_start.side_effect = lambda agent_name: AgentStartAttempt(
        agent_name,
        next(generations),
    )
    lifecycle.execute_start.return_value = outcome(LifecycleStartStatus.STARTED)
    return (
        WorkerPoolScheduler(max_workers, lifecycle, MagicMock()),
        lifecycle,
    )


def executed_names(lifecycle):
    return [call.args[0] for call in lifecycle.execute_start.call_args_list]


def test_initial_state_and_stats_are_consistent():
    scheduler, _ = make_scheduler()

    assert scheduler.can_start_agent()
    assert scheduler.running_count == 0
    assert scheduler.queue_size == 0
    assert scheduler.all_finished
    assert scheduler.get_stats()["capacity_used"] == "0/3"


def test_start_and_queue_use_reserved_capacity():
    scheduler, lifecycle = make_scheduler(max_workers=1)

    assert scheduler.start_agent("one").status is WorkerStartStatus.STARTED
    assert scheduler.start_agent("two").status is WorkerStartStatus.QUEUED

    assert scheduler.running_count == 1
    assert scheduler.queue_size == 1
    assert not scheduler.can_start_agent()
    assert executed_names(lifecycle) == ["one"]


def test_duplicate_active_start_is_rejected():
    scheduler, _ = make_scheduler()
    scheduler.start_agent("one")

    try:
        scheduler.start_agent("one")
        raise AssertionError("expected duplicate start to fail")
    except RuntimeError as error:
        assert "already active" in str(error)


def test_termination_starts_next_agent_fifo():
    scheduler, lifecycle = make_scheduler(max_workers=1)
    scheduler.start_agent("one")
    scheduler.start_agent("two")

    scheduler.on_agent_terminated("one")

    assert executed_names(lifecycle) == ["one", "two"]
    assert scheduler.is_started("two")
    assert scheduler.queue_size == 0


def test_unknown_termination_does_not_mutate_lifecycle():
    scheduler, lifecycle = make_scheduler()

    scheduler.on_agent_terminated("unknown")

    lifecycle.mark_terminated.assert_not_called()
    assert scheduler.all_finished


def test_clean_queued_failure_advances_to_following_agent():
    scheduler, lifecycle = make_scheduler(max_workers=1)
    scheduler.start_agent("running")
    scheduler.start_agent("fails")
    scheduler.start_agent("starts")
    lifecycle.execute_start.side_effect = [
        outcome(LifecycleStartStatus.FAILED_CLEAN),
        outcome(LifecycleStartStatus.STARTED),
    ]

    scheduler.on_agent_terminated("running")

    assert executed_names(lifecycle)[-2:] == ["fails", "starts"]
    assert scheduler.is_started("starts")
    assert scheduler.queue_size == 0


def test_live_queued_failure_remains_tracked_and_blocks_slot():
    scheduler, lifecycle = make_scheduler(max_workers=1)
    scheduler.start_agent("running")
    scheduler.start_agent("stubborn")
    scheduler.start_agent("later")
    lifecycle.execute_start.return_value = outcome(
        LifecycleStartStatus.FAILED_LIVE, "still alive"
    )

    scheduler.on_agent_terminated("running")

    stats = scheduler.get_stats()
    assert scheduler.tracks_agent("stubborn")
    assert stats["quarantined_agents"] == ["stubborn"]
    assert stats["capacity_used"] == "1/1"
    assert scheduler.queue_size == 1
    assert not scheduler.all_finished


def test_stats_separate_running_starting_and_quarantined():
    scheduler, _ = make_scheduler()
    scheduler._started_agents.add("running")
    scheduler._starting_agents.add("starting")
    scheduler._failed_live_agents.add("quarantined")
    scheduler._waiting_queue.append("queued")

    stats = scheduler.get_stats()

    assert stats["running"] == 2
    assert stats["starting"] == 1
    assert stats["quarantined"] == 1
    assert stats["queued"] == 1
    assert stats["capacity_used"] == "3/3"
    assert stats["quarantined_agents"] == ["quarantined"]


def test_immediate_live_failure_is_never_invisible():
    scheduler, lifecycle = make_scheduler()
    lifecycle.execute_start.return_value = outcome(LifecycleStartStatus.FAILED_LIVE)

    result = scheduler.start_agent("stubborn")

    assert result.status is WorkerStartStatus.FAILED_LIVE
    assert scheduler.tracks_agent("stubborn")
    assert scheduler.running_count == 1
    assert not scheduler.all_finished


def test_unexpected_start_exception_still_tracks_a_live_instance():
    scheduler, lifecycle = make_scheduler()
    lifecycle.execute_start.side_effect = RuntimeError("invariant failure")
    lifecycle.is_attempt_alive.return_value = True

    try:
        scheduler.start_agent("stubborn")
        raise AssertionError("expected startup exception")
    except RuntimeError as error:
        assert "invariant failure" in str(error)

    assert scheduler.tracks_agent("stubborn")
    assert scheduler.get_stats()["quarantined_agents"] == ["stubborn"]


def test_unknown_agent_never_reserves_or_quarantines_a_slot():
    scheduler, lifecycle = make_scheduler(max_workers=1)
    lifecycle.get_agent.side_effect = ValueError("Agent 'missing' not found.")

    try:
        scheduler.start_agent("missing")
        raise AssertionError("expected missing agent to fail")
    except ValueError as error:
        assert "not found" in str(error)

    lifecycle.execute_start.assert_not_called()
    assert not scheduler.tracks_agent("missing")
    assert scheduler.get_stats()["quarantined_agents"] == []
    assert scheduler.get_stats()["capacity_used"] == "0/1"
    assert scheduler.all_finished


def test_clean_immediate_failure_drains_work_queued_during_startup():
    scheduler, lifecycle = make_scheduler(max_workers=1)
    entered = threading.Event()
    release = threading.Event()

    def first_start(agent_name, _attempt):
        if agent_name == "fails":
            entered.set()
            release.wait(timeout=1)
            return outcome(LifecycleStartStatus.FAILED_CLEAN)
        return outcome(LifecycleStartStatus.STARTED)

    lifecycle.execute_start.side_effect = first_start
    startup = threading.Thread(target=scheduler.start_agent, args=("fails",))
    startup.start()
    assert entered.wait(timeout=1)
    assert scheduler.start_agent("next").status is WorkerStartStatus.QUEUED

    release.set()
    startup.join(timeout=1)

    assert scheduler.is_started("next")
    assert scheduler.queue_size == 0


def test_starting_reservation_prevents_finished_state():
    scheduler, _ = make_scheduler(max_workers=1)
    scheduler._starting_agents.add("slow")

    assert not scheduler.all_finished
    assert not scheduler.can_start_agent()


def test_pool_lock_is_available_during_blocking_startup():
    scheduler, lifecycle = make_scheduler(max_workers=1)
    entered = threading.Event()
    release = threading.Event()

    def blocking_start(_agent_name, _attempt):
        entered.set()
        release.wait(timeout=1)
        return outcome(LifecycleStartStatus.STARTED)

    lifecycle.execute_start.side_effect = blocking_start
    startup = threading.Thread(target=scheduler.start_agent, args=("slow",))
    startup.start()
    assert entered.wait(timeout=1)

    assert scheduler.get_stats()["starting_agents"] == ["slow"]
    scheduler.stop_agent("slow")
    lifecycle.stop_agent.assert_called_once_with("slow")

    release.set()
    startup.join(timeout=1)
    assert not startup.is_alive()


def test_stop_queued_agent_cancels_it():
    scheduler, lifecycle = make_scheduler(max_workers=1)
    scheduler.start_agent("running")
    scheduler.start_agent("queued")

    scheduler.stop_agent("queued")

    assert not scheduler.is_queued("queued")
    lifecycle.stop_agent.assert_called_once_with("queued")


def test_stop_all_clears_queue_before_delegating():
    scheduler, lifecycle = make_scheduler(max_workers=1)
    scheduler.start_agent("running")
    scheduler.start_agent("queued")

    scheduler.stop_all()

    assert scheduler.queue_size == 0
    lifecycle.stop_all.assert_called_once_with()


def test_stop_all_rejects_starts_arriving_during_shutdown():
    scheduler, lifecycle = make_scheduler(max_workers=1)
    entered = threading.Event()
    release = threading.Event()

    def blocking_stop_all():
        entered.set()
        assert release.wait(timeout=1)

    lifecycle.stop_all.side_effect = blocking_stop_all
    shutdown = threading.Thread(target=scheduler.stop_all)
    shutdown.start()
    assert entered.wait(timeout=1)

    try:
        scheduler.start_agent("late")
        raise AssertionError("expected a start during shutdown to fail")
    except RuntimeError as error:
        assert "stopping" in str(error)

    assert not scheduler.is_queued("late")
    assert not scheduler.tracks_agent("late")

    release.set()
    shutdown.join(timeout=1)
    assert not shutdown.is_alive()


def test_stop_command_preserves_slot_until_termination():
    scheduler, lifecycle = make_scheduler(max_workers=1)
    scheduler.start_agent("one")
    scheduler.start_agent("two")
    orchestrator = MagicMock()
    orchestrator.memory.get_agent.return_value = MagicMock()
    orchestrator.worker_pool = scheduler
    handler = CommandHandler(orchestrator, {"stop"})

    handler._cmd_stop_agent("one")

    assert scheduler.is_started("one")
    assert scheduler.is_queued("two")
    scheduler.on_agent_terminated("one")
    assert scheduler.is_started("two")


def test_stop_command_preserves_not_found_error():
    orchestrator = MagicMock()
    orchestrator.memory.get_agent.return_value = None
    handler = CommandHandler(orchestrator, {"stop"})

    try:
        handler._cmd_stop_agent("missing")
        raise AssertionError("expected CommandException")
    except CommandException as error:
        assert error.code == 404
