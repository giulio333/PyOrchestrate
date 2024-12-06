from multiprocessing import Process
from threading import Event
from logging import Logger
from framework.utilities.logger import setup_logger
from typing import Optional, List, final, Generic, TypeVar, Type, Callable, Literal
from threading import Thread, Event
import time

from framework.base_process.base import BaseConfig, BaseProcess, LoggerConfig
from framework.child.child import ChildProcess, ChildConfig


class MasterConfig(BaseConfig):
    """
    Configurazioni di un MasterProcess.

    Attributes:
        check_interval (int): Intervallo in secondi tra un controllo e l'altro.
        wait_mode (str): Modalità di attesa. Può essere "infinite", "limited", "none".
        max_restarts (int): Valido solo se wait_mode = "limited". Numero totale di riavvii consentiti.
    """

    check_interval: int = 2
    """Intervallo in secondi tra un HealthCheck e l'altro."""

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


MasterConfigType = TypeVar("MasterConfigType", bound=MasterConfig)


class MasterProcess(BaseProcess[MasterConfigType], Generic[MasterConfigType]):

    def __init__(
        self,
        config: MasterConfigType,
        monitor_health: bool = False,
    ) -> None:
        super().__init__(name=self.__class__.__name__, config=config)

        self.logger: Logger
        self.children: dict[str, ChildProcess[ChildConfig]] = {}
        self.childs_config: dict[str, ChildConfig] = {}
        self.monitor_health: bool = monitor_health

        # Evento stop del master
        self.stop_event = Event()

        # Contatore globale dei restart (solo se limited)
        self.total_restarts = 0

    def __check_config(self) -> None:

        if self.config.wait_mode == "limited":
            assert self.config.max_restarts > 0, "max_restarts deve essere > 0."

        elif self.config.wait_mode == "none":
            pass

        elif self.config.wait_mode == "infinite":
            pass

        else:
            raise ValueError("wait_mode non valido.")

    @final
    def work(self) -> None:

        self.__check_config()

        if len(self.children) > 0:
            self.__start_children()

        self.health_monitor = HealthMonitor(
            logger=self.logger,
            children=self.children,
            master_process=self,
            enabled=self.monitor_health,
            check_interval=self.config.check_interval,
        )

        self.health_monitor.start()

        self._main_loop()

        # Quando esco dal main_loop, fermo i figli
        self.stop_all_children()
        self.wait_for_children()

        self.logger.debug("%s terminato.", self.name)

    def _main_loop(self) -> None:
        """
        Gestisce il loop principale in base alla wait_mode.
        """
        if self.config.wait_mode == "infinite":
            self.logger.info("Wait mode: infinite. In attesa indefinita...")
            # Attendi finché non si chiama stop
            self.stop_event.wait()

        elif self.config.wait_mode == "limited":
            self.logger.info(
                f"Wait mode: limited con max_restarts={self.config.max_restarts}"
            )
            # In questa modalità, si rimane attivi finché non si esauriscono i riavvii
            # oppure si termina manualmente.
            while not self.stop_event.is_set():
                # Se abbiamo raggiunto il numero massimo di riavvii, fermiamo il master
                if self.total_restarts >= self.config.max_restarts:
                    self.logger.info("Raggiunto il numero massimo di riavvii. Esco.")
                    break
                time.sleep(1)

        elif self.config.wait_mode == "none":
            self.logger.info("Wait mode: none. Mi fermo appena i figli terminano.")
            # In questa modalità, aspettiamo che i figli si fermino una volta
            # e poi usciamo.
            while not self.stop_event.is_set():
                if all(not c.is_alive() for c in self.children.values()):
                    self.logger.info("Tutti i figli terminati una volta. Esco.")
                    break
                time.sleep(1)

    def init_children(
        self,
        child_class: type[ChildProcess],
        child_config: ChildConfig,
        name_suffix: str = "",
    ) -> None:
        self.setup_logger()

        child_instance: ChildProcess = child_class(config=child_config)

        if name_suffix:
            child_instance.name = f"{child_instance.__class__.__name__}_{name_suffix}"

        self.children[child_instance.name] = child_instance
        self.childs_config[child_instance.name] = child_config

        self.logger.info(f"Aggiunto figlio: {child_instance.name}")

        if self.monitor_health:
            self.logger.info(
                f"Monitoraggio dello stato di salute abilitato per: {child_instance.name}"
            )

    def init_multiple_children(
        self, child_class: type[ChildProcess], configs: List[ChildConfig]
    ) -> None:
        self.setup_logger()

        for i, config in enumerate(configs):
            self.init_children(
                child_class=child_class, child_config=config, name_suffix=str(i)
            )

    def __start_children(self) -> None:
        self.logger.info("Figli da avviare: %d", len(self.children))

        for child_instance in self.children.values():
            child_instance.start()
            self.logger.info(f"Avviato figlio: {child_instance.name}")

    def wait_for_children(self) -> None:
        for child in self.children.values():
            child.join()
            self.logger.info(f"Figlio terminato: {child.name}.")

        if all(not child.is_alive() for child in self.children.values()):
            self.logger.debug("Tutti i figli sono terminati.")

    def stop_all_children(self) -> None:
        for child in self.children.values():
            if child.is_alive():
                child.terminate()
                self.logger.warning(f"Figlio terminato forzatamente: {child.name}")
            else:
                self.logger.info(f"Figlio già terminato: {child.name}")

    def restart_all_children(self) -> None:
        self.stop_all_children()

        for child_name, child_instance in list(self.children.items()):
            # Riavvia i figli da config salvata
            self.init_children(
                child_class=child_instance.__class__,
                child_config=self.childs_config[child_name],
                name_suffix=child_name.split("_")[-1] if "_" in child_name else "",
            )

        self.__start_children()

    def remove_child(self, child_name: str) -> None:
        if child_name in self.children:
            del self.children[child_name]
        if child_name in self.childs_config:
            del self.childs_config[child_name]

        self.logger.info(f"Rimosso figlio: {child_name}")

    def get_child_status(self, child_name: str) -> Optional[str]:
        for child in self.children.values():
            if child.name == child_name:
                status = f"Processo {child_name} è {'attivo' if child.is_alive() else 'terminato'}"
                if self.monitor_health:
                    status += " (monitoraggio abilitato)"
                return status
        return None

    def restart_child(self, child_name: str) -> None:
        if child_name in self.children:
            child_class = self.children[child_name].__class__
            child_config: ChildConfig = self.childs_config[child_name]

            self.logger.info(f"Riavvio del figlio: {child_name}")

            assert not self.children[
                child_name
            ].is_alive(), "Impossibile riavviare, il figlio è ancora attivo."

            self.remove_child(child_name)

            name_suffix = child_name.split("_")[-1] if "_" in child_name else ""
            self.init_children(
                child_class=child_class,
                child_config=child_config,
                name_suffix=name_suffix,
            )
            self.total_restarts += 1
            self.children[list(self.children.keys())[-1]].start()
        else:
            self.logger.warning(
                f"Impossibile riavviare, figlio {child_name} non trovato."
            )


