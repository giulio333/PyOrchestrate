export const itConfig = {
  label: 'Italiano',
  lang: 'it',
  link: '/it/',
  themeConfig: {
    logo: '/logo.png',
    outline: 'deep',
    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2024-present Evan You'
    },
    search: {
      provider: 'local',
    },
    editLink: {
      pattern: ({ filePath }) => {
        if (filePath.startsWith('packages/')) {
          return `https://github.com/giulio333/CodeInMind/edit/main/${filePath}`
        } else {
          return `https://github.com/giulio333/CodeInMind/edit/main/docs/${filePath}`
        }
      }
    },
    nav: [
      { text: 'Home', link: '/it/' },
    ],
    sidebar: {
      '/it/learn/engineering/mathematics/': [
        {
          text: 'Mathematics',
          link: '/it/learn/engineering/mathematics/',
          items: [
            {
              text: 'Insiemi',
              collapsed: true,
              items: [
                { text: 'Introduzione', link: '/it/learn/engineering/mathematics/1-insiemi/' },
                { text: 'Insiemi Numerici', link: '/it/learn/engineering/mathematics/1-insiemi/insiemi-numerici' },
                { text: 'Operazioni Tra Insiemi', link: '/it/learn/engineering/mathematics/1-insiemi/operazioni-insiemi' },
                { text: 'Logica Predicativa', link: '/it/learn/engineering/mathematics/1-insiemi/logica' },
              ]
            },
            {
              text: 'Campi',
              collapsed: true,
              items: [
                { text: 'Introduzione', link: '/it/learn/engineering/mathematics/campi/' },
              ]
            },
            {
              text: 'Numeri Reali',
              collapsed: true,
              items: [
                { text: 'Assioma di Continuità', link: '/it/learn/engineering/mathematics/numeri_reali/' },
                { text: 'Valore Assoluto', link: '/it/learn/engineering/mathematics/numeri_reali/valore_assoluto' },
                { text: 'Disuguaglianza Triangolare', link: '/it/learn/engineering/mathematics/numeri_reali/disuguaglianza_triangolare' },
                { text: 'Intervalli', link: '/it/learn/engineering/mathematics/numeri_reali/intervalli' },
              ]
            },
            {
              text: 'Numeri Complessi',
              collapsed: true,
              items: [
                { text: 'Introduzione', link: '/it/learn/engineering/mathematics/numeri_complessi/' },
                { text: 'Radici Complesse', link: '/it/learn/engineering/mathematics/numeri_complessi/radici_complesse' },
              ]
            },
            {
              text: 'Calcolo Differenziale',
              collapsed: true,
              items: [
                { text: 'Polinomio di Taylor', link: '/it/learn/engineering/mathematics/calcolo_differenziale/' },
                { text: 'Tabella Sviluppi', link: '/it/learn/engineering/mathematics/calcolo_differenziale//taylor_tabella' },
              ]
            },
            {
              text: 'Equazioni Differenziali',
              collapsed: true,
              items: [
                { text: 'Equazioni Differenziali Ordinarie', link: '/it/learn/engineering/mathematics/equazioni_differenziali/eq_diff_ordinarie' },
                { text: 'Equazioni Differenziali Lineari Primo Ordine', link: '/it/learn/engineering/mathematics/equazioni_differenziali/eq_lineari_primo_ordine' },
                { text: 'Equazioni del Primo Ordine a variabili separabili', link: '/it/learn/engineering/mathematics/equazioni_differenziali/eq_primo_ordine_variabili_separabili' },
                { text: 'Equazioni del Secondo Ordine', link: '/it/learn/engineering/mathematics/equazioni_differenziali/eq_lineari_secondo_ordine' },
              ]
            },
            {
              text: 'Integrali Impropri',
              collapsed: true,
              items: [
                { text: 'Integrabilità in senso Improprio', link: '/it/learn/engineering/mathematics/integrali_impropri/' },
              ]
            }
          ]
        }
      ],
      '/it/learn/programming_languages/python/': [
        {
          text: 'Python',
          items: [
            { text: 'Home', link: '/it/learn/programming_languages/python/' },
            { 
              text: 'Strutture Dati',
              collapsed: true,
              link: '/it/learn/programming_languages/python/strutture_dati/',
              items: [
                { text: 'Introduzione', link: '/it/learn/programming_languages/python/strutture_dati/' },
                { text: 'Sequenze', link: '/it/learn/programming_languages/python/strutture_dati/sequence' },
              ]
            },
            { 
              text: 'Moduli', 
              link: '/it/learn/programming_languages/python/modules/',
              collapsed: true,
              items: [
                { text: 'Introduzione', link: '/it/learn/programming_languages/python/modules/' },
                { text: 'Namespace', link: '/it/learn/programming_languages/python/modules/namespace' },
                { text: 'Import', link: '/it/learn/programming_languages/python/modules/import' },
                { 
                  text: 'Standard Modules', 
                  collapsed: true,
                  link: '/it/learn/programming_languages/python/modules/standard_modules/',
                  items: [
                    { text: 'Random', link: '/it/learn/programming_languages/python/modules/standard_modules/random' },
                    { text: 'Platform', link: '/it/learn/programming_languages/python/modules/standard_modules/platform' },
                  ]
                },
                { text: 'Package', link: '/it/learn/programming_languages/python/modules/package' },
                { text: 'PIP', link: '/it/learn/programming_languages/python/modules/pip' },
              ]
            },
            {
              text: 'Stringhe',
              collapsed: true,
              link: '/it/learn/programming_languages/python/strings/',
              items: [
                { text: 'Introduzione', link: '/it/learn/programming_languages/python/strings/' },
                { text: 'ASCII', link: '/it/learn/programming_languages/python/strings/ASCII' },
                { text: 'Unicode', link: '/it/learn/programming_languages/python/strings/unicode' },
                { text: 'Stringhe Python', link: '/it/learn/programming_languages/python/strings/python_strings' },
                { text: 'Metodi Stringhe', link: '/it/learn/programming_languages/python/strings/strings_method' },
              ]
            },
            {
              text: 'Eccezioni',
              collapsed: true,
              link: '/it/learn/programming_languages/python/exceptions/',
              items: [
                { text: 'Introduzione', link: '/it/learn/programming_languages/python/exceptions/' },
                { text: 'BaseException', link: '/it/learn/programming_languages/python/exceptions/BaseException' },
             
              ]
            },
            {
              text: 'OOP',
              collapsed: true,
              link: '/it/learn/programming_languages/python/oop/',
              items: [
                { text: 'Introduzione', link: '/it/learn/programming_languages/python/oop/' },
                { text: 'Esempi', link: '/it/learn/programming_languages/python/oop/esempi' },
                { text: 'Variabili di Istanza', link: '/it/learn/programming_languages/python/oop/variabili-di-istanza' },
                { text: 'Variabili di Classe', link: '/it/learn/programming_languages/python/oop/variabili-di-classe' },
                { text: 'hasattr', link: '/it/learn/programming_languages/python/oop/hasattr' },
                { text: 'Metodi', link: '/it/learn/programming_languages/python/oop/metodi' },
             
              ]
            },
          ]
        }
      ],
      '/it/learn/tools/github/': [
        {
          text: 'GitHub',
          items: [
            { text: 'Home', link: '/learn/tools/github/.' },
            { text: 'Introduzione', link: '/learn/tools/github/introduzione' },
            { text: 'Workflow' , link: '/learn/tools/github/workflow' },
          ]
        }
      ],
      'it/learn/tools/vscode/': [
        {
          text: 'Visual Studio Code',
          items: [
            { text: 'Home', link: './' },
            { text: 'Task', link: './task' },
          ]
        }
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/giulio333/CodeInMind' }
    ]
  }
};
