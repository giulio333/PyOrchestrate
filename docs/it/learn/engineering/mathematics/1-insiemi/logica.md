# Logica Predicativa

Nel contesto insiemistico, la logica predicativa è una forma di logica che permette di esprimere proposizioni che coinvolgono variabili e quantificatori. 

In particolare, la logica predicativa permette di esprimere proposizioni che coinvolgono insiemi e relazioni tra insiemi.

## Proposizione o Enunciato

Una proposizione è un'affermazione che può essere classificata come vera o falsa, ma non entrambe. E' la forma più semplice di un'affermazione logica.

::: tip Esempio

"2 è un numero pari" è una proposizione vera.
:::

## Predicato o Proprietà

Un **predicato** è un'affermazione che contiene una o più variabili e diventa una **proposizione** quando le variabili vengono sostituite con valori.

::: tip Esempio
Il predicato $P(x)$ potrebbe essere "x è un numero pari".

Se sostituiamo $x$ con un valore, ad esempio $2$, otteniamo la proposizione "2 è un numero pari", che per $x = 2$ è vera.
:::



## Quantificatore

Un **quantificatore** è un simbolo che permette di esprimere la quantità di elementi che soddisfano un predicato.

### Quantificatore Universale

Il **quantificatore universale** $\forall$ si legge "per ogni" e permette di affermare che un predicato è vero per tutti gli elementi di un insieme.

::: tip Esempio

Per ogni numero Naturale $x$, $x$ è maggiore di zero.

$$
\forall x \in \mathbb{N} : x > 0
$$
:::

### Quantificatore Esistenziale

Il **quantificatore esistenziale** $\exists$ si legge "esiste" e permette di affermare che esiste almeno un elemento di un insieme che soddisfa un predicato.

::: tip Esempio

Esiste un numero Reale $x$ tale che il quadrato di $x$ è uguale a $4$.

$$
\exists x \in \mathbb{R} : x^2 = 4
$$
:::

## Implicazione Universale

L'**Implicazione universale** è una forma di proposizione che coinvolge un quantificatore universale.

E' espressa come 

$$
\forall x , P(x) \Rightarrow Q(x)
$$

ovvero, per ogni $x$, se $P(x)$ è vero, allora $Q(x)$ è vero.

::: tip Esempio

$$
\forall x \in \mathbb{R}, x > 2 \Rightarrow x^2 > 4
$$

Per ogni numero Reale $x$, se $x$ è maggiore di $2$, allora il quadrato di $x$ è maggiore di $4$.
:::

## Logica Predicativa e Teoremi

La logica predicativa è alla base della dimostrazione di teoremi matematici.

Generalmente un teorema è costituito da una **Implicazione Universale** nel quale il **Predicato** $p$ rappresenta l'**Ipotesi** e il **Predicato** $q$ rappresenta la **Tesi**.
