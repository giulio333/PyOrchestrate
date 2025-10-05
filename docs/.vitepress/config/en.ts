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
      { text: 'Learn', link: '/learn/introduction/' },
      { text: 'CLI', link: '/cli/' },
      { text: 'Examples', link: '/examples/' },
      { text: 'Advanced', link: '/advanced/' },
    ],
    sidebar: {
      '/learn': [
        {
          text: 'Learn',
          items: [
            {
              text: 'Introduction', items: [
                { text: 'General', link: '/learn/introduction/index.md' },
                { text: 'How Orchestration Works', link: '/learn/introduction/orchestrator/' },
                { text: 'How Agents Works', link: '/learn/introduction/agents/' },
                { text: 'Orchestrator API', link: '/learn/introduction/orchestrator_api/' },
              ]
            },
            {
              text: 'Getting Started',
              items: [
                { text: 'Agent', link: '/learn/agents/' },
                { text: 'Orchestrator', link: '/learn/orchestrator/' },
                { text: 'Config and Validation', link: '/learn/config_and_validation' },
              ]
            },
            {
              text: 'Utilities',
              items: [
                { text: 'Event Manager', link: '/learn/utilities/event-manager' },
                { text: 'Plugin Manager', link: '/learn/utilities/plugin-manager' },
                { text: 'Message Channel', link: '/learn/utilities/message-channel' },
              ]
            },
            {
              text: 'Built-in Agents',
              collapsed: true,
              items: [
                { text: 'BaseAgent', link: '/learn/agents/built-in-agents/baseagent' },
                { text: 'LoopingAgent', link: '/learn/agents/built-in-agents/loopingagent' },
                { text: 'PeriodicAgent', link: '/learn/agents/built-in-agents/periodicagent' },
              ]
            },
            {
              text: 'Built-in Orchestrator',
              collapsed: true,
              items: [
                { text: 'BaseOrchestrator', link: '/learn/orchestrator/built-in-orchestrator/baseorchestrator' },
              ]
            },
            {
              text: 'Plugins',
              collapsed: true,
              items: [
                {
                  text: 'Communication',
                  link: '/learn/agents/plugins/communication-plugins',
                  items: [
                    { text: 'ZeroMQPubSub', link: '/learn/agents/plugins/zeromqpubsub/zeromqpubsub' },
                    { text: 'ZeroMQReqRep', link: '/learn/agents/plugins/zeromqreqrep/zeromqreqrep' },
                  ]
                },
              ]
            }
          ]
        }
      ],
      '/cli': [
        {
          text: 'CLI Reference',
          items: [
            { text: 'Overview', link: '/cli/' },
            { text: 'Runtime Commands', link: '/cli/runtime-commands' },
            { text: 'Configuration', link: '/cli/configuration' },
            { text: 'Examples', link: '/cli/examples' },
          ]
        }
      ],
      '/examples/basic': [
        {
          text: 'Basic Examples',
          items: [
            { text: 'Project Initialization', link: '/examples/basic/project-initialization.md' },
            { text: 'Standalone Agent', link: '/examples/basic/standalone-agent.md' },
          ]
        }
      ],
      '/examples/advanced': [
        {
          text: 'Advanced Examples',
          items: [
            { text: 'Heartbeat Plugin', link: '/examples/advanced/heartbeat-plugin.md' },
            { text: 'Multiple Standalone Agents', link: '/examples/advanced/multiple-agents.md' },
            { text: 'Validation Policy', link: '/examples/advanced/validation.md' },
          ]
        }
      ],
      '/examples/cli': [
        {
          text: 'CLI Examples',
          items: [
            { text: 'Runtime Control', link: '/examples/cli/runtime-control.md' },
          ]
        }
      ],
      '/examples/events': [
        {
          text: 'Events Examples',
          items: [
            { text: 'Agent State Event', link: '/examples/events/agent-state-events.md' },
          ]
        }
      ],
      '/advanced': [
        {
          text: 'Advanced',
          items: [
            {
              text: 'Architecture',
              collapsed: false,
              items: [
                { text: 'MessageChannel', link: '/advanced/architecture/message-channel' },
              ]
            },
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
