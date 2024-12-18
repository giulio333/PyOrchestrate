---
title: PyOrchestrate Framework
---

PyOrchestrate è un framework concepito per semplificare la creazione e la gestione di architetture multi-processo e multi-thread in Python. La sua filosofia è quella di offrire un’infrastruttura versatile, in grado di adattarsi a diversi contesti operativi, dalla semplice esecuzione di un singolo task, alla gestione gerarchica di processi e thread multipli. Onestamente, è un approccio che sposa molto bene le necessità moderne di computing distribuito, evitando di reinventare continuamente la ruota.

## Concetti di Base

I due attori principali dell’architettura sono:

- **Orchestrator**: L’entità centrale incaricata di coordinare e supervisionare il lavoro degli Agenti.
- **Agent**: Un’unità esecutiva che può essere implementata come processo o thread.

L’idea chiave è che un Orchestrator possa agire come singolo punto di controllo, delegando compiti specifici a molteplici Agenti. Questo permette di mantenere una visione di insieme sulla pipeline di elaborazione, pur distribuendo l’esecuzione e ottimizzando le risorse disponibili.

## Scenari di Utilizzo

1. **Agente di tipo processo indipendente**  
   Un Agente di tipo processo può essere avviato ed eseguito senza alcun Orchestrator. Questo è particolarmente utile quando si ha un compito isolato: basta lanciare il processo e lasciare che svolga la sua attività fino al termine.

   **Esempio:**  
   Un processo che analizza un grande file di log, produce un report e poi termina. Non c’è bisogno di orchestrazione se l’attività è del tutto autonoma.

2. **Orchestrator che gestisce Agenti di tipo processo**  
   Un Orchestrator può coordinare molteplici processi, affidando a ciascuno un sottoinsieme di dati o un compito ben definito. Questo scenario è perfetto per implementare pipeline di elaborazione parallele, dove ogni processo svolge una parte del lavoro.

   **Esempio:**  
   Un Orchestrator riceve dati da sensori IoT e delega a diversi processi l’analisi di sottoinsiemi di questi dati, aggregando poi i risultati finali.

3. **Orchestrator Gerarchico**  
   Un livello ulteriore di complessità si ottiene quando un Orchestrator lancia Agenti di tipo processo, i quali a loro volta fungono da Orchestrator per un pool di thread. Questo consente di combinare la resilienza e l’isolamento dei processi con la leggerezza dei thread, massimizzando le prestazioni su hardware multi-core.

   **Esempio:**  
   Un Orchestrator principale avvia processi dedicati all’elaborazione di immagini di grandi dimensioni. Ogni processo lancia a sua volta thread multipli per analizzare porzioni dell’immagine in parallelo, riducendo i tempi di elaborazione.

## Gerarchia delle Unità

La gerarchia principale all’interno del framework è la seguente:

- **Orchestrator**

    - Gestisce direttamente gli **Agents (Process | Thread)**

- **Agent**

    - **OneShotAgent**
    - **LoopingAgent**
        - **PeriodicAgent**
        - **EventAgent**
        - **ScheduledAgent**

## Descrizione delle Unità Logiche

### Orchestrator

L’Orchestrator è il cuore pulsante del sistema. Coordina, supervisiona e gestisce il ciclo di vita degli Agenti.

**Funzionalità principali:**

- Creazione, avvio e arresto degli Agenti.
- Monitoraggio delle performance e dello stato degli Agenti.
- Possibile gestione gerarchica: un Orchestrator può orchestrare altri Orchestrator.

L’aspetto più affascinante è la sua natura flessibile: si presta sia a implementazioni semplici (pochi processi da coordinare) sia a scenari complessi (catene di elaborazione con diversi livelli gerarchici).

### OneShotAgent

Un **OneShotAgent** esegue un singolo compito per poi terminare. È l’agente perfetto per task di durata limitata e indipendenti.

**Esempi di utilizzo:**

- Elaborazione di un singolo file.
- Invio di una richiesta HTTP e gestione della risposta.
- Esecuzione di un comando di system check una tantum.

### LoopingAgent

Un **LoopingAgent** esegue ciclicamente un’attività, senza una frequenza predefinita. È come avere un “demone” personalizzato che continua a girare fino a quando non viene esplicitamente fermato o quando la sua logica interna lo richiede. Non ci sono regole stringenti: sta a te definire quando, quanto spesso e con quali condizioni fermarti o ripetere il ciclo.

Questo lo rende potentissimo in contesti dove la logica del loop è altamente specifica e non standardizzabile.

### PeriodicAgent

