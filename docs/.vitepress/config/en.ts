export const enConfig = {
  label: 'English',
  lang: 'en',
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
      { text: 'Home', link: '/' },
    ],
    sidebar: {
      '/learn/engineering/mathematics/': [
        {
          text: 'Mathematics',
          items: [
            {
              text: 'Differential Calculus',
              collapsed: true,
              items: [
                { text: 'Taylor Polynomial', link: '/learn/engineering/mathematics/calcolo_differenziale/' },
                { text: 'Taylor Table', link: '/learn/engineering/mathematics/calcolo_differenziale/taylor_tabella' },
              ]
            },
            {
              text: 'Differential Equations',
              collapsed: true,
              items: [
                { text: 'Ordinary Differential Equations', link: '/learn/engineering/mathematics/equazioni_differenziali/eq_diff_ordinarie' },
                { text: 'First Order Linear Differential Equations', link: '/learn/engineering/mathematics/equazioni_differenziali/eq_lineari_primo_ordine' },
                { text: 'First Order Separable Differential Equations', link: '/learn/engineering/mathematics/equazioni_differenziali/eq_primo_ordine_variabili_separabili' },
                { text: 'Second Order Differential Equations', link: '/learn/engineering/mathematics/equazioni_differenziali/eq_lineari_secondo_ordine' },
              ]
            },
            {
              text: 'Improper Integrals',
              collapsed: true,
              items: [
                { text: 'Improper Integrability', link: '/learn/engineering/mathematics/integrali_impropri/' },
              ]
            }
          ]
        }
      ],
      '/learn/programming_languages/': [
        {
          text: 'Programming Languages',
          items: [
            {
              text: 'Python',
              items: [
                { text: 'Home', link: '/learn/programming_languages/python/' },
                { 
                  text: 'Data Structures',
                  collapsed: true,
                  link: '/learn/programming_languages/python/strutture_dati/',
                  items: [
                    { text: 'Introduction', link: '/learn/programming_languages/python/strutture_dati/' },
                    { text: 'Sequences', link: '/learn/programming_languages/python/strutture_dati/sequence' },
                  ]
                },
                { 
                  text: 'Modules', 
                  link: '/learn/programming_languages/python/modules/',
                  collapsed: true,
                  items: [
                    { text: 'Introduction', link: '/learn/programming_languages/python/modules/' },
                    { text: 'Namespace', link: '/learn/programming_languages/python/modules/namespace' },
                    { text: 'Import', link: '/learn/programming_languages/python/modules/import' },
                    { 
                      text: 'Standard Modules', 
                      collapsed: true,
                      link: '/learn/programming_languages/python/modules/standard_modules/',
                      items: [
                        { text: 'Random', link: '/learn/programming_languages/python/modules/standard_modules/random' },
                        { text: 'Platform', link: '/learn/programming_languages/python/modules/standard_modules/platform' },
                      ]
                    },
                    { text: 'Package', link: '/learn/programming_languages/python/modules/package' },
                    { text: 'PIP', link: '/learn/programming_languages/python/modules/pip' },
                  ]
                },
                {
                  text: 'Strings',
                  collapsed: true,
                  link: '/learn/programming_languages/python/strings/',
                  items: [
                    { text: 'Introduction', link: '/learn/programming_languages/python/strings/' },
                    { text: 'ASCII', link: '/learn/programming_languages/python/strings/ASCII' },
                    { text: 'Unicode', link: '/learn/programming_languages/python/strings/unicode' },
                    { text: 'Python Strings', link: '/learn/programming_languages/python/strings/python_strings' },
                    { text: 'String Methods', link: '/learn/programming_languages/python/strings/strings_method' },
                  ]
                },
                {
                  text: 'Exceptions',
                  collapsed: true,
                  link: '/learn/programming_languages/python/exceptions/',
                  items: [
                    { text: 'Introduction', link: '/learn/programming_languages/python/exceptions/' },
                    { text: 'BaseException', link: '/learn/programming_languages/python/exceptions/BaseException' },
                 
                  ]
                },
                {
                  text: 'OOP',
                  collapsed: true,
                  link: '/learn/programming_languages/python/oop/',
                  items: [
                    { text: 'Introduction', link: '/learn/programming_languages/python/oop/' },
                    { text: 'Examples', link: '/learn/programming_languages/python/oop/esempi' },
                    { text: 'Instance Variables', link: '/learn/programming_languages/python/oop/variabili-di-istanza' },
                    { text: 'Class Variables', link: '/learn/programming_languages/python/oop/variabili-di-classe' },
                    { text: 'hasattr', link: '/learn/programming_languages/python/oop/hasattr' },
                    { text: 'Methods', link: '/learn/programming_languages/python/oop/metodi' },
                 
                  ]
                },
              ]
            }
          ]
        }
      ],
      '/learn/tools/': [
        {
          text: 'Tools',
          items: [
            {
              text: 'GitHub',
              items: [
                { text: 'Home', link: '/learn/tools/github/.' },
                { text: 'Introduction', link: '/learn/tools/github/introduzione' },
                { text: 'Workflow' , link: '/learn/tools/github/workflow' },
              ]
            },
            {
              text: 'Visual Studio Code',
              items: [
                { text: 'Home', link: './' },
                { text: 'Task', link: './task' },
              ]
            }
          ]
        }
      ],
      '/learn/frameworks/': [
        {
          text: 'Frameworks',
          items: [
            {
              text: 'GraphQL',
              items: [
                { text: 'Home', link: '/learn/frameworks/GraphQL/' },
                { text: 'Introduction', link: '/learn/frameworks/GraphQL/introduction' },
              ]
            },
            {
              text: 'Django',
              items: [
                { text: 'Home', link: '/learn/frameworks/Django/' },
              ]
            }
          ]
        }
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/giulio333/CodeInMind' }
    ]
  }
};
