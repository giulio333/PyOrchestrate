# Second-Order Linear Differential Equations

## Definition

Given an interval $I \subseteq \mathbb{R}$ and three functions $b, c, g \in C(I)$, the **second-order linear differential equation** is given by:

$$
y'' + by' + cy = g \text{ in } I
$$

Then a function $y \in C^2(I)$ is called a **solution** if

$$
y''(x) + b(x)y'(x) + c(x)y(x) = g(x) \text{ for } x \in I
$$

Given $x_0 \in I$ and $y_0, v_0 \in \mathbb{R}$, a solution $y$ that satisfies $y(x_0) = y_0$ and $y'(x_0) = v_0$ is called a **solution of the Cauchy problem**:

$$
\begin{cases}
y'' = -by' - cy + g \text{ in } I \\
y(x_0) = y_0 \\
y'(x_0) = v_0
\end{cases}
$$

## Homogeneous Equations with Constant Coefficients

Consider the **linear equation with constant coefficients**

$$
ay'' + by' + cy = 0 \text{ with } a \neq 0
$$

To find the **general solution**, it is sufficient to find **two linearly independent solutions**.

The general idea is to look for solutions of the form $y(x) = e^{\lambda x}$.

Substituting, we obtain the **associated characteristic equation**

$$
e^{\lambda x}(a\lambda^2 + b\lambda + c) = 0
$$

with $e^{\lambda x} \neq 0$

$$
a\lambda^2 + b\lambda + c = 0
$$

There are three cases as shown by the following theorem.

### Theorem

Let $a, b, c \in \mathbb{R}$ and $a \neq 0$.

::: tip If $b^2 - 4ac > 0$

Let $\lambda_1, \lambda_2 \in \mathbb{R}$ be the two real solutions of the **characteristic equation**, the general solution of the **homogeneous equation** is

$$
y(x) = \alpha e^{\lambda_1 x} + \beta e^{\lambda_2 x}
$$

> Indeed:
> - $y_1(x) = e^{\lambda_1 x}$
> - $y_2(x) = e^{\lambda_2 x}$
:::

::: tip If $b^2 - 4ac = 0$

Let $\lambda \in \mathbb{R}$ be the real solution of the **characteristic equation**, the general solution of the **homogeneous equation** is

$$
y(x) = (\alpha + \beta) e^{\lambda x}
$$

> Indeed, there is a real solution with multiplicity 2:

> $\lambda = -\frac{b}{2a} \in \mathbb{R}$, so
> - $y_1(x) = e^{\lambda x}$ is a solution.
> - To find the second solution, the method of variation of constants is used.
:::

::: tip If $b^2 - 4ac < 0$

Let $\lambda_1, \lambda_2 \in \mathbb{C}$ be the two complex solutions of the **characteristic equation**, the general solution of the **homogeneous equation** is

$$
y(x) = e^{\mu x}(\alpha \cos(\omega x) + \beta \sin(\omega x))
$$

> Indeed, there are two complex conjugate solutions

> - $\lambda_1 = \mu + i\omega$ 
> - $\lambda_2 = \mu - i\omega$ 
:::

## Examples

Consider the differential equation

$$
y'' + 4y = 0
$$

We look for a solution of the form $y(x) = e^{\lambda x}$ and substitute

$$
\lambda^2 + 4 = 0
$$

We obtain $\lambda = \pm 2i$

> In this case $\mu = 0$ and $\omega = 2$

So the general solution is

$$
y(x) = \alpha \cos (2x) + \beta \sin (2x)
$$

---

Consider the differential equation

$$
y'' - 3y' + 2y = 0
$$

We look for a solution of the form $y(x) = e^{\lambda x}$ and substitute

$$
\lambda^2 + 3\lambda + 2 = 0
$$

We obtain $\lambda_1 = 1, \lambda_2 = 2$

So the general solution is

$$
y(x) = \alpha e^{x} + \beta e^{2x}
$$

---

Consider the differential equation

$$
y'' - 2y' + 5y = 0
$$

We look for a solution of the form $y(x) = e^{\lambda x}$ and substitute

$$
\lambda^2 + 2\lambda + 5 = 0
$$

We obtain $\lambda_1 = -1 + 2i, \lambda_2 = -1 - 2i$

> In this case $\mu = -1, \omega = 2$

So the general solution is

$$
y(x) = e^{-x}(\alpha \cos(2x) + \beta \sin(2x))
$$

---

Consider the differential equation

$$
y'' - 6y' + 9y = 0
$$

We look for a solution of the form $y(x) = e^{\lambda x}$ and substitute

$$
\lambda^2 + 6\lambda + 9 = 0
$$

We obtain $\lambda = -3$

So the general solution is

$$
y(x) = (\alpha + \beta x)e^{-3x}
$$

## Non-Homogeneous Equations with Constant Coefficients

Consider the equation

$$
ay'' + by' + cy = g(x) \in \mathbb{R}
$$

where $a, b, c \in \mathbb{R}, a \neq 0, g \in C(\mathbb{R})$.

We know that it is enough to find a solution $\tilde{y}(x)$.

As with **first-order equations**, we have two methods.

### Variation of Constants

Let

$$
\alpha y_1(x) + \beta y_2(x)
$$

be the general solution of the associated homogeneous equation

$$
ay'' + by' + cy = 0
$$

We look for a solution of the form $y(x) = A(x)y_1(x) + B(x)y_2(x)$.

After further calculations, which we will not show here, we arrive at

$$
\begin{cases}
A'y_1 + B'y_2 = 0 \\
A'y_1' + B'y_2' = \frac{g(x)}{a} \\
\end{cases}
$$

Integrating, we obtain $A(x), B(x)$.

::: tip Example

Consider the equation

$$
y'' + 6y' + 9y = e^{-3x} \log(1+x^2) \text{ for } x \in \mathbb{R}
$$

The **characteristic equation** of the associated homogeneous equation is

$$
\lambda^2 + 6\lambda + 9 = 0
$$

That is, $\lambda = -3$

So the general solution is

$$
y(x) = (A + B x)e^{-3x}
$$

Now we look for a solution of the form

$$
A(x)e^{-3x} + B(x)xe^{-3x}
$$

We then solve the system

$$
\begin{cases}
A'e^{-3x} + B'xe^{-3x} = 0 \\
-3A'e^{-3x} + B'(-3x +1)e^{-3x} = e^{-3x}\log(1+x^2) \\
\end{cases}
$$

So

$$
\begin{cases}
A' = -x\log(1+x^2) \\
B' = \log(1+x^2) \\
\end{cases}
$$

Integrating, we obtain

$$
\begin{cases}
A(x) = -\frac{1}{2}x^2\log(1+x^2) + \frac{1}{2}x^2 -\frac{1}{2}\log(1+x^2) \\
B(x) = x\log(1+x^2) -2x +2 \arctan{x} \\
\end{cases}
$$

Thus, the general solution is

$$
y(x) = \alpha e^{-3x} + \beta xe^{-3x} + \frac{1}{2}((x^2-1)\log(1+x^2) -3x^2 + 4x\arctan{x})e^{-3x}
$$