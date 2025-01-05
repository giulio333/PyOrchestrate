# First order differential equations with separable variables

This is an equation in the form

$$
y'(x) = g(x)h(y(x))
$$

Where

- $g : I \to \mathbb{R}$.
- $h : J \to \mathbb{R}$.

We will proceed as in the case of **homogeneous linear equations**, noting that if $y_0$ is a zero of $h$ then $f(x) = y_0$ is a solution.

::: tip Example

Consider the Cauchy problem

$$
\begin{cases}
y' = y^{\frac{1}{3}} \text{ in } \mathbb{R} \\
y(0) = 0
\end{cases}
$$

$$
\int y^{\frac{1}{3}} dy = \int dx
$$

Therefore

$$
\frac{3}{2} y^{\frac{2}{3}} = x + C
$$

Since $y(0) = 0$ we get $C = 0$, substituting

$$
y(x) = \sqrt{(\frac{2}{3}x)^3} = \frac{2}{3} \sqrt{\frac{2}{3}x^3}
$$

Note that $y(x)$ is defined only for non-negative values of x and that it is a solution of the Cauchy problem in $[0, \infty)$.