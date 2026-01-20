<script setup>
defineProps({
    members: {
        type: Array,
        default: () => []
    }
});
</script>

<template>
    <div class="flex-1 overflow-y-auto px-4 py-4">
        <div v-for="member in members" :key="member.id" class="flex items-center mb-4">
            <img :src="'https://i.pravatar.cc/50?u=' + member.id" alt="avatar"
                class="w-10 h-10 rounded-full border border-gray-200 bg-gray-100 mr-3" />
            <div>
                <div class="font-bold text-blue-500">{{ member.username }}</div>
            </div>
        </div>
    </div>
</template>