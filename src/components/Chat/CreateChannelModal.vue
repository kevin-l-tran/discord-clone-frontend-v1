<script setup lang="ts">
import { BACKEND_URL } from '@/config';
import { ref } from 'vue';

const props = defineProps({
    groupId: {
        type: String,
        default: null
    }
})

const name = ref('')
const topic = ref('')
const type = ref('')

const errors = ref<{ name?: string; description?: string; image?: string }>({});

const isSubmitting = ref(false);

async function submitForm() {
    isSubmitting.value = true;
    const token = localStorage.getItem('access_token');
    const payload = {
        "name": name.value,
        "topic": topic.value,
        "type": type.value,
    }

    try {
        const res = await fetch(BACKEND_URL + '/group/' + props.groupId + '/channels', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(payload),
        });
        if (!res.ok) {
            const errorData = await res.json();
            console.error('Failed to create channel:', errorData);
            alert('Failed to create channel: ' + errorData.err)
        } else {
            const data = await res.json();
            console.log('Channel created!', data);
            // do something with the new channel…
        }
    } catch (err) {
        console.error('Network error:', err);
    } finally {
        isSubmitting.value = false;
        window.location.reload()
    }
}
</script>

<template>
    <Transition enter-from-class="opacity-0 scale-75" enter-to-class="opacity-100 scale-100"
        enter-active-class="transition duration-200" leave-from-class="opacity-100" leave-to-class="opacity-0"
        leave-active-class="transition duration-200 ">
        <!-- backdrop -->
        <div class="fixed inset-0 flex items-center justify-center z-50" @click="$emit('close')">
            <!-- modal box -->
            <div class="relative bg-white rounded-3xl overflow-hidden shadow-xl" @click.stop>
                <form class="w-full max-w-xl mx-auto bg-white p-16 rounded-lg shadow space-y-4"
                    @submit.prevent="submitForm">
                    <h2 class="text-4xl font-semibold text-gray-800 text-center mb-5">Add a Channel</h2>

                    <!-- Group Name -->
                    <div>
                        <input type="text" placeholder="Channel Name" v-model="name"
                            class="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400" />
                    </div>

                    <!-- Channel Topic -->
                    <div>
                        <input type="text" placeholder="Channel Topic" v-model="topic"
                            class="w-full border border-gray-300 rounded px-4 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-400" />
                    </div>

                    <!-- Channel Type -->
                    <div class="mb-6">
                        <label for="channel-type" class="text-gray-400 pr-20">Channel Type: </label>
                        <select id="channel-type" v-model="type" class="text-sky-500 bg-gray-200 p-2 rounded-lg px-4">
                            <option value="text">Text</option>
                            <option value="voice">Voice</option>
                        </select>
                    </div>

                    <!-- Submit -->
                    <button type="submit"
                        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition text-lg">
                        Create Channel
                    </button>
                </form>
            </div>
        </div>
    </Transition>
</template>