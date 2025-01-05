import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid';
import { itConfig } from './config/it';
import { enConfig } from './config/en';

// https://vitepress.dev/reference/site-config
export default withMermaid({
  base: '/CodeInMind/',
  title: "Code In Mind",
  description: "Code In Mind",
  lastUpdated: true,
  head: [
    ['link', 
      { rel: 'icon', href: '/CodeInMind/favicon.ico' }
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
    it: itConfig
  },
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

    socialLinks: [
      { icon: 'github', link: 'https://github.com/giulio333/CodeInMind' }
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

