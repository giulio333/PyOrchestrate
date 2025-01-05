# Variabili Di Classe

Le variabili di classe sono quelle che appartengono alla classe stessa. Questo significa che le variabili di classe sono condivise da tutte le istanze di una classe e non sono specifiche di un'istanza particolare.

::: tip 
Una **variabile di istanza** esiste solo se è stata creata un'istanza della classe, mentre una **variabile di classe** esiste a prescindere dal fatto che sia stata creata un'istanza della classe. Essa infatti è memorizzata all'esterno di qualsiasi oggetto.
:::

A differenza delle **variabili di istanza**, le **variabili di classe** sono uniche, cioè esiste solo una copia della variabile di classe che è condivisa da tutte le istanze della classe.

Vediamo un esempio per capire meglio:

```python
class Persona:

    contatore = 0

    def __init__(self, nome, cognome):
        self.nome = nome
        self.cognome = cognome
        Persona.contatore += 1

persona1 = Persona("Mario", "Rossi")
persona2 = Persona("Luca", "Bianchi")

print(persona1.__dict__, persona1.contatore) # Output: {'nome': 'Mario', 'cognome': 'Rossi'} 2
print(persona2.__dict__, persona2.contatore) # Output: {'nome': 'Luca', 'cognome': 'Bianchi'} 2
```

Per definire una variabile di classe, basta definirla all'interno della classe, ma all'esterno di qualsiasi metodo. In questo caso, abbiamo definito la variabile `contatore` all'interno della classe `Persona`.

Quando creiamo un'istanza della classe `Persona`, incrementiamo il valore della variabile `contatore` di 1. In questo modo, la variabile `contatore` tiene traccia del numero di istanze create della classe `Persona`.

Notare il modo in cui accediamo alla variabile di classe `contatore` utilizzando il nome della classe `Persona` invece di `self`.

::: tip
Come mostra l'esempio precedente, le variabili di classe non vengono mostrate nell'attributo `__dict__` dell'oggetto.
:::

Come abbiamo fatto per le variabili di istanza, possiamo utilizzare il metodo `__dict__` per accedere alle variabili di classe di una classe.

```python
class Persona:

    contatore = 0

    def __init__(self, nome, cognome):
        self.nome = nome
        self.cognome = cognome
        Persona.contatore += 1

p = Persona("Mario", "Rossi")
print(Persona.__dict__)
print(p.__dict__)

# Output: {'__module__': '__main__', 'contatore': 0, '__init__': <function Persona.__init__ at 0x7f8b1b3b7d30>, '__dict__': <attribute '__dict__' of 'Persona' objects>, '__weakref__': <attribute '__weakref__' of 'Persona' objects>, '__doc__': None}

# Output: {'nome': 'Mario', 'cognome': 'Rossi'}
```

Come si vede dall'output, la variabile di classe `contatore` è presente nell'attributo `__dict__` della classe `Persona`.

Al contrario, la variabile di classe `contatore` non è presente nell'attributo `__dict__` dell'oggetto `p`.
