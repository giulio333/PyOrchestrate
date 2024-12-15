from typing import Type, TypeVar, Generic, final
from threading import Event
import time
from abc import abstractmethod

from framework.core.base import BaseConfig
from framework.core.worker import WorkerThread, WorkerConfig


class OneShotSlaveConfig(WorkerConfig):
    pass


OneShotWorkerConfigType = TypeVar("OneShotWorkerConfigType", bound=OneShotSlaveConfig)


class OneShotWorker(
    WorkerThread[OneShotWorkerConfigType], Generic[OneShotWorkerConfigType]
):
    """
    Theese processes are executed only once.

    Usage:
        Override the `work` method with the logic to be executed.
    """

    def __init__(self, config: OneShotWorkerConfigType) -> None:
        super().__init__(config=config)

    @abstractmethod
    def work(self) -> None:
        """
        Here you have to implement the logic to be executed only once.
        """
        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )


class LoopingWorkerConfig(WorkerConfig):
    """
    LoppingSlave configuration.

    Attributes:
        check_config (CheckConfig): Configurazioni thread di controllo del Master.
        logger (LoggerConfig): Configurazioni del `logger`.

    Methods:
        validate: Metodo per validare i parametri di configurazione.
    """

    pass


LoopingWorkerConfigType = TypeVar("LoopingWorkerConfigType", bound=LoopingWorkerConfig)


class LoopingWorker(WorkerThread[LoopingWorkerConfigType]):
    """
    Theese processes are executed periodically.

    Usage:
        Override the `setup` and `runner` method with the logic to be executed.
        First the `setup` method is called (only once) and then the `runner` method will be called periodically.

        When you want to terminate the process, call the `stop` method or raise `TerminateProcess`.
    """

    def __init__(self, config: LoopingWorkerConfigType) -> None:
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

    def check_worker_config(self, config_class: type[BaseConfig] = LoopingWorkerConfig):
        return super().check_worker_config(config_class)
