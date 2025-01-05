# Equazioni del primo ordine a variabili separabili

Si tratta di una equazione nella forma

$$
y'(x) = g(x)h(y(x))
$$

Dove

- $g : I \to \mathbb{R}$.
- $h : J \to \mathbb{R}$.

Procederemo come nel caso di **euazioni lineari omogenee**, osservando che se $y_0$ è uno zero di $h$ allora $f(x) = y_0$ è una soluzione.

::: tip Esempio

Consideriamo il problema di Cauchy

$$
\begin{cases}
y' = y^{\frac{1}{3}} \text{ in } \mathbb{R} \\
y(0) = 0
\end{cases}
$$

$$
\int y^{\frac{1}{3}} dy = \int dx
$$

Quindi

$$
\frac{3}{2} y^{\frac{2}{3}} = x + C
$$

Poichè $y(0) = 0$ si ottiene $C = 0$, sostituendo

$$
y(x) = \sqrt{(\frac{2}{3}x)^3} = \frac{2}{3} \sqrt{\frac{2}{3}x^3}
$$

Si noti che $y(x)$ è definita solo per valori non negativi di x e che è soluzione del problema di Cauchy in $[0, \infty)$.