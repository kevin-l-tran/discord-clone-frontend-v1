<script setup lang="ts">
import AuthModal from '@/components/AuthModal.vue'
import { ref } from 'vue';

const showAuth = ref(false);
</script>

<template>
  <div
    class="h-screen w-full flex flex-col justify-center items-center bg-center bg-cover text-center text-white bg-gray-800 bg-[url(../assets/background.avif)]">
    <!-- logo -->
    <div class="mb-6">
      <svg class="w-12 h-12" viewBox="0 0 24 24"><!-- … --></svg>
    </div>

    <!-- title / subtitle -->
    <div class="border-t-1 border-b-1 py-8">
      <h1 class="text-6xl font-bold tracking-widest">DIMENSION</h1>
      <p class="mt-4 max-w-2xl leading-relaxed text-lg">
        A fully responsive site template designed by HTML5 UP and
        released for free under the Creative Commons license.
      </p>
    </div>

    <!-- modal popups -->
    <nav class="mt-18 flex w-full max-w-md mx-auto">
      <button class="px-4 py-2 border border-white/70 hover:bg-white/10 transition flex-1 bg-blue-400 cursor-pointer" @click="showAuth = true">Get Started</button>
      <button class="px-4 py-2 border border-white/70 hover:bg-white/10 transition flex-1 cursor-pointer">About</button>
    </nav>

    <Teleport to="body">
      <AuthModal v-show="showAuth" @close="showAuth = false"></AuthModal>
    </Teleport>
  </div>
</template>