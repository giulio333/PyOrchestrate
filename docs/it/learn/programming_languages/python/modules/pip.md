# PIP

**PIP** (Python Package Installer) è uno strumento che consente di installare e gestire i pacchetti Python. È il metodo più comune e semplice per accedere ai pacchetti pubblicati su [PyPI](https://pypi.org).

Per capire la differenza tra **PIP** e **PyPI**, considera quanto segue:

1. **Repository centralizzato**: Un luogo dove tutti i pacchetti disponibili possono essere archiviati e distribuiti. Il più famoso repository per Python è il **Python Package Index (PyPI)**.
2. **Strumento di gestione dei pacchetti**: Un sistema che consente agli sviluppatori di accedere facilmente a PyPI per scaricare, installare e gestire i pacchetti. Questo strumento si chiama **PIP**.

::: tip
PIP è preinstallato con Python 3.4 e versioni successive. Se stai utilizzando una versione precedente di Python, dovrai installare PIP manualmente.
:::

## Il Ciclo di Vita di un Pacchetto

L’ecosistema dei pacchetti Python funziona in questo modo:

1.	**Sviluppo**: Un programmatore scrive del codice per risolvere un problema specifico.

2.	**Condivisione**: Il codice viene pacchettizzato e pubblicato su un repository come **PyPI**, rendendolo disponibile per altri sviluppatori.

3.	**Utilizzo**: Un altro sviluppatore trova il pacchetto su **PyPI**, lo installa con **PIP** e lo utilizza nel proprio progetto.

4.	**Modifica e miglioramento**: Il nuovo sviluppatore può modificare il pacchetto per adattarlo alle sue necessità, creando una nuova versione o un progetto derivato.

## Ecosistema dei pacchetti Python

Il **repository** (o repo, in breve) si chiama **PyPI** (che sta per Python Package Index) ed è mantenuto da un gruppo di lavoro chiamato **Packaging Working Group**, che fa parte della **Python Software Foundation**, il cui compito principale è supportare gli sviluppatori Python nella distribuzione efficiente del codice.

Ovviamente non è l’unico repository Python esistente. Al contrario, ce ne sono molti altri, creati per progetti e gestiti da numerose comunità Python, grandi e piccole.

## Dove si trova Pip?

Quando installi Python, **pip** viene installato automaticamente nella stessa directory di Python. Di solito, **pip** si trova nella cartella Scripts all’interno della directory di installazione di Python. Ad esempio:

- Su **Windows**: `C:\Users\tuo_utente\AppData\Local\Programs\Python\PythonXX\Scripts\pip`
- Su **macOS** e **Linux**: `/usr/local/bin/pip` o `/usr/bin/pip`

::: tip
Per sapere esattamente dove si trova pip nel tuo sistema, puoi eseguire il comando:

```bash
which pip   # Su macOS o Linux
where pip   # Su Windows
```
:::

Quando installi **più versioni di Python**, avrai anche più comandi **pip** disponibili. Questo perché ogni versione di Python ha il suo pip **dedicato** per gestire i pacchetti per quella versione specifica.

Ad esempio, se hai installato sia Python 2.x che Python 3.x, potresti avere:

- **pip** o **pip2**: Si riferisce alla versione di **Python 2**.
- **pip3**: Si riferisce alla versione di P**ython 3**.

In generale, se esegui il comando pip senza specificare una versione, pip installerà i pacchetti per la versione di Python predefinita nel tuo sistema. Tuttavia, potresti voler utilizzare pip3 se desideri installare pacchetti specificamente per Python 3.

## Gestire versioni multiple di pip

Se vuoi essere sicuro di usare il **pip** giusto per una specifica versione di **Python**, puoi eseguire pip direttamente usando il comando associato alla versione Python, ad esempio

```bash
python3 -m pip install nome_pacchetto
```

Questo comando esegue il **pip** associato alla versione di Python 3.

## Comandi Utili

Ecco alcuni comandi utili per iniziare a lavorare con PIP

### Verifica la Versione di PIP

Per verificare la versione di **PIP** installata, esegui il comando:

::: code-group
```bash [Comando]
pip --version
```

```text [Output]
pip 21.1.3 from /usr/local/lib/python3.9/site-packages/pip (python 3.9)
```
:::

### Help

L'output di questo comando ti mostrerà tutti i comandi disponibili e le loro opzioni

::: code-group

```bash [Comando]
pip --help
```

```text [Output]
Usage:
  pip3 <command> [options]

Commands:
  install                     Install packages.
  download                    Download packages.
  uninstall                   Uninstall packages.
  freeze                      Output installed packages in requirements format.
  inspect                     Inspect the python environment.
  list                        List installed packages.
  show                        Show information about installed packages.
  check                       Verify installed packages have compatible dependencies.
  config                      Manage local and global configuration.
  search                      Search PyPI for packages.
  cache                       Inspect and manage pips wheel cache.
  index                       Inspect information available from package indexes.
  wheel                       Build wheels from your requirements.
  hash                        Compute hashes of package archives.
  completion                  A helper command used for command completion.
  debug                       Show information useful for debugging.
  help                        Show help for commands.
```

:::

Se hai bisogno di aiuto su un comando specifico, puoi eseguire:

::: code-group

```bash [Comando]
pip <comando> --help
```

```text [Output]
Usage:
  pip3 install [options] <requirement specifier> [package-index-options] ...
  pip3 install [options] -r <requirements file> [package-index-options] ...
  pip3 install [options] [-e] <vcs project url> ...
  pip3 install [options] [-e] <local project path> ...
  pip3 install [options] <archive url/path> ...

Description:
  Install packages from:

  - PyPI (and other indexes) using requirement specifiers.
  - VCS project urls.
  - Local project directories.
  - Local or remote source archives.

  pip also supports installing from "requirements files", which provide
  an easy way to specify a whole environment to be installed.
```
:::


### Installa un Pacchetto

Per installare un pacchetto, esegui il comando:

::: code-group

```bash [Comando]
pip install nome_pacchetto
```

```text [Output]
Collecting nome_pacchetto
  Downloading nome_pacchetto-1.0.0.tar.gz (1.0 kB)
  ...
```
:::

Se vuoi installare una versione specifica di un pacchetto, puoi farlo specificando la versione:

::: code-group

```bash [Comando]
pip install nome_pacchetto==versione
```

```text [Output]
Collecting nome_pacchetto==versione
  Downloading nome_pacchetto-1.0.0.tar.gz (1.0 kB)
  ...
```
:::

::: tip
Se non specifichi alcun altro parametro Python installerà il pacchetto per tutti gli utenti del sistema. Se vuoi installare il pacchetto solo per l'utente corrente, aggiungi il parametro `--user`.

```bash
pip install --user nome_pacchetto 
```
:::

### Disinstalla un Pacchetto

Per disinstallare un pacchetto, esegui il comando:

::: code-group

```bash [Comando]
pip uninstall nome_pacchetto
```

```text [Output]
Found existing installation: nome_pacchetto 1.0.0
Uninstalling nome_pacchetto-1.0.0:
  Would remove:
    ...
Proceed (y/n)?
```
:::

### Mostra i Pacchetti Installati

Per visualizzare tutti i pacchetti installati, esegui il comando:

::: code-group

```bash [Comando]
pip list
```

```text [Output]
Package            Version
------------------ -------
certifi            2021.5.30
chardet            4.0.0
...
```
:::

### Mostra Informazioni su un Pacchetto

Per visualizzare informazioni su un pacchetto specifico, esegui il comando:

::: code-group

```bash [Comando]
pip show nome_pacchetto
```

```text [Output]
Name: nome_pacchetto
Version: 1.0.0
Summary: A short description of the package
Home-page:
Author:
Author-email:
License:
Location: /usr/local/lib/python3.9/site-packages
Requires:
Required-by:
```
:::

### Aggiorna un Pacchetto

Per aggiornare un pacchetto, esegui il comando:

::: code-group

```bash [Comando]
pip install --upgrade nome_pacchetto
```

```text [Output]
Collecting nome_pacchetto
  Downloading nome_pacchetto-1.0.1.tar.gz (1.0 kB)
  ...
```
:::

### Cerca un Pacchetto

Per cercare un pacchetto su PyPI, esegui il comando:

::: code-group

```bash [Comando]
pip search nome_pacchetto
```

```text [Output]
nome_pacchetto (1.0.0)  - A short description of the package
```
:::

::: tip
Puoi sempre cercare un pacchetto da [PyPI](https://pypi.org/search) direttamente dal tuo browser.