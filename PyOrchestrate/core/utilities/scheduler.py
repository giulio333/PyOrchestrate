import sched
import time
import datetime
from logging import Logger


class Scheduler:
    """
    Schedules functions flexibly, allowing execution at a specific time, after
    a given delay, or at regular intervals.

    Attributes:
        _scheduler (sched.scheduler): The scheduler shared by every instance of
            the class.
    """

    # Class attribute holding the shared scheduler
    _scheduler = None

    def __init__(
        self,
        func,
        logger,
        args=(),
        kwargs={},
        start_time=None,
        delay=0,
        interval=None,
    ) -> None:
        """
        Initializes a new schedule.

        Args:
            func (callable): The function to run when the event fires.
            logger (Logger): Logger object used to record events.
            args (tuple): Positional arguments passed to the function (optional).
            kwargs (dict): Keyword arguments passed to the function (optional).
            start_time (str | datetime.time | datetime.datetime, optional): The
                specific time of the first execution. Accepts a string in the
                ``'HH:MM:SS'`` or ``'YYYY-MM-DD HH:MM:SS'`` format.
            delay (int, optional): Delay in seconds before the first execution.
                Ignored when ``start_time`` is given.
            interval (int, optional): Interval in seconds between periodic runs.

        Raises:
            ValueError: If ``start_time`` is in the past or is not a valid format.
        """

        if not Scheduler._scheduler:
            Scheduler._scheduler = sched.scheduler(time.time, time.sleep)

        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.delay = delay
        self.interval = interval  # Interval between periodic runs
        self.event = None  # Scheduled event
        self.logger: Logger = logger

        # start_time handling
        if start_time:
            if isinstance(start_time, str):
                # Try to parse the string as datetime.time or datetime.datetime
                try:
                    # Try 'YYYY-MM-DD HH:MM:SS' first
                    self.start_time = datetime.datetime.strptime(
                        start_time, "%Y-%m-%d %H:%M:%S"
                    )
                except ValueError:
                    try:
                        # Fall back to 'HH:MM:SS'
                        time_obj = datetime.datetime.strptime(
                            start_time, "%H:%M:%S"
                        ).time()
                        self.start_time = time_obj
                    except ValueError:
                        raise ValueError(
                            "start_time must use the 'HH:MM:SS' or "
                            "'YYYY-MM-DD HH:MM:SS' format"
                        )
            elif isinstance(start_time, (datetime.time, datetime.datetime)):
                self.start_time = start_time
            else:
                raise ValueError(
                    "start_time must be a string, datetime.time or datetime.datetime"
                )
        else:
            self.start_time = None

        # Schedule the first execution
        self.start()

    def compute_initial_delay(self):
        """
        Computes the initial delay before the first execution of the function.

        Returns:
            float: The delay in seconds before the first execution.

        Raises:
            ValueError: If ``start_time`` is a ``datetime.datetime`` in the past.
        """

        if self.start_time:
            now = datetime.datetime.now()
            if isinstance(self.start_time, datetime.time):
                scheduled_time = datetime.datetime.combine(now.date(), self.start_time)
                if scheduled_time < now:
                    scheduled_time += datetime.timedelta(days=1)
            elif isinstance(self.start_time, datetime.datetime):
                scheduled_time = self.start_time
                if scheduled_time < now:
                    raise ValueError(f"start_time={scheduled_time} is in the past.")
            else:
                raise ValueError(
                    "start_time must be datetime.time or datetime.datetime"
                )

            delay = (scheduled_time - now).total_seconds()
            return max(0, delay)
        else:
            # Without an explicit start_time, use the delay provided
            return self.delay

    def start(self):
        """
        Starts scheduling the function, computing the initial delay and
        planning the first execution.
        """
        initial_delay = self.compute_initial_delay()
        self._schedule_next_run(initial_delay)

    def _schedule_next_run(self, delay):
        """
        Schedules the next execution of the function.

        Args:
            delay (float): Delay in seconds before the next execution.
        """
        if Scheduler._scheduler:
            self.event = Scheduler._scheduler.enter(delay, 1, self._run_function)

    def _run_function(self):
        """
        Runs the function and, when an interval is configured, schedules the
        next execution after that interval.
        """

        self.logger.info(f"executing scheduler job=[{self.func.__name__}]")

        self.func(*self.args, **self.kwargs)

        if self.interval:
            self._schedule_next_run(self.interval)

    @classmethod
    def run(cls, blocking=True):
        """
        Runs the global scheduler to process the planned events.

        Args:
            blocking (bool): If True, the scheduler blocks until no scheduled
                events are left.
        """
        if cls._scheduler:
            cls._scheduler.run(blocking=blocking)

    def cancel(self):
        """
        Cancels the scheduled event.

        Handles the error safely when the event has already run or been
        cancelled.
        """
        if self.event:
            try:
                if Scheduler._scheduler:
                    Scheduler._scheduler.cancel(self.event)
                    self.logger.debug("Schedule cancelled.")
                else:
                    self.logger.debug("Unable to cancel the event.")
            except ValueError:
                self.logger.debug("The event has already run or been cancelled.")
            self.event = None
