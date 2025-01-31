import time
import multiprocessing
import requests
import zmq

from PyOrchestrate.core.orchestrator import Orchestrator, AgentEntry
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.plugins.communication_plugins import ZeroMQPlugin


class MyConfig(BaseProcessAgent.Config):
    # URL della API di esempio (restituisce dati JSON)
    api_url: str = "https://catfact.ninja/fact"
    # Keyword da cercare nella risposta
    keyword: str = "and"
    # Intervallo di polling (in secondi)
    poll_interval: float = 1.0


class APIFetchAgent(BaseProcessAgent[MyConfig]):
    Config = MyConfig

    def setup(self) -> None:
        """
        Inizializzazione dell'agente: registra il plugin di comunicazione e logga il setup.
        """
        super().setup()
        zmq_plugin = ZeroMQPlugin("tcp://localhost:5555", zmq.PUB)
        self.plugin_manager.register(zmq_plugin)
        self.logger.info(
            f"Inizializzazione di APIFetchAgent con API: {self.config.api_url}"
        )
        time.sleep(1)

    def execute(self) -> None:
        """
        Effettua il polling dell'API esterna e, se la keyword viene trovata nei dati,
        invia un messaggio all'altro agente.
        """
        super().execute()
        self.logger.info(
            f"Inizio polling dell'API ogni {self.config.poll_interval} secondi per la keyword: '{self.config.keyword}'"
        )
        try:
            # Ad esempio, eseguiamo 5 richieste
            for _ in range(5):
                self.logger.info("Richiedo i dati dall'API esterna...")
                response = requests.get(self.config.api_url)
                if response.status_code == 200:
                    json_data = response.json()
                    # Costruiamo una stringa contenente alcune informazioni utili
                    message_str = f"Corpo: {json_data.get('fact', '')}"
                    self.logger.info("Dati ricevuti dall'API:")
                    self.logger.info(message_str)
                    # Verifica se la keyword è presente nella stringa
                    if self.config.keyword in message_str:
                        self.logger.warning(f"Keyword '{self.config.keyword}' trovata!")
                        self.com.send(
                            f"Keyword '{self.config.keyword}' trovata: {message_str}"
                        )
                    else:
                        self.logger.info("Keyword non trovata in questo ciclo.")
                else:
                    self.logger.error(
                        f"Errore nell'accesso all'API: codice {response.status_code}"
                    )
                time.sleep(self.config.poll_interval)
        except Exception as e:
            self.logger.exception(f"Errore durante il polling dell'API: {e}")
        finally:
            # Al termine del ciclo, invia un segnale di STOP all'altro agente
            self.com.send("STOP")
            self.plugin_manager.unregister()

    def on_stop(self):
        """
        Log della terminazione dell'agente.
        """
        self.logger.info("APIFetchAgent terminato.")


class APIAlertAgent(BaseProcessAgent[MyConfig]):
    Config = MyConfig

    def setup(self) -> None:
        """
        Inizializza l'agente per la ricezione dei messaggi.
        """
        super().setup()
        zmq_plugin = ZeroMQPlugin("tcp://localhost:5555", zmq.SUB)
        self.plugin_manager.register(zmq_plugin)
        # Impostiamo il livello di log a INFO
        self.config.logger_config.level = "INFO"
        self.logger.info(
            "Inizializzazione di APIAlertAgent per la ricezione degli alert dall'API."
        )

    def execute(self) -> None:
        """
        Resta in ascolto dei messaggi provenienti da APIFetchAgent.
        """
        super().execute()
        self.logger.info("In ascolto dei messaggi inviati da APIFetchAgent...")
        try:
            while True:
                message = self.com.recv()
                self.logger.success(f"Messaggio ricevuto: {message}")
                if message == "STOP":
                    self.logger.info("Ricevuto segnale di STOP.")
                    break
        except Exception as e:
            self.logger.exception(f"Errore durante la ricezione dei messaggi: {e}")
        finally:
            self.plugin_manager.unregister()

    def on_stop(self):
        """
        Log della terminazione dell'agente.
        """
        self.logger.info("APIAlertAgent terminato.")


if __name__ == "__main__":
    # Necessario per il supporto al multiprocessing
    multiprocessing.set_start_method("spawn")

    # Inizializzazione dell'orchestrator
    orchestrator = Orchestrator()

    # Registrazione degli agenti
    fetch_agent: AgentEntry = orchestrator.register_agent(
        APIFetchAgent, "APIFetchAgent"
    )
    alert_agent: AgentEntry = orchestrator.register_agent(
        APIAlertAgent, "APIAlertAgent"
    )

    # Avvio degli agenti
    orchestrator.start()

    # Attesa della terminazione degli agenti
    orchestrator.join()
