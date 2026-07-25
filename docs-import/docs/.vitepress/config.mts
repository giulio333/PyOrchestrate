import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid';
import { enConfig } from './config/en';

// https://vitepress.dev/reference/site-config
export default withMermaid({
  base: '/PyOrchestrateDocumentation/',
  title: "PyOrchestrate",
  description: "PyOrchestrate Documentation",
  lastUpdated: true,
  head: [
    ['link', 
      { rel: 'icon', href: '/PyOrchestrateDocumentation/favicon.ico' }
    ]
  ],
  markdown: {
    math: true,
    image: {
      lazyLoading: true
    }
  },
  locales: {
    root: enConfig,
  },
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

    socialLinks: [
      { icon: 'github', link: 'https://github.com/giulio333/PyOrchestrateDocumentation' }
    ]
  },
  mermaid: {
    // refer https://mermaid.js.org/config/setup/modules/mermaidAPI.html#mermaidapi-configuration-defaults for options
  },
  // optionally set additional config for plugin itself with MermaidPluginConfig
  mermaidPlugin: {
    class: "mermaid my-class", // set additional css classes for parent container 
  },
})

