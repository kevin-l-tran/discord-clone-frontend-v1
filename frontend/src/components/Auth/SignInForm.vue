<script setup lang="ts">
import { BACKEND_URL } from '@/config';
import { nextTick, ref } from 'vue';

const username = ref('');
const password = ref('');

const usernameWarn = ref('');
const passwordWarn = ref('');

const usernameInput = ref(null);
const passwordInput = ref(null);

async function signin() {
    const payload = { username: username.value, password: password.value };

    usernameWarn.value = '';
    passwordWarn.value = '';

    let firstInvalid = null

    if (!username.value) {
        usernameWarn.value = "Please enter a username";
        if (!firstInvalid) firstInvalid = usernameInput;
    }
    if (!password.value) {
        passwordWarn.value = "Please enter a password";
        if (!firstInvalid) firstInvalid = passwordInput;
    }

    if (!firstInvalid) {
        try {
            const res = await fetch(BACKEND_URL + '/signin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await res.json();

            if (!res.ok) {
                passwordWarn.value = "Incorrect username or password."
                firstInvalid = passwordInput;
            } else {
                localStorage.setItem('access_token', data.access_token)
                window.location.href = '/groups/';
            }
        } catch (err) {
            console.error(err);
            alert('An unexpected network error occurred. Please try again later.');
            return;
        }
    }

    if (firstInvalid && firstInvalid.value) {
        await nextTick();
        (firstInvalid.value as HTMLInputElement).focus();
        return;
    }
}
</script>

<template>
    <form class="flex flex-col items-center justify-center" @submit.prevent="signin">
        <h1 class="text-3xl font-bold mb-4">Sign In</h1>
        <input type="username" placeholder="Username" id="username" v-model="username" ref="usernameInput"
            class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-400"
            :class="usernameWarn ? 'mb-1' : 'mb-4'" />
        <div v-if="usernameWarn" class="text-xs self-end text-red-500 mb-3">{{ usernameWarn }}</div>
        <input type="password" placeholder="Password" id="password" v-model="password" ref="passwordInput"
            class="w-full mb-2 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-400"
            :class="passwordWarn ? 'mb-1' : 'mb-4'" />
        <div v-if="passwordWarn" class="text-xs self-end text-red-500 mb-5">{{ passwordWarn }}</div>
        <a href="#" class="self-end text-sm text-gray-500 hover:underline mb-6">Forgot your password?</a>
        <button
            class="cursor-pointer w-full py-3 bg-indigo-600 text-white font-semibold rounded-md hover:bg-indigo-800 transition-colors duration-500">
            Sign In
        </button>
    </form>
</template>