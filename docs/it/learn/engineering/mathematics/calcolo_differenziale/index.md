# Polinomio di Taylor

Si tratta di uno strumento molto potente per risolvere un problema ricorrente dell'analisi matematica.

Come possiamo approssimare una funzione in termini di funzioni più semplici, come polinomi, pur mantenendo alcune delle sue proprietà originali?

Il polinomio di Taylor serve proprio a questo, almeno in un intorno di un punto interni al dominio.

Siano 

- $f: (a, b) \to \mathbb{R}$ continua in $x_0$

- $x_0 \in (a, b)$

allora

$$
f(x) = f(x_0) + o(1) \text{ per } x \to x_0
$$

mentre se $f$ è derivabile in $x_0$, allora

$$
f(x) = f(x_0) + f'(x - x_0) + o(x - x_0) \text{ per } x \to x_0
$$

La prima approssimazione si indica come $T_0(x)$ mentre la seconda $T_1(x)$. 

Queste rappresentano rispettivamente le migliori approssimazioni **costante** e **lineare** di $f(x)$ per $x \to x_0$.

::: tip
L'approssimazione $T_1(x)$ ha grado $\leq 1$, infatti

- $T_0(x)$ ha grado $1$ se $f'(x_0) \neq 0$
- $T_1(x)$ ha grado $1$ se $f'(x_0) = 0$
:::

Si noti che 

$$
T_0(x_0) = T_1(x_0) = f(x_0)
$$

e

$$
T'_1(x_0) = f'(x_0)
$$

e in generale, se $f$ è derivabile $n$ volte

$$
T^{(n)}_n(x_0) = f^{(n)}(x_0) \quad \forall n \in \mathbb{N}
$$