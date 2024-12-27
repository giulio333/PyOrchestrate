from typing import Type, TypeVar, Generic, final
from threading import Event
import time
from abc import abstractmethod

from PyOrchestrate.core.base import BaseConfig
from PyOrchestrate.core.slave import SlaveProcess, SlaveConfig


class OneShotSlaveConfig(SlaveConfig):
    pass


OneShotSlaveConfigType = TypeVar("OneShotSlaveConfigType", bound=OneShotSlaveConfig)


class OneShotSlaveProcess(
    SlaveProcess[OneShotSlaveConfigType], Generic[OneShotSlaveConfigType]
):
    """
    Theese processes are executed only once.

    Usage:
        Override the `work` method with the logic to be executed.
    """

    def __init__(self, config: OneShotSlaveConfigType) -> None:
        super().__init__(config=config)

    @abstractmethod
    def work(self) -> None:
        """
        Here you have to implement the logic to be executed only once.
        """
        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )


class LoopingSlaveConfig(SlaveConfig):
    """
    LoppingSlave configuration.

    Attributes:
        check_config (CheckConfig): Configurazioni thread di controllo del Master.
        logger (LoggerConfig): Configurazioni del `logger`.

    Methods:
        validate: Metodo per validare i parametri di configurazione.
    """

    pass


LoopingSlaveConfigType = TypeVar("LoopingSlaveConfigType", bound=LoopingSlaveConfig)


class LoopingSlave(SlaveProcess[LoopingSlaveConfigType]):
    """
    Theese processes are executed periodically.

    Usage:
        Override the `setup` and `runner` method with the logic to be executed.
        First the `setup` method is called (only once) and then the `runner` method will be called periodically.

        When you want to terminate the process, call the `stop` method or raise `TerminateProcess`.
    """

    def __init__(self, config: LoopingSlaveConfigType) -> None:
        super().__init__(config=config)

    @final
    def work(self) -> None:
        self.stop_event = Event()

        self.setup()

        while not self.stop_event.is_set():
            self.cycle()

    @abstractmethod
    def cycle(self):
        """
        Here you have to implement the logic to be executed.
        """

    @final
    def stop(self):
        """
        Stops the process.
        """
        self.stop_event.set()

    @abstractmethod
    def setup(self):
        """
        Here you can implement the setup logic.

        This method is called once before the runner loop method.
        """
        pass

    @abstractmethod
    def runner(self):
        """
        Here you have to implement the logic to be executed periodically.
        """
        pass

    def check_process_config(self, config_class: type[BaseConfig] = LoopingSlaveConfig):
        return super().check_process_config(config_class)
