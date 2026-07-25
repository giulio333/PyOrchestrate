<template>
  <div class="note">
    <h3 class="note-title">{{ title }}</h3>
    <p class="note-text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  text: {
    type: String,
    required: true
  }
})
</script>

<style scoped>
.note {
  background-color: #fdf6e3;
  border-left: 5px solid #ff9800;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin: 20px 0;
}

.note-title {
  margin: 0;
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.note-text {
  margin: 10px 0 0;
  font-size: 16px;
  color: #555;
}
</style>