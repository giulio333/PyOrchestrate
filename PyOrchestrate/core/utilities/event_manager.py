"""
event_manager module.
This module implements the EventManager class for centralized event handling within the application.
EventManager keeps a dictionary of callbacks (listeners) associated with events identified by their enum member.
Use this class to:
- Register unique events and attach callback functions to them.
- Emit events passing specific parameters and default data (event date and time).
It isolates errors in one callback so that they do not affect the execution of others.
"""

from enum import Enum
import inspect
import logging
import atexit
import threading
import weakref
from datetime import datetime
from typing import Callable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

# Thread-safe logger configuration
logger = logging.getLogger(__name__)


def _shutdown_on_exit(manager_ref: "weakref.ref[EventManager]") -> None:
    """
    Shut a manager down at interpreter exit, unless it is already collected.

    Registering the bound method instead kept every EventManager — and through
    its listeners the whole orchestrator — reachable for the life of the
    process. The weak reference makes this a backstop for a manager nobody shut
    down, not an owner.
    """
    manager = manager_ref()
    if manager is not None:
        manager.shutdown()


class EventManager:
    """
    Event manager class.

    Manages the registration, attachment, and emission of events.

    Attributes:
        _listeners (dict): A dictionary mapping enum members to lists of callback functions.
        _executor (ThreadPoolExecutor): Thread pool for executing callbacks asynchronously.
        _shutdown (bool): Flag indicating if the event manager is shutting down.

    Features:
        - register_event: Registers a new event and attaches a callback to it.
        - emit: Emits the event by calling all attached callbacks, including default data such as event date and time.
        - shutdown: Safely shuts down the event manager and its thread pool.

    Example:
        >>> from enum import Enum
        >>> from PyOrchestrate.core.utilities.event_manager import EventManager
        >>>
        >>> # Define your events
        >>> class MyEvents(Enum):
        ...     TASK_STARTED = "task_started"
        ...     TASK_COMPLETED = "task_completed"
        ...     TASK_FAILED = "task_failed"
        >>>
        >>> # Create callback functions
        >>> def on_task_started(task_name, **kwargs):
        ...     print(f"Task {task_name} started at {kwargs.get('event_time')}")
        >>>
        >>> def on_task_completed(task_name, result, **kwargs):
        ...     print(f"Task {task_name} completed with result: {result}")
        >>>
        >>> def on_task_failed(task_name, error, **kwargs):
        ...     print(f"Task {task_name} failed with error: {error}")
        >>>
        >>> # Initialize the event manager
        >>> event_manager = EventManager()
        >>>
        >>> # Register events and callbacks
        >>> event_manager.register_event(MyEvents.TASK_STARTED, on_task_started)
        >>> event_manager.register_event(MyEvents.TASK_COMPLETED, on_task_completed)
        >>> event_manager.register_event(MyEvents.TASK_FAILED, on_task_failed)
        >>>
        >>> # Emit events
        >>> event_manager.emit(MyEvents.TASK_STARTED, task_name="data_processing")
        >>> event_manager.emit(MyEvents.TASK_COMPLETED, task_name="data_processing", result="success")
        >>> event_manager.emit(MyEvents.TASK_FAILED, task_name="data_processing", error="timeout")
        >>>
        >>> # Shutdown when done
        >>> event_manager.shutdown()
    """

    def __init__(self, max_workers: int = 10):
        """
        Initializes the EventManager instance.

        Creates the internal dictionary for managing listeners and initializes the thread pool.

        Args:
            max_workers (int): Maximum number of worker threads in the thread pool.
        """
        self._listeners: Dict[Enum, List[Callable]] = {}
        self._shutdown: bool = False
        self._max_workers: int = max_workers
        self._executor: Optional[ThreadPoolExecutor] = None
        self._executor_lock: threading.Lock = threading.Lock()

        # Backstop for a manager nobody shuts down explicitly. Weak, so that
        # registering it does not keep this manager alive until exit.
        atexit.register(_shutdown_on_exit, weakref.ref(self))

    def register_event(self, event: Enum, callback: Callable):
        """
        Registers and attaches a callback to an event.

        If the event is not present, it is automatically registered.
        Callbacks are stored in the order they are added.
        Exceptions raised by one callback do not prevent others from executing.

        The listeners are keyed by the enum member itself, so members sharing a
        name across different enums stay independent: a callback registered for
        `AgentEvent.AGENT_ERROR` is not invoked when
        `OrchestratorEvent.AGENT_ERROR` is emitted.

        Args:
            event (Enum): The Enum member identifying the event.
            callback (Callable): The function to be invoked when the event is emitted.

        Example:
            >>> event_manager.register_event(AgentEvent.AGENT_START, on_agent_started)
        """
        # register the event if it doesn't exist
        if event not in self._listeners:
            self._listeners[event] = []
        # add the callback to the list
        self._listeners[event].append(callback)

    def emit(self, event: Enum, *args, **kwargs):
        """
        Emits an event by invoking all attached callbacks.

        If listeners exist for the event, they are executed asynchronously.
        Before execution, default data such as the `event_date` and `event_time` are added to kwargs.

        Only the parameters accepted by each callback are passed, via filtering based on the function signature.
        Exceptions raised by a callback are caught to avoid interrupting the execution of the others.

        Only the callbacks registered for this exact enum member are invoked.

        Args:
            event (Enum): The Enum member identifying the event to be emitted.
            *args: Positional arguments passed to the callbacks.
            **kwargs: Keyword arguments passed to the callbacks.

        Example:
            >>> event_manager.emit(AgentEvent.AGENT_START, agent_name="Agent_1")
        """
        if self._shutdown:
            logger.warning(
                "EventManager is shutting down, ignoring event emission: %s", event
            )
            return

        # Thread-safe lazy initialization of executor
        if self._executor is None:
            with self._executor_lock:
                # Double-check pattern to avoid race condition
                if self._executor is None and not self._shutdown:
                    self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
                elif self._shutdown:
                    logger.warning(
                        "EventManager shutdown during executor initialization, ignoring event: %s",
                        event,
                    )
                    return

        listeners = []
        if event in self._listeners:
            listeners = self._listeners[event].copy()

        if not listeners:
            return

        # Create default data only if needed by at least one callback
        default_data = self._create_default_data_if_needed(listeners)

        for callback in listeners:
            # Filter parameters based on function signature
            sig = inspect.signature(callback)

            # Check if callback accepts **kwargs (variable keyword arguments)
            accepts_var_kwargs = any(
                p.kind == p.VAR_KEYWORD for p in sig.parameters.values()
            )

            if accepts_var_kwargs:
                # If callback accepts **kwargs, pass all kwargs
                filtered_kwargs = kwargs.copy()
            else:
                # Otherwise, filter kwargs based on parameter names
                filtered_kwargs = {
                    k: v for k, v in kwargs.items() if k in sig.parameters
                }

            # Add default data only if the callback accepts these parameters
            for key, value in default_data.items():
                if accepts_var_kwargs or key in sig.parameters:
                    filtered_kwargs[key] = value

            # Execute callback asynchronously
            if self._executor is not None:  # Safety check
                self._executor.submit(
                    self._execute_callback, callback, args, filtered_kwargs
                )

    def _create_default_data_if_needed(
        self, listeners: List[Callable]
    ) -> Dict[str, str]:
        """
        Creates default data only if at least one callback needs it.

        Args:
            listeners: List of callback functions to check.

        Returns:
            Dictionary with default data if needed, empty dictionary otherwise.
        """
        default_keys = {"event_date", "event_time"}

        # Check if any listener needs default data
        needs_default_data = False
        for callback in listeners:
            sig = inspect.signature(callback)

            # Check if callback accepts **kwargs or explicitly named default parameters
            accepts_var_kwargs = any(
                p.kind == p.VAR_KEYWORD for p in sig.parameters.values()
            )
            has_default_params = any(key in sig.parameters for key in default_keys)

            if accepts_var_kwargs or has_default_params:
                needs_default_data = True
                break

        if not needs_default_data:
            return {}

        # Create default data only when needed
        return {
            "event_date": datetime.now().date().isoformat(),
            "event_time": datetime.now().time().isoformat(),
        }

    def _execute_callback(self, callback: Callable, args, kwargs):
        """
        Executes the callback safely, catching any exceptions.

        Args:
            callback (Callable): The callback to execute.
            args (tuple): Positional arguments.
            kwargs (dict): Keyword arguments.
        """
        try:
            callback(*args, **kwargs)
        except Exception as e:
            logger.exception(
                "Error executing callback %s: %s", callback.__name__, str(e)
            )

    def shutdown(self, wait: bool = True):
        """
        Shuts down the event manager and thread pool.

        Args:
            wait (bool): If True, waits for all running tasks to complete.
        """
        if self._shutdown:
            return

        self._shutdown = True

        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None
