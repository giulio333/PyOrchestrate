from typing import TypeVar, Any
from threading import Thread
from dataclasses import dataclass
from time import sleep
from framework.core.base import BaseConfig
from framework.core.slave import PeriodicSlave, PeriodicSlaveConfig
from framework.core.worker import WorkerThread, WorkerConfig


@dataclass
class w_config:
    worker_name: str
    worker_class: type[WorkerThread]
    worker_config: BaseConfig


class ThreadPoolSlaveConfig(PeriodicSlaveConfig):
    """
    ThreadPoolSlave configuration.

    Attributes:
        interval (int): Interval in seconds between each execution
        compensate_delay (bool): If True, the process will try to compensate the delay between the executions
        check_config (CheckConfig): Configurazioni thread di controllo del Master.
        logger (LoggerConfig): Configurazioni del `logger`.

    Methods:
        validate: Metodo per validare i parametri di configurazione.
    """

    interval: float = 5
    """Interval in seconds between each execution"""
    compensate_delay: bool = True
    """If True, the process will try to compensate the delay between the executions"""


ThreadPoolSlaveConfigType = TypeVar(
    "ThreadPoolSlaveConfigType", bound=ThreadPoolSlaveConfig
)


class ThreadPoolSlave(PeriodicSlave[ThreadPoolSlaveConfigType]):
    """
    Theese processes can create a thread pool.

    Usage:
        Override the `setup` and `runner` method with the logic to be executed.
        First the `setup` method is called (only once) and then the `runner` method will be called periodically.

        When you want to terminate the process, call the `stop` method or raise `TerminateProcess`.
    """

    def __init__(
        self, config: ThreadPoolSlaveConfigType, workers: list[w_config]
    ) -> None:
        super().__init__(config=config)

        self.config: ThreadPoolSlaveConfigType = config
        self.w_config: list[w_config] = workers
        self.workers: dict[str, WorkerThread] = {}
        self.workers_config: dict[str, BaseConfig] = {}

    def init_worker(
        self,
        worker_class: type[WorkerThread],
        config,
        name_suffix: str = "",
    ) -> None:

        self.setup_logger()

        worker_instance: WorkerThread = worker_class(config=config)

        if name_suffix:
            worker_instance.name = f"{worker_instance.__class__.__name__}_{name_suffix}"

        self.workers[worker_instance.name] = worker_instance
        self.workers_config[worker_instance.name] = config

        self.logger.info(f"Aggiunto figlio: {worker_instance.name}")

    def runner(self):

        for worker_name, worker in self.workers.items():
            if not worker.is_alive():
                self.logger.error(f"Worker {worker_name} is not alive")

    def setup(self):
        super().setup()

        # instantiate and start threads
        for w_config in self.w_config:
            self.init_worker(
                worker_class=w_config.worker_class,
                config=w_config.worker_config,
                name_suffix=w_config.worker_name,
            )

        for worker_name, worker in self.workers.items():
            worker.start()

    def check_process_config(
        self, config_class: type[BaseConfig] = ThreadPoolSlaveConfig
    ):
        return super().check_process_config(config_class)
