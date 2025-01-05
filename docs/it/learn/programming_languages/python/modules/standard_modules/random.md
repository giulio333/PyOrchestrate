# Modulo Random

<ImageComponent 
  src="/CodeInMind/random.png" 
  alt="Description of the image" 
  :width="200" 
/>

Il modulo `random` di Python offre strumenti per generare numeri **pseudocasuali**, fornendo la possibilità di simulare eventi casuali come il lancio di dadi, l'estrazione di una carta o la selezione casuale di un elemento da una lista.

## Cos'è la pseudocasualità?

I numeri generati dal modulo `random` non sono veramente casuali; sono infatti **pseudocasuali**. Ciò significa che, anche se i valori generati sembrano casuali, essi sono il risultato di **algoritmi deterministici** che seguono delle regole specifiche. Questo tipo di numeri è sufficiente per la maggior parte delle applicazioni, ma non può essere considerato veramente casuale.

### Determinismo e seed

Un **generatore di numeri pseudocasuali** parte da un valore chiamato **seed** (seme). 

Il seed funge da punto di partenza per il generatore, e in base a questo valore l'algoritmo produce una sequenza di numeri che sembra casuale. Il ciclo di questi numeri ha una lunghezza definita, il che significa che prima o poi i numeri inizieranno a ripetersi.

Quando si avvia un programma Python, il modulo `random` inizializza automaticamente il seed utilizzando l'orario corrente, il che garantisce che ogni esecuzione del programma produca una sequenza di numeri diversa.

## Funzionalità principali del modulo `random`

Ecco alcune delle funzioni più utili del modulo `random`:

### 1. `random.random()`

Restituisce un numero pseudocasuale in virgola mobile compreso tra 0.0 e 1.0.

``` python
import random

print(random.random())  # Es. output: 0.7321...
```

### 2. `random.randint(a, b)`

Restituisce un intero pseudocasuale compreso tra 'a' e 'b' inclusi.

```python
import random

print(random.randint(1, 10))  # Es. output: 7
```

### 3. `random.choice(seq)`

Seleziona e restituisce un elemento casuale da una sequenza (come una lista o una tupla).

```python
import random

fruits = ['mela', 'banana', 'ciliegia']
print(random.choice(fruits))  # Es. output: `banana`
```

### 4. `random.shuffle(seq)`

Mescola in modo casuale una lista in loco, modificando direttamente l`ordine degli elementi.

```python
import random

cards = [1, 2, 3, 4, 5]
random.shuffle(cards)
print(cards)  # Es. output: [3, 5, 1, 4, 2]
```

### 5. `random.sample(population, k)`

Restituisce una lista di `k` elementi unici selezionati casualmente dalla popolazione.

```python
import random

numbers = range(10)
print(random.sample(numbers, 3))  # Es. output: [2, 5, 8]
```

## Utilizzo del seed

Se vuoi controllare la sequenza di numeri generati, puoi impostare manualmente il **seed** usando `random.seed()`:

```python
import random

random.seed(42)  # Imposta il seed a 42
print(random.random())  # L'output sarà sempre lo stesso: 0.6394267984578837
```