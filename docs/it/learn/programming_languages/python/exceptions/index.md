# Eccezioni

Le eccezioni sono errori che si verificano durante l'esecuzione di un programma. 

::: tip Definizione
In Python, un'**eccezione** è un evento che interrompe il normale flusso di un programma. 
:::

In effetti, quando Python rileva che qualcosa non va nel codice, fa due cose:

- Interrompe il programma
- Crea un tipo speciale di dati, chiamato eccezione.

D'ora in poi ci riferiremo a questo evento con il termine **solleva un'eccezione**, o in inglese **raising an exception**.

::: tip
L'eccezione contiene informazioni sul tipo di errore che si è verificato e su dove si è verificato.
:::

Ecco un semplice esempio di eccezione sollevata a seguito di conversione di una stringa in un intero:

::: code-group

```python [input]
numero = int("ciao")
```

```python [output]
ValueError: invalid literal for int() with base 10: 'ciao'
```
:::

In questo caso viene sollevata un'eccezione di tipo `ValueError` perché la stringa "ciao" non può essere convertita in un intero.

## Gestione delle Eccezioni in Python

La gestione delle eccezioni è una parte fondamentale della programmazione. 

Permette di gestire situazioni impreviste, come errori di runtime, in modo elegante, prevenendo crash dell'applicazione e mantenendo un'esperienza utente fluida. 

Quando viene sollevata un'eccezione, di norma Python termina forzatamente l'esecuzione del programma e scriverà il messaggio di errore.

Se invece l'eccezione viene **gestita**, il programma continuerà a eseguire il codice successivo.

A tal proposito esploreremo il blocco `try-except`, come utilizzarlo correttamente e come integrarlo con `finally` per gestire le risorse in modo sicuro.

## Try-Except

L'approccio di cui parleremo si chiama `EAFP` che sta per **Easier to Ask for Forgiveness than Permission**.

Significa che **è meglio provare ad eseguire un'azione e gestire l'errore se qualcosa va storto, piuttosto che controllare preventivamente se l'azione può essere eseguita**.

::: code-group
    
```python [Senza Try-Except]
import os

file_name = "test.txt"

# Controlli preventivi
if os.path.exists(file_name):
    with open(file_name, 'r') as file:
        content = file.read()
        print("Contenuto del file:", content)
else:
    print("Il file non esiste.")
```

```python [Con Try-Except]
file_name = "test.txt"

try:
    with open(file_name, 'r') as file:
        content = file.read()
        print("Contenuto del file:", content)
except FileNotFoundError:
    print("Errore: il file non esiste.")
```
:::

Spieghiamo nel dettaglio come funziona il blocco `try-except`:

```python
try:
    # Codice che potrebbe sollevare un'eccezione
except:
    # Codice che gestisce l'eccezione
```

Il blocco `try` contiene il codice che potrebbe sollevare un'eccezione. Se l'eccezione viene sollevata, il blocco `except` viene eseguito.

Questo significa che alcune operazioni nel blocco `try` potrebbero non essere completate, ma il programma non si interromperà.

::: tip
Ovviamente, nel caso in cui non si verifichino eccezioni nel blocco `try`, il codice nel blocco `except` non verrà eseguito e Python riprenderà dalla riga successiva al blocco `try-except`.
:::

## Eccezioni Multiple

Cosa fare se il codice contenuto nel blocco `try` può sollevare più di un tipo di eccezione?

In questo caso, si preferisce utilizzare un singolo blocco `try-except` per gestire tutte le eccezioni.

```python
try:
    # Codice che potrebbe sollevare un'eccezione
except TipoDiEccezione1:
    # Codice che gestisce l'eccezione 1
except TipoDiEccezione2:
    # Codice che gestisce l'eccezione 2
```

Se si desidera gestire più eccezioni allo stesso modo, è possibile utilizzare una tupla di tipi di eccezione:

```python
try:
    # Codice che potrebbe sollevare un'eccezione
except (TipoDiEccezione1, TipoDiEccezione2):
    # Codice che gestisce l'eccezione
```

Facciamo un esempio reale:

::: code-group

```python [input]
try:

    numero = int(input("Inserisci un numero: "))
    divisore = int(input("Inserisci il divisore: "))
    risultato = numero / divisore

except ZeroDivisionError:
    print("Errore: non è possibile dividere per zero.")

except ValueError:
    print("Errore: per favore inserisci solo numeri.")
```

```python [output 1]
Inserisci un numero: 10
Inserisci il divisore: 0
Errore: non è possibile dividere per zero.
```

```python [output 2]
Inserisci un numero: ciao
Errore: per favore inserisci solo numeri.
```
:::

::: tip exception ZeroDivisionError
Fa parte delle [ArithmeticError](https://docs.python.org/3/library/exceptions.html#ArithmeticError):

- [OverflowError](https://docs.python.org/3/library/exceptions.html#OverflowError)
- [ZeroDivisionError](https://docs.python.org/3/library/exceptions.html#ZeroDivisionError)
- [FloatingPointError](https://docs.python.org/3/library/exceptions.html#FloatingPointError)
:::

::: warning
Ricorda che le eccezioni vengono valuatate nell'ordine in cui vengono dichiarate!

In oltre, se viene sollevata una eccezione, le altre (se presenti) non verranno alutate.

Se infine, viene sollevata un'eccezione non gestita da quelle che hai definito nel blocco `except`, Python interromperà l'esecuzione del programma.
:::

Se non sai esattamente quale tipo di eccezione potrebbe essere sollevata, o se in generale, vuoi essere sicuro che nessuna eccezione sfugga al blocco `try-except`, puoi inserire alla fine della catena una eccezione generica `Exception`.

```python
try:
    # Codice che potrebbe sollevare un'eccezione
except ZeroDivisionError:
    # Codice che gestisce l'eccezione
except ValueError:
    # Codice che gestisce l'eccezione
except BaseException:
    # Codice che gestisce tutte le altre eccezioni
```