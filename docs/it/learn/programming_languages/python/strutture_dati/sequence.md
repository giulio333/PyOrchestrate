# Sequenze in Python

Le sequenze sono strutture dati che contengono una sequenza ordinata di elementi.

I tratti distintivi di una sequenza in Python sono:

- Una sequenza è un **iterabile**, il che significa che è possibile iterarla.
- Una sequenza è **indicizzata**, il che significa che è possibile accedere a ciascun elemento utilizzando un indice, inclusa la notazione **sqare bracket** `[]`.
- Una sequenza è **ordinata**, il che significa che gli elementi sono disposti in un ordine specifico.

## Metodi Speciali per le Sequenze

I metodi speciali per le sequenze in Python sono progettati per consentire l'accesso e la manipolazione degli elementi all'interno di una sequenza.

I metodi speciali per le sequenze includono:

- `__iter__()`: restituisce un iteratore per la sequenza. È possibile accedere a questo metodo utilizzando la funzione `iter()`.
- `__len__()`: restituisce la lunghezza della sequenza. La funzione `len()` chiama questo metodo.
- `__getitem__()`: restituisce l'elemento all'indice specificato. È possibile accedere a questo metodo utilizzando la notazione **square bracket** `[]`.

::: tip
Tutte le **sequenze** in Python implementano `__len__()` e `__getitem__()`. Molti tipi di sequenze implementano anche `__iter__()`.

Tuttavia, avere questi metodi non è sufficiente per garantire che un oggetto sia una sequenza.
:::

## Slicing delle Sequenze

Lo **slicing** è un'operazione che consente di estrarre una sotto-sequenza da una sequenza più grande.

La notazione per lo slicing è `[start:stop:step]`, dove:

- `start`: l'indice iniziale della sotto-sequenza.
- `stop`: l'indice finale della sotto-sequenza.
- `step`: il passo tra gli elementi della sotto-sequenza.

::: tip Esempio di Slicing
``` python
lista = [1, 2, 3, 4, 5]

print(lista[1:4]) # Output: [2, 3, 4]
print(lista[::2]) # Output: [1, 3, 5]
```
:::

## Concatenazione delle Sequenze

La **concatenazione** delle sequenze è un'operazione che consente di unire due o più sequenze in una singola sequenza.

In Python, è possibile concatenare sequenze utilizzando l'operatore `+`.

::: tip Esempio di Concatenazione
``` python
lista1 = [1, 2, 3]
lista2 = [4, 5, 6]

lista3 = lista1 + lista2
print(lista3) # Output: [1, 2, 3, 4, 5, 6]
```
:::

## Comparazione delle Sequenze

La **comparazione** delle sequenze è un'operazione che consente di confrontare due sequenze per determinare se sono uguali o meno.

In Python, è possibile confrontare sequenze utilizzando gli operatori di confronto, come `==`, `!=`, `<`, `>`, `<=`, `>=`.

::: tip Esempio di Comparazione
``` python
lista1 = [1, 2, 3]
lista2 = [1, 2, 3]
lista3 = [4, 5, 6]

print(lista1 == lista2) # Output: True
print(lista1 == lista3) # Output: False
```
:::

Vale la pena fare un esempio con l'operatore `>` tra sequenze:

Quando Python confronta due sequenze:

- Confronta elemento per elemento.
- Se trova un elemento maggiore in una sequenza, considera quella sequenza come maggiore.

::: tip Esempio di Comparazione con `>`
``` python
lista1 = [1, 2, 3]
lista2 = [1, 2, 4]

print(lista1 > lista2) # Output: False
print(lista2 > lista1) # Output: True
```
:::

Se la lunghezza delle liste è diversa, Python considera come **minore** quella con meno elementi

::: tip Esempio di Comparazione con Lunghezze Diverse
``` python
lista1 = [1, 2, 3]
lista2 = [1, 2, 3, 4]

print(lista1 > lista2) # Output: False
print(lista2 > lista1) # Output: True
```
:::