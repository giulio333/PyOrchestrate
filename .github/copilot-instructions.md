# GitHub Copilot Instructions

## Aggiornamento della Documentazione

Quando si richiede un aggiornamento o l'aggiunta di nuovi file di documentazione, è **necessario** aggiornare anche il file di configurazione della navigazione:

### File da Aggiornare

- **`docs/.vitepress/config/en.ts`**: Contiene la configurazione della sidebar e della navigazione per la documentazione in inglese.

### Cosa Aggiornare

Quando aggiungi o modifichi file di documentazione, assicurati di:

1. **Aggiungere voci alla sidebar**: Se crei un nuovo file `.md`, aggiungi il corrispondente link nella sezione appropriata della `sidebar`.

2. **Mantenere la struttura coerente**: Rispetta la gerarchia esistente delle sezioni (`/learn`, `/cli`, `/examples`, `/advanced`).

3. **Aggiornare i percorsi**: Verifica che i percorsi dei link corrispondano alla posizione effettiva dei file nella cartella `docs/`.

4. **Considerare la navigazione**: Se necessario, aggiorna anche l'array `nav` per le voci del menu principale.

### Esempio

Se aggiungi un nuovo file `docs/learn/agents/custom-agent.md`, devi aggiungere:

```typescript
{
  text: 'Getting Started',
  items: [
    { text: 'Agent', link: '/learn/agents/' },
    { text: 'Custom Agent', link: '/learn/agents/custom-agent' }, // NUOVO
    { text: 'Orchestrator', link: '/learn/orchestrator/' },
    // ...
  ]
}
```

### Verifica

Dopo aver aggiornato la configurazione:

1. Avvia il server di sviluppo: `npm run docs:dev`
2. Verifica che i nuovi link appaiano nella sidebar
3. Controlla che i link funzionino correttamente

---

**Nota**: Questo file serve come riferimento per GitHub Copilot per garantire che la struttura della documentazione rimanga consistente e navigabile.
