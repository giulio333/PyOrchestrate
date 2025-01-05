# Integrabilità in senso Improprio

Fin ora abbiamo sempre definito il concetto di **integrale** sotto le condizioni che $f$ fosse una funzione limitata e che $I$ fosse un intervallo limitato.

Ora vediamo come si può estendere queste ipotesti ai casi in cui $f$ e/o $I$ non sono limitati.

::: tip Teorema

Sia $f: (a, b] \to \mathbb{R}, \ a \in \mathbb{R} \cup \{-\infty\}, \text{ tale che } f \text{ sia integrabile in } [\omega, b] \ \forall \omega \in (a, b]$.

Se esiste in $\mathbb{R}^*$ il limite

$$
\lim_{\omega \to a^+} \int_{\omega}^{b} f(x) \, dx
$$

tale limite è detto **integrale improprio** o **generalizzato** di $f$ in $(a, b]$.

Ora, se il limite esiste finito:
- $f$ è **integrabile in senso improprio** in $(a, b]$ e l'integrale improprio di $f$ è **convergente**.

Al contrario, se esiste non finito:

- l'integrale improprio di $f$ è detto **divergente** in $(a, b]$.
:::

::: tip Teorema

Sia $f: [a, b) \to \mathbb{R}, \ b \in \mathbb{R} \cup \{\infty\}, \text{ tale che } f \text{ sia integrabile in } [a, \lambda] \ \forall \lambda \in [a, b)$.

Se esiste in $\mathbb{R}^*$ il limite

$$
\lim_{\lambda \to b^-} \int_{a}^{\lambda} f(x) \, dx
$$

tale limite è detto **integrale improprio** o **generalizzato** di $f$ in $[a, b)$.

Ora, se il limite esiste finito:
- $f$ è **integrabile in senso improprio** in $[a, b)$ e l'integrale improprio di $f$ è **convergente**.

Al contrario, se esiste non finito:

- l'integrale improprio di $f$ è detto **divergente** in $[a, b)$.
:::

Dimostriamo il teorema con un esempio...

$$
\int_{a}^{b} x^{-k}dx
$$

Con $x \in \mathbb{R^+}$, $k \in \mathbb{R}$ e $0 < a < b$.

Dobbiamo distinguere due casi in base al valore assunto da $k$, infatti

- se $k = 1$

$$
\int_{a}^{b} x^{-k}dx = \int_{a}^{b} \frac{1}{x} = \ln |x| \bigg\rvert_{a}^{b}
$$

- se $k \neq 1$

$$
\int_{a}^{b} x^{-k}dx = \int_{a}^{b} \frac{1}{x^k}dx = \frac{x^{1 - k}}{1 - k} \bigg\rvert_{a}^{b}
$$

Ora procediamo fissando, per esempio, $b = 1$

- se $k = 1$

$$
\int_{a}^{1} x^{-k}dx = - \ln (a)
$$

- se $k \neq 1$

$$
\int_{a}^{1} x^{-k}dx = \frac{1}{1 - k} - \frac{a^{1-k}}{1 - k}
$$

Ora dobbiamo calcolare il limite

$$
\lim_{a \to 0^+} \int_{a}^{1} x^{-k}dx
$$

- se $k = 1$

$$
\lim_{a \to 0^+} - \ln (a) = \infty
$$

Questo limite **non è convergente**.

- se $k \neq 1$

$$
\lim_{a \to 0^+} \frac{1}{1 - k} - \frac{a^{1-k}}{1 - k}
$$

Questo limite **è convergente se e solo se** $1 - k > 0$ ovvero $k < 1$.

Sotto tale ipotesi il limite vale

$$
- \frac{1}{1 - k}
$$

Abbiamo quindi dimostrato che

$$
f(x) = \frac{1}{x^k} \text{ è integrabile in senso improprio in } (0, 1] \text{ se } k < 1
$$

----

Vale un discorso analogo se si pone $a = 1$ e si manda $b$ a infinito.

In tal caso si ottiene

$$
f(x) = \frac{1}{x^k} \text{ è integrabile in senso improprio in } [1, \infty) \text{ se } k > 1
$$

::: tip Grafico di $f(x) = \frac{1}{\sqrt{x}}$

Questo esempio contiene un risultato sorprendente!

E' possibile che l'area di una funzione illimitata in un intervallo assuma un valore finito, infatti

$$
f(x) = \frac{1}{\sqrt{x}} \text{ è integrabile in senso improprio in } (0, 1] \text{ poichè } k = \frac{1}{2} < 1
$$

Svolgendo i calcoli si ottiene

$$
\lim_{a \to 0^+} \int_{a}^{1} \frac{1}{x^{\frac{1}{2}}}dx = \lim_{a \to 0^+} 2 x^{\frac{1}{2}} \bigg\rvert_{a}^{1} = \lim_{a \to 0^+} 2( 1 - a^{\frac{1}{2}} ) = 2
$$

come mostrato nel teorema precedente.

> In questo caso la funzione è **illimitata** per $x \to 0$.

![plot](./plot_1.png)

:::






