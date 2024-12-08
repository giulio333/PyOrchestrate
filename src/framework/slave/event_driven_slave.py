from typing import TypeVar, Generic, Any
from abc import abstractmethod

from framework.slave import PeriodicSlave, PeriodicSlaveConfig


class EventDrivenSlaveConfig(PeriodicSlaveConfig):
    event_source: Any


EventDrivenSlaveConfigType = TypeVar(
    "EventDrivenSlaveConfigType", bound=EventDrivenSlaveConfig
)


class EventDrivenSlaveProcess(
    PeriodicSlave[EventDrivenSlaveConfigType], Generic[EventDrivenSlaveConfigType]
):
    """
    Classe base EventDrivenSlaveProcess.

    Il metodo `work` deve essere implementato nelle sottoclassi per definire il lavoro da svolgere.

    Attributes:
        name (str): Nome del processo.
        config (Config): Configurazioni del processo.
    """

    def __init__(self, config: EventDrivenSlaveConfigType) -> None:
        super().__init__(config)

        self.event_source = config.event_source

    def runner(self) -> None:

        event = self.wait_for_event()

        if event:
            self.handle_event(event)

    @abstractmethod
    def wait_for_event(self):
        """
        Implementa qui la logica per attendere un evento dalla fonte specificata.
        """
        pass

    @abstractmethod
    def handle_event(self, event):
        """
        Implementa qui la logica per gestire l'evento ricevuto.
        """
        pass
