---
title: BaseClass
---

# BaseClass e BaseConfig: Fondamenta del Framework PyOrchestrate

La classe `BaseClass` e la classe `BaseConfig` sono i pilastri fondamentali del framework PyOrchestrate. Forniscono una 
struttura comune e delle funzionalità essenziali che possono essere estese dagli Orchestrator e dagli Agent definiti 
dall'utente. Questo documento descrive in dettaglio la loro progettazione, funzionalità e utilizzo.

---

## BaseConfig

### Descrizione
`BaseConfig` è una classe astratta (Abstract Base Class) progettata per essere estesa da tutte le configurazioni 
utilizzate dagli Agent e dagli Orchestrator. Questa classe assicura che ogni configurazione abbia una struttura coerente 
e che possa includere funzionalità di validazione personalizzabili.

### Struttura
- **Attributi:**
  - `logger` (LoggerConfig): Una configurazione del logger fornita dall'utente o, in assenza di questa, una 
  - configurazione di default.

### Metodi
- **`__init__(logger_config: LoggerConfig | None = None)`**:
  Inizializza l'istanza con una configurazione del logger. Se non viene fornita, utilizza una configurazione di default 
- (`LoggerConfig`).

- **`validate()`**:
  Metodo vuoto che può essere sovrascritto nelle sottoclassi per implementare logiche di validazione personalizzate.

---

## BaseClass

### Descrizione
`BaseClass` è una classe base progettata per fornire un'interfaccia standardizzata agli Agent e agli Orchestrator del 
framework. Ogni istanza eredita una configurazione (`Config`) e un sistema di logging personalizzabile.

### Struttura
- **Attributi:**
  - `start_time`: Tempo di avvio dell'istanza.
  - `config`: Configurazione specifica, un'istanza di una sottoclasse di `BaseConfig`.
  - `logger`: Logger utilizzato per registrare eventi e messaggi.

- **Classe Interna Config:**
  Una sottoclasse di `BaseConfig` per definire configurazioni specifiche per `BaseClass`.

### Metodi

#### `__init__(name: str | None = None, config: BaseConfig | None = None, *args, **kwargs)`
Costruttore che inizializza l'istanza della classe base.

- **Parametri:**
  - `name`: Nome dell'istanza, che di default corrisponde al nome della classe.
  - `config`: Configurazione personalizzata o istanza di `Config`.

#### `setup_logger()`
Metodo per configurare il logger associato alla classe.

- **Descrizione:**
  Se il logger è già stato configurato, il metodo non fa nulla. Altrimenti:
  - Legge i parametri di configurazione dal campo `logger` della configurazione.
  - Configura il logger utilizzando il `LoggerFactory`.
  - Registra un messaggio di debug per confermare l'inizializzazione del logger.

- **Eccezioni:**
  - Utilizza la libreria `loguru` per catturare e rilanciare eventuali errori durante l'inizializzazione del logger.

---

## Esempio di Utilizzo

### Definizione di un'Implementazione Personalizzata
Di seguito un esempio di come estendere `BaseClass` e `BaseConfig` per creare una classe personalizzata con funzionalità 
aggiuntive.

```python
from PyOrchestrate.core.base import BaseClass, BaseConfig

class CustomConfig(BaseConfig):
    def validate(self):
        if not hasattr(self.logger, 'level'):
            raise ValueError("La configurazione del logger deve includere un livello.")

class CustomAgent(BaseClass):
    class Config(CustomConfig):
        pass

    def __init__(self, name: str, config: CustomConfig):
        super().__init__(name=name, config=config)
        self.setup_logger()

    def execute(self):
        self.logger.info(f"Esecuzione avviata per {self.name}.")
```

### Avvio del CustomAgent
```python
if __name__ == "__main__":
    config = CustomConfig()
    agent = CustomAgent(name="TestAgent", config=config)
    agent.execute()
```