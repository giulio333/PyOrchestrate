from multiprocessing import Process
from threading import Event, Thread
from logging import Logger
from framework.utilities.logger import setup_logger
from typing import Optional, List, final, Generic, TypeVar, Type, Callable, Literal
from dataclasses import dataclass
import time

from framework.base_process.base import BaseConfig, BaseProcess
from framework.master.utilities import HealthCheckConfig
from framework.slave.slave import SlaveProcess, SlaveConfig


class MasterConfig(BaseConfig):
    """
    Configurazioni di un MasterProcess.

    Attributes:
        wait_mode (Literal["infinite", "limited", "none"]): Modalità di attesa.
        max_restarts (int): Numero totale di riavvii consentiti (solo per wait_mode = "limited").
        health_check (HealthCheckConfig): Configurazione per il monitoraggio dello stato di salute.

    Methods:
        validate: Metodo per validare i parametri di configurazione.
    """

    wait_mode: Literal["infinite", "limited", "none"] = "none"
    """
    - "infinite": rimane attivo e riavvia se possibile.
    - "limited": rimane attivo solo fino a un certo numero di riavvii.
    - "none": termina appena i figli completano la prima esecuzione.
    """

    max_restarts: int = 0
    """
    Numero massimo di riavvii complessivi consentiti per tutti i figli.
    Valido solo se wait_mode = "limited".
    """

    health_check: HealthCheckConfig = HealthCheckConfig()
    """
    Configurazione per il monitoraggio dello stato di salute.
    """


MasterConfigType = TypeVar("MasterConfigType", bound=MasterConfig)


class MasterProcess(BaseProcess[MasterConfigType], Generic[MasterConfigType]):

    def __init__(
        self,
        config: MasterConfigType,
    ) -> None:
        super().__init__(name=self.__class__.__name__, config=config)

        self.slaves: dict[str, SlaveProcess[SlaveConfig]] = {}
        self.slaves_config: dict[str, SlaveConfig] = {}
        self.monitor_health: bool = config.health_check.enabled

        # Contatore globale dei restart (solo se limited)
        self.total_restarts = 0

    @final
    def work(self) -> None:

        self.stop_event = Event()

        self.__check_config()

        if len(self.slaves) > 0:
            self.__start_slave()

        self.health_monitor = HealthMonitor(
            logger=self.logger,
            slave=self.slaves,
            master_process=self,
            enabled=self.config.health_check.enabled,
            check_interval=self.config.health_check.check_interval,
        )

        self.health_monitor.start()

        if self.config.wait_mode == "infinite":
            self.logger.info("Wait mode: infinite. In attesa indefinita...")

            self.stop_event.wait()

        elif self.config.wait_mode == "none":
            self.logger.info("Wait mode: none. Mi fermo appena i figli terminano.")

            while not self.stop_event.is_set():
                if all(not c.is_alive() for c in self.slaves.values()):
                    self.logger.info("Tutti i figli terminati. Esco.")
                    break
                time.sleep(1)

        # Quando esco dal main_loop, fermo i figli e health_monitor
        self.stop_all_slave()
        self.wait_for_slave()

        self.logger.debug("{} terminato.", self.name)

    def init_slave(
        self,
        slave_class: type[SlaveProcess],
        config: SlaveConfig,
        name_suffix: str = "",
    ) -> None:

        self.setup_logger()

        slave_instance: SlaveProcess = slave_class(config=config)

        if name_suffix:
            slave_instance.name = f"{slave_instance.__class__.__name__}_{name_suffix}"

        self.slaves[slave_instance.name] = slave_instance
        self.slaves_config[slave_instance.name] = config

        self.logger.info(f"Aggiunto figlio: {slave_instance.name}")

        if self.monitor_health:
            self.logger.info(
                f"Monitoraggio dello stato di salute abilitato per: {slave_instance.name}"
            )

    def init_multiple_slave(
        self, slave_class: type[SlaveProcess], configs: list[type[SlaveConfig]]
    ) -> None:
        """
        Init multiple slave processes.

        If no config is provided, a default SlaveConfig will be used.

        Args:
            slave_class (type[SlaveProcess]): SlaveProcess class.
            configs (list[SlaveConfig]): List of SlaveConfig classes.
        """

        self.setup_logger()

        if len(configs) == 0:
            self.logger.warning("No config provided. Assuming default SlaveConfig.")
            configs = [SlaveConfig]

        for i, config in enumerate(configs):
            self.init_slave(
                slave_class=slave_class, config=config(), name_suffix=str(i)
            )

    def __start_slave(self) -> None:
        self.logger.info("Figli da avviare: %d", len(self.slaves))

        for slave_instance in self.slaves.values():
            slave_instance.start()
            self.logger.info(f"Avviato figlio: {slave_instance.name}")

    def wait_for_slave(self) -> None:

        for slave in self.slaves.values():
            slave.join()
            self.logger.info(f"Figlio terminato: {slave.name}.")

        if all(not slave.is_alive() for slave in self.slaves.values()):
            self.logger.debug("Tutti i figli sono terminati.")

    def stop_all_slave(self) -> None:

        for slave in self.slaves.values():
            if slave.is_alive():
                slave.terminate()
                self.logger.warning(f"Figlio terminato forzatamente: {slave.name}")
            else:
                self.logger.info(f"Figlio già terminato: {slave.name}")

    def restart_all_slave(self) -> None:
        self.stop_all_slave()

        for slave_name, slave_instance in list(self.slaves.items()):
            # Riavvia i figli da config salvata
            self.init_slave(
                slave_class=slave_instance.__class__,
                config=self.slaves_config[slave_name],
                name_suffix=slave_name.split("_")[-1] if "_" in slave_name else "",
            )

        self.__start_slave()

    def remove_slave(self, slave_name: str) -> None:
        if slave_name in self.slaves:
            del self.slaves[slave_name]
        if slave_name in self.slaves_config:
            del self.slaves_config[slave_name]

        self.logger.info(f"Rimosso figlio: {slave_name}")

    def get_slave_status(self, slave_name: str) -> Optional[str]:
        for slave in self.slaves.values():
            if slave.name == slave_name:
                status = f"Processo {slave_name} è {'attivo' if slave.is_alive() else 'terminato'}"
                if self.monitor_health:
                    status += " (monitoraggio abilitato)"
                return status
        return None

    def restart_slave(self, slave_name: str) -> None:
        if slave_name in self.slaves:

            slave_class: Type[SlaveProcess] = self.slaves[slave_name].__class__
            slave_config: SlaveConfig = self.slaves_config[slave_name]

            self.logger.info(f"Riavvio del figlio: {slave_name}")

            assert not self.slaves[
                slave_name
            ].is_alive(), "Impossibile riavviare, il figlio è ancora attivo."

            self.remove_slave(slave_name)

            name_suffix = slave_name.split("_")[-1] if "_" in slave_name else ""
            self.init_slave(
                slave_class=slave_class,
                config=slave_config,
                name_suffix=name_suffix,
            )
            self.total_restarts += 1
            self.slaves[list(self.slaves.keys())[-1]].start()

        else:
            self.logger.warning(
                f"Impossibile riavviare, figlio {slave_name} non trovato."
            )

    def __check_config(self) -> None:

        if self.config.wait_mode == "limited":
            assert self.config.max_restarts > 0, "max_restarts deve essere > 0."

        elif self.config.wait_mode == "none":
            pass

        elif self.config.wait_mode == "infinite":
            pass

        else:
            raise ValueError("wait_mode non valido.")


