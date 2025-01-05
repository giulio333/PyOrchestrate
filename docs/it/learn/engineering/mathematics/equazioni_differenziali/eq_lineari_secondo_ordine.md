# Equazioni Lineari del Secondo Ordine

## Definizione

Dati un intervallo $I \subseteq \mathbb{R}$ e tre funzioni $b, c, g \in C(I)$ e l'**equazione differenziale lineare del secondo ordine** data da:

$$
y'' + by' + cy = g \text{ in } I
$$

Allora una funzione $y \in C^2(I)$ si dice **soluzione** se

$$
y''(x) + b(x)y'(x) + c(x)y(x) = g(x) \text{ per } x \in I
$$

Dati in oltre $x_0 \in I$ e $y_0, v_0 \in \mathbb{R}$, una soluzione $y$ che verifica $y(x_0) = y_0$ e $y'(x_0) = v_0$ si dice **soluzione del problema di Cauchy**:

$$
\begin{cases}
y'' = -by' - cy + g \text{ in } I \\
y(x_0) = y_0 \\
y'(x_0) = v_0
\end{cases}
$$

## Equazioni omogenee a coefficienti costanti

Consideriamo l'equazione **lineare a coefficienti costanti**

$$
ay'' + by' + cy = 0 \text{ con } a \neq 0
$$

Per trovare la **soluzione generale** è sufficiente trovare **due soluzioni linearmente indipendenti**.

L'idea generale è quella di cercare soluzioni del tipo $y(x) = e^{\lambda x}$ 

Sostituendo si ottiene l'**equazione caratteristica associata**

$$
e^{\lambda x}(a\lambda^2 + b\lambda + c) = 0
$$

con $e^{\lambda x} \neq 0$

$$
a\lambda^2 + b\lambda + c = 0
$$

Si distunguono tre casi come mostra seguente il teorema.

### Teorema

Siano $a, b, c \in \mathbb{R}$ e $a \neq 0$.

::: tip Se $b^2 - 4ac > 0$

Dette $\lambda_1, \lambda_2 \in \mathbb{R}$ le due soluzioni reali dell'**equazione caratteristica**, la soluzione generale dell'**equazione omogenea** è

$$
y(x) = \alpha e^{\lambda_1 x} + \beta e^{\lambda_2 x}
$$

> Si ha infatti:
> - $y_1(x) = e^{\lambda_1 x}$
> - $y_2(x) = e^{\lambda_2 x}$
:::

::: tip Se $b^2 - 4ac = 0$

Detta $\lambda \in \mathbb{R}$ la soluzione reale dell'**equazione caratteristica**, la soluzione generale dell'**equazione omogenea** è

$$
y(x) = (\alpha + \beta) e^{\lambda x}
$$

> Si ha infatti una soluzione reale con molteplicità 2:

> $\lambda = -\frac{b}{2a} \in \mathbb{R}$, quindi
> - $y_1(x) = e^{\lambda x}$ è una soluzione.
> - Per individuare la seconda soluzione si usa il metodo di variazione delle costanti.
:::

::: tip Se $b^2 - 4ac < 0$

Detta $\lambda_1, \lambda_2 \in \mathbb{C}$ le due soluzioni complesse dell'**equazione caratteristica**, la soluzione generale dell'**equazione omogenea** è

$$
y(x) = e^{\mu x}(\alpha cos(\omega x) + \beta sin(\omega x))
$$

> Si ha infatti due soluzioni complesse coniugate

> - $\lambda_1 = \mu + i\omega$ 
> - $\lambda_2 = \mu - i\omega$ 
:::

## Esempi

Si consideri l'equazione differenziale

$$
y'' + 4y = 0
$$

Cerchiamo una soluzione del tipo $y(x) = e^{\lambda x}$ e sostuiamo

$$
\lambda^2 + 4 = 0
$$

Otteniamo $\lambda = \pm 2i$

> In questo caso $\mu = 0$ e $\omega = 2$

Quindi la soluzione generale è

$$
y(x) = \alpha cos (2x) + \beta sin (2x)
$$

