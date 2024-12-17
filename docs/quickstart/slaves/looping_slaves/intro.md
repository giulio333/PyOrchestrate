---
title: SlaveProcess
---

Vediamo come creare e personalizzare uno **SlaveProcess** e come configurare le sue opzioni.

Per implementare uno **SlaveProcess**, creare una classe che estende `MasterProcess` all'interno della cartella `models`. Ad esempio:

```python
from framework.slave import SlaveProcess, SlaveConfig

class Worker(SlaveProcess[SlaveConfig]):
    def __init__(self, config: SlaveConfig) -> None:
        super().__init__(config)
```

## SlaveConfig

Ora possiamo definire una configurazione personalizzata per il nostro **SlaveProcess**.

Per farlo, estendere la classe `SlaveConfig`, ad esempio:

```python
from framework.slave import SlaveProcess

@dataclass
class WorkerConfig(SlaveProcess):
    message: str = "Hello, World!"
    repeat: int = 5


    def validate(self) -> None:
        if self.repeat < 0:
            raise ValueError("Repeat must be greater than 0.")
```

Qui abbiamo definito una configurazione personalizzata che contiene i campi:

- `message`: un messaggio di testo predefinito
- `repeat`: il numero di volte che il messaggio verrà ripetuto

Questi dati saranno accessibili all'interno del processo tramite l'attributo `config`.

Ogni configurazione (`SlaveConfig`) dispone di un metodo `validate`, che può essere sovrascritto per implementare logiche di validazione personalizzate.

Questo oggetto contiene anche configurazioni predefinite molto utili, elenchiamone alcune...

### CheckConfig

Ogni **MasterProcess** dispone di un meccanismo di controllo della salute per verificare lo stato dei propri **Slave**.

Puoi personalizzare il comportamento del controllo della salute su questo particolare **Slave** attraverso la configurazione `CheckConfig`.

```python
from framework.slave import CheckConfig

@dataclass
class LauncherConfig(MasterConfig):
    check_config = CheckConfig(to_monitor=True, autorestart=True, interval=1)
```

In questo modo, il **MasterProcess** monitora lo stato del **SlaveProcess** e lo riavvia automaticamente se necessario.

??? "code"
    ::: framework.core.slave.utilities.CheckConfig
        options:
            show_source: false
            merge_init_into_class: true
            members: false
            heading_level: 0

### LoggerConfig

Puoi personalizzare il logger del processo attraverso la configurazione `LoggerConfig`.

```python
from framework.slave import LoggerConfig

@dataclass
class LauncherConfig(MasterConfig):
    logger = LoggerConfig(level=DEBUG)
```

??? "code"
    ::: framework.core.slave.LoggerConfig
        options:
            show_source: false
            merge_init_into_class: true
            members: false
            heading_level: 0