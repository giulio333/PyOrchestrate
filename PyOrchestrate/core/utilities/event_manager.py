"""
Event manager module.
"""

from enum import Enum
import threading
import inspect
from datetime import datetime
from typing import Callable


class EventManager:
    """
    Event manager class.

    This class is used to manage events and listeners. It allows registering events and connecting listeners to them.

    Attributes:
        _listeners (dict): A dictionary where keys are event names (str) and values are lists of callback functions.
        _lock (threading.Lock): A lock to ensure thread safety when accessing _listeners.

    Methods:
        register_event(event): Registers a new event.
        connect(event, callback): Connects a listener (callback function) to an event.
        emit(event, *args, **kwargs): Emits an event, triggering all connected listeners.
    """

    def __init__(self):
        """
        Initializes the event manager.
        """
        self._listeners: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()

    def register_event(self, event: Enum):
        """
        Registers a new event.

        If the event already exists, it will not be overwritten. This method is idempotent.

        Args:
            event (Enum): An Enum instance representing the event to register. Its 'name' attribute is used as the identifier.

        Examples:
            >>> from PyOrchestrate.core.utilities.event_manager import EventManager
            >>> from PyOrchestrate.core.base.base import AgentEvent
            >>> event_manager = EventManager()
            >>> event_manager.register_event(AgentEvent.AGENT_START)
            >>> event_manager.register_event(AgentEvent.AGENT_STOP)
        """
        with self._lock:
            if event.name not in self._listeners:
                self._listeners[event.name] = []

    def connect(self, event: Enum, callback: Callable):
        """
        Connects a listener (callback function) to an event.

        If the event does not exist, it will be automatically registered using its 'name' attribute.
        Multiple listeners can be connected to the same event in the order they are added.
        If a listener raises an exception when the event is emitted, the emission will stop for that listener only.

        Args:
            event (Enum): An Enum instance representing the event. Its 'name' attribute is used as the identifier.
            callback (callable): A function to execute when the event is emitted. The function can accept arguments passed during emission.

        Examples:
            >>> from PyOrchestrate.core.utilities.event_manager import EventManager
            >>> from PyOrchestrate.core.base.base import AgentEvent
            >>> def on_agent_started(agent_name):
            ...     print(f"Agent {agent_name} started.")
            >>> event_manager = EventManager()
            >>> event_manager.connect(AgentEvent.AGENT_START, on_agent_started)
        """
        with self._lock:
            if event.value not in self._listeners:
                self.register_event(event)
            self._listeners[event.name].append(callback)

    def emit(self, event: Enum, *args, **kwargs):
        """
        Emits an event, triggering all connected listeners.

        If no listeners are connected to the event, nothing happens.
        If a listener raises an exception, other listeners will still be executed.
        Default data such as the current date and time are included in kwargs but only passed to listeners that accept them.

        Args:
            event (Enum): An Enum instance representing the event to emit. Its 'name' attribute is used to lookup listeners.
            *args: Positional arguments passed to the connected listeners.
            **kwargs: Keyword arguments passed to the connected listeners. Defaults include:
                - 'event_date' (str): The date the event occurred (YYYY-MM-DD).
                - 'event_time' (str): The time the event occurred (HH:MM:SS).

        Examples:
            >>> from PyOrchestrate.core.utilities.event_manager import EventManager
            >>> from PyOrchestrate.core.base.base import AgentEvent
            >>> def on_agent_started(agent_name):
            ...     print(f"Agent {agent_name} started.")
            >>> def on_agent_started_with_time(agent_name, event_date, event_time):
            ...     print(f"Agent {agent_name} started on {event_date} at {event_time}.")
            >>> event_manager = EventManager()
            >>> event_manager.register_event(AgentEvent.AGENT_START)
            >>> event_manager.connect(AgentEvent.AGENT_START, on_agent_started)
            >>> event_manager.connect(AgentEvent.AGENT_START, on_agent_started_with_time)
            >>> event_manager.emit(AgentEvent.AGENT_START, "Agent_1")
        """
        listeners = []
        with self._lock:
            if event.name in self._listeners:
                listeners = self._listeners[event.name][:]

        if listeners:
            # Add default data to kwargs
            now = datetime.now()
            kwargs.setdefault("event_date", now.strftime("%Y-%m-%d"))
            kwargs.setdefault("event_time", now.strftime("%H:%M:%S"))

            for callback in listeners:
                try:
                    # Get the list of accepted parameters for the callback
                    callback_params = inspect.signature(callback).parameters
                    # Filter kwargs to pass only parameters accepted by the callback
                    filtered_kwargs = {
                        key: value
                        for key, value in kwargs.items()
                        if key in callback_params
                    }
                    # Call the callback with args and filtered kwargs
                    callback(*args, **filtered_kwargs)
                except Exception as e:
                    pass
                    # skip the listener if an exception is raised
