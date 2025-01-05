# Equazioni Differenziali Ordinarie

## Definizione

Si tratta di **equazioni** la cui **icognita** è una **funzione** e in cui compaiono le **derivate** della funzione incognita.

Se l'incognita è una funzione di una sola variabile indipendente, si parla di **equazioni differenziali ordinarie (EDO)**.

::: info Notazione
Indicheremo con 
- $y$ la **variabile dipendente** (o funzione ingognita).
- con $x$ la **variabile indipendente**.
:::

La **forma generale** di un'equazione differenziale è del tipo

$$
f(x, y, y', ... , y^{(n)}) = 0
$$

dove $f$ è una funzione definita in un sottoinsieme di $\mathbb{R}^{n+2}$, a valori in $\mathbb{R}$.

::: tip Perchè $\mathbb{R}^{n+2}$ ?
Basta contare gli elementi della funzione $f$:

- $t$ e $y$ sono 2 elementi.
- $y', ... , y^{(n)}$ sono n elementi.

Quindi $n+2$ elementi.
:::

## Classificazione delle EDO

### Ordine di una EDO

L'ordine di una funzine differenziale è l'ordine massimo delle derivate della funzione incognita che compaiono nell'equazione.

### EDO Lineari

Un'equazione differenziale si dice **lineare** se $f$ è lineare rispetto a $y, ... , y^n$.

Detto in modo più semplice, è sufficiente che $y$ e le sue derivate abbiano esponente 1.

### EDO Omogenee

Un'equazione differenziale si dice **omogenea** se esiste $k \in \mathbb{R}$ tale che

$$
f(x, \lambda y, ..., \lambda y^{(n)}) = \lambda^k f(x, y, ... , y^{(n)}) \quad \forall \lambda > 0
$$

In parole più semplici, per essere omogenea tutti i termini che compaiono nell'equazione dipendono dalla funzione incognita $y$ o dalle sue derivate.

Al contrario, una equazione del tipo

$$
f(x, y, y', ..., y^{(n)}) = g(x) \quad \text{con } g(x) \neq 0
$$

si dirà **non omogenea**.


### EDO Autonoma

Un'equazione differenziale si dice **autonoma** se $f$ non dipende da $t$

### Forma Normale di una EDO

Un'equazione differenziale si dice in **forma normale** se la derivata di ordine massimo è determinata epslicitamente in funzione delle altre, ovvero

$$
y^{(n)}(x) = f(x,y(x),y(x)',...,y^{(n-1)}(x))
$$

Questa volta la funzione è definita in $f: A \subseteq \mathbb{R}^{n+1} \to \mathbb{R}$ 

::: tip Esempio Legge di Newton

Un classico esempio di equazione differenziale ordinaria è la **Legge di Newton**

$$
my''(t) = F(t, y(t), y'(t))
$$

che, nel caso più generale,descrive il moto di un punto matieriale di massa $m$ lungo una guida verticale, dove:

- $y(t)$ indica la posizione del punto in funzione del tempo $t$
- $y'(t)$ indica la velocità del punto in funzione del tempo $t$
- $y''(t)$ indica l'acceleration del punto in funzione del tempo $t$

$$
my''(t) = -mg
$$

Integrando ambo i membri si ottengono le già note equazioni

$y'(t) = -gt + A$

$y(t) = -\frac{1}{2}gt^2 + At + B$

dove $A$ e $B$ sono costanti.

- Qui $f$ è data da

$$
f(t, y, y', y'') = my'' - F(t, y, y', y') 
$$

- E' una equazione differenziale del **Secondo Ordine** in quanto il grado massimo è 2.
- E' **Lineare**.
- Non è **omogenea** in quanto $f(y, y', y'') \not = 0$.
:::

## Esempi

::: tip Studiare $y^{(3)} + x^2y' + y = 0$
L'equazione differenziale:

- E' lineare poichè le sue derivate hanno tutte esponente uno.
- Il suo ordine è 3, infatti il massimo ordine di derivazione è 3 $y^{(3)}$.
- E' omogenea poichè $g(x) = 0$.

Si tratta quindi di un'equazione differenziale lineare, del terzo ordine, omogenea, non a coefficienti costanti.
:::

::: tip Studiare $y'' + y^2 - x^3 -1 = 0$
L'equazione differenziale:

- Non è lineare poichè $y$ ha esponente $> 1$.
- Il suo ordine è 2, infatti il massimo ordine di derivazione è 2 ($y''$).
- Non è omogenea poichè $g(x) \neq 0$.

Si tratta quindi di un'equazione differenziale non lineare, del secondo ordine, non omogenea e a coefficienti costanti.

::: warning "Omogenea?"
Non lasciatevi ingannare dal fatto che a destra dell'uguale c'è $0$.

In questo caso infatti, l'equazione va riscritta come

$f(x, y, y', y'') = g(x)$

Che nel nostro caso corrisponde a

$y'' + y^2 = x^3 + 1$

Quindi $g(x) = x^3 + 1$
:::