Un **PeriodicAgent** è una specializzazione di LoopingAgent con intervalli regolari di esecuzione. In altre parole, fa sempre la stessa cosa, ma a intervalli di tempo ben definiti.

**Esempi di utilizzo:**

- Raccolta dati da sensori ogni N secondi.
- Lettura di frame da una telecamera a un framerate costante.
- Invio di notifiche o report a intervalli pianificati.

### EventAgent

Un **EventAgent** esegue operazioni in risposta a un evento o a un segnale. È l’agente “reattivo” per definizione, perfetto per reagire immediatamente a cambiamenti nel contesto.

**Esempi di utilizzo:**

- Avvio di un task quando viene rilevato un nuovo file in una directory.
- Attivazione di un job quando un utente invia un input o un comando.
- Esecuzione di operazioni al verificarsi di un determinato segnale esterno.

### ScheduledAgent

Lo **ScheduledAgent** è un altro perfezionamento del concetto di LoopingAgent. A differenza del PeriodicAgent, che si limita a intervalli regolari, lo ScheduledAgent supporta pianificazioni più complesse, come orari precisi, date specifiche, o regole di calendario.

**Esempi di utilizzo:**

- Eseguire backup ogni giorno alle 02:00.
- Pianificare elaborazioni settimanali, mensili o basate su calendari aziendali.
- Avviare task in orari non regolari, come ogni primo lunedì del mese.

**Estendibilità e Personalizzazione degli Agenti**

Una delle caratteristiche più potenti di PyOrchestrate è la possibilità di partire dalle classi fornite dal framework, “prelevarle” ed estenderle per creare implementazioni su misura. Ogni classe, infatti, è stata progettata per essere sovrascrivibile in modo selettivo, con metodi già pronti all’uso e altri non modificabili, affinché tu possa concentrare i tuoi sforzi solo sulle logiche di business necessarie al tuo caso.

La scelta di quale classe utilizzare dipende direttamente dal livello di complessità della tua esigenza:

-   Se il tuo compito è semplice, come eseguire un backup di un file a intervalli regolari, potresti “attingere” direttamente dal **PeriodicAgent**. Questa classe, infatti, offre già un loop di esecuzione scandito da timer regolari e ti permette di intervenire solo sul “cosa” eseguire, senza dover reinventare il meccanismo di scheduling.
    
-   Nel caso in cui nessuno degli Agent forniti “chiavi in mano” soddisfi la tua logica, puoi risalire la gerarchia delle classi. Se, ad esempio, un **LoopingAgent** non basta, puoi spostarti a livelli superiori, fino ad arrivare alla classe Base di tutti gli Agent. Ovviamente, questo approccio ti metterà di fronte a un po’ più di lavoro, poiché salendo nella gerarchia avrai maggiore libertà ma dovrai occuparti di dettagli più bassi livello. Tuttavia, anche la classe Base non ti lascia a mani vuote: fornisce già i meccanismi fondamentali per gestire thread e processi in Python, così non dovrai mai partire davvero da zero.
    

In altre parole, PyOrchestrate ti permette di adottare un approccio graduale: parti da classi specializzate e, solo se necessario, risali alla sorgente della gerarchia. Puoi così trovare il perfetto equilibrio tra facilità di utilizzo e flessibilità, creando soluzioni eleganti e robuste senza compromessi. Con PyOrchestrate, la scalabilità non riguarda solo la mole di dati o la complessità del computing, ma anche il tuo stesso modo di implementare, estendere e plasmare il comportamento dei tuoi Agenti.

## Perché Scegliere PyOrchestrate?

PyOrchestrate non è solo una raccolta di pattern, ma un vero e proprio framework che mira a rendere la gestione dei task paralleli e distribuiti più chiara, strutturata e robusta.  
Sì, potresti scrivere tutto a mano con qualche riga di Python, `multiprocessing` o `threading`, ma perderesti la visione d’insieme, la flessibilità di combinare più livelli di orchestrazione e la semplicità di usare modelli già pronti. In un’epoca in cui le risorse computazionali devono essere sfruttate al massimo, avere un framework dedicato, come PyOrchestrate, è quasi una scelta obbligata se non vuoi incappare in un groviglio di codice difficile da mantenere.

## Conclusioni

PyOrchestrate offre una gerarchia chiara, funzionalità avanzate e flessibilità operativa. Dall’esecuzione di un singolo task a intere pipeline complesse, il framework può adattarsi a qualsiasi scenario. Tutto ciò rende lo sviluppo di architetture multi-processo e multi-thread meno stressante e più gratificante.

Se hai bisogno di scalabilità, robustezza e organizzazione in architetture complesse, PyOrchestrate è, secondo me, una strada da esplorare.
