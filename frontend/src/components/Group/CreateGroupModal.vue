<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import GroupCard from './GroupCard.vue';
import defaultImageUrl from '@/assets/background.avif';
import { BACKEND_URL } from '@/config';

const MAX_DESC = 150;

const name = ref('');
const description = ref('');
const image = ref<File | null>(null);

const descRemaining = computed(() => MAX_DESC - description.value.length);
const imageInput = ref<HTMLInputElement | null>(null);
const previewUrl = ref<string>(defaultImageUrl)
const isSubmitting = ref(false);

const errors = ref<{ name?: string; description?: string; image?: string }>({});

watch(image, (file, prevFile) => {
    // free the old URL if there was one
    if (prevFile) URL.revokeObjectURL(previewUrl.value)

    // new URL or fallback to default asset
    previewUrl.value = file
        ? URL.createObjectURL(file)
        : defaultImageUrl
})

function handleImageUpload(e: Event) {
    const files = (e.target as HTMLInputElement).files;
    image.value = files && files.length ? files[0] : null;
}

function clearImage() {
    image.value = null;
    if (imageInput.value) {
        imageInput.value.value = '';
    }
}

function validate() {
    errors.value = {};
    if (name.value.trim().length < 4) {
        errors.value.name = 'Name must be at least 4 characters long';
    }
    return Object.keys(errors.value).length === 0;
}

async function fetchDefaultImage(): Promise<Blob> {
    const res = await fetch(defaultImageUrl);
    if (!res.ok) throw new Error('Failed to load default image');
    return await res.blob();
}

async function submitForm() {
    if (!validate()) return;

    isSubmitting.value = true;
    
    const formData = new FormData();
    formData.append('name', name.value);
    formData.append('description', description.value);
    if (image.value) {
        formData.append('img', image.value);
    } else {
        const blob = await fetchDefaultImage();
        formData.append('img', blob, 'background.avif');
    }

    const token = localStorage.getItem('access_token');

    try {
        const res = await fetch(BACKEND_URL + '/group', {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
            },
            body: formData,
        });
        const data = await res.json();

        if (res.ok) {
            window.location.href = `/groups/#/${data.id}`;
        } else {
            alert('Failed to create group: ' + (data.err || res.statusText));
        }
    } catch (err) {
        console.error(err);
        alert('An unexpected network error occurred. Please try again later.');
    } finally {
        isSubmitting.value = false;
    }

    name.value = '';
    description.value = '';
    image.value = null;
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
            <div class="relative bg-white rounded-3xl overflow-hidden shadow-xl" @click.stop>
                <form class="w-full max-w-xl mx-auto bg-white p-16 rounded-lg shadow space-y-4"
                    @submit.prevent="submitForm">
                    <h2 class="text-4xl font-semibold text-gray-800 text-center mb-5">Create Your Group</h2>

                    <!-- Group Name -->
                    <div>
                        <input type="text" placeholder="Group Name" v-model="name"
                            class="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400" />
                        <p v-if="errors.name" class="mt-1 text-red-500 text-sm">{{ errors.name }}</p>
                    </div>

                    <!-- Description -->
                    <div>
                        <textarea v-model="description" :maxlength="MAX_DESC" placeholder="Description" rows="4"
                            class="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"></textarea>
                        <div class="mt-1 flex justify-between items-center text-sm">
                            <p class="text-gray-500">
                                {{ descRemaining }} characters remaining
                            </p>
                            <p v-if="errors.description" class="mt-1 text-red-500 text-sm">{{ errors.description }}</p>
                        </div>
                    </div>

                    <!-- Image Upload -->
                    <div class="flex justify-center items-center space-x-4">
                        <label for="groupImage" v-if="!image"
                            class="inline-block bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-lg cursor-pointer text-sm">
                            Upload Group Image
                        </label>
                        <input id="groupImage" type="file" accept="image/*" class="hidden"
                            @change="handleImageUpload" />

                        <template v-if="image">
                            <span class="text-gray-700 italic bg-gray-300 px-3 py-1 rounded">{{ image.name }}</span>
                            <button type="button" @click="clearImage" class="ml-2 text-sm text-red-500 hover:underline">
                                Clear
                            </button>
                        </template>
                        <p v-if="errors.image" class="mt-1 text-red-500 text-sm">{{ errors.image }}</p>
                    </div>

                    <!-- Preview -->
                    <div class="w-full mt-6 flex justify-center">
                        <GroupCard :group-image="previewUrl" :group-name="name" :group-description="description" />
                    </div>

                    <!-- Submit -->
                    <button type="submit"
                        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition text-lg">
                        {{ isSubmitting ? 'Creating…' : 'Create Group' }}
                    </button>
                </form>
            </div>
        </div>
    </Transition>
</template>