import time
import multiprocessing
import zmq

from PyOrchestrate.core.orchestrator import Orchestrator, AgentEntry
from PyOrchestrate.core.plugins.communication_plugins import ZeroMQPubSub
from PyOrchestrate.core.base.periodic_agent import PeriodicProcessAgent

############################################################
# AGENTE DI INVIO DEL FILE (FILE SEND AGENT)
############################################################


class FileSendConfig(PeriodicProcessAgent.Config):
    # Percorso del file da inviare
    file_path: str = "file_to_send.dat"
    # Dimensione del chunk (in bytes)
    chunk_size: int = 1024
    # Intervallo di esecuzione in secondi
    execution_interval = 0.2
    # Se 'limit' è 0 si esegue indefinitamente (qui lo usiamo per inviare il file a pezzi)
    limit = 0


class FileSendAgent(PeriodicProcessAgent[FileSendConfig]):
    Config = FileSendConfig

    def setup(self) -> None:
        super().setup()
        # Configuriamo il plugin ZeroMQ in modalità PUB e lo "bindiamo" su tcp://0.0.0.0:5555
        zmq_plugin = ZeroMQPubSub("tcp://0.0.0.0:5555", zmq.PUB)
        self.plugin_manager.register(zmq_plugin)
        self.logger.info(
            f"Inizializzazione di FileSendAgent. File da inviare: {self.config.file_path}"
        )
        try:
            self.file = open(self.config.file_path, "rb")
        except Exception as e:
            self.logger.error(f"Errore nell'apertura del file: {e}")
            self.file = None
        self.finished = False

    def runner(self) -> None:
        super().runner()
        # Se il file non è stato aperto o abbiamo finito di leggerlo, non facciamo nulla
        if self.file is None or self.finished:
            return

        # Leggiamo un chunk dal file
        chunk = self.file.read(self.config.chunk_size)
        if chunk:
            self.logger.info(f"Invio chunk di {len(chunk)} byte...")
            self.com.send_string(chunk)
        else:
            self.logger.info("Invio completato: file terminato.")
            # Inviamo un messaggio speciale per segnalare la fine del trasferimento
            self.com.send_string("FILE_COMPLETE")
            self.finished = True

    def on_close(self):
        self.logger.warning("FileSendAgent terminato.")
        if self.file and not self.file.closed:
            self.file.close()
        # Inviamo un messaggio di STOP (opzionale)
        self.com.send_string("STOP")
        self.plugin_manager.unregister()


############################################################
# AGENTE DI RICEZIONE DEL FILE (FILE RECEIVE AGENT)
############################################################


class FileReceiveConfig(PeriodicProcessAgent.Config):
    # Percorso dove salvare il file ricevuto
    output_file: str = "file_received.dat"
    execution_interval = 0.2
    limit = 0  # esecuzione indefinita


class FileReceiveAgent(PeriodicProcessAgent[FileReceiveConfig]):
    Config = FileReceiveConfig

    def setup(self) -> None:
        super().setup()
        # Configuriamo il plugin ZeroMQ in modalità SUB e ci connettiamo al publisher
        zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)
        self.plugin_manager.register(zmq_plugin)
        # Sottoscriviamo a tutti i messaggi
        self.com.setsockopt(zmq.SUBSCRIBE, b"")
        self.logger.info(
            "FileReceiveAgent inizializzato, in attesa del file in arrivo..."
        )
        try:
            self.file = open(self.config.output_file, "wb")
        except Exception as e:
            self.logger.error(f"Errore nell'apertura del file di destinazione: {e}")
            self.file = None

    def runner(self) -> None:
        super().runner()
        if self.file is None:
            return

        try:
            # Ricezione in modalità non bloccante
            message = self.com.recv(flags=zmq.NOBLOCK)
        except zmq.Again:
            message = None

        if message is not None:
            # Se riceviamo il segnale di completamento, chiudiamo il file e logghiamo
            if isinstance(message, bytes) and message == b"FILE_COMPLETE":
                self.logger.info("Ricevuto segnale di completamento file.")
                self.file.close()
            # Se riceviamo il messaggio di STOP, chiudiamo il file (opzionale)
            elif isinstance(message, bytes) and message == b"STOP":
                self.logger.info("Ricevuto segnale di STOP.")
                if not self.file.closed:
                    self.file.close()
            else:
                # Ricevuto un chunk di dati
                # Se il messaggio è una stringa (in teoria ci aspettiamo bytes), lo convertiamo in bytes
                if isinstance(message, str):
                    message = message.encode("utf-8")
                self.file.write(message)
                self.file.flush()
                self.logger.info(f"Ricevuto e salvato un chunk di {len(message)} byte.")

    def on_close(self):
        self.logger.warning("FileReceiveAgent terminato.")
        if self.file and not self.file.closed:
            self.file.close()
        self.plugin_manager.unregister()


############################################################
# MAIN: REGISTRAZIONE DEGLI AGENTI E AVVIO
############################################################

if __name__ == "__main__":
    # Necessario per il supporto al multiprocessing
    multiprocessing.set_start_method("spawn")

    # Inizializzazione dell'orchestrator
    orchestrator = Orchestrator()

    # Registrazione degli agenti
    send_agent: AgentEntry = orchestrator.register_agent(FileSendAgent, "FileSendAgent")
    receive_agent: AgentEntry = orchestrator.register_agent(
        FileReceiveAgent, "FileReceiveAgent"
    )

    # Avvio degli agenti
    orchestrator.start()

    # Attesa della terminazione degli agenti
    orchestrator.join()
