<script setup lang="ts">
</script>

<template>
    <form class="flex flex-col items-center justify-center">
        <h1 class="text-3xl font-bold mb-4">Sign In</h1>
        <input type="username" placeholder="Username" id="username"
            class="w-full mb-4 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-400" />
        <input type="password" placeholder="Password" id="password"
            class="w-full mb-2 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-400" />
        <a href="#" class="self-end text-sm text-gray-500 hover:underline mb-6">Forgot your password?</a>
        <button
            class="cursor-pointer w-full py-3 bg-indigo-600 text-white font-semibold rounded-md hover:bg-indigo-800 transition-colors duration-500">
            Sign In
        </button>
    </form>
</template>