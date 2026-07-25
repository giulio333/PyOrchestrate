# PyOrchestrate

Framework Python per orchestrare applicazioni multi-processo e multi-thread
composte da agenti. Il package è `PyOrchestrate/`, la documentazione `docs/`.

## Documentazione

La documentazione è un sito [Mintlify](https://mintlify.com) che vive in
`docs/`, nello stesso repo del codice. Il deploy è automatico via GitHub App a
ogni push su `main`: sul dashboard Mintlify il repo è configurato in modalità
monorepo con path `/docs`, quindi `docs.json` sta in `docs/docs.json` e tutti i
path nella navigation sono relativi a `docs/` (`learn/agents/index`, non
`docs/learn/agents/index`).

### Anteprima locale

```bash
rm -rf docs/.mint          # vedi nota sulla cache, qui sotto
cd docs
npx mint dev               # anteprima su http://localhost:3000
npx mint broken-links      # verifica dei link interni
```

Da lanciare sempre prima di pushare modifiche alla documentazione.

> **Se il tab API Reference è vuoto in locale, è la CLI vecchia, non la
> configurazione.** Serve `mint` >= 4.2.742: con la 4.2.507 il dev server non
> renderizzava la feature SDK reference — il tab compariva nella barra ma era
> vuoto e ogni `/api/...` rispondeva 404. Attenzione che `npx mint` preferisce
> il binario installato globalmente e **non** scarica da sé la versione nuova:
>
> ```bash
> npm install -g mint@latest    # poi verifica con: mint --version
> ```
>
> Non toccare `docs.json` per inseguire questo sintomo: la config è valida
> contro lo schema Mintlify (`mint validate` passa) e l'artifact viene letto
> nonostante `sdk-artifacts/` sia in `.mintignore`. Verificato entrambi.

> **`mint broken-links` segnala come rotti tutti i link `/api/...`: sono falsi
> positivi.** Il checker guarda solo le pagine con un file `.mdx` alle spalle e
> non conosce quelle generate dall'artifact SDK, quindi continua a riportarli
> anche con la CLI aggiornata e con il dev server che le serve a 200. Prima di
> "correggere" uno di quei link, provalo su `http://localhost:3000/api/...`.
> Gli slug corretti sono `/api/<nome-del-rst>`, come da `directory: "api"`.

> **Svuota sempre `docs/.mint` prima di avviare `mint dev`.** Il dev server vi
> tiene la cache della build precedente e non rilegge da zero tutto il
> contenuto — in particolare l'artifact Sphinx. Senza questo passaggio continui
> a vedere la versione vecchia e ti convinci che una modifica non abbia avuto
> effetto: è già successo sia con le pagine dell'API reference sia con gli slug
> `/api/...` dopo aver spostato i `.rst`. Se una modifica "non si vede",
> sospetta la cache prima di sospettare la configurazione.

### Regole di scrittura delle pagine

- **Le pagine sono `.mdx`, mai `.md`.** In `.md` Mintlify non renderizza i
  componenti: `<Tip>`, `<Warning>`, `<Card>` finirebbero come testo grezzo o
  sparirebbero del tutto, e il problema si nota solo a deploy fatto.
- **Ogni pagina ha `title` nel frontmatter.**
- **Link e immagini vanno in path assoluti dalla docs root, senza estensione:**
  `/learn/agents/index`, non `./index.mdx` né `../agents/index.md`.
- **Ogni pagina va inserita in `docs.json`**, altrimenti esiste ma è
  irraggiungibile dalla navigazione.
- I diagrammi esistono in coppia light/dark e si alternano con
  `className="block dark:hidden"` / `"hidden dark:block"`.

### API Reference

Il tab API Reference non è scritto a mano: è generato dalle docstring dei
sorgenti. Sphinx produce un artifact JSON che Mintlify consuma tramite la sua
feature *SDK reference* (`"sdk": {"format": "sphinx"}` in `docs.json`).

```bash
./scripts/build_api_reference.sh   # richiede sphinx, da eseguire con Python 3.13
```

> **Rigenera sempre con la versione di Python indicata da `.python-version`
> (3.13), la stessa del workflow.** Autodoc rende anche le firme ereditate
> dalla stdlib, che cambiano tra versioni: generando con un Python diverso
> l'artifact rimbalza avanti e indietro a ogni build — la firma di `enum.Enum`
> è cambiata nella 3.12 — e la CI produce commit di rigenerazione che non
> corrispondono a nessuna modifica delle docstring. Se il diff dell'artifact
> mostra cambiamenti nelle firme senza che tu abbia toccato le docstring,
> stai usando l'interprete sbagliato.

- `sphinx/conf.py` — configurazione (autodoc + napoleon, docstring Google)
- `sphinx/*.rst` — un file per sezione (`agent`, `orchestrator`, `plugins`,
  `utilities`, `base`, `cli`, `web`); **aggiungere qui i moduli nuovi** e
  inserirli nel toctree di `sphinx/index.rst`, altrimenti non compaiono nella
  reference
- Le pagine narrative **rimandano alla reference per firme e parametri**
  (`/api/plugins`, `/api/agent`, …) invece di ricopiarli: una firma scritta a
  mano in un `.mdx` è un secondo posto da cui può divergere dal codice, ed è il
  meccanismo che ha prodotto i metodi fantasma di `OMemory`.
- `docs/sdk-artifacts/` — output generato, committato perché Mintlify lo legge
  dal repo; escluso dalla pubblicazione via `docs/.mintignore`

I `.rst` stanno nella root di `sphinx/`, non in una sottocartella: Mintlify
somma il percorso interno a `directory` di `docs.json` e si otterrebbero URL
tipo `/api/api/agent`.

L'artifact si rigenera da solo su `main` quando cambiano i sorgenti Python,
tramite `.github/workflows/docs-api-reference.yml`. In locale va rigenerato a
mano dopo aver modificato le docstring.

Dopo ogni rigenerazione dell'artifact riavvia `mint dev` svuotando la cache,
come descritto nella nota sull'anteprima locale: altrimenti continui a vedere
la reference precedente.

## Test

```bash
uv sync --extra web      # crea .venv con dipendenze, extra web e gruppo dev
uv run pytest
```

**Questo repo non ha un devcontainer, e la regola globale «i test girano nel
devcontainer» qui non si applica.** `.devcontainer/devcontainer.json` è stato
rimosso: conteneva solo `tasks`, senza `image` né `build`, quindi non definiva
nessun ambiente e non era avviabile — chi lo seguiva alla lettera restava
bloccato. L'isolamento lo dà `uv`, che ricrea `.venv` da `uv.lock` senza
toccare l'interprete di sistema.

Non installare le dipendenze con `pip` sull'host: `uv run` lo fa da sé nella
venv del progetto.

### Dipendenze

- **Core** (`[project.dependencies]`): solo ciò che il package importa —
  `loguru`, `psutil`, `pyzmq`.
- **Extra `web`**: `fastapi`, `uvicorn`, `pydantic`, usati unicamente da
  `PyOrchestrate/web_interface/server.py`. Senza l'extra la web interface non
  è importabile: se aggiungi un test o un modulo che la tocca, ricordati che
  la CI installa `pip install -e ".[web]"`.
- **Gruppo `dev`** (`[dependency-groups]`, PEP 735): pytest, black, flake8,
  pylint, coverage, sphinx. `uv` lo installa di default, quindi `uv run pytest`
  basta. Ha sostituito `requirements-dev.txt`.
- `requirements.txt` è **generato**, non scritto a mano: rigeneralo con il
  comando annotato nella sua prima riga dopo ogni `uv lock`. È uno dei due file
  che Dependabot legge (l'altro è `uv.lock`), quindi un lock aggiornato ma un
  export vecchio lascia gli alert aperti.
