# Metodi

I metodi sono funzioni definite all'interno di una classe. Essi sono chiamati su un'istanza della classe e possono accedere ai dati dell'istanza.

I metodi che vedremo ora sono metodi di **istanza**. Questi metodi vengono definiti con un parametro `self` come primo parametro. Questo parametro è un riferimento all'oggetto stesso che viene creato. Quindi tutto ciò che viene definito all'interno del metodo è associato all'oggetto stesso. E' unico per ogni oggetto!

::: tip
Il nome `self` è una convenzione e può essere sostituito con qualsiasi altro nome. Tuttavia, è una pratica comune utilizzare `self` per rendere il codice più leggibile.
:::

Quando invece il metodo viene invocato, non è necessario passare il parametro `self` esplicitamente. Python lo fa automaticamente per noi.

Facciamo un esempio:

```python
class Persona:
    def __init__(self, nome, cognome):
        self.nome = nome
        self.cognome = cognome

    def saluta(self):
        print(f"Ciao, mi chiamo {self.nome} {self.cognome}!")

p = Persona("Mario", "Rossi")
p.saluta() # Output: Ciao, mi chiamo Mario Rossi!
```

In questo esempio abbiamo definito una classe `Persona` con due attributi `nome` e `cognome` e un metodo `saluta` che stampa un messaggio di saluto. Come abbiamo già detto, il metodo possiede un parametro `self` che fa riferimento all'oggetto stesso. Quindi stampa il nome e il cognome dell'oggetto su cui è chiamato.

Ora proviamo a definire un un metodo che accetta un parametro oltre a `self`:

```python
class Persona:
    def __init__(self, nome, cognome):
        self.nome = nome
        self.cognome = cognome

    def saluta(self, saluto):
        print(f"{saluto}, mi chiamo {self.nome} {self.cognome}!")

p = Persona("Mario", "Rossi")
p.saluta("Buongiorno") # Output: Buongiorno, mi chiamo Mario Rossi!
```

I metodi possono anche invocare altri metodi della stessa classe:

```python
class Persona:
    def __init__(self, nome, cognome):
        self.nome = nome
        self.cognome = cognome

    def saluta(self, saluto):
        print(f"{saluto}.")
        self.stampa_nome()

    def stampa_nome(self):
        print(f"Mi chiamo {self.nome} {self.cognome}!")

p = Persona("Mario", "Rossi")
p.saluta("Buongiorno") # Output: Buongiorno. Mi chiamo Mario Rossi!
```

::: tip "Name Mangling"
Tutto ciò che abbiamo detto sul Name Mangling per gli attributi vale anche per i metodi. Se un metodo inizia con due caratteri di sottolineatura `__`, Python lo rinomina in modo che il nome della classe sia incluso nel nome del metodo.
:::

## Metodi Speciali

Python definisce una serie di metodi speciali che iniziano e finiscono con due caratteri di sottolineatura `__`. Questi metodi vengono chiamati automaticamente in determinate circostanze. Ad esempio, il metodo `__init__` viene chiamato quando un oggetto viene creato.

### `__init__`

Il metodo `__init__` è il costruttore della classe. Viene chiamato automaticamente quando un oggetto viene creato. E' il posto giusto per inizializzare gli attributi dell'oggetto.

```python
class Persona:
    def __init__(self, nome, cognome):
        self.nome = nome
        self.cognome = cognome

p = Persona("Mario", "Rossi")
```

Notate qualcosa di particolare? Questo metodo è il primo metodo visto fin ora che restituisce un valore. In questo caso, restituisce un oggetto di tipo `Persona`.

Tienilo a mente, perchè non potrà mai restituire un valore diverso da un oggetto di tipo `Persona`.

## `__dict__`

Abbiamo già visto l'attributo `__dict__` che contiene tutti gli attributi dell'oggetto. Vediamo come si comporta con i metodi:

```python
class Persona:
    def __init__(self, nome, cognome):
        self.nome = nome
        self.cognome = cognome

    def saluta(self):
        print(f"Ciao, mi chiamo {self.nome} {self.cognome}!")

p = Persona("Mario", "Rossi")
print(p.__dict__) # Output: {'nome': 'Mario', 'cognome': 'Rossi'}
```

Come possiamo vedere, l'attributo `__dict__` contiene solo gli attributi dell'oggetto, non i metodi.

Tuttavia, possiamo accedere ai metodi della classe tramite l'attributo `__dict__` della classe stessa:

```python
print(Persona.__dict__) # Output: {'__module__': '__main__', '__init__': <function Persona.__init__ at 0x7f8b1c7b7d30>, 'saluta': <function Persona.saluta at 0x7f8b1c7b7dc0>, '__dict__': <attribute '__dict__' of 'Persona' objects>, '__weakref__': <attribute '__weakref__' of 'Persona' objects>, '__doc__': None}
```