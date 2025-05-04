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
      { text: 'Examples', link: '/examples/' },
      { text: 'Advanced', link: '/advanced/' },
    ],
    sidebar: {
      '/learn': [
        {
          text: 'Learn',
          items: [
            {
              text: 'Core Concepts',
              items: [
                { text: 'Orchestrator', link: '/learn/core/orchestrator/' },
                { text: 'Agent', link: '/learn/core/agents/' },
        
              ]
            },
            {
              text: 'Getting Started',
              items: [
                { text: 'Agent', link: '/learn/agents/' },
                { text: 'Orchestrator', link: '/learn/orchestrator/' },
              ]
            },
            {
              text: 'Utilities',
              items: [
                { text: 'Event Manager', link: '/learn/utilities/event-manager' },
              ]
            },
            {
              text: 'Built-in Agents',
              collapsed: true,
              items: [
                { text: 'BaseAgent', link: '/learn/agents/built-in-agents/baseagent' },
                { text: 'LoopingAgent', link: '/learn/agents/built-in-agents/loopingagent' },
              ]
            },
            {
              text: 'Plugins',
              collapsed: true,
              items:[
                { 
                  text: 'Communication', 
                  link: '/learn/agents/plugins/communication-plugins', 
                  items:[
                    { text: 'ZeroMQPubSub', link: '/learn/agents/plugins/zeromqpubsub/zeromqpubsub' },
                    { text: 'ZeroMQReqRep', link: '/learn/agents/plugins/zeromqreqrep/zeromqreqrep' },
                  ]
                },
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