class HealthMonitor:
    def __init__(
        self,
        logger: Logger,
        children: dict[str, ChildProcess[ChildConfig]],
        master_process: MasterProcess,
        enabled: bool = False,
        check_interval: int = 2,
    ) -> None:
        self.logger: Logger = logger
        self.children: dict[str, ChildProcess[ChildConfig]] = children
        self.enabled: bool = enabled
        self.check_interval: int = check_interval
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self.master_process: MasterProcess = master_process

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            self.logger.warning("Il monitoraggio della salute è già attivo.")
            return

        self.logger.info("Avvio monitoraggio dello stato di salute.")

        self._stop_event.clear()

        self._thread = Thread(
            target=self._run,
            name="HealthCheck",
            daemon=True,
        )

        if any(
            child.config.check_config.to_monitor for child in self.children.values()
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
                child.name
                for child in self.children.values()
                if child.config.check_config.to_monitor
            ],
        )

        while not self._stop_event.is_set():
            self.logger.info("Health_check...")
            self._check_children()
            time.sleep(self.check_interval)

    def _check_children(self) -> None:
        to_restart = []

        for child in self.children.values():
            if child.config.check_config.to_monitor and not child.is_alive():
                self.logger.warning(f"Figlio non risponde: {child.name}")
                if child.config.check_config.autorestart:
                    to_restart.append(child.name)

        for child_name in to_restart:
            self.master_process.restart_child(child_name)

        # Se non siamo in "infinite" e non ci sono figli attivi
        # e non possiamo più fare nulla, fermiamo il master
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
            # In modalità infinite non facciamo nulla, continua a girare.
            pass
