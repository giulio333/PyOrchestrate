---
title: ThreadPoolSlave
---

Vediamo come creare e personalizzare uno **ThreadPoolSlave** e come configurare le sue opzioni.

Per implementare uno **ThreadPoolSlave**, dobbiamo definire una configurazione che estenda `ThreadPoolSlaveConfig` e uno
processo che estenda `ThreadPoolSlave`.

```python
from PyOrchestrate.core.slave import ThreadPoolSlave, ThreadPoolSlaveConfig


@dataclass
class PrinterConfig(ThreadPoolSlaveConfig):
    interval = 1
    compensate_delay = True

    logger = LoggerConfig(level="TRACE")
    check_config = CheckConfig(to_monitor=False, autorestart=False)


class PrinterPool(ThreadPoolSlave[PrinterConfig]):

    def __init__(self, config: PrinterConfig) -> None:
        super().__init__(config=config, workers=[printer])
```

## ThreadPoolSlaveConfig

Analizziamo la configurazione `ThreadPoolSlaveConfig`...

??? "code"
::: framework.core.slave.ThreadPoolSlaveConfig
options:
show_source: false
merge_init_into_class: true
members: false
heading_level: 0

Questi dati saranno accessibili all'interno del processo tramite l'attributo `config`.

Ogni configurazione (`ThreadPoolSlaveConfig`) dispone di un metodo `validate`, che può essere sovrascritto per
implementare logiche di validazione personalizzate.

Questo oggetto contiene anche configurazioni predefinite molto utili:

- `logger`: per personalizzare il logger del processo.
- `check_config`: per monitorare lo stato del processo e riavviarlo automaticamente se necessario.
- `compensate_delay`: per compensare il ritardo di esecuzione del processo.
- `interval`: per impostare l'intervallo di esecuzione del processo.

### CheckConfig

Ogni **MasterProcess** dispone di un meccanismo di controllo della salute per verificare lo stato dei propri **Slave**.

Puoi personalizzare il comportamento del controllo della salute su questo particolare **Slave** attraverso la
configurazione `CheckConfig`.

```python
from PyOrchestrate.slave import CheckConfig


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
from PyOrchestrate.slave import LoggerConfig


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