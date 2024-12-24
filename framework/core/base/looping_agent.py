from abc import abstractmethod
from typing import final

from ..base.baseagent import BaseProcessAgent, BaseThreadAgent


class LoopingProcessAgent(BaseProcessAgent):

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @final
    def execute(self):
        """Esegue un loop continuo finché non viene richiesto di fermarsi."""

        self.setup()

        while not self._stop_event.is_set():
            self.cycle()

    @abstractmethod
    def cycle(self):
        """Definisce il lavoro da eseguire in ogni iterazione del loop."""
        pass

    @abstractmethod
    def setup(self):
        """
        Abstract method to be implemented in derived classes: Agent setup logic.

        Notes:
            Here you can implement the setup logic.
            This method is called once before the Agent cycle method.
        """
        pass


class LoopingThreadAgent(BaseThreadAgent):

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    @final
    def execute(self):
        """Esegue un loop continuo finché non viene richiesto di fermarsi."""

        self.setup()

        while not self._stop_event.is_set():
            self.cycle()

    @abstractmethod
    def cycle(self):
        """Definisce il lavoro da eseguire in ogni iterazione del loop."""
        pass

    @abstractmethod
    def setup(self):
        """
        Abstract method to be implemented in derived classes: Agent setup logic.

        Notes:
            Here you can implement the setup logic.
            This method is called once before the Agent cycle method.
        """
        pass
