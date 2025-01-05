# Variabili Di Istanza

Sappiamo già che una classe può avere due tipi di dati che formano le proprietà di un oggetto: **Variabili di Classe** e **Variabili di Istanza**. 

Le variabili di istanza sono quelle che appartengono a un'istanza specifica di una classe. Questo significa che ogni oggetto ha le proprie copie delle variabili di istanza e non interferiscono con le variabili di istanza di altri oggetti.

Facciamo un esempio per capire meglio:

```python
class Persona:
    def __init__(self, nome, cognome):
        self.nome = nome
        self.cognome = cognome

persona1 = Persona("Mario", "Rossi")
persona2 = Persona("Luca", "Bianchi")

print(persona1.nome) # Output: Mario
print(persona2.nome) # Output: Luca
```

In oltre, tutti gli oggetti hanno un insieme di proprietà e metodi predefiniti che possono essere utilizzati per accedere alle informazioni sull'oggetto stesso. Questi metodi e proprietà sono chiamati **metodi e attributi speciali**. Un esempio di attributo speciale è `__dict__` che restituisce un dizionario contenente gli attributi dell'oggetto.

```python
class Persona:
    def __init__(self, nome, cognome):
        self.nome = nome
        self.cognome = cognome

persona1 = Persona("Mario", "Rossi")

print(persona1.__dict__) # Output: {'nome': 'Mario', 'cognome': 'Rossi'}
```

Il metodo `__dict__` restituisce un dizionario che contiene tutte le variabili di istanza dell'oggetto `persona1`, a patto che siano state definite o che non siano state rimosse.

Vediamo un altro esempio, in cui definiamo anche attributi privati:

```python
class Persona:
    def __init__(self, nome, cognome):
        self.nome = nome
        self.__cognome = cognome

persona1 = Persona("Mario", "Rossi")

print(persona1.__dict__) # Output: {'nome': 'Mario', '_Persona__cognome': 'Rossi'}
```

In questo caso, l'attributo `__cognome` è un attributo privato, quindi Python lo rinomina in `_Persona__cognome`.

Questo significa che puoi ancora accedere all'attributo privato, ma devi farlo utilizzando il nome che Python ha generato per esso.

```python
print(persona1._Persona__cognome) # Output: Rossi
```

::: tip "Mangling"
Il processo di aggiungere il nome della classe come prefisso a un attributo privato è chiamato **mangling**.
:::