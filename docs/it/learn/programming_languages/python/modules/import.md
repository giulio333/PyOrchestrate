
# Importazione di un modulo

## Primo Metodo

Il primo modo per utilizzare un modulo è il seguente:

``` python
import math

print(math.pi)
```

In questo caso, non importa se i nomi nel tuo codice e quelli presenti nel namespace del modulo sono in conflitto. 

Per accedere agli elementi del namespace del modulo, devi comunque utilizzare il prefisso del modulo, in questo caso `math`.

## Secondo Metodo

Il secondo modo per utilizzare un modulo è:

``` python
from math import pi

print(pi)
```

In questo caso, viene importata solo l'**entità** `pi` e nient'altro dal modulo. 

Tuttavia, bisogna fare attenzione, poiché il nome `pi` non deve entrare in conflitto con altri nomi già presenti nel nostro namespace.

::: warning
L'utilizzo di questo metodo è sconsigliato.
:::

## Terzo Metodo

Il terzo metodo è il più aggressivo in quanto importa **tutte le entità** del modulo in un'unica operazione.

``` python
from math import *

print(pi)
```

Attenzione! Se si utilizza questo metodo risulta complicato evitare conflitti nel namespace.

::: warning
L'utilizzo di questo metodo è sconsigliato.
:::

## Alias

L'aliasing fa si che il modulo venga identificato con un nome diverso da quello originale.

``` python
import math as mt

print(mt.pi)
```

oppure

``` python
from math import pi as num_pi

print(num_pi)
```

## sys.path

Di default, Python cerca nella **directory corrente** e in altre **directory predefinite**. E' possibile però aggiungere nuove directory in cui cercare i moduli.

Qui entra in gioco la lista `sys.path`, che specifica le directory in cui Python deve cercare i moduli.

Se Python non trova il modulo della directory corrente, cerca nelle directory elencate in `sys.path`.

Puoi visualizzare la lista dei percorsi eseguendo questo codice

``` python
import sys

for p in sys.path:
    print(p)
```

L'output sarà una lista di directory in cui Python cerca i moduli

``` text
C:\Users\user
C:\Users\user\AppData\Local\Programs\Python\Python36-32\python36.zip
C:\Users\user\AppData\Local\Programs\Python\Python36-32\DLLs
C:\Users\user\AppData\Local\Programs\Python\Python36-32\lib
C:\Users\user\AppData\Local\Programs\Python\Python36-32
C:\Users\user\AppData\Local\Programs\Python\Python36-32\lib\site-packages
```

::: tip
Python cerca i moduli in tutti i percorsi specificati nel `sys.path` **in ordine**!. 
:::

Per aggiungere un percorso alla lista `sys.path` puoi utilizzare due metodi:

### sys.path.insert()

Per dare priorità al nuovo percorso, puoi aggiungerlo all'inizio della lista `sys.path`:

``` python
from sys import path

# Inserisci il nuovo percorso all'inizio della lista
sys.path.insert(0, '/path/to/module')

# Ora puoi importare il modulo
import module
```

### sys.path.append()

Per aggiungere il nuovo percorso alla fine della lista `sys.path`:

```python
from sys import path

# Aggiungi il nuovo percorso alla fine della lista
sys.path.append('/path/to/module')

# Ora puoi importare il modulo
import module
```

## Best Practice

Abbiamo detto che è legittimo importare più moduli con

``` python
import mod1, mod2, mod2
```

Per motivi stilistici però si preferisce la forma

``` python
import mod1
import mod2
import mod3
```