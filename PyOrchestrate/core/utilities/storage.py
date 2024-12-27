from typing import Type, Dict, Any, List
from threading import Thread
from multiprocessing import Process

from PyOrchestrate.core.base import BaseConfig, BaseProcess


class Storage:
    """
    Classe per gestire lo storage di classi Thread e Process insieme alle loro configurazioni.
    """

    def __init__(self):
        self.thread_storage: Dict[str, List[Dict[str, Any]]] = {}
        self.process_storage: Dict[str, List[Dict[str, Any]]] = {}

    def register_thread(
            self, name: str, thread_class: Type[Thread], config: BaseConfig, *args, **kwargs
    ):
        """
        Registra una classe Thread e la sua configurazione.

        Args:
            name (str): Nome del gruppo di thread.
            thread_class (Type[Thread]): Classe del thread.
            config (BaseConfig): Configurazione per il thread.
        """
        if name not in self.thread_storage:
            self.thread_storage[name] = []

        self.thread_storage[name].append(
            {
                "class": thread_class,
                "config": config,
                "args": args,
                "kwargs": kwargs,
            }
        )

    def register_process(
            self,
            name: str,
            process_class: Type[Process],
            config: BaseConfig,
            *args,
            **kwargs,
    ):
        """
        Registra una classe Process e la sua configurazione.

        Args:
            name (str): Nome del gruppo di processi.
            process_class (Type[Process]): Classe del processo.
            config (BaseConfig): Configurazione per il processo.
        """
        if name not in self.process_storage:
            self.process_storage[name] = []

        self.process_storage[name].append(
            {
                "class": process_class,
                "config": config,
                "args": args,
                "kwargs": kwargs,
            }
        )

    def instantiate_thread(self, name: str, index: int) -> Thread:
        """
        Istanzia un nuovo thread dalla configurazione registrata.

        Args:
            name (str): Nome del gruppo di thread.
            index (int): Indice del thread nel gruppo.

        Returns:
            Thread: Istanza del thread.
        """
        if name not in self.thread_storage or index >= len(self.thread_storage[name]):
            raise ValueError(f"Thread '{name}' con indice {index} non registrato.")

        thread_data = self.thread_storage[name][index]
        return thread_data["class"](
            name=f"{name}_{index}",
            config=thread_data["config"],
            *thread_data["args"],
            **thread_data["kwargs"],
        )

    def instantiate_process(self, name: str, index: int) -> BaseProcess:
        """
        Istanzia un nuovo processo dalla configurazione registrata.

        Args:
            name (str): Nome del gruppo di processi.
            index (int): Indice del processo nel gruppo.

        Returns:
            Process: Istanza del processo.
        """
        if name not in self.process_storage or index >= len(self.process_storage[name]):
            raise ValueError(f"Processo '{name}' con indice {index} non registrato.")

        process_data = self.process_storage[name][index]
        return process_data["class"](
            # name=f"{name}_{index}",
            config=process_data["config"],
            *process_data["args"],
            **process_data["kwargs"],
        )

    def restart_thread(self, name: str, index: int) -> Thread:
        """
        Riavvia un thread dalla configurazione registrata.

        Args:
            name (str): Nome del gruppo di thread.
            index (int): Indice del thread nel gruppo.

        Returns:
            Thread: Istanza del thread riavviato.
        """
        if name not in self.thread_storage or index >= len(self.thread_storage[name]):
            raise ValueError(f"Thread '{name}' con indice {index} non registrato.")

        try:
            thread = self.instantiate_thread(name, index)
            if thread.is_alive():
                raise RuntimeError(f"Il thread '{name}_{index}' è già in esecuzione.")
            thread.start()
            return thread
        except Exception as e:
            raise RuntimeError(
                f"Errore durante il riavvio del thread '{name}_{index}': {e}"
            )

    def restart_process(self, name: str, index: int) -> Process:
        """
        Riavvia un processo dalla configurazione registrata.

        Args:
            name (str): Nome del gruppo di processi.
            index (int): Indice del processo nel gruppo.

        Returns:
            Process: Istanza del processo riavviato.
        """
        if name not in self.process_storage or index >= len(self.process_storage[name]):
            raise ValueError(f"Processo '{name}' con indice {index} non registrato.")

        try:
            process = self.instantiate_process(name, index)
            if process.is_alive():
                raise RuntimeError(f"Il processo '{name}_{index}' è già in esecuzione.")
            process.start()
            return process
        except Exception as e:
            raise RuntimeError(
                f"Errore durante il riavvio del processo '{name}_{index}': {e}"
            )

    def stop_thread(self, name: str, index: int):
        """
        Termina un thread dalla configurazione registrata, se possibile.

        Args:
            name (str): Nome del gruppo di thread.
            index (int): Indice del thread nel gruppo.
        """
        if name not in self.thread_storage or index >= len(self.thread_storage[name]):
            raise ValueError(f"Thread '{name}' con indice {index} non registrato.")

        try:
            thread = self.instantiate_thread(name, index)
            if thread.is_alive():
                # Gestione della terminazione specifica per il thread
                raise NotImplementedError(
                    "Il metodo di terminazione del thread non è implementato."
                )
        except Exception as e:
            raise RuntimeError(
                f"Errore durante la terminazione del thread '{name}_{index}': {e}"
            )

    def stop_process(self, name: str, index: int):
        """
        Termina un processo dalla configurazione registrata, se possibile.

        Args:
            name (str): Nome del gruppo di processi.
            index (int): Indice del processo nel gruppo.
        """
        if name not in self.process_storage or index >= len(self.process_storage[name]):
            raise ValueError(f"Processo '{name}' con indice {index} non registrato.")

        try:
            process = self.instantiate_process(name, index)
            if process.is_alive():
                process.terminate()
        except Exception as e:
            raise RuntimeError(
                f"Errore durante la terminazione del processo '{name}_{index}': {e}"
            )


if __name__ == "__main__":
    # Esempio di utilizzo
    storage = Storage()
    storage.register_thread("example_thread", MyThreadClass, config, arg1, arg2)  # type: ignore
    thread_instance: Thread = storage.restart_thread("example_thread", 0)
