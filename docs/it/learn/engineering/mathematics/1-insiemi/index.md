# Insiemi 

Il concetto di **insieme** è uno dei più fondamentali della matematica. 

Possiamo dire che un **insieme** è determinato dai suoi **elementi**, ovvero che un insieme è definito quando esiste un criterio che permette di stabilire se un elemento appartiene o meno all'insieme.

::: tip
Sinonimi di insieme sono: classe, famiglia, collezione.
:::

Generalmente gli insiemi si indicano con lettere maiuscole, ad esempio $A$, $B$, $C$, ecc. e gli elementi con lettere minuscole, ad esempio $a$, $b$, $c$, ecc.

Per indicare che un elementi appartiene ad un insieme si usa la seguente notazione

$$
a \in A
$$

che si legge "a appartiene ad A".

mentre per indicare che un elemento non appartiene ad un insieme si usa la seguente notazione

$$
a \notin A
$$

che si legge "a non appartiene ad A".

Per indicare che un insieme è composto da un certo numeri finito di elementi si usa la seguente notazione

$$
A = \{a_1, a_2, a_3\} = \{a_3, a_2, a_1\}
$$

::: tip
I due insiemi sopra sono uguali, infatti l'ordine degli elementi non conta. Ciò che determina l'uguaglianza di due insiemi è l'insieme degli elementi che li compongono.

Ciò si traduce nel fatto che negli insieme il concetto di **ordine** non ha senso.
:::

GLi elementi di un insieme sono unici, ovvero non possono esserci elementi ripetuti. Se un elemento è ripetuto, esso viene contato una sola volta.

::: tip
Ciò si traduce nel fatto che negli insieme il concetto di **molteplicità** non ha senso.
:::


## Insieme vuoto

Un insieme che non contiene elementi si chiama **insieme vuoto** e si indica con il simbolo $\emptyset$.

## Insieme Universo

L'insieme che contiene tutti gli elementi di interesse in un certo contesto si chiama **insieme universo** e si indica con la lettera $U$.

## Relazioni tra insiemi

Le relazioni tra insiemi permettono di stabilire una connessione logica tra due o più insiemi.

### Inclusione

Un insieme $A$ è **incluso** in un insieme $B$ se ogni elemento di $A$ è anche un elemento di $B$. In tal caso si scrive

$$
A \subseteq B
$$

che si legge "A è incluso in B".

Questo è vero se e solo se

$$
\forall x \in A \Rightarrow x \in B
$$

::: tip
Dire che $A$ è incluso in $B$ non esclude che $A$ possa essere uguale a $B$.

Per affermare che $A$ è strettamente incluso in $B$, ovvero che $A$ è diverso da $B$, si usa la notazione

$$
A \subset B
$$

In formule

$$
\forall x \in A \Rightarrow x \in B \land \exists y \in B \Rightarrow y \notin A
$$
:::

### Uguaglianza

Due insiemi $A$ e $B$ sono **uguali** se contengono gli stessi elementi. In tal caso si scrive

$$
A = B {\text{ se }} \forall x \in A \Rightarrow x \in B \land \forall x \in B \Rightarrow x \in A
$$

Notare che la relazione di uguaglianza tra insiemi è una relazione di **doppia inclusione**.

Infatti deve essere vero che $A \subseteq B$ e $B \subseteq A$.

## Insieme delle Parti

L'insieme delle parti di un insieme $A$ è l'insieme di tutti i sottoinsiemi di $A$.

Ogni insieme ha almeno due sottoinsiemi: l'insieme vuoto e l'insieme stesso.

Si indica con $P(A)$.

::: tip esempio
Dato l'insieme $A = \{1, 2\}$, l'insieme delle parti di $A$ è

$$
P(A) = \{\emptyset, \{1\}, \{2\}, \{1, 2\}\}
$$
:::

In generale, se un insieme ha $n$ elementi, allora l'insieme delle parti ha $2^n$ elementi.
