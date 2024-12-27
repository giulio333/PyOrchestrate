---
title: Utilizzo del Framework
---

Questo documento illustra come utilizzare il framework, partendo dalla definizione degli Agent nel file `models.py` e
arrivando all’avvio dell’intero sistema tramite un Orchestrator.
Il file `models.py` è obbligatorio e rappresenta il punto di ingresso principale per la definizione dei propri Agent
personalizzati e delle loro configurazioni.

## Definizione degli Agent in `models.py`

All’interno di `models.py` è possibile definire nuove classi che ereditano dalle classi fornite dal framework. Queste
classi devono implementare i metodi necessari a svolgere il compito specifico dell’Agent. Inoltre, è possibile
specificare una classe interna `Config` per stabilire i parametri chiave dell’Agent.

Ad esempio, di seguito è mostrata la definizione di un `WeatherCollector` che eredita da `PeriodicAgent` e `BaseProcessAgent`. 
Questo Agent di tipo processo esegue periodicamente le chiamate, utilizzando un intervallo stabilito nella sua `Config`. 

``` python
from PyOrchestrate.core.base import BaseProcessAgent
from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.base.periodic_agent import PeriodicAgent
from PyOrchestrate.core.base.utilities import LoggerConfig

class WeatherCollector(PeriodicAgent, BaseProcessAgent):
    """
    Makes a request to an API and saves the data in a file.
    """

    class Config(PeriodicAgent.Config):
        def __init__(self, output_file: str = "weather_data.json", url:str="https://catfact.ninja/fact"):
            super().__init__()
            self.output_file = output_file
            self.url = url

            # PeriodicAgent data
            self.limit = 5
            self.execution_interval = 5
            self.logger = LoggerConfig(level="INFO")

        def validate(self):
            pass

    def setup(self):
        """
        Initial setup of the WeatherCollector.
        """
        super().setup()
        self.logger.info("Configurazione iniziale del WeatherCollector...")
        if not os.path.exists(self.config.output_file):
            with open(self.config.output_file, "w") as file:
                json.dump([], file)  # Inizializza il file come lista vuota
            self.logger.info(f"Creato file di output: {self.config.output_file}")

    def runner(self):
        """
        Periodic logic (makes a request to the API and saves the data in a file).
        """
        self.logger.info(f"Making request to {self.config.url}...")

        try:
            response = requests.get(self.config.url)
            response.raise_for_status()
            data = response.json()

            with open(self.config.output_file, "r+") as file:
                records = json.load(file)
                records.append(data)
                file.seek(0)
                json.dump(records, file, indent=4)

            self.logger.info(f"Dati salvati correttamente in {self.config.output_file}.")

        except requests.RequestException as e:
            self.logger.error(f"Errore nella richiesta API: {e}")
```

## Avvio con un Orchestrator

Dopo aver definito gli Agent in `models.py`, è possibile utilizzare un Orchestrator per avviarli come processi o thread,
a seconda delle necessità. Nell’esempio seguente, si istanzia un Orchestrator, si registra il `WeatherCollector` e poi 
si avvia l’esecuzione. L’Orchestrator si occuperà di caricare gli Agent definiti, di monitorarli e di gestirne il ciclo 
di vita.

``` python
from PyOrchestrate.core.orchestrator import Orchestrator
from models import WeatherCollector

if __name__ == "__main__":
    orchestrator = Orchestrator()

    orchestrator.register_agent(WeatherCollector, "WeatherCollector1")

    orchestrator.start()
    orchestrator.join()
```

## Configurazione degli Agent

Le Config sono un elemento chiave per personalizzare il comportamento degli Agent. Nel caso del `PeriodicAgent`, la
`Config` fornisce i seguenti parametr:

| Parametro             | Descrizione                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **execution_interval** | (in secondi) specifica la frequenza con cui l’Agent esegue il compito.      |
| **delay_compensation** | se `True`, l’Agent tenterà di compensare eventuali ritardi mantenendo l’intervallo medio di esecuzione. |
| **limit**             | il numero massimo di esecuzioni.                                            |
| **logger**            | un dizionario che definisce il livello del logger, il formato dei messaggi e i gestori (ad es. `StreamHandler` per stampare su console). |

Questi parametri possono essere modificati per adattarsi alle esigenze specifiche della propria applicazione, senza
dover alterare la logica dell’Agent. Ad esempio, per aumentare la frequenza delle richieste, basterà ridurre `execution_interval`.