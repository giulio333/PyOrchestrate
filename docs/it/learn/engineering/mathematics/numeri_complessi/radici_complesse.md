# Radici Complesse

Quando parliamo di **radici n-esime** di un numero complesso $\omega$ stiamo cercando tutti i numeri complessi $z$ tali che, elevati alla potenza $n$, diano $\omega$.

$$
z^n = \omega
$$

A differenza dei **numeri reali**, nei numeri complessi questo problema **non ha una sola soluzione**, ma **n soluzioni distinte**. 

::: tip
Questo deriva dalla natura del **piano complesso**, dove possiamo immaginare di “girare” attorno all’origine per ottenere diverse versioni di  z  che, quando elevate alla stessa potenza, risultano uguali.
:::

Pensiamo al numero complesso $\omega$ in forma polare

$$
\omega = r(\cos \varphi + i \sin \varphi)
$$

con 

- $r = |\omega|$ il **modulo** di $\omega$, cioè la distanza del punto rappresentante  w  dall’origine nel piano complesso.
- $\theta$ l’**argomento** di $\omega$, cioè l’angolo tra il segmento che congiunge l’origine con il punto rappresentante  w  e l’asse reale positivo.

Per trovare le **radici n-esime** di un numero complesso $\omega$, usiamo il fatto che esistono n radici diverse che si distribuiscono uniformemente sul cerchio di raggio pari a $r^{1/n}$ . 

La r**appresentazione polare** è particolarmente utile perché ci permette di vedere facilmente come queste radici sono legate tra loro.

Dato $w \neq 0$ e un intern $n > 0$ esistono esattamente $n$ radici n-esime di $w$ date da

$$
z_k = \rho_k(\cos \theta_k + i \sin \theta_k)
$$

- $\rho_k = r^\frac{1}{n}$ rappresenta il **modulo** di ogni radice.

Quindi il modulo delle radici è sempre uguale alla radice n-esima del modulo di $\omega$.

Questo significa che **tutte le radici si trovano su un cerchio di raggio** $r^\frac{1}{n}$ **nel piano complesso**.

- $\theta_k = \frac{\varphi + 2k\pi}{n}$ rappresenta l'**argomento** di ogni radice.

Questo argomento si ottiene prendendo l’argomento originale  $\varphi$  di  $\omega$, dividendolo per $n$, e poi aggiungendo un multiplo di $\frac{2\pi}{n}$  per ottenere tutte le possibili soluzioni. 

L’indice  $k$  varia da  $0$  a  $n-1$ , e ciascun valore di  $k$  fornisce una radice diversa. Il termine  $2k\pi$  è usato per considerare tutte le possibili rotazioni attorno al cerchio, dato che i numeri complessi possono essere rappresentati come punti sul piano complesso.

$z_0, z_1, \dots, z_{n-1}$

## Interpretazione Geometrica

Proviamo ora a vedere la cosa dal punto di vista geometrico. 

Quando cerchiamo le radici n-esime, stiamo cercando $n$ numeri complessi $z_0, z_1, \dots, z_{n-1}$ che, elevati alla $n$ , ci diano $\omega$. 

Queste radici saranno equidistanti tra loro, e si troveranno su un cerchio di raggio  $r^{1/n}$ . 

L’angolo tra due radici consecutive sarà sempre uguale e pari a $\frac{2\pi}{n}$, il che fa sì che le radici siano disposte in modo simmetrico rispetto all’origine.

## Esempio

Supponiamo di voler trovare le radici cubiche di un numero complesso $\omega$, con modulo $r$ e argomento $\varphi$.

Le radici saranno tre $z_0, z_1, z_2$ con modulo

$$
\rho_k = r^\frac{1}{3}
$$

e argomenti

$$
\theta_k = \frac{\varphi + 2k\pi}{3}
$$

con $k = 0, 1, 2$.

Ovvero

$$
\begin{cases}
z_0 = r^\frac{1}{3}(\cos \frac{\varphi}{3} + i \sin \frac{\varphi}{3}) \\
z_1 = r^\frac{1}{3}(\cos \frac{\varphi + 2\pi}{3} + i \sin \frac{\varphi + 2\pi}{3}) \\
z_2 = r^\frac{1}{3}(\cos \frac{\varphi + 4\pi}{3} + i \sin \frac{\varphi + 4\pi}{3})
\end{cases}
$$