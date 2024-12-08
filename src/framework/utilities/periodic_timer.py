"""
A module providing a PeriodicTimer class to manage periodic execution intervals with optional
compensation for accumulated delays. This is particularly useful in scenarios where tasks
need to be executed at consistent intervals, such as in real-time processing, polling mechanisms,
or scheduling repeated tasks.

The PeriodicTimer class encapsulates the logic for calculating sleep times between iterations,
handling compensations for any delays that may occur during task execution to maintain the
desired frequency of execution.

Example:
    ```python
    from datetime import datetime
    import threading
    from framework.utilities.periodic_timer import PeriodicTimer


    def periodic_task():
        now = datetime.now()
        timestamp = now.strftime("%H:%M:%S.%f")[:-3]
        print(f"Task executed at {timestamp}")


    stop_event = threading.Event()
    timer = PeriodicTimer(interval=1, compensate_delay=False)

    try:
        while not stop_event.is_set():
            periodic_task()
            if timer.wait(stop_event):
                break
    except KeyboardInterrupt:
        stop_event.set()
    ```
"""

import time
import threading
from logging import Logger


class PeriodicTimer:
    """
    Manages periodic execution intervals with optional delay compensation.

    The PeriodicTimer class is designed to facilitate the execution of tasks at consistent
    intervals. It calculates the appropriate sleep time between iterations and can optionally
    compensate for any delays that occur during task execution to maintain the desired
    frequency.

    Attributes:
        interval (float): The time interval in seconds between each iteration.
        compensate_delay (bool): Determines whether to compensate for accumulated delays.
        next_time (float): The scheduled start time for the next iteration.
        _lock (threading.Lock): A lock to ensure thread-safe operations on internal state.
    """

    def __init__(self, logger: Logger, interval: float, compensate_delay: bool = True):
        """
        Initializes a new instance of PeriodicTimer.

        Args:
            logger (Logger): The logger to use for reporting any errors or warnings.
            interval (float): The time interval in seconds between each iteration.
                Must be a positive number representing the desired period.
            compensate_delay (bool, optional): If set to True, the timer will adjust the
                next scheduled time to compensate for any delays that occur, preventing
                the accumulation of timing errors. Defaults to True.

        Raises:
            ValueError: If the provided interval is not a positive number.
        """
        if interval <= 0:
            raise ValueError("Interval must be a positive number representing seconds.")

        self.logger: Logger = logger
        self.interval: float = interval
        self.compensate_delay: bool = compensate_delay
        self.next_time: float = time.perf_counter()
        self._lock = threading.Lock()

    def wait(self, stop_event: threading.Event) -> bool:
        """
        Calculates the remaining sleep time and pauses the thread accordingly.

        This method determines how long the current thread should sleep to maintain the
        desired interval between task executions. If `compensate_delay` is enabled and
        the thread is running behind schedule, it adjusts the next scheduled time to
        prevent delays from accumulating over iterations.

        Args:
            stop_event (threading.Event): An event used to signal the thread to stop waiting
                and terminate the loop. If the event is set during the wait period, the
                method returns immediately.

        Returns:
            bool: Returns True if the `stop_event` was set during the wait, indicating
                that the loop should terminate. Returns False otherwise.

        Example:
            ```python
            import threading
            from periodic_timer import PeriodicTimer

            stop_event = threading.Event()
            timer = PeriodicTimer(interval=2.0)

            if timer.wait(stop_event):
                print("Stop event detected. Exiting loop.")
            else:
                print("Continuing to next iteration.")
            ```
        """

        with self._lock:
            self.next_time += self.interval
            sleep_time = self.next_time - time.perf_counter()

            if sleep_time > 0:
                # Wait for the remaining time or until the stop_event is set
                return stop_event.wait(timeout=sleep_time)
            else:
                if self.compensate_delay:
                    # Adjust the next_time to the current time to compensate for delay
                    self.next_time = time.perf_counter()
                # If not compensating, allow next_time to continue accumulating delays
                return False

    def reset(self):
        """
        Resets the timer to the current time.

        This method reinitializes the `next_time` attribute to the current high-resolution
        counter, effectively resetting the timer's schedule. This can be useful if the
        timing sequence needs to be restarted without waiting for the next interval.
        """
        with self._lock:
            self.next_time = time.perf_counter()
