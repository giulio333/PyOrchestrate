---
title: BaseAgent
---

# BaseAgent, ThreadAgent e ProcessAgent: Componenti Principali del Framework PyOrchestrate

Questa documentazione descrive le classi `BaseAgent`, `ThreadAgent` e `ProcessAgent`, che costituiscono i componenti
principali per la definizione di Agent astratti, thread-based e process-based nel framework PyOrchestrate. Ogni classe
estende la funzionalità di `BaseClass` aggiungendo logiche specifiche per thread e processi.

---

## BaseAgent

### Descrizione

`BaseAgent` è una classe astratta che fornisce l'interfaccia comune per tutti gli Agent. Include la validazione della
configurazione e la gestione del ciclo di vita degli Agent.

### Metodi

#### validate_config()

!!! Abstract "Code"
    ::: PyOrchestrate.core.base.base_agent.BaseAgent.validate_config
        options:
            heading_level: 0

Valida la configurazione dell'Agent.

Questo chiama il metodo `config.validate()` dove sarà possibile definire la logica di validazione della configurazione.
La validazione della configurazione è facoltativa e può essere implementata nelle sottoclassi di `BaseConfig`.

La validazione viene eseguita automaticamente all'avvio dell'Agent nel metodo `run` subito dopo la configurazione
del logger.

#### run()

!!! Abstract "Code"
    ::: PyOrchestrate.core.base.base_agent.BaseAgent.run
        options:
            heading_level: 0
            
Gestisce il ciclo di vita dell'Agent.

Rappresenta il ciclo di vita dell'Agent e include la configurazione del logger, la validazione della configurazione ed
esegue il metodo `execute` che contiene la logica dell'Agent.

!!! warning
Se la configurazione non è valida, l'Agent non verrà eseguito.

Se una eccezione viene propagata durante l'esecuzione dell'Agent, verrà loggata e l'Agent verrà arrestato.

!!! tip
Gli Agent più specializzati gestiscono l'arresto in modo specifico impedendo la propagazione dell'eccezione.

#### `execute()` (Astratto)

Metodo astratto che deve essere implementato nelle sottoclassi per definire la logica dell'Agent.

#### `stop()`

Gestisce l'arresto dell'Agent. Questo metodo è facoltativo e può essere implementato per aggiungere funzionalità di
terminazione specifiche.

---

## ThreadAgent

### Descrizione

`ThreadAgent` estende `BaseAgent` e `threading.Thread`, permettendo l'esecuzione di Agent come thread.

### Metodi

#### `run()`

Override del metodo `run` di `threading.Thread`.

#### `stop()`

Gestisce la richiesta di arresto del thread.

Per comandare l'arresto del thread, è necessario invocare il metodo `stop` che imposta il flag `_stop_event`. L'utilizzo
specifico di `_stop_event` è delegato agli Agent specializzati.

#### `execute()` (Astratto)

Metodo astratto che deve essere implementato per definire la logica del thread.

---

## ProcessAgent

### Descrizione

`ProcessAgent` estende `BaseAgent` e `multiprocessing.Process`, permettendo l'esecuzione di Agent come processi
separati.

### Metodi

#### `run()`

Override del metodo `run` di `multiprocessing.Process`.

#### `stop()`

Gestisce la richiesta di arresto del processo.

Per comandare l'arresto del processo, è necessario invocare il metodo `stop` che imposta il flag `_stop_event`.
L'utilizzo specifico di `_stop_event` è delegato agli Agent specializzati.

#### `execute()` (Astratto)

Metodo astratto che deve essere implementato per definire la logica del processo.

---

## Esempio di Utilizzo

### Definizione di un ThreadAgent Personalizzato

```python 
import time
from PyOrchestrate.core.base.base_agent import ThreadAgent


class CustomThreadAgent(ThreadAgent):
    def execute(self):
        while not self.stop_event.is_set():
            self.logger.info("Esecuzione di CustomThreadAgent...")
            time.sleep(1)


if __name__ == "__main__":
    agent = CustomThreadAgent(name="MyThreadAgent", config=None)
    agent.start()
    time.sleep(5)
    agent.stop()
    agent.join()
```

### Definizione di un ProcessAgent Personalizzato

```python 
import time
from PyOrchestrate.core.base.base_agent import ProcessAgent


class CustomProcessAgent(ProcessAgent):
    def execute(self):
        while not self.stop_event.is_set():
            self.logger.info("Esecuzione di CustomProcessAgent...")
            time.sleep(1)


if __name__ == "__main__":
    agent = CustomProcessAgent(name="MyProcessAgent", config=None)
    agent.start()
    time.sleep(5)
    agent.stop()
    agent.join()
```