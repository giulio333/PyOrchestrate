# Operazioni tra insiemi

Le operazioni tra insiemi sono operazioni che coinvolgono due o più insiemi e che restituiscono un nuovo insieme.

## Intersezione

L'**intersezione** tra due insiemi $A$ e $B$ è l'insieme degli elementi che appartengono sia ad $A$ che a $B$.

Si indica con $A \cap B$.

$$
A \cap B = \{x \mid x \in A \land x \in B\}
$$

## Unione

L'**unione** tra due insiemi $A$ e $B$ è l'insieme degli elementi che appartengono ad $A$ o a $B$.

Si indica con $A \cup B$.

$$
A \cup B = \{x \mid x \in A \lor x \in B\}
$$

Quindi un elemento $x$ appartiene all'unione di due insiemi $A$ e $B$ se e solo se $x$ appartiene ad $A$ oppure $x$ appartiene a $B$ oppure $x$ appartiene ad entrambi.

## Differenza

La **differenza** tra due insiemi $A$ e $B$ è l'insieme degli elementi che appartengono ad $A$ ma non appartengono a $B$.

Si indica con $A \setminus B$.

$$
A - B = \{x \mid x \in A \land x \notin B\}
$$

Quindi un elemento $x$ appartiene alla differenza tra due insiemi $A$ e $B$ se e solo se $x$ appartiene ad $A$ e non appartiene a $B$.

## Complemento

Il **complemento** di un insieme $A$ rispetto a un insieme $U$ è l'insieme degli elementi di $U$ che non appartengono ad $A$.

Si indica con $A^c$.

## Prodotto Cartesiano

Il **prodotto cartesiano** tra due insiemi $A$ e $B$ è l'insieme di tutte le coppie ordinate $(a, b)$ dove $a$ appartiene ad $A$ e $b$ appartiene a $B$.

Si indica con $A \times B$.

$$
A \times B = \{(a, b) \mid a \in A \land b \in B\}
$$


::: tip Esempio
Un esempio classico di prodotto cartesiano è $\mathbb{R} \times \mathbb{R} = \mathbb{R}^2$, che rappresenta il piano cartesiano.

Esso denota l'insieme di tutte le coppie ordinate di numeri reali

$$
\mathbb{R}^2 = \{(x, y) \mid x, y \in \mathbb{R}\}
$$

O più in generale, $\mathbb{R}^n$ denota l'insieme di tutte le $n$-uple ordinate di numeri reali.

$$
\mathbb{R}^n = \{(x_1, x_2, \ldots, x_n) \mid x_1, x_2, \ldots, x_n \in \mathbb{R}\}
$$
:::

## Operazioni con Insieme Vuoto e Insieme Universo

L'insieme vuoto $\emptyset$ e l'insieme universo $U$ sono due insiemi speciali che partecipano alle operazioni tra insiemi.

$$
A \cap \emptyset = \emptyset
$$

$$
A \cup \emptyset = A
$$

$$
A \cap U = A
$$

$$
A \cup U = U
$$

$$
U^c = \emptyset
$$

$$
\emptyset^c = U
$$