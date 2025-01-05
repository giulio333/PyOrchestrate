# First-Order Linear Differential Equations

## Definition

Given an interval $I \subseteq \mathbb{R}$ and two functions $a, b \in C(I)$, the **first-order linear differential equation** is given by:

$$
y' = ay + b \text{ in } I
$$

Then a function $y \in C^1(I)$ is called a **solution** if

$$
y'(x) = a(x)y(x) + b(x) \text{ for } x \in I
$$

::: info Notation
$y \in C^1(I)$ means that 
- y is **continuous** in $I$
- y is **differentiable** in $I$
- $y'$ is **continuous** in $I$.
:::

::: tip Example
Consider the differential equation:

$$
y'(x) = 2y(x)
$$

where

- $a(x) = 2$
- $b(x) = 0$

> **A function $y(x)$ is a solution to this equation if, by substituting $y(x)$ and its derivatives into the equation, the equality is satisfied.**

Suppose the solution is $y(t) = Ce^{2x}$ with $C \in \mathbb{R}$.

Then

$y'(x) = 2Ce^{2x}$

Substituting

$
2Ce^{2x} = 2Ce^{2x}
$

The equation is verified, so $y(x) = Ce^{2x}$ is a solution.
:::

::: tip Example
Consider the differential equation:

$$ 
y'(x) = 0
$$

where

- $a(x) = 0$
- $b(x) = 0$

Suppose the solution is $y(x) = 2$.

Then

$y'(x) = 0$

Substituting

$
0 = 0
$

The equation is verified, so $y(x) = 2$ is a solution.
:::

From the previous examples, it emerges that the proposed solutions are not unique but infinite.

To select one, additional conditions must be imposed, as shown in the next theorem.

## Cauchy Problem

Given $x_0 \in I$ and $y_0 \in \mathbb{R}$, a solution $y$ that satisfies $y(x_0) = y_0$ is called a **solution to the Cauchy problem**:

$$
\begin{cases}
y' = a(x)y + b(x) \text{ in } I \\
y(x_0) = y_0
\end{cases}
$$

::: tip Associated Homogeneous Equation
We know that the equation is **homogeneous** if $b(x) = 0 \quad \forall x \in I$ and **non-homogeneous** otherwise.

Thus,

$$
y' = ay \text{ in } I
$$

is called the **associated homogeneous equation** of $y' = ay + b \text{ in } I$.
:::

## General Solution

> or **General Integral**

Let 

- $I \subset \mathbb{R}$ be an interval.
- $a(x) \in C(I)$.
- $A(x)$ be a primitive of $a(x)$ in $I$.

All solutions of $y'(x) = a(x)y(x)$ in $I$ are 

$$
y(x) = Ce^{A(x)} \text{ with } C \in \mathbb{R}
$$ 

If $x_0 \in I$ and $y_0 \in \mathbb{R}$ are also known, the function

$$
y(x) = y_0e^{A(x) - A(x_0)}
$$

is the unique solution to the Cauchy problem 

$$
\begin{cases}
y' = a(x)y(x) + b(x) \text{ in } I \\
y(x_0) = y_0
\end{cases}
$$

Thus,

$$
Ce^{A(x)} \text{ with } C \in \mathbb{R}
$$ 

is called the **general solution** or the **general integral** of $y'(x) = a(x)y(x)$

::: tip Study of the Associated Homogeneous Equation
Let's study the associated homogeneous equation, assuming that $y$ is a solution of $y'=ay$ in $I$ and that $y(x) \neq 0 \quad \forall x \in I$.

Then

