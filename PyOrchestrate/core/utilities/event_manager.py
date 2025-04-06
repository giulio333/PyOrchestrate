"""
event_manager module.
This module implements the EventManager class for centralized event handling within the application.
EventManager keeps a dictionary of callbacks (listeners) associated with events identified by their name.
Use this class to:
- Register unique events.
- Attach callback functions to events.
- Emit events passing specific parameters and default data (event date and time).
It isolates errors in one callback so that they do not affect the execution of others.
"""

from enum import Enum
import inspect
from datetime import datetime
from typing import Callable
from concurrent.futures import ThreadPoolExecutor


class EventManager:
    """
    Event manager class.

    Manages the registration, attachment, and emission of events.

    Attributes:
        _listeners (dict): A dictionary mapping event names to lists of callback functions.

    Features:
        - register_event: Registers a new event if not already present.
        - connect: Attaches a callback to an event (registering the event if necessary).
        - emit: Emits the event by calling all attached callbacks, including default data such as event date and time.
    """

    def __init__(self):
        """
        Initializes the EventManager instance.

        Creates the internal dictionary for managing listeners.
        """
        self._listeners: dict[str, list[Callable]] = {}
        self._executor = ThreadPoolExecutor(max_workers=10)

    def register_event(self, event: Enum):
        """
        Registers a new event.

        If the event is not already present, a new entry is created in the listeners dictionary.
        The event is identified by the 'name' attribute of the provided enum.

        Args:
            event (Enum): An Enum instance representing the event to register.

        Example:
            >>> event_manager.register_event(AgentEvent.AGENT_START)
        """
        if event.name not in self._listeners:
            self._listeners[event.name] = []

    def connect(self, event: Enum, callback: Callable):
        """
        Attaches a callback to an event.

        If the event is not present, it is automatically registered.
        Callbacks are stored in the order they are added.
        Exceptions raised by one callback do not prevent others from executing.

        Args:
            event (Enum): An Enum instance identifying the event by its 'name' attribute.
            callback (Callable): The function to be invoked when the event is emitted.

        Example:
            >>> event_manager.connect(AgentEvent.AGENT_START, on_agent_started)
        """
        if event.value not in self._listeners:
            self.register_event(event)
        self._listeners[event.name].append(callback)

    def emit(self, event: Enum, *args, **kwargs):
        """
        Emits an event by invoking all attached callbacks.

        If listeners exist for the event, they are executed sequentially.
        Before execution, default data such as the `event_date` and `event_time` are added to kwargs.

        Only the parameters accepted by each callback are passed, via filtering based on the function signature.
        Exceptions raised by a callback are caught to avoid interrupting the execution of the others.

        Args:
            event (Enum): The event to be emitted, identified by its 'name' attribute.
            *args: Positional arguments passed to the callbacks.
            **kwargs: Keyword arguments passed to the callbacks.

        Example:
            >>> event_manager.emit(AgentEvent.AGENT_START, agent_name="Agent_1")
        """
        listeners = []
        if event.name in self._listeners:
            listeners = self._listeners[event.name][:]

        if listeners:
            now = datetime.now()
            kwargs.setdefault("event_date", now.strftime("%Y-%m-%d"))
            kwargs.setdefault("event_time", now.strftime("%H:%M:%S"))

            for callback in listeners:
                try:
                    callback_params = inspect.signature(callback).parameters
                    filtered_kwargs = {
                        key: value
                        for key, value in kwargs.items()
                        if key in callback_params
                    }
                    future = self._executor.submit(callback, *args, **filtered_kwargs)
                    future.add_done_callback(
                        lambda fut, cb=callback: self._handle_future_exception(cb, fut)
                    )
                except Exception as e:
                    print(f"Error in callback {callback.__name__}: {e}")

    def _handle_future_exception(self, callback, future):
        try:
            future.result()
        except Exception as e:
            print(f"Error in callback {callback.__name__} execution: {e}")
