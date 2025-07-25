<script setup lang="ts">
import SignInForm from './Auth/SignInForm.vue'
import SignUpForm from './Auth/SignUpForm.vue'
import { ref, defineEmits } from 'vue'

const emit = defineEmits(['close'])

const isSignUp = ref(false)

function toggle() {
  isSignUp.value = !isSignUp.value
}
</script>

<template>
  <Transition enter-from-class="opacity-0 scale-75" enter-to-class="opacity-100 scale-100"
    enter-active-class="transition duration-200" leave-from-class="opacity-100" leave-to-class="opacity-0"
    leave-active-class="transition duration-200 ">
    <!-- backdrop -->
    <div class="fixed inset-0 flex items-center justify-center z-50" @click="$emit('close')">
      <!-- modal box -->
      <div class="relative w-[720px] h-[480px] bg-white rounded-xl overflow-hidden shadow-xl" @click.stop>

        <!-- static forms side-by-side (full modal) -->
        <div class="absolute inset-0 flex">
          <SignInForm class="w-1/2 h-full p-8"></SignInForm>

          <SignUpForm class="w-1/2 h-full p-8"></SignUpForm>
        </div>

        <!-- overlay panel (slides left/right over forms) -->
        <div
          class="absolute top-0 right-0 w-1/2 h-full flex flex-col items-center justify-center px-8 text-white bg-gradient-to-r from-indigo-950 to-indigo-900 transition-transform duration-700 z-10"
          :class="isSignUp ? '-translate-x-full' : 'translate-x-0'">
          <h2 class="text-3xl font-bold mb-2">
            {{ isSignUp ? 'Welcome Back!' : 'Hello, Friend!' }}
          </h2>
          <p class="text-center mb-6">
            {{ isSignUp
              ? 'To keep connected with us, login with your personal info!'
              : 'Enter your personal details and start your journey with us!' }}
          </p>
          <button @click="toggle"
            class="cursor-pointer mt-2 px-6 py-2 border-2 border-white rounded-full uppercase text-sm font-medium hover:bg-white hover:text-sky-500 transition-colors duration-500">
            {{ isSignUp ? 'Sign In' : 'Sign Up' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>
