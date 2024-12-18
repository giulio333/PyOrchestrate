---
title: Utilizzo del Framework
---

Questo documento illustra come utilizzare il framework, partendo dalla definizione degli Agent nel file `models.py` e arrivando all’avvio dell’intero sistema tramite un Orchestrator. Il file `models.py` è obbligatorio e rappresenta il punto di ingresso principale per la definizione dei propri Agent personalizzati e delle loro configurazioni.

## Definizione degli Agent in `models.py`

All’interno di `models.py` è possibile definire nuove classi che ereditano dalle classi fornite dal framework. Queste classi devono implementare i metodi necessari a svolgere il compito specifico dell’Agent. Inoltre, è possibile specificare una classe interna `Config` per stabilire i parametri chiave dell’Agent, come l’intervallo di esecuzione (nel caso di un PeriodicAgent), la compensazione dei ritardi e le configurazioni del logger.

Ad esempio, di seguito è mostrata la definizione di un `VideoReaderAgent` che eredita da `PeriodicAgent`. Questo Agent legge periodicamente frame da un flusso video, utilizzando un intervallo stabilito nella sua `Config`. Se il ciclo impiega più tempo del previsto, la modalità `compensate_delay` tenta di mantenere l’intervallo complessivo costante. Inoltre, viene definito un logger con livello di log, formato e output standard.

``` python
from pyorchestrate.agents import PeriodicAgent
import logging
import cv2  # per la gestione di flussi video

class VideoReaderAgent(PeriodicAgent):
    class Config:
        interval = 5
        compensate_delay = True
        logger = {
            'level': logging.INFO,
            'format': '%(asctime)s [%(levelname)s] %(message)s',
            'handlers': [logging.StreamHandler()]
        }

    def run_task(self):
        # Lettura di un frame da un flusso video (esempio: RTSP)
        cap = cv2.VideoCapture("rtsp://example.com/myvideo")
        ret, frame = cap.read()
        cap.release()

        if ret:
            self.log("Frame letto con successo", level="info")
            # Inserire qui la logica di elaborazione del frame
            # ad esempio: salvataggio su disco, analisi di immagine, ecc.
        else:
            self.log("Impossibile leggere il frame", level="warning")
```

## Avvio con un Orchestrator

Dopo aver definito gli Agent in `models.py`, è possibile utilizzare un Orchestrator per avviarli come processi o thread, a seconda delle necessità. Nell’esempio seguente, si istanzia un Orchestrator, si registra il `VideoReaderAgent` come processo e poi si avvia l’esecuzione. L’Orchestrator si occuperà di caricare gli Agent definiti, di monitorarli e di gestirne il ciclo di vita.

``` python
from pyorchestrate import Orchestrator
from models import VideoReaderAgent

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.add_agent(VideoReaderAgent, agent_type='process')
    orchestrator.start()
    orchestrator.join()
```

## Configurazione degli Agent

Le Config sono un elemento chiave per personalizzare il comportamento degli Agent. Nel caso del `VideoReaderAgent`, la `Config` fornisce tre parametri:

- **interval**: (in secondi) specifica la frequenza con cui l’Agent esegue il compito.
- **compensate_delay**: se `True`, l’Agent tenterà di compensare eventuali ritardi mantenendo l’intervallo medio di esecuzione.
- **logger**: un dizionario che definisce il livello del logger, il formato dei messaggi e i gestori (ad es. `StreamHandler` per stampare su console).

Questi parametri possono essere modificati per adattarsi alle esigenze specifiche della propria applicazione, senza dover alterare la logica dell’Agent. Ad esempio, per aumentare la frequenza di lettura, basterà ridurre `interval`, mentre per scrivere i log su file si potrà aggiungere un `FileHandler` alla configurazione del logger.

## Conclusioni

L’obiettivo del file `models.py` e delle Config degli Agent è fornire un sistema chiaro e scalabile per definire, modificare e avviare gli Agent. Dalla semplice lettura periodica di un flusso video ad architetture più complesse, l’approccio basato sugli Agent e sull’Orchestrator consente di concentrare l’attenzione sulla logica dell’applicazione, lasciando al framework il compito di gestire i dettagli di basso livello relativi a processi, thread, logging e schedulazione.