$$
\frac{y'(x)}{y(x)} = a(x)
$$

$
\int \frac{y'(x)}{y(x)} dx = \int a(x) dx + C_0 \text{ with } C_0 \in \mathbb{R}
$

$
\log|y(x)| = \int a(x) dx + C_0
$

$
|y(x)| = e^{\int a(x)dx + C_0}
$

$
y(x) = \pm e^{C_0}e^{\int a(x)dx}
$

Setting $C = \pm e^{C_0}$ 
we get

$$
y(x) = Ce^{\int a(x)dx}
$$

Thus,

$$
y(x) = Ce^{A(x)} \text{ is a solution } \forall C \in \mathbb{R}
$$
:::

## Particular Solution

Let 

- $I \subset \mathbb{R}$ be an interval.
- $a$ and $b$ $\in C(I)$.
- $A(x)$ be a primitive of $a$ in $I$.

If $\tilde{y}(x)$ is a solution of

$$
y'(x) = a(x)y(x) + b(x)
$$

then all solutions are

$$
y(x) = \tilde{y}(x) + Ce^{A(x)} \text{ with } C \in \mathbb{R}
$$

::: tip Study of the Non-Homogeneous Equation

$$
y'(x) = a(x)y(x) + b(x) \text{ in } I
$$

Let $y(x)$ and $\tilde{y}(x)$ be two solutions.

Setting $z(x) := y(x) - \tilde{y}(x)$ we have

$$
z'(x) = y'(x) - \tilde{y}'(x) = a(x)y(x) + b(x) - a(x)\tilde{y}(x) - b(x) = a(y(x) - \tilde{y}(x)) = az(x)
$$

But the differential equation $z'(x) = az(x)$ is known to have the solution

$$
z(x) = Ce^{A(x)}
$$

Thus,

$$
y(x) = z(x) + \tilde{y}(x) = \tilde{y}(x) + Ce^{A(x)}
$$
:::

The problem remains to determine a solution $\tilde{y}(x)$ called the **particular solution** of the **non-homogeneous equation**.

> There are 2 possible methods: Variation of the constant, by intuition.

### Variation of the Constant

We seek a solution in the form $K(x)e^{A(x)}$.

Substituting into the equation $y'(x) = a(x)y(x) + b(x)$ we get

$$
K'(x)e^{A(x)} + a(x)K(x)e^{A(x)} = a(x)K(x)e^{A(x)} + b(x)
$$

Thus,

$$
K'(x) = b(x)e^{-A(x)}
$$

Then if $K(x)$ is a primitive of $b(x)e^{-A(x)}$ in $I$, the function

$$
\tilde{y}(x) = K(x)e^{A(x)}
$$

is the sought solution.

::: tip Theorem
Let $I \subset \mathbb{R}$ be an interval, $a, b \in C(I)$, and $A(x)$ be a primitive of $a$ in $I$.

- All **solutions of the non-homogeneous equation** $y'(x) = a(x)y(x) + b(x)$ are

$$
y(x) = (C + K(x))e^{A(x)} \text{ with } C \in \mathbb{R}
$$

where $K(x)$ is a primitive of $b(x)e^{-A(x)}$ in $I$.

- Given $x_0 \in I$ and $y_0 \in \mathbb{R}$, the function

$$
y(x) = (y_0 + K(x) - K(x_0))e^{A(x) - A(x_0)}
$$

is the unique **solution to the Cauchy problem**.
:::

::: tip Example
Determine the solutions of the equation

$$
y'(x) = -2y(x) + 3 \text{ in } \mathbb{R}
$$

First, let's study the associated homogeneous equation

$$
y'(x) = -2y(x)
$$

which has the **general solution** $y(x) = Ce^{\int a(x)dx}$ with $a(x) = -2$

$$
Ce^{-2x} \text{ with } C \in \mathbb{R}
$$

Following the method of variation of the constant, we set 

$$
\tilde{y}(x) = K(x)e^{-2x}
$$

Substituting $\tilde{y}(x)$ into the non-homogeneous equation, we get $K'(x)e^{-2x} = 3$, that is

$$
K'(x) = 3e^{2x}
$$

Integrating, we get

$$
K(x) = \frac{3}{2}e^{2x} + C
$$

Thus, choosing $K(x) = \frac{3}{2}e^{2x}$, we get the solution of the non-homogeneous equation

$$
\tilde{y}(x) = \frac{3}{2}e^{2x}e^{-2x} = \frac{3}{2} 
$$

All solutions are

$$
y(x) = \frac{3}{2} +Ce^{-2x} \text{, with } C \in \mathbb{R}
$$
:::

### Intuitive Method

It is possible to derive a **particular solution** $\tilde{y}(x)$ of $y' = ay + b$ by intuition.

::: tip Example

Consider the equation

$$
y' = 3y + 4x^3 + 2x^2 -x +1 \text{ in } \mathbb{R}
$$

Suppose the solution is of the form

$$
\tilde{y}(x) = ax^3 + bx^2 + cx + d
$$

Substituting into the equation, we get

$$
3a^2 + 2bx + c = 3ax^3 + 3bx^2 + 3cx + 3d + 4x^3 + 2x^2 -x +1
$$

Collecting terms,

$$
(3a + 4)x^3 + (-3a + 3b + 2)x^2 (-2b +3c -1)x + (-c +3d +1) = 0
$$

The equation is satisfied if

$$
\begin{cases}
3a + 4 = 0 \\
-3a + 3b +2 = 0 \\
-2b +3c -1 = 0 \\
-c +3d +1 = 0
\end{cases}
$$

That is, if and only if

- $a = - \frac{4}{3}$
- $b = -2$
- $c = -1$
- $a = - \frac{2}{3}$

Then

$$
\tilde{y}(x) = \frac{4}{3}x^3 - 2x^2 - x - \frac{2}{3}
$$

And all solutions are 

$$
\tilde{y}(x) = Ce^{3x} - \frac{4}{3}x^3 - 2x^2 -x - \frac{2}{3} \text{ with } C \in \mathbb{R}
$$

> Solving this equation with the **Constant Method** would have led to laborious calculations.

:::
