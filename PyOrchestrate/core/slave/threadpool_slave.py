from typing import TypeVar, Any
from threading import Thread
from dataclasses import dataclass
from typing import TypeVar, Type, final

from PyOrchestrate.core.base import BaseConfig
from PyOrchestrate.core.slave import PeriodicSlave, PeriodicSlaveConfig
from PyOrchestrate.core.worker import WorkerThread, WorkerConfig


@dataclass
class w_config:
    worker_class: type[WorkerThread]
    worker_config: BaseConfig
    worker_name: str = ""


@dataclass
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
    These processes can create a thread pool.

    Usage:
        Override the `setup` method with the logic to be executed.
        First, the `setup` method is called (only once) and then the `runner` method will be called periodically to execute checks on the launched threads.

        The `runner` method will run every `ThreadPoolSlaveConfig.interval` seconds to ensure all threads are alive.

        Threads should be passed to the `__init__` method in the `workers` parameter as a list of `w_config` objects.

        When you want to terminate the process, call the `stop` method or raise `TerminateProcess`.

    Examples:
        ```python
        my_worker = w_config(MyWorker, MyWorkerConfig())

        class MyThreadPoolSlaveConfig(ThreadPoolSlaveConfig):
            interval = 1

        class MyThreadPoolSlave(ThreadPoolSlave[MyThreadPoolSlaveConfig]):
            def __init__(self, config: MyThreadPoolSlaveConfig) -> None:
                super().__init__(config=config, workers=[my_worker])

            def setup(self):
                super().setup()

                self.logger.info(f"Configurazione: {self.config}")

        if __name__ == "__main__":
            config = MyThreadPoolSlaveConfig()
            slave = MyThreadPoolSlave(config=config)
            slave.run()
        ```
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

    @final
    def runner(self):
        """
        This method is called periodically every `ThreadPoolSlaveConfig.interval` seconds.
        It checks if all workers are alive, otherwise it stops the process.

        Warning:
            This method should not be overridden.
        """

        for worker_name, worker in self.workers.items():

            if not worker.is_alive():
                self.logger.warning(f"Worker {worker_name} is not alive")

        # if at least one worker is not alive, stop the process
        if not all(worker.is_alive() for worker in self.workers.values()):
            self.stop()

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
