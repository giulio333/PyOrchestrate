# Standard Modules

Python ha una libreria standard molto vasta che include numerosi moduli utilizzabili per una varietà di applicazioni. 

Qui di seguito sono elencati alcuni dei moduli più importanti e utili.

> Per una lista completa, consulta il [Python Module Index](https://docs.python.org/3/py-modindex.html)

## 1. Gestione di file e directory

- **`os`**: Fornisce funzioni per interagire con il sistema operativo, inclusa la gestione di file e directory.
- **`shutil`**: Offre operazioni di alto livello per la gestione di file, come copiare e spostare file.
- **`glob`**: Consente di trovare percorsi di file che corrispondono a determinati pattern.
- **`pathlib`**: Fornisce un'interfaccia orientata agli oggetti per la gestione di percorsi di file.

## 2. Manipolazione di file

- **`io`**: Gestisce le operazioni di input/output su file e stream.
- **`csv`**: Modulo per leggere e scrivere file CSV (Comma Separated Values).
- **`json`**: Offre strumenti per lavorare con dati JSON (JavaScript Object Notation).
- **`pickle`**: Serve per serializzare e deserializzare strutture dati Python.

## 3. Gestione delle date e orari

- **`datetime`**: Modulo principale per la gestione di date e orari.
- **`time`**: Fornisce funzioni per lavorare con il tempo e misurare la durata di esecuzione.
- **`calendar`**: Modulo per gestire calendari e creare rappresentazioni di calendari.

## 4. Matematica e calcoli scientifici

- **`math`**: Fornisce funzioni matematiche di base come radici quadrate, logaritmi, funzioni trigonometriche e altro.
- **`statistics`**: Offre funzioni per calcoli statistici come medie, mediane, deviazioni standard, ecc.
- **`random`**: Consente di generare numeri casuali, mescolare sequenze e selezionare elementi casuali.
- **`fractions`**: Gestisce frazioni razionali.
- **`decimal`**: Lavora con numeri decimali con precisione maggiore rispetto a `float`.

## 5. Networking e comunicazione

- **`socket`**: Permette di creare e gestire connessioni di rete (TCP/UDP).
- **`http.client`**: Modulo per la creazione di client HTTP per inviare richieste e ottenere risposte.
- **`urllib`**: Offre una serie di funzioni per l'elaborazione di URL e per l'interazione con risorse web.
- **`smtplib`**: Modulo per inviare email usando il protocollo SMTP.
- **`ssl`**: Fornisce strumenti per gestire connessioni sicure tramite SSL.

## 6. Sistema e subprocessi

- **`sys`**: Fornisce accesso a variabili e funzioni che interagiscono con l'interprete Python.
- **`subprocess`**: Consente di eseguire comandi di sistema come subprocessi e di gestire input/output.
- **`signal`**: Gestisce segnali per la gestione di eventi esterni (come l'interruzione di esecuzione di programmi).
- **`argparse`**: Modulo per creare parser di linea di comando, utile per la gestione degli argomenti di programmi eseguiti da shell.

## 7. Threading e parallelismo

- **`threading`**: Modulo per la gestione di thread multipli.
- **`multiprocessing`**: Modulo per eseguire codice in processi paralleli, utile per migliorare le prestazioni.
- **`concurrent.futures`**: Facilita l'esecuzione di operazioni in parallelo utilizzando thread o processi.

## 8. Testing e debug

- **`unittest`**: Modulo per eseguire test automatici su unità di codice.
- **`doctest`**: Consente di testare il codice Python direttamente dalla documentazione.
- **`pdb`**: Debugger interattivo per Python.

## 9. Gestione delle eccezioni

- **`warnings`**: Modulo per generare avvertimenti nel codice.
- **`traceback`**: Fornisce strumenti per stampare, formattare e gestire tracebacks durante le eccezioni.
- **`logging`**: Modulo per gestire log di errori e informazioni sul funzionamento del codice.

## 10. Crittografia e hashing

- **`hashlib`**: Modulo per creare hash sicuri (come MD5, SHA).
- **`hmac`**: Offre strumenti per creare HMAC (Hash-based Message Authentication Code).
- **`secrets`**: Modulo per la generazione di token e stringhe segrete (usato per password o chiavi).

## 11. Altri moduli utili

- **`functools`**: Offre strumenti per la manipolazione di funzioni e oggetti.
- **`itertools`**: Modulo per creare iteratori complessi, utile per il trattamento di grandi dataset o combinazioni.
- **`collections`**: Modulo per lavorare con strutture dati avanzate come `deque`, `Counter` e `namedtuple`.
- **`re`**: Fornisce strumenti per la gestione di espressioni regolari e la ricerca avanzata nei testi.

## Esempio di utilizzo dei moduli

Ecco un esempio di come usare il modulo `math`:

```python
import math

# Calcolo della radice quadrata di un numero
result = math.sqrt(16)
print(result)  # Output: 4.0