---

Si consideri l'equazione differenziale

$$
y'' - 3y' + 2y = 0
$$

Cerchiamo una soluzione del tipo $y(x) = e^{\lambda x}$ e sostuiamo

$$
\lambda^2 + 3\lambda + 2 = 0
$$

Otteniamo $\lambda_1 = 1, \lambda_2 = 2$

Quindi la soluzione generale è

$$
y(x) = \alpha e^{x} + \beta e^{2x}
$$

---

Si consideri l'equazione differenziale

$$
y'' - 2y' + 5y = 0
$$

Cerchiamo una soluzione del tipo $y(x) = e^{\lambda x}$ e sostuiamo

$$
\lambda^2 + 2\lambda + 5 = 0
$$

Otteniamo $\lambda_1 = -1 + 2i, \lambda_2 = -1 - 2i$

> In questo caso $\mu = -1, \omega = 2$

Quindi la soluzione generale è

$$
y(x) = e^-{x}(\alpha cos(2x) + \beta sin(2x))
$$

---

Si consideri l'equazione differenziale

$$
y'' - 6y' + 9y = 0
$$

Cerchiamo una soluzione del tipo $y(x) = e^{\lambda x}$ e sostuiamo

$$
\lambda^2 + 6\lambda + 9 = 0
$$

Otteniamo $\lambda = -3$

Quindi la soluzione generale è

$$
y(x) = (\alpha + \beta x)e^{-3x}
$$

## Equazioni non omogenee a coefficienti costanti

Consideriamo l'equazione

$$
ay'' + by' + cy = g(x) \in \mathbb{R}
$$

dove $a, b, c \in \mathbb{R}, a \neq 0, g \in C(\mathbb{R})$.

Sappiamo che basta trovare una soluzione $\tilde{y}(x)$

Come per le **euqazioni del primo ordine**, abbiamo due metodi.

### Variazione delle Costanti

Sia

$$
\alpha y_1(x) + \beta y_2(x)
$$

la soluzione generale dell'equazione omogenea associata

$$
ay'' + by + cy = 0
$$

Cerchiamo una soluzione della forma $y(x) = A(x)y_1(x) + B(x)y_2(x)$

Dopo ulteriori calcoli che qui non mostreremo, si arriva a

$$
\begin{cases}
A'y_1 + B'y_2 = 0 \\
A'y_1' + B'y_2' = \frac{g(x)}{a} \\
\end{cases}
$$

Integrando si ottengono quindi $A(x), B(x)$

::: tip Esempio

Consideriamo l'euqazione

$$
y'' + 6y' + 9y = e^{-3x} \log(1+x^2) \text{ per } x \in \mathbb{R}
$$

L'**equazione caratteristica** dell'equazione omogenea associata è

$$
\lambda^2 + 6\lambda + 9 = 0
$$

Ossia $\lambda = -3$

Quindi la soluzione generale è

$$
y(x) = (A + B x)e^{-3x}
$$

Ora sicerca una soluzione del tipo

$$
A(x)e^{-3x} + B(x)xe^{-3x}
$$

Si risolve quindi il sistema

$$
\begin{cases}
A'e^{-3x} + B'xe^{-3x} = 0 \\
-3A'e^{-3x} + B'(-3x +1)e^{-3x} = e^{-3x}\log(1+x^2) \\
\end{cases}
$$

Quindi

$$
\begin{cases}
A' = -x\log(1+x^2) \\
B' = \log(1+x^2) \\
\end{cases}
$$

Integrando si ottiene

$$
\begin{cases}
A(x) = -\frac{1}{2}x^2\log(1+x^2) + \frac{1}{2}x^2 -\frac{1}{2}\log(1+x^2) \\
B(x) = x\log(1+x^2) -2x +2 \arctan{x} \\
\end{cases}
$$

Dunque la soluzione generale è

$$
y(x) = \alpha e^{-3x} + \beta xe^{-3x} + \frac{1}{2}((x^2-1)\log(1+x^2) -3x^2 + 4x\arctan{x})e^{-3x}
$$