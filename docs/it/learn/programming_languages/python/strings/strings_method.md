# Metodi di Stringhe

Le stringhe in Python sono oggetti **immutabili**, il che significa che non possono essere modificate dopo la creazione. 

Tuttavia, Python fornisce molti metodi per manipolare le stringhe. Questi metodi restituiscono una **nuova stringa** e non modificano la stringa originale.

## Index

Il metodo `index()` cerca nella sequenza un valore specifico e restituisce la posizione della prima occorrenza di tale valore.

```python
stringa = 'Hello, world!'
print(stringa.index('w')) # Output: 7
```

La sua assenza genererà un errore `ValueError`.

```python
stringa = 'Hello, world!'
print(stringa.index('z')) # ValueError: substring not found
```

## capitalize()

Il metodo `capitalize()` restituisce una nuova stringa con il primo carattere maiuscolo e tutti gli altri caratteri minuscoli.

::: code-group
```python [Comando]
string = "hello, world!"
new_string = string.capitalize()
print(new_string)
```

```text [Output]
Hello, world!
```
:::

Se il primo carattere (string[0]) è una lettera, esso verrà convertito in maiuscolo, tutte le altre lettere verranno convertite in minuscolo.

Ovviamente la stringa originale **non viene modificata** in alcun modo, quindi devi recuperare il valore restituito dal metodo `capitalize()`.

::: tip 

E' possibile utilizzare i metodi di stringa direttamente su uno **string literal**, senza doverlo assegnare ad una variabile.

::: code-group
```python [Comando]
print("hello, world!".capitalize())
```

```text [Output]
Hello, world!
```
:::

Uno **string literal** è una sequenza di caratteri racchiusi tra apici singoli (`'`) o doppi (`"`).
:::

## center()

Il metodo `center()` restituisce una nuova stringa centrata in una stringa di lunghezza `width`.

::: code-group
```python [Comando]
string = "hello, world!"
new_string = string.center(20)
print(new_string)
```

```text [Output]
   hello, world!    
```
:::

Il metodo `center()` accetta un argomento opzionale `fillchar` che specifica il carattere di riempimento. Il valore predefinito è uno spazio.

::: code-group
```python [Comando]
string = "hello, world!"
new_string = string.center(20, "*")
print(new_string)
```

```text [Output]
***hello, world!****
```
:::

## endswith()

Il metodo `endswith()` restituisce `True` se la stringa termina con il suffisso specificato, altrimenti restituisce `False`.

::: code-group
```python [Comando]
string = "hello, world!"
result = string.endswith("world!")
print(result)
```

```text [Output]
True
```
:::

## startswith()

Il metodo `startswith()` restituisce `True` se la stringa inizia con il prefisso specificato, altrimenti restituisce `False`.

::: code-group
```python [Comando]
string = "hello, world!"
result = string.startswith("hello")
print(result)
```

```text [Output]
True
```
:::

## find()

Il metodo `find()` restituisce l'indice della prima occorrenza della sottostringa specificata. Se la sottostringa non è presente, restituisce `-1`.

::: tip
E' **case-sensitive**.
:::

::: code-group
```python [Comando]
string = "hello, world!"
index = string.find("world")
print(index)
```

```text [Output]
7
```
:::

E' simile al metodo `index()`, ma `index()` genera un'eccezione se la sottostringa non è presente.

::: note
- Funziona solo con le stringhe, non con le liste.
- Non usare `find()` per cercare un carattere singolo, usa `in` o `index()` al suo posto.
:::

E' possibile eseguire la ricerca a partire da un indice specificato.

::: code-group
```python [Comando]
string = "hello, world!"
index = string.find("world", 8)
print(index)
```

```text [Output]
-1
```
:::


## isalnum()

Il metodo `isalnum()` restituisce `True` se tutti i caratteri della stringa sono alfanumerici, altrimenti restituisce `False`.

::: tip
Lo spazio è considerato un carattere non alfanumerico, quindi `isalnum()` restituirà `False` se la stringa ne contiene uno.
:::

::: code-group
```python [Comando]
string = "hello123"
result = string.isalnum()
print(result)
```

```text [Output]
True
```
:::

::: code-group
```python [Comando]
string = "hello, world!"
result = string.isalnum()
print(result)
```

```text [Output]
False
```
:::

## isalpha()

Il metodo `isalpha()` restituisce `True` se tutti i caratteri della stringa sono alfabetici, altrimenti restituisce `False`.

::: code-group
```python [Comando]
string = "hello"
result = string.isalpha()
print(result)
```

```text [Output]
True
```
:::

::: code-group
```python [Comando]
string = "hello123"
result = string.isalpha()
print(result)
```

```text [Output]
False
```
:::

Si tratta di una variante di `isalnum()` più specializzata.

## isdigit()

Il metodo `isdigit()` restituisce `True` se tutti i caratteri della stringa sono numerici, altrimenti restituisce `False`.

::: code-group
```python [Comando]
string = "123"
result = string.isdigit()
print(result)
```

```text [Output]
True
```
:::

::: code-group
```python [Comando]
string = "hello123"
result = string.isdigit()
print(result)
```

```text [Output]
False
```
:::

## islower()

Il metodo `islower()` restituisce `True` se tutti i caratteri della stringa sono minuscoli, altrimenti restituisce `False`.

::: code-group
```python [Comando]
string = "hello"
result = string.islower()
print(result)
```

```text [Output]
True
```
:::

