# Esempi

Creiamo la nostra prima classe in Python.

```python
class MyClass:
    pass
```

Abbiamo appena definito una classe vuota chiamata `MyClass`. Questa classe non ha attributi o metodi, ma possiamo comunque creare un'istanza di essa.

- La keyword `class` è utilizzata per definire una classe in Python.
- La keyword `pass` è utilizzata per definire un blocco vuoto. In Python, un blocco vuoto è considerato un errore di sintassi. Tuttavia, possiamo utilizzare `pass` per evitare l'errore.

```python
obj = MyClass()
```

In questo esempio, `obj` è un'istanza della classe `MyClass`. Abbiamo quindi appena creato uno e un solo oggetto di tipo `MyClass`.

Si usa comunemente il termine **istanziare** per riferirsi alla creazione di un oggetto da una classe. In altre parole, `obj` è un'istanza della classe `MyClass`.

Proviamo ora a definire una classe più complessa che risolve un problema reale.

## Queue

Una coda è una struttura dati che segue il principio **FIFO** (First In First Out). Questo significa che l'elemento che è stato inserito per primo è quello che viene rimosso per primo.

Iniziamo definendo la classe.

```python
class Queue:
    def __init__(self):
        self.__items = []
```

Abbiamo definito una classe `Queue` con un metodo `__init__`. Questo metodo è chiamato **costruttore** e viene eseguito automaticamente quando viene creata un'istanza della classe. Il costruttore inizializza una struttura dati `__items` come una lista vuota. 

::: tip Incapsulamento
In Python, i membri di una classe possono essere resi privati anteponendo due trattini bassi `__` al loro nome. Questo significa che i membri privati non possono essere accessibili direttamente dall'esterno della classe.
:::

Il costruttore è un metodo speciale in Python che viene chiamato automaticamente quando viene creata un oggetto. Il costruttore è identificato dal nome `__init__`. Come potete notare il costruttore accetta un parametro `self`. Questo parametro è un riferimento all'oggetto stesso che viene creato. Quindi tutto ciò che viene definito all'interno del costruttore è associato all'oggetto stesso. E' unico per ogni oggetto!

Viene chiamato **costruttore** anche perchè ha il compito di costruire l'oggetto e effettuare tutte le inizializzazioni necessarie.

Cosa succede se proviamo ad accedere direttamente all'attributo `__items`?

```python
q = Queue()

print(q.__items) # Output: AttributeError: 'Queue' object has no attribute '__items'
```

Questo perchè `__items` è un attributo privato e non può essere accessibile direttamente dall'esterno della classe. Questo è esattamente ciò che volevamo ottenere.

Ora definiamo i metodi necessari per la classe `Queue`. Le operazioni tipiche di una semplice coda sono:

- `get` per ottenere l'elemento in testa alla coda
- `put` per inserire un elemento in coda

Questi metodi dovranno ovviamente essere accessibili dall'esterno della classe. Ovvero sono metodi pubblici.

```python
class Queue:
    def __init__(self):
        self.__items = []

    def put(self, item):
        self.__items.append(item)

    def get(self):
        if len(self.__items) == 0:
            return None
        return self.__items.pop(0)
```

Abbiamo definito due metodi `put` e `get`. Il metodo `put` aggiunge un elemento alla coda, mentre il metodo `get` rimuove e restituisce l'elemento in testa alla coda.

Notare che i metodi hanno tutti un parametro `self`. Perchè? Esso è necessario per accedere agli attributi e ai metodi dell'oggetto stesso. Infatti sia il metodo `put` che il metodo `get` accedono all'attributo `__items` dell'oggetto. Questo è possibile grazie al parametro `self`.

In generale il parametro `self` è necessario per accedere a qualsiasi **entità** dell'oggetto (attributi e metodi).

Proviamo ad utilizzare la classe `Queue`.

```python

q = Queue()

q.put(1)
q.put(2)
q.put(3)

print(q.get()) # Output: 1
print(q.get()) # Output: 2
print(q.get()) # Output: 3
print(q.get()) # Output: None
```

Abbiamo creato un'istanza della classe `Queue` e inserito tre elementi. Abbiamo poi estratto gli elementi dalla coda utilizzando il metodo `get`. Tutto funziona correttamente.

Ora immaginiamo di voler modificare il comportamento del metodo `get` in modo che restituisca un messaggio di errore se la coda è vuota. Non vogliamo però modificare la classe `Queue` originale. Invece di modificare la classe originale, possiamo creare una nuova classe che eredita dalla classe `Queue` e sovrascrivere il metodo `get`.

::: tip Overridden
Quando una classe eredita da un'altra classe, e sovrascrive (Override) un metodo della sua superclasse, si dice che la classe figlia mantiene la stessa **interfaccia** mentre cambia l'**implementazione**.
:::

```python
class ImprovedQueue(Queue):
    def get(self):
        item = super().get()
        if item is None:
            print("Queue is empty")
        return item
```

Ora proviamo ad utilizzare la classe `ImprovedQueue`.

```python
iq = ImprovedQueue()

iq.put(1)
iq.put(2)
iq.put(3)

print(iq.get()) # Output: 1
print(iq.get()) # Output: 2
print(iq.get()) # Output: 3
print(iq.get()) # Output: Queue is empty
```

Come potete vedere, il metodo `put` funziona esattamente come nella classe `Queue`, mentre il metodo `get` è stato sovrascritto per restituire un messaggio di errore se la coda è vuota.

Ora immaginiamo di voler specializzare ulteriormente la classe `ImprovedQueue` in modo che abbia un contatore delle operazioni effettuate. Possiamo aggiungere un attributo `__operations` e un metodo `operations` per ottenere il numero di operazioni effettuate.

```python
class ImprovedQueue(Queue):
    def get(self):
        item = super().get()
        if item is None:
            print("Queue is empty")
        return item

class AdvancedQueue(ImprovedQueue):
    def __init__(self):
        self.__operations = 0

    def put(self, item):
        super().put(item)
        self.__operations += 1

    def get(self):
        item = super().get()
        if item is not None:
            self.__operations += 1
        return item

    def operations(self):
        return self.__operations
```

Ci sono alcune cose che vale la pena notare:

- Il costruttore della classe `AdvancedQueue` crea un attributo `__operations` per tenere traccia del numero di operazioni effettuate.
- Il metodo `put` della classe `AdvancedQueue` chiama il metodo `put` della classe `ImprovedQueue` tramite `super().put(item)`. In questo modo possiamo riutilizzare il codice della classe `ImprovedQueue`. Dopo aver aggiunto un elemento alla coda, incrementiamo il contatore delle operazioni.
- Il metodo `get` della classe `AdvancedQueue` chiama il metodo `get` della classe `ImprovedQueue` tramite `super().get()`. Dopo aver estratto un elemento dalla coda, incrementiamo il contatore delle operazioni.
- Il metodo `operations` restituisce il numero di operazioni effettuate, che essendo un attributo privato, non sarebbe accessibile dall'esterno della classe.