class HealthMonitor:
    def __init__(
        self,
        logger,
        slave: dict[str, SlaveProcess[SlaveConfig]],
        master_process: MasterProcess,
        enabled: bool = False,
        check_interval: int = 2,
    ) -> None:
        self.logger = logger
        self.slave_processes: dict[str, SlaveProcess[SlaveConfig]] = slave
        self.enabled: bool = enabled
        self.check_interval: int = check_interval
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self.master_process: MasterProcess = master_process

    def start(self) -> None:

        if self._thread is not None and self._thread.is_alive():
            self.logger.warning("Il monitoraggio della salute è già attivo.")
            return

        if not self.enabled:
            self.logger.info("Monitoraggio della salute disabilitato.")
            return

        self.logger.info("Avvio monitoraggio dello stato di salute.")

        self._stop_event.clear()

        self._thread = Thread(
            target=self._run,
            name="HealthCheck",
            daemon=True,
        )

        if any(
            slave.config.check_config.to_monitor
            for slave in self.slave_processes.values()
        ):
            self._thread.start()
        else:
            self.logger.warning(
                "HealthMonitoring attivo ma nessun figlio da monitorare. Spegnimento..."
            )

    def stop(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            self.logger.info("Arresto del monitoraggio della salute in corso...")

            self._stop_event.set()
            self._thread.join()

            self.logger.info("Monitoraggio della salute arrestato.")

    def _run(self) -> None:
        time.sleep(2)  # Delay iniziale

        self.logger.debug(
            "Monitoraggio attivo per %s",
            [
                slave.name
                for slave in self.slave_processes.values()
                if slave.config.check_config.to_monitor
            ],
        )

        while not self._stop_event.is_set():
            self.logger.info("Health_check...")
            self._check_slave()
            time.sleep(self.check_interval)

    def _check_slave(self) -> None:
        to_restart = []

        for slave in self.slave_processes.values():
            if slave.config.check_config.to_monitor and not slave.is_alive():
                self.logger.warning(f"Figlio non risponde: {slave.name}")
                if slave.config.check_config.autorestart:
                    to_restart.append(slave.name)

        for slave in to_restart:
            self.master_process.restart_slave(slave)

        if self.master_process.config.wait_mode == "none":
            # In modalità none, se i figli sono terminati, stop_event sul master è settato dall'outer loop
            pass

        elif self.master_process.config.wait_mode == "limited":
            # In modalità limited, se abbiamo superato i restart permessi, settare stop_event
            if (
                self.master_process.total_restarts
                >= self.master_process.config.max_restarts
            ):
                self.master_process.stop_event.set()

        elif self.master_process.config.wait_mode == "infinite":
            # In modalità infinite non facciamo nulla, continua a lavorare.
            pass
