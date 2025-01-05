# Numeri Reali

Iniziamo introducendo concetti utili per la definizione dell'**assioma di continuità**.

## Insiemi Limitati

Sia $A$ un insieme contenuto in $X$ con $X$ generico.

- Un insieme $A$ è detto **limitato superiormente** se esiste un numero $M$ tale che $x \leq M$ per ogni $x \in A$.

- Un insieme $A$ è detto **limitato inferiormente** se esiste un numero $m$ tale che $m \leq x$ per ogni $x \in A$.

- Un insieme $A$ è detto **limitato** se è limitato sia **superiormente** che **inferiormente**, ossia $m \leq x \leq M$ per ogni $x \in A$.

## Massimo

Un insieme $A$ si dice che ha un **massimo** se esiste un numero $M$ tale che $x \leq M$ per ogni $x \in A$ e $M \in A$.

## Minimo

Un insieme $A$ si dice che ha un **minimo** se esiste un numero $m$ tale che $m \leq x$ per ogni $x \in A$ e $m \in A$.

::: tip

Si noti la differenza tra la definizione di **massimo** e di **insieme superiormente limitato**: 

- un insieme può essere **superiormente limitato** senza avere un **massimo**.

Infatti un insieme $A$ è **superiormente limitato** se esiste un numero $M$ tale che $x \leq M$ per ogni $x \in A$, ma non necessariamente $M \in A$.

E' evidente che affinchè $A$ abbia un **massimo** e un **minimo**, deve anche essere **limitato**.
:::

## Estremo Superiore (sup)

Il concetto di **estremo superiore** o **sup** è sostituibile al concetto di **massimo**. Sia ancora $A \subseteq X$ e $k$ un numero appartenente a $X$ ma non necessariamente ad $A$.

Si dice che $k$ è un **maggiorante** di $A$ se $k \geq x$ per ogni $x \in A$.

Si noti che un insieme **superiormente limitato** possiede molti **maggioranti**.

Definiamo allora **estremo superiore** di $A$ il minimo di tutti i **maggioranti** di $A$, e si indica con $\sup A$.

::: tip
Se un insieme possiede un **massimo**, allora il **massimo** coincide con l'**estremo superiore**.
:::

Definizioni analoghe valgono per l'**estremo inferiore** o **inf**.

### Esempio

Prendiamo l'insieme

$$
x \in \mathbb{Q} \quad \text{tale che} \quad x^2 < 2 \quad \text{e} \quad x \geq 0
$$

L'insieme è chiaramente **superiormente limitato**. Infatti, $2$ è un **maggiorante** di $A$ (così come $3$, $4$, $5$, ...).

L'insieme è anche **inferiormente limitato**. Infatti, $0$ è un **minorante** di $A$. In particolare, essendo $0 \in A$, $0$ è anche il **minimo** di $A$.

Se volessimo cercare l'**estremo superiore** di $A$, dovremmo cercare un numero il cui quadrato è $2$. Ma in $\mathbb{Q}$ non esiste un tale numero.

::: tip
Esiste però in $\mathbb{R}$ ed è $\sqrt{2}$, il quale è un **numero irrazionale**.
:::

Da qui nasce una nuova proprietà detta **proprietà dell'estremo superiore**.

## Proprietà $R_4$

Ogni insieme $A \subseteq X$ non vuoto e **superiormente limitato** ammette **estremo superiore**.

::: tip
La proprietà $R_4$ è un'ulteriore proprietà che caratterizza i numeri reali rispetto ai numeri razionali.

Infatti, l'insieme $A$ definito sopra non ammette **estremo superiore** in $\mathbb{Q}$, ma ammette **estremo superiore** in $\mathbb{R}$.
:::

Questa è una proprietà fondamentale dell'insieme dei numeri reali, e prende il nome di **proprietà dell'estremo superiore**, **proprietà di completezza** o **assioma di continuità**.

## Assioma di Continuità di $\mathbb{R}$

Definiamo $\mathbb{R}$ come un **campo ordinato** che soddisfa le proprietà $R_1$, $R_2$, $R_3$ e $R_4$.

D'altro cantro, $\mathbb{Q}$ è un **campo ordinato** che soddisfa le proprietà $R_1$, $R_2$ e $R_3$, ma non soddisfa la proprietà $R_4$.