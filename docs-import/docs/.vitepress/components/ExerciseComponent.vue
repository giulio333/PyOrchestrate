<template>
  <div>
    <h3 class="exercise-title">{{ title }}</h3>
    <div class="exercise-component">
      <p>{{ description }}</p>
      <button @click="showAnswer = !showAnswer" class="check-button">Check</button>
      <p v-if="showAnswer" class="answer">{{ answer }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  answer: {
    type: String,
    required: true
  }
})

const showAnswer = ref(false)
</script>

<style scoped>
.exercise-title {
  font-size: 20px;
  color: var(--vp-c-brand-1);
  margin-bottom: 10px;
}

.exercise-component {
  background-color: var(--vp-c-default-4);
  color: var(--vp-c-default-hard);
  padding: 10px;
  border: 1px solid var(--vp-c-default-2);
  border-radius: 5px;
  margin-bottom: 15px;
}

.check-button {
  background-color: var(--vp-c-brand-2);
  color: white;
  padding: 5px 10px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 5px;
}

.check-button:hover {
  background-color: var(--vp-c-brand-1);
}

.answer {
  margin-top: 10px;
  font-style: italic;
  color: var(--vp-c-default-hard);
}

.dark .exercise-component {
  background-color: var(--vp-c-default-4);
  color: var(--vp-c-default-hard);
  border-color: var(--vp-c-default-3);
}

.dark .check-button {
  background-color: var(--vp-c-brand-1);
}

.dark .check-button:hover {
  background-color: var(--vp-c-brand-2);
}

.dark .answer {
  color: var(--vp-c-brand-1);
}
</style>