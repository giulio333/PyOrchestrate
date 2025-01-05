# Unicode

La soluzione delle [code page](ASCII.md#code-page) è stata un primo passo per risolvere il problema della rappresentazione di caratteri di lingue diverse. 
Tuttavia, il numero di caratteri che possono essere rappresentati è limitato. 

Per risolvere questo problema, è stato sviluppato **Unicode**.

**Unicode** è un sistema di codifica di caratteri che assegna un numero univoco per più di un milione di [code point](ASCII#code-points).

::: tip Attenzione
Lo standard **Unicode** non specifica come codificare i caratteri in binario. Si limita a nominare i caratteri assegnando loro un numero univoco e a raggrupparli in blocchi logici chiamati **piani**. 

Esistono diversi standard che descrivono come codificare i caratteri **Unicode** in binario. I più comuni sono **UTF-8**, **UTF-16** e **UTF-32**.
:::

## USC-4

Il nome deriva da **Universal Character Set** e **4** byte, che è la dimensione di ogni carattere.

Utilizza quindi **32 bit** per memorizzare ogni carattere, e il codice di ogni carattere è uguale al suo **code point**.

::: tip Nota
Un file può iniziare con un **BOM** (Byte Order Mark) per indicare l'ordine dei byte.
:::

## UTF-8

Il nome deriva da **Unicode Transformation Format** e **8** bit, che è la dimensione di ogni carattere.

Utilizza il numero di bit necessario per rappresentare ciascuno **code point**.

::: tip Nota
Python supporta completamente **Unicode** e **UTF-8**. Ciò significa che è completamente internazionalizzato.