::: code-group
```python [Comando]
string = "Hello"
result = string.islower()
print(result)
```

```text [Output]
False
```
:::

## isupper()

Il metodo `isupper()` restituisce `True` se tutti i caratteri della stringa sono maiuscoli, altrimenti restituisce `False`.

::: code-group
```python [Comando]
string = "HELLO"
result = string.isupper()
print(result)
```

```text [Output]
True
```
:::

::: code-group
```python [Comando]
string = "Hello"
result = string.isupper()
print(result)
```

```text [Output]
False
```
:::

## isspace()

Il metodo `isspace()` restituisce `True` se tutti i caratteri della stringa sono spazi, altrimenti restituisce `False`.

::: code-group
```python [Comando]
string = "   "
result = string.isspace()
print(result)
```

```text [Output]
True
```
:::

## join()

Il metodo `join()` restituisce una nuova stringa ottenuta concatenando gli elementi di un'iterabile, separati dalla stringa su cui è stato chiamato.

E' necessario assicurarsi che tutti gli elementi dell'iterabile siano stringhe, altrimenti il metodo solleverà un'eccezione `TypeError`.

::: code-group
```python [Comando]
iterable = ["hello", "world"]
string = " ".join(iterable)
print(string)
```

```text [Output]
hello world
```
:::

In questo esempio si nota che la stringa su cui è stato chiamato il metodo `join()` viene utilizzata come separatore tra gli elementi dell'iterabile.

## lower()

Il metodo `lower()` restituisce una nuova stringa con tutti i caratteri convertiti in minuscolo.

::: code-group
```python [Comando]
string = "Hello, World!"
new_string = string.lower()
print(new_string)
```

```text [Output]
hello, world!
```
:::

## upper()

Il metodo `upper()` restituisce una nuova stringa con tutti i caratteri convertiti in maiuscolo.

::: code-group
```python [Comando]
string = "Hello, World!"
new_string = string.upper()
print(new_string)
```

```text [Output]
HELLO, WORLD!
```
:::

## lstrip()

Il metodo `lstrip()` restituisce una nuova stringa con tutti i caratteri di spaziatura rimossi dall'inizio della stringa.

::: code-group
```python [Comando]
string = "   hello, world!"
new_string = string.lstrip()
print(new_string)
```

```text [Output]
hello, world!
```
:::

Se si desidera rimuovere solo uno specifico carattere di spaziatura, è possibile passarlo come argomento al metodo.

::: code-group
```python [Comando]
string = "###hello, world!"
new_string = string.lstrip("#")
print(new_string)
```

```text [Output]
hello, world!
```
:::

## rstrip()

Il metodo `rstrip()` restituisce una nuova stringa con tutti i caratteri di spaziatura rimossi dalla fine della stringa.

::: code-group
```python [Comando]
string = "hello, world!   "
new_string = string.rstrip()
print(new_string)
```

```text [Output]
hello, world!
```
:::

## strip()

Il metodo `strip()` restituisce una nuova stringa con tutti i caratteri di spaziatura rimossi dall'inizio e dalla fine della stringa.

::: code-group
```python [Comando]
string = "   hello, world!   "
new_string = string.strip()
print(new_string)
```

```text [Output]
hello, world!
```
:::

## replace()

Il metodo `replace()` restituisce una nuova stringa in cui tutte le occorrenze di una sottostringa specificata vengono sostituite con un'altra sottostringa.

::: code-group
```python [Comando]
string = "hello, world!"
new_string = string.replace("world", "python")
print(new_string)
```

```text [Output]
hello, python!
```
:::

Il metodo `replace()` accetta un argomento opzionale `count` che specifica il numero di occorrenze da sostituire.

::: code-group
```python [Comando]
string = "hello, world!"
new_string = string.replace("o", "0", 2)
print(new_string)
```

```text [Output]
hell0, w0rld!
```
:::

## rfind()

Il metodo `rfind()` restituisce l'indice dell'ultima occorrenza della sottostringa specificata. Se la sottostringa non è presente, restituisce `-1`.

E' simile al metodo `find()`, ma restituisce l'indice dell'ultima occorrenza invece del primo (r sta per **right**).

::: code-group
```python [Comando]
string = "hello, world!"
index = string.rfind("o")
print(index)
```

```text [Output]
8
```
:::

## split()

Il metodo `split()` restituisce una lista di sottostringhe ottenute dividendo la stringa in base al separatore specificato.

Il separatore predefinito è lo **spazio**, ma è possibile specificarne uno personalizzato.

::: code-group
```python [Comando]
string = "hello, world!"
words = string.split()
print(words)
```

```text [Output]
['hello,', 'world!']
```
:::

::: code-group
```python [Comando]
string = "hello, world!"
words = string.split(",")
print(words)
```

```text [Output]
['hello', ' world!']
```
:::

## swapcase()

Il metodo `swapcase()` restituisce una nuova stringa con le lettere maiuscole convertite in minuscole e viceversa.

::: code-group
```python [Comando]
string = "Hello, World!"
new_string = string.swapcase()
print(new_string)
```

```text [Output]
hELLO, wORLD!
```
:::

## title()

Il metodo `title()` restituisce una nuova stringa con la prima lettera di ogni parola convertita in maiuscolo.

::: code-group
```python [Comando]
string = "hello, world!"
new_string = string.title()
print(new_string)
```

```text [Output]
Hello, World!
```
:::

