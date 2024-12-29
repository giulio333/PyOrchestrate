class EventManager:
    def __init__(self):
        self._listeners = {}

    def register_event(self, event):
        if event not in self._listeners:
            self._listeners[event] = []

    def connect(self, event, callback):
        if event not in self._listeners:
            self.register_event(event)
        self._listeners[event].append(callback)

    def emit(self, event, *args, **kwargs):
        """
        Emit an event.

        Args:
            event(str): Event to emit.

        Returns:
            None
        """
        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(*args, **kwargs)
