<script setup lang="ts">
import { BACKEND_URL } from '@/config';
import { ref } from 'vue';

const id = ref('')
const isSubmitting = ref(false);

async function submitForm() {
    isSubmitting.value = true;
    const token = localStorage.getItem('access_token');

    try {
        const res = await fetch(BACKEND_URL + '/group/' + id.value + '/join', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
            },
        });

        if (!res.ok) {
            const err = await res.json();
            console.error("Join failed:", err);
            alert("Failed to join group: " + err.err);
        } else {
            const data = await res.json();
            console.log("Joined successfully!");
            window.location.href = `/groups/#/${data.id}`;
        }
    } catch(err) {
        console.error(err);
        alert('An unexpected network error occurred. Please try again later.');
    } finally {
        isSubmitting.value = false;
    }
}
</script>

<template>
    <Transition enter-from-class="opacity-0 scale-75" enter-to-class="opacity-100 scale-100"
        enter-active-class="transition duration-200" leave-from-class="opacity-100" leave-to-class="opacity-0"
        leave-active-class="transition duration-200 ">
        <!-- backdrop -->
        <div class="fixed inset-0 flex items-center justify-center z-50" @click="$emit('close')" :class="{ 'cursor-wait': isSubmitting }">
            <!-- modal box -->
            <div class="relative bg-white rounded-3xl overflow-hidden shadow-xl" @click.stop>
                <form class="w-full max-w-xl mx-auto bg-white p-16 rounded-lg shadow space-y-4" @submit.prevent="submitForm">
                    <h2 class="text-4xl font-semibold text-gray-800 text-center mb-5">Add a Group</h2>

                    <!-- Group Name -->
                    <div>
                        <input type="text" placeholder="Group Id" v-model="id"
                            class="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400" />
                    </div>

                    <!-- Submit -->
                    <button type="submit"
                        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition text-lg">
                        {{ isSubmitting ? 'Adding Group…' : 'Add Group' }}
                    </button>
                </form>
            </div>
        </div>
    </Transition>
</template>