# hasattr

Ora che abbiamo parlato di **variabilie di istanza** e **variabili di classe**, vediamo come possiamo verificare se un oggetto ha un attributo specifico o meno.

Prendiamo il seguente esempio:

```python
class Persona:
    def __init__(self, info):
        
        if isinstance(info, int):
            self.eta = info
        else:
            self.nome = info

p = Persona("Mario")

print(p.nome) # Output: Mario
print(p.eta) # AttributeError: 'Persona' object has no attribute 'eta'
```

Nel codice sopra, abbiamo definito una classe `Persona` con un metodo `__init__` che accetta un argomento `info`. Se `info` è un intero, allora lo assegniamo all'attributo `eta`, altrimenti lo assegniamo all'attributo `nome`.

Fortunatamente Python ci fornisce una funzione built-in chiamata `hasattr()` che possiamo utilizzare per verificare se un oggetto ha un attributo specifico o meno.

```python
class Persona:
    def __init__(self, info):
        
        if isinstance(info, int):
            self.eta = info
        else:
            self.nome = info

p = Persona("Mario")

if hasattr(p, 'nome'):
    print(p.nome) # Output: Mario

if hasattr(p, 'eta'):
    print(p.eta) # Non verrà stampato
```

::: tip 
Il metodo `hasattr()` accetta due argomenti: l'oggetto e il nome dell'attributo da verificare. Restituisce `True` se l'attributo è presente nell'oggetto, altrimenti restituisce `False`.

E' possibile utilizzare `hasattr()` per verificare sia gli attributi di istanza che quelli di classe.
:::
