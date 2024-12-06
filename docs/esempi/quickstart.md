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

Un **MasterProcess** è il processo principale responsabile della gestione e del controllo di altri processi (SlaveProcess).

Per implementare un **MasterProcess**, crea una classe che estende `MasterProcess` all'interno della cartella `models`. Ad esempio:

```python
from framework.master import MasterProcess, MasterConfig, LoggerConfig

class Launcher(MasterProcess):
    def __init__(self, config: MasterConfig, monitor_health: bool = False) -> None:
        super().__init__(config, monitor_health)
```

## Personalizzazioni del MasterProcess

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

!!! tip
    Esempio di configurazione avanzata con logger e modalità di attesa specifica:

    ```python
    @dataclass
    class LauncherConfig(MasterConfig):
        logger = LoggerConfig(level=DEBUG)
        wait_mode = "none"
    ```