"""Unit tests for PeriodicTimer's handling of accumulated delay.

`compensate_delay` decides what happens to the time an overrunning iteration
has already lost: keeping the absolute schedule recovers it over the following
iterations, resetting the timer drops it.
"""

import threading
import time
import unittest

from PyOrchestrate.utilities.periodic_timer import PeriodicTimer


class TestPeriodicTimerDelayHandling(unittest.TestCase):

    def test_compensating_keeps_the_absolute_schedule(self):
        timer = PeriodicTimer(interval=1.0, compensate_delay=True)
        # An iteration that overran by two intervals leaves the timer behind
        timer.next_time = time.perf_counter() - 2.0

        self.assertFalse(timer.wait(threading.Event()))

        # Still in the past, so the following waits keep returning immediately
        # until the accumulated delay has been recovered
        self.assertLess(timer.next_time, time.perf_counter())

    def test_not_compensating_drops_the_accumulated_delay(self):
        timer = PeriodicTimer(interval=1.0, compensate_delay=False)
        timer.next_time = time.perf_counter() - 2.0

        before = time.perf_counter()
        self.assertFalse(timer.wait(threading.Event()))

        # Realigned to now, so the next wait is a full interval again
        self.assertGreaterEqual(timer.next_time, before)
        remaining = timer.next_time + timer.interval - time.perf_counter()
        self.assertGreater(remaining, 0.9)

    def test_wait_reports_a_set_stop_event(self):
        timer = PeriodicTimer(interval=5.0)
        stop_event = threading.Event()
        stop_event.set()

        self.assertTrue(timer.wait(stop_event))

    def test_interval_must_be_positive(self):
        with self.assertRaises(ValueError):
            PeriodicTimer(interval=0)


if __name__ == "__main__":
    unittest.main()
