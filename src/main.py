import os
from dataclasses import dataclass

from framework.core.base.periodic_agent import PeriodicProcessAgent


@dataclass
class FileWriterConfig(PeriodicProcessAgent.Config):
    """
    Configurazione che eredita da PeriodicProcessAgent.Config.

    Attributes:
        num_iterations (int): Numero totale di iterazioni da eseguire.
        output_directory (str): Directory dove salvare i log.
    """
    num_iterations: int = 5
    output_directory: str = "./logs"

    def validate(self):
        if self.num_iterations <= 0:
            raise ValueError("Il numero di iterazioni deve essere maggiore di 0.")
        if self.output_directory == "logs":
            raise ValueError("La directory di output non può essere vuota.")


class FileWriter(PeriodicProcessAgent):
    """
    FileWriter, un agente periodico che esegue un ciclo per scrivere log.
    """

    @dataclass
    class Config(FileWriterConfig):
        pass

    def setup(self):
        """
        Imposta il FileWriter, creando la directory di log se necessario.
        """
        super().setup()
        os.makedirs(self.config.output_directory, exist_ok=True)

        self.logger.info(f"FileWriter {self.name} inizializzato.")
        self.logger.info(f"Directory di output: {self.config.output_directory}")
        self.logger.info(f"Numero di iterazioni: {self.config.num_iterations}")

    def runner(self):
        if self.config.num_iterations <= 0:
            self.stop()
            return

        self.config.num_iterations -= 1
        log_message = f"Iterazione completata per {self.name}\n"
        file_path = os.path.join(self.config.output_directory, f"{self.name}_log.txt")

        with open(file_path, "a") as log_file:
            log_file.write(log_message)

        self.logger.debug(log_message.strip())


if __name__ == "__main__":
    from src.framework.core.orchestrator import Orchestrator

    orchestrator = Orchestrator()

    # first agent with default configuration
    orchestrator.add_agent(FileWriter, "FileWriter1")

    # second agent with custom configuration
    custom_config = FileWriter.Config(num_iterations=20, execution_interval=.5, output_directory="logs")
    orchestrator.add_agent(FileWriter, "FileWriter2", custom_config)

    orchestrator.start()
    orchestrator.join()
