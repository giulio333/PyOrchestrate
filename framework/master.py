from multiprocessing import Process
from threading import Event
from logging import Logger
from framework.logger import setup_logger
from typing import Optional, List, final, Generic, TypeVar, Type
from threading import Thread, Event
import time

from framework.base import BaseConfig, BaseProcess, Config
from framework.child import ChildProcess, ChildConfig


class MasterConfig(BaseConfig):
    """
    Configurazioni di un MasterProcess.

    Attributes:
        check_interval (int): Intervallo in secondi tra un controllo e l'altro.
        logger (LoggerConfig): Configurazioni del `logger`.
    """

    check_interval: int = 2
    """Intervallo in secondi tra un HealthCheck e l'altro."""


MasterConfigType = TypeVar("MasterConfigType", bound=MasterConfig)


class MasterProcess(BaseProcess[MasterConfigType], Generic[MasterConfigType]):
    """
    Gestisce processi figli definiti dall'utente.
    """

    def __init__(
        self,
        config: MasterConfigType,
        monitor_health: bool = False,
    ) -> None:
        """
        Inizializza un'istanza di MasterProcess.

        Args:
            config (Config): Configurazioni del processo.
            monitor_health (bool): Flag per abilitare o disabilitare il monitoraggio dello stato di salute dei processi figli.
        """
        super().__init__(name=self.__class__.__name__, config=config)

        self.logger: Logger

        # dizionario dei processi figli
        self.children: dict[str, ChildProcess[ChildConfig]] = {}

        # dizionario delle configurazioni dei processi figli
        self.childs_config: dict[str, ChildConfig] = {}

        # Flag per il monitoraggio dello stato di salute dei processi figli
        self.monitor_health: bool = monitor_health

        # Barriera per terminare il master
        self.end = Event()

    @final
    def work(self) -> None:
        """
        Questo metodo non va sovrascritto.
        """

        if len(self.children) > 0:
            self.__start_children()

        # Thread per il monitoraggio dello stato di salute
        self.health_monitor = HealthMonitor(
            logger=self.logger,
            children=self.children,
            master_process=self,
            enabled=self.monitor_health,
            check_interval=self.config.check_interval,
        )

        self.health_monitor.start()

        self.end.wait()

        self.wait_for_children()

        self.logger.debug("%s terminato.", self.name)

    def init_children(
        self,
        child_class: type[ChildProcess],
        child_config: ChildConfig,
        name_suffix: str = "",
    ) -> None:
        """
        Istanzia e salva un processo figlio e le sue configurazioni.
        Permette, opzionalmente, di aggiungere un suffisso al nome del processo figlio.
        """

        self.setup_logger()

        # crea un'istanza del processo figlio
        child_instance: ChildProcess = child_class(config=child_config)

        if name_suffix:
            child_instance.name = f"{child_instance.__class__.__name__}_{name_suffix}"

        # aggiunge il processo figlio al dizionario
        self.children[child_instance.name] = child_instance

        # salva la configurazione originale del processo figlio
        self.childs_config[child_instance.name] = child_config

        self.logger.info(f"Aggiunto figlio: {child_instance.name}")

        if self.monitor_health:
            self.logger.info(
                f"Monitoraggio dello stato di salute abilitato per: {child_instance.name}"
            )

    def init_multiple_children(
        self, child_class: type[ChildProcess], configs: List[ChildConfig]
    ) -> None:
        """
        Istanzia e salva più processi figli della stessa classe con configurazioni diverse,
        usando internamente init_children e delegando a quest’ultima la creazione del suffisso.
        """
        self.setup_logger()

        for i, config in enumerate(configs):
            self.init_children(
                child_class=child_class, child_config=config, name_suffix=str(i)
            )

    def __start_children(self) -> None:
        """Avvia tutti i processi figli."""

        self.logger.info("Figli da avviare: %d", len(self.children))

        for child_instance in self.children.values():
            child_instance.start()
            self.logger.info(f"Avviato figlio: {child_instance.name}")

    def wait_for_children(self) -> None:
        """
        Aspetta che tutti i processi figli terminino.
        """

        for child in self.children.values():
            child.join()
            self.logger.info(f"Figlio terminato: {child.name}.")

        if all(not child.is_alive() for child in self.children.values()):
            self.logger.debug("Tutti i figli sono terminati.")

    def stop_all_children(self) -> None:
        """Ferma tutti i processi figli."""

        for child in self.children.values():
            if child.is_alive():
                child.terminate()
                self.logger.warning(f"Figlio terminato forzatamente: {child.name}")
            else:
                self.logger.info(f"Figlio già terminato: {child.name}")

    def restart_all_children(self) -> None:
        """
        Riavvia tutti i processi figli.
        """

        self.stop_all_children()

        for child_name, child_instance in self.children.items():

            self.init_children(
                child_class=child_instance.__class__,
                child_config=self.childs_config[child_name],
            )

        self.__start_children()

    def remove_child(self, child_name: str) -> None:
        """
        Rimuove un processo figlio specifico.
        """

        if child_name in self.children:
            del self.children[child_name]

        self.logger.info(f"Rimosso figlio: {child_name}")

    def get_child_status(self, child_name: str) -> Optional[str]:
        """
        Restituisce lo stato di un processo figlio.

        Args:
            child_name (str): Nome del processo figlio.

        Returns:
            Optional[str]: Stato del processo figlio.
        """

        for child in self.children.values():

            if child.name == child_name:
                status = f"Processo {child_name} è {'attivo' if child.is_alive() else 'terminato'}"

                if self.monitor_health:
                    status += " (monitoraggio abilitato)"

                return status

        return None

    def restart_child(self, child_name: str) -> None:
        """
        Riavvia un singolo processo figlio se presente.
        """

        if child_name in self.children:

            child_class = self.children[child_name].__class__
            child_config: ChildConfig = self.childs_config[child_name]

            self.logger.info(f"Riavvio del figlio: {child_name}")

            assert not self.children[
                child_name
            ].is_alive(), "Impossibile riavviare, il figlio è ancora attivo."

            # Rimuove il vecchio figlio
            self.remove_child(child_name)

            # Ricrea e riavvia il figlio
            name_suffix = child_name.split("_")[-1] if "_" in child_name else ""
            self.init_children(
                child_class=child_class,
                child_config=child_config,
                name_suffix=name_suffix,
            )
            self.children[child_name].start()
        else:
            self.logger.warning(
                f"Impossibile riavviare, figlio {child_name} non trovato."
            )


