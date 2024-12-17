---
title: MasterProcess
---

Vediamo come creare e personalizzare un **MasterProcess** e come configurare le sue opzioni.

Un **MasterProcess** è il processo principale responsabile della gestione e del controllo di altri processi (SlaveProcess).

Per implementare un **MasterProcess**, crea una classe che estende `MasterProcess` all'interno della cartella `models`. Ad esempio:

```python
from framework.master import MasterProcess, MasterConfig

class Launcher(MasterProcess):
    def __init__(self, config: MasterConfig, monitor_health: bool = False) -> None:
        super().__init__(config, monitor_health)
```

## MasterConfig

Ora possiamo definire una configurazione personalizzata per il nostro **MasterProcess**.

Per farlo, estendi la classe `MasterConfig`, ad esempio:

```python
from framework.master import MasterConfig

@dataclass
class LauncherConfig(MasterConfig):
    version: str = "1.0"
    start_time: datetime = datetime.now()
    output_folder: str = "output"


    def validate(self) -> None:
        if os.path.exists(self.output_folder):
            # do something
```

Qui abbiamo definito una configurazione personalizzata che contiene i campi:

- `version`: versione del processo.
- `start_time`: data di avvio del processo.
- `output_folder`: cartella di output del processo.

Questi dati saranno accessibili all'interno del processo tramite l'attributo `config`.

Ogni configurazione (`MasterConfig`) dispone di un metodo `validate`, che può essere sovrascritto per implementare logiche di validazione personalizzate.

Questo oggetto contiene anche configurazioni predefinite molto utili, elenchiamone alcune...

### HealthCheckConfig

Ogni **MasterProcess** dispone di un meccanismo di controllo della salute per verificare lo stato del processo.

Puoi personalizzare il controllo della salute del processo attraverso la configurazione `HealthCheckConfig`.

```python
from framework.master import HealthCheckConfig

@dataclass
class LauncherConfig(MasterConfig):
    version: str = "1.0"
    start_time: datetime = datetime.now()

    health_check = HealthCheckConfig(enabled=True, check_interval=5)
```

In questo modo, il processo controlla i propri slave ogni 5 secondi.

??? "code"
    ::: framework.core.master.utilities.HealthCheckConfig
        options:
            show_source: false
            merge_init_into_class: true
            members: false
            heading_level: 0

### LoggerConfig

Puoi personalizzare il logger del processo attraverso la configurazione `LoggerConfig`.

```python
from framework.master import LoggerConfig

@dataclass
class LauncherConfig(MasterConfig):
    version: str = "1.0"
    start_time: datetime = datetime.now()

    logger = LoggerConfig(level=DEBUG)
```