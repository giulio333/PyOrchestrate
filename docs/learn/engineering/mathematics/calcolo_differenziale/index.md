# Taylor's Theorem

It is a very powerful tool for solving a recurring problem in mathematical analysis.

How can we approximate a function in terms of simpler functions, such as polynomials, while maintaining some of its original properties?

The Taylor polynomial serves precisely this purpose, at least in a neighborhood of a point within the domain.

Let

- $f: (a, b) \to \mathbb{R}$ be continuous at $x_0$

- $x_0 \in (a, b)$

then

$$
f(x) = f(x_0) + o(1) \text{ as } x \to x_0
$$

whereas if $f$ is differentiable at $x_0$, then

$$
f(x) = f(x_0) + f'(x - x_0) + o(x - x_0) \text{ as } x \to x_0
$$

The first approximation is denoted as $T_0(x)$ while the second as $T_1(x)$.

These represent respectively the best **constant** and **linear** approximations of $f(x)$ as $x \to x_0$.

::: tip
The approximation $T_1(x)$ has degree $\leq 1$, in fact

- $T_0(x)$ has degree $1$ if $f'(x_0) \neq 0$
- $T_1(x)$ has degree $1$ if $f'(x_0) = 0$
:::

Note that

$$
T_0(x_0) = T_1(x_0) = f(x_0)
$$

and

$$
T'_1(x_0) = f'(x_0)
$$

and in general, if $f$ is differentiable $n$ times

$$
T^{(n)}_n(x_0) = f^{(n)}(x_0) \quad \forall n \in \mathbb{N}
$$