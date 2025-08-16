import requests
import json
import time
import os
import logging
from multiprocessing import set_start_method
from PyOrchestrate.core.orchestrator import Orchestrator, RunMode
from PyOrchestrate.core.agent.periodic_agent import PeriodicProcessAgent
from PyOrchestrate.core.base.exceptions import RecoverableException
from PyOrchestrate.core.utilities.event import OrchestratorEvent

# Telegram configuration
TELEGRAM_TOKEN = "***REMOVED_TELEGRAM_TOKEN***"
TELEGRAM_CHAT_ID = "***REMOVED_TELEGRAM_CHAT_ID***"


def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.info(f"Messaggio inviato con successo: {message}")
    except requests.RequestException as e:
        logging.error(f"Errore nell'invio del messaggio Telegram: {e}")


def on_agent_ready(agent_name: str, event_date, event_time):
    message = f"Agent: {agent_name} \nDate: {event_date}, \nTime: {event_time}\nmessage: Agent is ready."
    print(message)
    send_telegram_message(message)


def on_agent_started(agent_name: str, event_date, event_time):
    message = f"Agent: {agent_name} \nDate: {event_date}, \nTime: {event_time}\nmessage: Agent started."
    print(message)
    send_telegram_message(message)


def on_agent_stopped(agent_name: str):
    message = f"Agent: {agent_name}\nmessage: Agent stopped."
    print(message)
    send_telegram_message(message)


class WeatherCollector(PeriodicProcessAgent):

    class Config(PeriodicProcessAgent.Config):
        limit: int = 2
        execution_interval: float = 2
        url: str = "https://catfact.ninja/fact"
        output_file: str = "weather_data.json"
        print_result: bool = False

    config: Config

    def setup(self):
        super().setup()
        self.logger.info("Initial configuration of the WeatherCollector...")
        if not os.path.exists(self.config.output_file):
            with open(self.config.output_file, "w") as file:
                json.dump([], file)  # type: ignore
            self.logger.info(f"Output file created: {self.config.output_file}")

        time.sleep(2)

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

            self.logger.info(f"Data successfully saved in {self.config.output_file}.")

            if self.config.print_result:
                self.logger.info(f"Risultato: {data}")

        except Exception as e:
            raise RecoverableException(f"Errore nella richiesta: {e}")


if __name__ == "__main__":
    set_start_method("spawn")

    o_config = Orchestrator.Config(run_mode=RunMode.DAEMON)
    orchestrator = Orchestrator(name="Orchestrator", config=o_config)

    orchestrator.register_event(OrchestratorEvent.AGENT_READY, on_agent_ready)
    orchestrator.register_event(OrchestratorEvent.AGENT_STARTED, on_agent_started)
    orchestrator.register_event(OrchestratorEvent.AGENT_TERMINATED, on_agent_stopped)

    orchestrator.register_agent(WeatherCollector, "WeatherCollector1")
    orchestrator.register_agent(
        WeatherCollector,
        "WeatherCollector2",
        custom_config=WeatherCollector.Config(limit=5),
    )

    orchestrator.start()
    orchestrator.join()
