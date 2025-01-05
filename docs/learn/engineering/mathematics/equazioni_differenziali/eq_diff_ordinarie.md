# Ordinary Differential Equations

## Definition

These are **equations** whose **unknown** is a **function** and in which the **derivatives** of the unknown function appear.

If the unknown is a function of a single independent variable, we speak of **ordinary differential equations (ODEs)**.

::: info Notation
We will denote
- $y$ as the **dependent variable** (or unknown function).
- $x$ as the **independent variable**.
:::

The **general form** of a differential equation is of the type

$$
f(x, y, y', ... , y^{(n)}) = 0
$$

where $f$ is a function defined in a subset of $\mathbb{R}^{n+2}$, with values in $\mathbb{R}$.

::: tip Why $\mathbb{R}^{n+2}$?
Just count the elements of the function $f$:

- $t$ and $y$ are 2 elements.
- $y', ... , y^{(n)}$ are n elements.

So $n+2$ elements.
:::

## Classification of ODEs

### Order of an ODE

The order of a differential equation is the highest order of the derivatives of the unknown function that appear in the equation.

### Linear ODEs

A differential equation is called **linear** if $f$ is linear with respect to $y, ... , y^n$.

In simpler terms, it is sufficient that $y$ and its derivatives have exponent 1.

### Homogeneous ODEs

A differential equation is called **homogeneous** if there exists $k \in \mathbb{R}$ such that

$$
f(x, \lambda y, ..., \lambda y^{(n)}) = \lambda^k f(x, y, ... , y^{(n)}) \quad \forall \lambda > 0
$$

In simpler terms, to be homogeneous, all the terms that appear in the equation depend on the unknown function $y$ or its derivatives.

Conversely, an equation of the type

$$
f(x, y, y', ..., y^{(n)}) = g(x) \quad \text{with } g(x) \neq 0
$$

is called **non-homogeneous**.

### Autonomous ODE

A differential equation is called **autonomous** if $f$ does not depend on $t$.

### Normal Form of an ODE

A differential equation is said to be in **normal form** if the highest order derivative is explicitly determined as a function of the others, that is

$$
y^{(n)}(x) = f(x,y(x),y(x)',...,y^{(n-1)}(x))
$$

This time the function is defined as $f: A \subseteq \mathbb{R}^{n+1} \to \mathbb{R}$.

::: tip Example Newton's Law

A classic example of an ordinary differential equation is **Newton's Law**

$$
my''(t) = F(t, y(t), y'(t))
$$

which, in the most general case, describes the motion of a material point of mass $m$ along a vertical guide, where:

- $y(t)$ indicates the position of the point as a function of time $t$
- $y'(t)$ indicates the velocity of the point as a function of time $t$
- $y''(t)$ indicates the acceleration of the point as a function of time $t$

$$
my''(t) = -mg
$$

By integrating both sides, the well-known equations are obtained

$y'(t) = -gt + A$

$y(t) = -\frac{1}{2}gt^2 + At + B$

where $A$ and $B$ are constants.

- Here $f$ is given by

$$
f(t, y, y', y'') = my'' - F(t, y, y', y') 
$$

- It is a **Second Order** differential equation since the highest degree is 2.
- It is **Linear**.
- It is not **homogeneous** since $f(y, y', y'') \not = 0$.
:::

## Examples

::: tip Study $y^{(3)} + x^2y' + y = 0$
The differential equation:

- It is linear because its derivatives all have exponent one.
- Its order is 3, as the highest order of derivation is 3 $y^{(3)}$.
- It is homogeneous because $g(x) = 0$.

It is therefore a linear, third-order, homogeneous differential equation, not with constant coefficients.
:::

::: tip Study $y'' + y^2 - x^3 -1 = 0$
The differential equation:

- It is not linear because $y$ has an exponent $> 1$.
- Its order is 2, as the highest order of derivation is 2 ($y''$).
- It is not homogeneous because $g(x) \neq 0$.

It is therefore a non-linear, second-order, non-homogeneous differential equation with constant coefficients.

::: warning "Homogeneous?"
Do not be fooled by the fact that on the right side of the equal sign there is $0$.

In this case, the equation should be rewritten as

$f(x, y, y', y'') = g(x)$

Which in our case corresponds to

$y'' + y^2 = x^3 + 1$

So $g(x) = x^3 + 1$
:::

