<script setup lang="ts">
import { ref } from 'vue';

const email = ref('');
const username = ref('');
const password = ref('');

const emailWarn = ref('')
const usernameWarn = ref('')
const passwordWarn = ref('')
</script>

<template>
    <form class="flex flex-col items-center justify-center">
        <h2 class="text-3xl font-bold mb-4">Create Account</h2>
        <input type="email" placeholder="Email" id="email"
            class="w-full mb-4 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-400" />
        <div v-if="emailWarn" class="text-xs self-end text-red-500">{{ emailWarn }}</div>
        <input type="text" placeholder="Username" id="username"
            class="w-full mb-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-400" />
        <div class="text-xs self-end" :class="!usernameWarn ? 'text-gray-500' : 'text-red-500'">{{ !usernameWarn ?
            "Username must be over 3 characters long." : usernameWarn }}</div>
        <input type="password" placeholder="Password" id="password"
            class="w-full mb-1 mt-3 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-400" />
        <div class="text-xs self-end mb-5" :class="!passwordWarn ? 'text-gray-500' : 'text-red-500'">{{
            !passwordWarn ?
                "Password must be over 7 characters long." : passwordWarn }}</div>
        <button
            class="cursor-pointer w-full py-3 bg-indigo-600 text-white font-semibold rounded-md hover:bg-indigo-800 transition-colors duration-500">
            Sign Up
        </button>
    </form>
</template>