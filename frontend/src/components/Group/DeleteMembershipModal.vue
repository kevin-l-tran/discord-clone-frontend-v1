<script setup lang="ts">
import { BACKEND_URL } from '@/config';
import { ref } from 'vue';

const props = defineProps({
    id: String
});

const isSubmitting = ref(false);

async function submitForm() {
    isSubmitting.value = true;
    const token = localStorage.getItem('access_token');

    try {
        const res = await fetch(BACKEND_URL + '/group/' + props.id + '/members', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
            },
        });

        if (!res.ok) {
            const err = await res.json();
            console.error("Leave failed:", err);
        } else {
            console.log("Leaved successfully!");
            window.location.reload();
        }
    } catch (err) {
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
        <div class="fixed inset-0 flex items-center justify-center z-50" @click="$emit('close')"
            :class="{ 'cursor-wait': isSubmitting }">
            <!-- modal box -->
            <div class="relative bg-white rounded-2xl overflow-hidden shadow-xl" @click.stop>
                <form
                    class="w-full max-w-xl mx-auto bg-white p-16 rounded-lg shadow space-y-4 flex-col items-center justify-center align-center"
                    @submit.prevent="submitForm">
                    <h2 class="text-2xl font-semibold text-red-500 text-center mb-5">Are you sure you want to leave?
                    </h2>
                    <div class="flex justify-center">
                        <button
                            class="text-2xl font-semibold text-white bg-red-500 p-3 rounded-lg text-center mb-5">Leave
                            Group</button>
                    </div>
                </form>
            </div>
        </div>
    </Transition>
</template>