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
import logging
import threading
import atexit
from datetime import datetime
from typing import Callable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, Future


# Configurazione del logger thread-safe
logger = logging.getLogger(__name__)


class EventManager:
    """
    Event manager class.

    Manages the registration, attachment, and emission of events.

    Attributes:
        _listeners (dict): A dictionary mapping event names to lists of callback functions.
        _executor (ThreadPoolExecutor): Thread pool for executing callbacks asynchronously.
        _lock (threading.Lock): Lock for thread-safe operations on listeners.
        _shutdown (bool): Flag indicating if the event manager is shutting down.

    Features:
        - register_event: Registers a new event if not already present.
        - connect: Attaches a callback to an event (registering the event if necessary).
        - emit: Emits the event by calling all attached callbacks, including default data such as event date and time.
        - shutdown: Safely shuts down the event manager and its thread pool.
    """

    def __init__(self, max_workers: int = 10):
        """
        Initializes the EventManager instance.

        Creates the internal dictionary for managing listeners and initializes the thread pool.

        Args:
            max_workers (int): Maximum number of worker threads in the thread pool.
        """
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = None  # Inizializziamo il lock a None
        self._shutdown = False
        self._max_workers = max_workers
        self._executor = None

        # Registra la chiusura dell'executor quando l'applicazione termina
        atexit.register(self.shutdown)

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
        if self._lock is None:
            self._lock = threading.Lock()
        with self._lock:
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
        if self._lock is None:
            self._lock = threading.Lock()
        with self._lock:
            if event.name not in self._listeners:
                self.register_event(event)
            self._listeners[event.name].append(callback)

    def emit(self, event: Enum, *args, **kwargs):
        """
        Emits an event by invoking all attached callbacks.

        If listeners exist for the event, they are executed asynchronously.
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
        if self._shutdown:
            logger.warning(
                "EventManager is shutting down, ignoring event emission: %s", event.name
            )
            return

        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        if self._lock is None:
            self._lock = threading.Lock()

        listeners = []
        with self._lock:
            if event.name in self._listeners:
                listeners = self._listeners[event.name].copy()

        if not listeners:
            return

        # Aggiungi dati predefiniti
        kwargs["event_date"] = datetime.now().date().isoformat()
        kwargs["event_time"] = datetime.now().time().isoformat()

        for callback in listeners:
            # Filtra i parametri in base alla firma della funzione
            sig = inspect.signature(callback)
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

            # Esegui il callback in modo asincrono
            self._executor.submit(
                self._execute_callback, callback, args, filtered_kwargs
            )

    def _execute_callback(self, callback: Callable, args, kwargs):
        """
        Esegue il callback in modo sicuro, catturando eventuali eccezioni.

        Args:
            callback (Callable): Il callback da eseguire.
            args (tuple): Argomenti posizionali.
            kwargs (dict): Argomenti keyword.
        """
        try:
            callback(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error executing callback {callback.__name__}: {str(e)}")

    def shutdown(self, wait: bool = True):
        """
        Chiude l'event manager e il thread pool.

        Args:
            wait (bool): Se True, attende che tutti i task in esecuzione siano completati.
        """
        if self._shutdown:
            return

        self._shutdown = True

        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None