class HealthMonitor:
    """
    Monitora lo stato di salute dei processi figli.

    Avvia un thread dedicato che, a intervalli regolari,
    controlla se i processi sono ancora attivi.
    """

    def __init__(
        self,
        logger: Logger,
        children: dict[str, ChildProcess[ChildConfig]],
        master_process: MasterProcess,
        enabled: bool = False,
        check_interval: int = 2,
    ) -> None:
        """
        Inizializza il monitor.

        Args:
            logger (Logger): Logger da utilizzare.
            children (Dict[str, ChildProcess]): Dizionario dei processi figli.
            enabled (bool): Flag per abilitare o disabilitare il monitoraggio.
            check_interval (int): Intervallo in secondi tra un controllo e l'altro.
        """

        self.logger: Logger = logger
        self.children: dict[str, ChildProcess[ChildConfig]] = children
        self.enabled: bool = enabled
        self.check_interval: int = check_interval
        self._stop_event = Event()
        self._thread: Thread | None = None
        self.master_process: MasterProcess = master_process

    def start(self) -> None:
        """
        Avvia il monitoraggio in un thread separato.
        """

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

        # avvia solo se almeno un figlio è da monitorare
        if any(child.config.to_monitor for child in self.children.values()):
            self._thread.start()
        else:
            self.logger.warning(
                "HalthMonitoring attivo ma nessun figlio da monitorare. Spegnimento..."
            )

    def stop(self) -> None:
        """
        Ferma il monitoraggio della salute.
        """

        if self._thread is not None and self._thread.is_alive():
            self.logger.info("Arresto del monitoraggio della salute in corso...")

            self._stop_event.set()
            self._thread.join()

            self.logger.info("Monitoraggio della salute arrestato.")

    def _run(self) -> None:
        """
        Thread di controllo che verifica periodicamente lo stato dei figli.
        """
        # Delay iniziale per dare il tempo ai processi di avviarsi
        time.sleep(2)

        self.logger.debug(
            "Monitoraggio attivo per %s",
            [
                children.name
                for children in self.children.values()
                if children.config.to_monitor
            ],
        )

        while not self._stop_event.is_set():

            self.logger.info("Health_check...")
            self._check_children()
            time.sleep(self.check_interval)

    def _check_children(self) -> None:
        """
        Controlla lo stato di salute dei processi figli.

        Se un processo non risponde, viene riavviato se specificato in ChildConfig.
        """
        to_restart = []

        for child in self.children.values():

            if child.config.to_monitor and not child.is_alive():

                self.logger.warning(f"Figlio non risponde: {child.name}")

                if child.config.autorestart:
                    to_restart.append(child.name)

        for child_name in to_restart:
            self.master_process.restart_child(child_name)
