export const enConfig = {
  label: 'English',
  lang: 'en',
  themeConfig: {
    logo: '/logo.png',
    outline: 'deep',
    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2025-present Evan You'
    },
    search: {
      provider: 'local',
    },
    editLink: {
      pattern: ({ filePath }) => {
        if (filePath.startsWith('packages/')) {
          return `https://github.com/giulio333/PyOrchestrateDocumentation/edit/main/${filePath}`
        } else {
          return `https://github.com/giulio333/PyOrchestrateDocumentation/edit/main/docs/${filePath}`
        }
      }
    },
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Learn', link: '/learn/' },
      { text: 'Advanced', link: '/advanced/' },
    ],
    sidebar: {
      '/learn/agents': [
        {
          text: 'Explore Agents',
          items: [
            {
              text: 'The Basics',
              items: [
                { text: 'Agent', link: '/learn/agents/' },
              ]
            },
            {
              text: 'Built-in Agents',
              collapsed: true,
              items: [
                { text: 'BaseAgent', link: '/learn/agents/built-in-agents/baseagent' },
                { text: 'LoopingAgent', link: '/learn/agents/built-in-agents/loopingagent' },
              ]
            }
          ]
        }
      ],
      '/advanced/built-in-agents': [
        {
          text: 'Advanced Agents',
          items: [
            {
              text: 'Built-in Agents',
              collapsed: false,
              items: [
                { text: 'BaseAgent', link: '/advanced/built-in-agents/baseagent' },
                { text: 'LoopingAgent', link: '/advanced/built-in-agents/loopingagent' },
              ]
            }
          ]
        }
      ],
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/giulio333/PyOrchestrateDocumentation' }
    ]
  }
};
