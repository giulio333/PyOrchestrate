"""
Event manager module.
"""
import inspect
from datetime import datetime


class EventManager:
    """
    Event manager class.

    This class is used to manage events and listeners. It allows registering events and connecting listeners to them.

    Attributes:
        _listeners (dict): A dictionary where keys are event names (str) and values are lists of callback functions.

    Methods:
        register_event(event): Registers a new event.
        connect(event, callback): Connects a listener (callback function) to an event.
        emit(event, *args, **kwargs): Emits an event, triggering all connected listeners.
    """

    def __init__(self):
        """
        Initializes the EventManager.

        Notes:
            The _listeners dictionary starts as an empty dictionary and grows as events are registered.
        """
        self._listeners = {}

    def register_event(self, event):
        """
        Registers a new event.

        Notes:
            If the event already exists, it will not be overwritten. This method is idempotent.

        Args:
            event (str): The name of the event to register.

        Examples:
            >>> event_manager = EventManager()
            >>> event_manager.register_event("agent_started")
            >>> event_manager.register_event("agent_stopped")
        """
        if event not in self._listeners:
            self._listeners[event] = []

    def connect(self, event, callback):
        """
        Connects a listener (callback function) to an event.

        Notes:
            If the event does not exist, it will be automatically registered.
            Multiple listeners can be connected to the same event. Listeners are stored in the order they are added.
            If a listener raises an exception when the event is emitted, the emission will stop for that listener only.

        Args:
            event (str): The name of the event to connect the listener to.
            callback (callable): A function to execute when the event is emitted. The function can accept arguments passed during emission.

        Examples:

            >>> def on_agent_started(agent_name):
            ...     print(f"Agent {agent_name} started.")
            >>> event_manager = EventManager()
            >>> event_manager.connect("agent_started", on_agent_started)
        """
        if event not in self._listeners:
            self.register_event(event)
        self._listeners[event].append(callback)

    def emit(self, event, *args, **kwargs):
        """
        Emits an event, triggering all connected listeners.

        Notes:
            If no listeners are connected to the event, nothing happens.
            If a listener raises an exception, other listeners will still be executed.
            Default data such as the current date and time are included in the kwargs,
            but only passed to listeners that accept them.

        Args:
            event (str): The name of the event to emit.
            *args: Positional arguments passed to the connected listeners.
            **kwargs: Keyword arguments passed to the connected listeners. Default values include:
                - 'event_date' (str): The date the event occurred (in YYYY-MM-DD format).
                - 'event_time' (str): The time the event occurred (in HH:MM:SS format).

        Examples:
            >>> def on_agent_started(agent_name):
            ...     print(f"Agent {agent_name} started.")
            >>> def on_agent_started_with_time(agent_name, event_date, event_time):
            ...     print(f"Agent {agent_name} started on {event_date} at {event_time}.")
            >>> event_manager = EventManager()
            >>> event_manager.register_event("agent_started")
            >>> event_manager.connect("agent_started", on_agent_started)
            >>> event_manager.connect("agent_started", on_agent_started_with_time)
            >>> event_manager.emit("agent_started", "Agent_1")
            Agent Agent_1 started.
            Agent Agent_1 started on 2024-12-29 at 14:30:00.
        """
        if event in self._listeners:
            # Add default data to kwargs
            now = datetime.now()
            kwargs.setdefault('event_date', now.strftime('%Y-%m-%d'))
            kwargs.setdefault('event_time', now.strftime('%H:%M:%S'))

            for callback in self._listeners[event]:
                try:
                    # Get the list of accepted parameters for the callback
                    callback_params = inspect.signature(callback).parameters
                    # Filter kwargs to pass only parameters accepted by the callback
                    filtered_kwargs = {key: value for key, value in kwargs.items() if key in callback_params}
                    # Call the callback with args and filtered kwargs
                    callback(*args, **filtered_kwargs)
                except Exception as e:
                    # Handle exceptions raised by callbacks
                    print(f"Error in listener '{callback.__name__}': {e}")
