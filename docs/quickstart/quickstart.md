---
title: QuickStart
---

L'elemento fondamentale di questo framework è il **processo**.

Il framework offre due tipologie di **processi** per creare un'architettura personalizzata:

1.  **`MasterProcess`**: un processo principale che può creare e gestire altri processi.
2.  **`SlaveProcess`**: un processo secondario che viene creato e gestito da un processo master.

!!! info
    - Per creare un **MasterProcess**, estendi la classe `MasterProcess`. 
    - Per creare un **SlaveProcess**, estendi la classe `SlaveProcess`.

Ogni **processo** può essere personalizzato attraverso un set di configurazioni specifiche:

1.  **`MasterConfig`**: configurazioni personalizzate per un **MasterProcess**.
2.  **`SlaveConfig`**: configurazioni personalizzate per uno **SlaveProcess**.

!!! tip 
    - Estendi la classe `MasterConfig` per definire configurazioni personalizzate per un **MasterProcess**. 
    - Estendi la classe `SlaveConfig` per definire configurazioni personalizzate per uno **SlaveProcess**.



## Models

Ogni **processo** può essere definito come un modello. I modelli devono essere collocati nella cartella `models` e rappresentano l'implementazione di uno specifico processo o configurazione.

## MasterProcess


### Personalizzazioni

Puoi personalizzare un **MasterProcess** definendo una configurazione specifica. Per farlo, estendi la classe `MasterConfig`, ad esempio:

```python
from framework.master import MasterConfig,

@dataclass
class LauncherConfig(MasterConfig):
    version: str = "1.0"
    start_time: datetime = datetime.now()
    output_folder: str = "output"


    def validate(self) -> None:
        if os.path.exists(self.output_folder):
            # do something
```

Ogni configurazione (`MasterConfig`) dispone di un metodo `validate`, che può essere sovrascritto per implementare logiche di validazione personalizzate.

### MasterConfig

Questo oggetto contiene anche delle configurazioni predefinite che possono essere utilizzate per personalizzare il comportamento del processo.

- `LoggerConfig`: configurazioni per il logger.
- `check_interval`: intervallo di controllo della salute del processo.
- `wait_mode`: modalità di attesa del processo.
- `max_restart`: numero massimo di riavvii del processo.

!!! example
    Esempio di configurazione avanzata con logger e modalità di attesa specifica:

    ```python
    @dataclass
    class LauncherConfig(MasterConfig):
        logger = LoggerConfig(level=DEBUG)
        wait_mode = "none"
    ```

## SlaveProcess

Uno **SlaveProcess** è un processo secondario che viene creato e gestito da un processo master.

Per implementare uno **SlaveProcess**, crea una classe che estenda `SlaveProcess` all'interno della cartella `models`. Ad esempio:

```python
from framework.slave import SlaveProcess, SlaveConfig

class Worker(SlaveProcess):
    def __init__(self, config: SlaveConfig) -> None:
        super().__init__(config=config)
```

### Personalizzazioni

Puoi personalizzare uno **SlaveProcess** definendo una configurazione specifica. Per farlo, estendi la classe `SlaveConfig`, ad esempio:

```python
from framework.slave import SlaveConfig,

@dataclass
class WorkerConfig(SlaveConfig):
    message: str = "Hello, World!"
    repeat: int = 5

    def validate(self) -> None:
        if "Hello" not in self.message:
            # do something
```

Ogni configurazione (`SlaveConfig`) dispone di un metodo `validate`, che può essere sovrascritto per implementare logiche di validazione personalizzate.

??? "code"
    ::: framework.slave.slave.SlaveProcess
        options:
            show_source: false
            merge_init_into_class: true
            members: false
            heading_level: 0

### SlaveConfig

Questo oggetto contiene anche delle configurazioni predefinite che possono essere utilizzate per personalizzare il comportamento del processo.

- `LoggerConfig`: configurazioni per il logger.
- `check_config`: configurazioni di controllo del processo.

!!! example
    Esempio di configurazione avanzata con logger e configurazioni di controllo specifiche:

    ```python
    @dataclass
    class WorkerConfig(SlaveConfig):

        message: str = "Hello, World!"
        repeat: int = 5

        logger = LoggerConfig(level=DEBUG)
        check_config = CheckConfig(to_monitor=False, autorestart=False, interval=1)
    ```

??? "code"
    ::: framework.slave.slave.SlaveConfig
        options:
            show_source: false
            merge_init_into_class: true
            members: false
            heading_level: 0

#### LoggerConfig

La classe `LoggerConfig` permette di configurare i parametri del logger per un processo. 

Descrizione

Questa classe definisce due attributi principali per configurare il logger:

1.	`level`: il livello di log da utilizzare, espresso come intero. I valori seguono la convenzione standard dei livelli di log (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).

2.	`filename`: il nome del file in cui i log verranno salvati. Se lasciato vuoto (stringa vuota ""), il framework utilizzerà il nome del processo come file di log predefinito.

??? "code"
    ::: framework.base_process.utilities.LoggerConfig
        options:
            show_source: false
            merge_init_into_class: true
            members: false
            heading_level: 0
