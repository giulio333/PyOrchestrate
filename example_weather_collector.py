import requests
import json
import os
import logging
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicProcessAgent
from PyOrchestrate.core.base.exceptions import RecoverableException
from PyOrchestrate.core.utilities.event import OrchestratorEvent

# Configura il bot di Telegram
TELEGRAM_TOKEN = "***REMOVED_TELEGRAM_TOKEN***"
TELEGRAM_CHAT_ID = "***REMOVED_TELEGRAM_CHAT_ID***"


def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.info(f"Messaggio inviato con successo: {message}")
    except requests.RequestException as e:
        logging.error(f"Errore nell'invio del messaggio Telegram: {e}")


def on_agent_started(agent_name: str, event_date, event_time):
    message = f"Agent {agent_name} started. Date: {event_date}, Time: {event_time}"
    print(message)
    send_telegram_message(message)


def on_agent_stopped(agent_name: str, **kwargs):
    message = f"Agent {agent_name} stopped."
    print(message)
    send_telegram_message(message)


def on_all_agents_stopped():
    message = "All agents stopped."
    print(message)
    send_telegram_message(message)


class WeatherCollector(PeriodicProcessAgent["WeatherCollector.Config"]):
    class Config(PeriodicProcessAgent.Config):
        limit: int = 2
        execution_interval: float = 2
        url: str = "https://catfact.ninja/fact"
        output_file: str = "weather_data.json"
        print_result: bool = False

    def setup(self):
        super().setup()
        self.logger.info("Configurazione iniziale del WeatherCollector...")
        if not os.path.exists(self.config.output_file):
            with open(self.config.output_file, "w") as file:
                json.dump([], file)  # type: ignore
            self.logger.info(f"Creato file di output: {self.config.output_file}")

    def runner(self):
        self.logger.info(f"Making request to {self.config.url}...")

        try:
            response = requests.get(self.config.url)
            response.raise_for_status()
            data = response.json()

            with open(self.config.output_file, "r+") as file:
                records = json.load(file)
                records.append(data)
                file.seek(0)
                json.dump(records, file, indent=4)  # type: ignore

            self.logger.info(f"Dati salvati correttamente in {self.config.output_file}.")

            if self.config.print_result:
                self.logger.info(f"Risultato: {data}")

        except requests.RequestException as e:
            raise RecoverableException(f"Errore nella richiesta: {e}")


if __name__ == "__main__":
    orchestrator = Orchestrator("Orchestrator")

    orchestrator.event_manager.connect(OrchestratorEvent.AGENT_STARTED.value, on_agent_started)
    orchestrator.event_manager.connect(OrchestratorEvent.AGENT_TERMINATED.value, on_agent_stopped)
    orchestrator.event_manager.connect(OrchestratorEvent.ALL_AGENTS_COMPLETED.value, on_all_agents_stopped)

    orchestrator.register_agent(WeatherCollector, "WeatherCollector1")

    orchestrator.start()
    orchestrator.join()
