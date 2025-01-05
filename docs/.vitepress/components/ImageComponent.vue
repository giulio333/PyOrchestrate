<template>
    <div class="image-container">
      <img :src="src" :alt="alt" :style="{ width: width + 'px' }" />
    </div>
  </template>
  
  <script setup>
  defineProps({
    src: {
      type: String,
      required: true
    },
    alt: {
      type: String,
      default: 'Image'
    },
    width: {
      type: Number,
      required: true
    }
  })
  </script>
  
  <style scoped>
  .image-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 20px 0;
  }
  
  img {
    max-width: 100%;
    height: auto;
    border-radius: 5px;
  }
  </style>