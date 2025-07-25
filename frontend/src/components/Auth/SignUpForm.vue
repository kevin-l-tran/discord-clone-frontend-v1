<script setup lang="ts">
import { BACKEND_URL } from '@/config';
import { nextTick, ref } from 'vue';

const email = ref('');
const username = ref('');
const password = ref('');

const emailWarn = ref('');
const usernameWarn = ref('');
const passwordWarn = ref('');

const emailInput = ref(null);
const usernameInput = ref(null);
const passwordInput = ref(null);

async function signin() {
    const payload = { email: email.value, username: username.value, password: password.value };

    emailWarn.value = '';
    usernameWarn.value = '';
    passwordWarn.value = '';

    let firstInvalid = null

    if (!email.value) {
        emailWarn.value = "Please enter an email";
        firstInvalid = emailInput;
    }
    if (!username.value) {
        usernameWarn.value = "Please enter a username";
        if (!firstInvalid) firstInvalid = usernameInput;
    } else if (username.value.length < 4) {
        usernameWarn.value = "Your username must be over 3 characters long";
        if (!firstInvalid) firstInvalid = usernameInput;
    }
    if (!password.value) {
        passwordWarn.value = "Please enter a password";
        if (!firstInvalid) firstInvalid = passwordInput;
    } else if (password.value.length < 8) {
        passwordWarn.value = "Your password must be over 7 characters long";
        if (!firstInvalid) firstInvalid = passwordInput;
    }

    // check email validity
    try {
        const res = await fetch(BACKEND_URL + '/check/email?email=' + email.value, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        const data = await res.json();

        if (!res.ok) {
            if (data.err === 'Disposable email') {
                emailWarn.value = "Please enter a nondisposable email";
            } else {
                emailWarn.value = "Please enter a valid email";
            }
            if (!firstInvalid) firstInvalid = emailInput;
        }
    } catch (err) {
        console.error(err);
        alert("An unexpected network error occurred. Please try again later.");
        return;
    }

    // check username profanity
    try {
        const res = await fetch(BACKEND_URL + '/check/profanity?text=' + username.value, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!res.ok) {
            usernameWarn.value = "Avoid profanity in your name"
            if (!firstInvalid) firstInvalid = usernameInput;
        }
    } catch (err) {
        console.error(err);
        alert("An unexpected network error occurred. Please try again later.");
        return;
    }

    if (firstInvalid && firstInvalid.value) {
        await nextTick();
        (firstInvalid.value as HTMLInputElement).focus();
        return;
    }

    try {
        const res = await fetch(BACKEND_URL + '/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (res.ok) {
            localStorage.setItem('access_token', data.access_token)
            const payload = data.access_token.split('.')[1];
            const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
            console.log(decoded);
            alert('Login successful!');
        } else {
            alert('Login failed: ' + data.err);
        }
    } catch (err) {
        console.error(err);
        alert("An unexpected network error occurred. Please try again later.");
    }
}
</script>

<template>
    <form class="flex flex-col items-center justify-center" @submit.prevent="signin">
        <h2 class="text-3xl font-bold mb-4">Create Account</h2>
        <input type="email" placeholder="Email" id="email" v-model="email" ref="emailInput"
            class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-400"
            :class="emailWarn ? 'mb-1' : 'mb-4'" />
        <div v-if="emailWarn" class="text-xs self-end text-red-500 mb-3">{{ emailWarn }}</div>
        <input type="text" placeholder="Username" id="username" v-model="username" ref="usernameInput"
            class="w-full mb-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-400" />
        <div class="text-xs self-end mb-3" :class="!usernameWarn ? 'text-gray-500' : 'text-red-500'">{{ !usernameWarn ?
            "Username must be over 3 characters long." : usernameWarn }}</div>
        <input type="password" placeholder="Password" id="password" v-model="password" ref="passwordInput"
            class="w-full mb-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-400" />
        <div class="text-xs self-end mb-5" :class="!passwordWarn ? 'text-gray-500' : 'text-red-500'">{{
            !passwordWarn ?
                "Password must be over 7 characters long." : passwordWarn }}</div>
        <button
            class="cursor-pointer w-full py-3 bg-indigo-600 text-white font-semibold rounded-md hover:bg-indigo-800 transition-colors duration-500">
            Sign Up
        </button>
    </form>
</template>