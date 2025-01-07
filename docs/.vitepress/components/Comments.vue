<script setup lang="ts">
import { useData } from 'vitepress'

const { title } = useData()
</script>

<template>
  <div :key="title" class="giscus">
    <component
      :is="'script'"
      src="https://giscus.app/client.js"
      data-repo="giulio333/PyOrchestrateDocumentation"
      data-repo-id="R_kgDONmOVpQ"
      data-category="General"
      data-category-id="DIC_kwDONmOVpc4Cl09y"
      data-mapping="pathname"
      data-strict="0"
      data-reactions-enabled="1"
      data-emit-metadata="0"
      data-input-position="bottom"
      data-theme="preferred_color_scheme"
      data-lang="it"
      crossorigin="anonymous"
      async
    />
  </div>
</template>