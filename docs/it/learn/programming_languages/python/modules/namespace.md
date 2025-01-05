# Namespace

In Python, il concetto di **namespace** è fondamentale per comprendere come le **variabili**, le **funzioni** e altri **oggetti** vengono gestiti e risolti all`interno di un programma. 

Un **namespace** è semplicemente uno spazio 



## Cos'è un namespace?

Un **namespace** è come uno **spazio** (dizionario) in cui i **nomi** (variabili, funzioni, classi, ecc.) vengono mappati ai rispettivi **oggetti**. 

::: tip Esempio

Qui vengono mostrati due Namespace ciascuno con i propri nomi.

``` mermaid
graph TD
    subgraph Namespace A
    A1["math.sqrt()"]
    A2["math.pi"]
    A3["math.factorial()"]
    end

    subgraph Namespace B
    B1["random.randint()"]
    B2["random.random()"]
    B3["random.choice()"]
    end
```
:::

Python mantiene più namespace attivi contemporaneamente:

- **Namespace globale**: contiene i nomi definiti a livello del **modulo**.
- **Namespace locale**: contiene i nomi definiti all`interno di una **funzione**.
- **Namespace integrato**: contiene i nomi delle funzioni e delle eccezioni **predefinite di Python**.

Ogni volta che accedi a una variabile o a una funzione, Python cerca il nome nel namespace attuale, partendo da quello **locale** e passando al namespace **globale** e poi a quello **integrato**, se necessario.

::: details 
``` mermaid
graph TD
    A["Nome richiesto"] --> B["Namespace Locale"]
    B -->|Trovato| C["Usa Nome"]
    B -->|Non trovato| D["Namespace Globale"]
    D -->|Trovato| C["Usa Nome"]    
    D -->|Non trovato| E["Namespace Integrato"]
    E -->|Trovato| C["Usa Nome"]
    E -->|Non trovato| F["Errore: NameError"]
```
:::

> Attenzione!
>   Quando Python importa il contenuto di un modulo, **tutti i nomi** definiti nel modulo diventano conosciuti, ma non entrano ancora nel **namespace**!
