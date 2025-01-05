# Stringhe

In Python, i caratteri sono memorizzati come numeri.

Ogni carattere corrisponde a un numero intero, chiamato **codice Unicode**, o **code point**.

Alcuni di questi caratteri vengono chiamati **whitespace characters**, altri **control characters**.

## Witespace characters

I **whitespace characters** sono caratteri che non sono visibili, ma che vengono utilizzati per formattare il testo.

I principali **whitespace characters** sono:

- ` ` (spazio)
- `\t` (tab)
- `\n` (newline)
- `\r` (carriage return)
- `\f` (form feed)
- `\v` (vertical tab)

## Control characters

I **control characters** sono caratteri che hanno funzioni di controllo.

I principali **control characters** sono:

- `\b` (backspace)
- `\a` (bell)
- `\e` (escape)
- `\0` (null)

----

Esiste uno **standard** universale ampiamente accettato, implementato da quasi tutti i computer e sistemi operativi, chiamato **ASCII**.

## ASCII

L'**American Standard Code for Information Interchange** (**ASCII**) è un codice standard per la rappresentazione di testo in computer.

Il codice offre spazio per 256 caratteri diversi, qui potete vedere la tabella dei primi 128 caratteri.

| Decimale | Simbolo | Descrizione         |
|----------|---------|---------------------|
| 0        | NUL     | Null character      |
| 1        | SOH     | Start of Heading    |
| 2        | STX     | Start of Text       |
| 3        | ETX     | End of Text         |
| 4        | EOT     | End of Transmission |
| 5        | ENQ     | Enquiry             |
| 6        | ACK     | Acknowledgment      |
| 7        | BEL     | Bell                |
| 8        | BS      | Backspace           |
| 9        | TAB     | Horizontal Tab      |
| 10       | LF      | Line Feed           |
| 11       | VT      | Vertical Tab        |
| 12       | FF      | Form Feed           |
| 13       | CR      | Carriage Return     |
| 14       | SO      | Shift Out           |
| 15       | SI      | Shift In            |
| 16       | DLE     | Data Link Escape    |
| 17       | DC1     | Device Control 1    |
| 18       | DC2     | Device Control 2    |
| 19       | DC3     | Device Control 3    |
| 20       | DC4     | Device Control 4    |
| 21       | NAK     | Negative Ack.       |
| 22       | SYN     | Synchronous Idle    |
| 23       | ETB     | End of Block        |
| 24       | CAN     | Cancel              |
| 25       | EM      | End of Medium       |
| 26       | SUB     | Substitute          |
| 27       | ESC     | Escape              |
| 28       | FS      | File Separator      |
| 29       | GS      | Group Separator     |
| 30       | RS      | Record Separator    |
| 31       | US      | Unit Separator      |
| 32       | (space) | Space               |
| 33       | !       | Exclamation mark    |
| 34       | "       | Quotation mark      |
| 35       | #       | Number sign         |
| 36       | $       | Dollar sign         |
| 37       | %       | Percent sign        |
| 38       | &       | Ampersand           |
| 39       | '       | Apostrophe          |
| 40       | (       | Left parenthesis    |
| 41       | )       | Right parenthesis   |
| 42       | *       | Asterisk            |
| 43       | +       | Plus sign           |
| 44       | ,       | Comma               |
| 45       | -       | Hyphen/minus        |
| 46       | .       | Period              |
| 47       | /       | Slash               |
| 48       | 0       | Digit 0             |
| 49       | 1       | Digit 1             |
| 50       | 2       | Digit 2             |
| 51       | 3       | Digit 3             |
| 52       | 4       | Digit 4             |
| 53       | 5       | Digit 5             |
| 54       | 6       | Digit 6             |
| 55       | 7       | Digit 7             |
| 56       | 8       | Digit 8             |
| 57       | 9       | Digit 9             |
| 58       | :       | Colon               |
| 59       | ;       | Semicolon           |
| 60       | <       | Less-than sign      |
| 61       | =       | Equals sign         |
| 62       | >       | Greater-than sign   |
| 63       | ?       | Question mark       |
| 64       | @       | At sign             |
| 65       | A       | Uppercase A         |
| 66       | B       | Uppercase B         |
| 67       | C       | Uppercase C         |
| 68       | D       | Uppercase D         |
| 69       | E       | Uppercase E         |
| 70       | F       | Uppercase F         |
| 71       | G       | Uppercase G         |
| 72       | H       | Uppercase H         |
| 73       | I       | Uppercase I         |
| 74       | J       | Uppercase J         |
| 75       | K       | Uppercase K         |
| 76       | L       | Uppercase L         |
| 77       | M       | Uppercase M         |
| 78       | N       | Uppercase N         |
| 79       | O       | Uppercase O         |
| 80       | P       | Uppercase P         |
| 81       | Q       | Uppercase Q         |
| 82       | R       | Uppercase R         |
| 83       | S       | Uppercase S         |
| 84       | T       | Uppercase T         |
| 85       | U       | Uppercase U         |
| 86       | V       | Uppercase V         |
| 87       | W       | Uppercase W         |
| 88       | X       | Uppercase X         |
| 89       | Y       | Uppercase Y         |
| 90       | Z       | Uppercase Z         |
| 91       | [       | Left square bracket |
| 92       | \       | Backslash           |
| 93       | ]       | Right square bracket|
| 94       | ^       | Caret               |
| 95       | _       | Underscore          |
| 96       | `       | Grave accent        |
| 97       | a       | Lowercase a         |
| 98       | b       | Lowercase b         |
| 99       | c       | Lowercase c         |
| 100      | d       | Lowercase d         |
| 101      | e       | Lowercase e         |
| 102      | f       | Lowercase f         |
| 103      | g       | Lowercase g         |
| 104      | h       | Lowercase h         |
| 105      | i       | Lowercase i         |
| 106      | j       | Lowercase j         |
| 107      | k       | Lowercase k         |
| 108      | l       | Lowercase l         |
| 109      | m       | Lowercase m         |
| 110      | n       | Lowercase n         |
| 111      | o       | Lowercase o         |
| 112      | p       | Lowercase p         |
| 113      | q       | Lowercase q         |
| 114      | r       | Lowercase r         |
| 115      | s       | Lowercase s         |
| 116      | t       | Lowercase t         |
| 117      | u       | Lowercase u         |
| 118      | v       | Lowercase v         |
| 119      | w       | Lowercase w         |
| 120      | x       | Lowercase x         |
| 121      | y       | Lowercase y         |
| 122      | z       | Lowercase z         |
| 123      | {       | Left curly brace    |
| 124      | |       | Vertical bar        |
| 125      | }       | Right curly brace   |
| 126      | ~       | Tilde               |
| 127      | DEL     | Delete              |

## I18N

**Internationalization** (**I18N**) è il processo di progettazione e sviluppo di un prodotto software che può essere facilmente adattato a diverse lingue e regioni senza modifiche tecniche.

Notare che **I18N** è un acronimo, formato dalla lettera **I**, seguita da 18 lettere, e dalla lettera **N**.

## Code points

Un **code point** è un numero intero che rappresenta un carattere.

::: tip Nota
Un **code point** non è la rappresentazione binaria di un carattere, ma un numero intero che rappresenta un carattere.
:::

Possiamo dire che **ASCII** standard è formato da 128 **code points**.

## Code Page

Una **code page** è una tabella che associa caratteri specifici di una lingua ai relativi **code point**.

Esistono diverse pagine di codice per l'Europa occidentale e orientale, per il greco, il turco, il cirillico, l'arabo, l'ebraico, ecc.

Di conseguenza, per determinate il significato di un **code point**, è necessario conoscere la **code page**.