<script setup lang="ts">
defineProps({
    groupImage: String,
    groupName: String,
    groupDescription: String,
    groupId: String
});

function redirect(group_id: any) {
  window.location.href = '/chat/#/' + group_id;
}
</script>

<template>
    <div
        class="w-80 bg-white shadow-lg border-3 border-white rounded-xl overflow-hidden transition duration-500 hover:shadow-xl hover:border-sky-300 hover:shadow-xl">
        <img :src="groupImage" alt="Group" class="w-full h-40 object-cover cursor-pointer" @click="redirect(groupId)"/>
        <div class="p-4">
            <div class="relative group mb-1">
                <h3 class="text-2xl font-semibold truncate">
                    {{ groupName }}
                </h3>
                <div class="absolute left-0 bottom-full mb-2 w-max max-w-xs 
                 bg-gray-800 text-white text-m rounded px-2 py-1 
                 opacity-0 group-hover:opacity-100 transition-opacity
                 whitespace-normal z-20">
                    {{ groupName }}
                </div>
            </div>

            <p class="text-sm text-gray-500">{{ groupDescription }}</p>
        </div>
        <button class="m-2 mx-4 mb-3 text-red-500 bg-gray-200 py-1 px-2 rounded-lg cursor-pointer" @click="$emit('deleteMembership')">Leave Group</button>
    </div>
</template>