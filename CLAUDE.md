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

L'anteprima rende il sito come sarà online, tab API Reference compreso. Da
lanciare sempre prima di pushare modifiche alla documentazione.

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
./scripts/build_api_reference.sh   # richiede sphinx
```

- `sphinx/conf.py` — configurazione (autodoc + napoleon, docstring Google)
- `sphinx/*.rst` — un file per sezione; **aggiungere qui i moduli nuovi**,
  altrimenti non compaiono nella reference
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

Vedi le istruzioni globali: i test girano nel devcontainer, non sull'host.
