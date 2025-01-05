# Campi

Un **campo** è una struttura algebrica che soddisfa alcune proprietà particolari.

Iniziamo prendendo come riferimento l'insieme dei numeri **Razionali** $\mathbb{Q}$ elencando alcune proprietà che soddisfa:

## Proprietà ${R_1}$

Viene definita in $\mathbb{Q}$ un'operazione, detta **somma**, con le seguenti proprietà:

### Proprietà Commutativa

$\forall a,b$ , $a+b = b+a$

### Proprietà Associativa

$\forall a,b,c$ , $(a+b)+c = a+(b+c)$

### Proprietà dell'Elemento Neutro

$\exists 0$ tale che $\forall a$ , $a+0 = a$

Il numero $0$ è detto **elemento neutro** rispetto all'operazione di somma.

### Proprietà dell'Elemento Opposto

$\forall a$ , $\exists -a$ tale che $a+(-a) = 0$

## Proprietà ${R_2}$

Viene definita in $\mathbb{Q}$ un'operazione, detta **prodotto**, con le seguenti proprietà:

### Proprietà Commutativa

$\forall a,b$ , $a \cdot b = b \cdot a$

### Proprietà Associativa

$\forall a,b,c$ , $(a \cdot b) \cdot c = a \cdot (b \cdot c)$

### Proprietà dell'Elemento Neutro

$\exists 1$ tale che $\forall a$ , $a \cdot 1 = a$

Il numero $1$ è detto **elemento neutro** rispetto all'operazione di prodotto.

### Proprietà dell'Elemento Inverso

$\forall a \neq 0$ , $\exists a^{-1}$ tale che $a \cdot a^{-1} = 1$

::: tip Proprietà Distributiva
Le operazioni di somma e prodotto sono legate dalla **proprietà distributiva**:

$\forall a,b,c$ , $a \cdot (b+c) = a \cdot b + a \cdot c$
:::

Da queste proprietà possiamo definire le quattro operazioni aritmetiche fondamentali.

Infatti, possiamo definire:

- la sottrazione come l'operazione inversa della somma ponendo $a-b = a+(-b)$
- la divisione come l'operazione inversa del prodotto ponendo $\frac{a}{b} = a \cdot b^{-1} \quad b \neq 0$

## Proprietà ${R_3}$

Viene definita in $\mathbb{Q}$ una relazione d'ordine $\leq$ con le seguenti proprietà:

### Proprietà Riflessiva

$\forall a$ , $a \leq a$

### Proprietà Antisimmetrica

$\forall a,b$ se $a \leq b$ e $b \leq a$ allora $a = b$

### Proprietà Transitiva

$\forall a,b,c$ se $a \leq b$ e $b \leq c$ allora $a \leq c$

Questo significa che l'ordinamento di $\mathbb{Q}$ è **totale**, oppure che $\mathbb{Q}$ è un **insieme totalmente ordinato**.

## Definizione di Campo

Un **campo** è una struttura algebrica che soddisfa le proprietà ${R_1}$, ${R_2}$.

## Definizione di Campo Ordinato

Un **campo ordinato** è una struttura algebrica che soddisfa le proprietà ${R_1}$, ${R_2}$, ${R_3}$.

Tali proprietà velgono sia per l'insieme $\mathbb{Q}$ dei numeri razionali, sia per l'insieme $\mathbb{R}$ dei numeri reali.

Possiamo quindi dire che $\mathbb{Q}$ e $\mathbb{R}$ sono **campi ordinati**.

::: tip
Nonostante $\mathbb{Q}$ e $\mathbb{R}$ siano campi ordinati, $\mathbb{Q}$ non è **completo**.

Questo significa ad esempio, che non è possibile avere una corrispondenza biunivoca tra i numeri razionali e i punti di una retta.

Generalmente in analisi, linsieme $\mathbb{R}$ dei numeri reali è preferito a $\mathbb{Q}$ proprio per la sua **completezza**. Infatti quest'ultimo può essere messo in corrispondenza biunivoca con i punti di una retta.

Sarebbe scomodo lavorare con un insieme di numeri che non è completo, non credete?
:::
