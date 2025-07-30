<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';

import ChannelsList from './components/Chat/ChannelsList.vue';
import MembersList from './components/Chat/MembersList.vue';
import MessageChannel from './components/Chat/MessageChannel.vue';
import CreateChannelModal from './components/Chat/CreateChannelModal.vue';
import { BACKEND_URL } from './config';

const route = useRoute();

const channels = ref([]);
const member_data = ref([]);
const members = ref([]);
const current_member_data = ref();
const selectedChannel = ref();
const groupId = computed(() => String(route.params.group_id || ''));

const showCreateTextChannel = ref(false);

const token = localStorage.getItem('access_token') || '';
watch(
    groupId,
    async (id) => {
        if (!id) return;
        try {
            const [resCh, resMem, resSelf] = await Promise.all([
                fetch(`${BACKEND_URL}/group/${encodeURIComponent(id)}/channels`, {
                    headers: { Authorization: `Bearer ${token}` },
                }),
                fetch(`${BACKEND_URL}/group/${encodeURIComponent(id)}/members`, {
                    headers: { Authorization: `Bearer ${token}` },
                }),
                fetch(`${BACKEND_URL}/group/${encodeURIComponent(id)}/members/self`, {
                    headers: { Authorization: `Bearer ${token}` },
                })
            ]);
            if (!resCh.ok || !resMem.ok) {
                throw new Error(`Fetch failed: ${resCh.status}, ${resMem.status}`);
            }

            channels.value = await resCh.json();

            const rawList = await resMem.json();
            member_data.value = rawList;
            members.value = rawList.map(item => item.user);

            current_member_data.value = await resSelf.json();

            selectedChannel.value = channels.value[0];
        } catch (e) {
            console.error('Error loading group data', e);
            alert('Could not load channels/members');
        }
    },
    { immediate: true }
);

function groupView() {
    window.location.href = '/groups/';
}
</script>

<template>
    <div class="flex h-screen bg-gray-50" v-if="selectedChannel">
        <!-- Channel List (Left) -->
        <aside class="w-60 bg-white border-r border-gray-200 flex flex-col" aria-label="channel list">
            <div class="flex items-center align-center h-16 px-2 border-b border-gray-200">
                <button class="text-2xl font-bold text-gray-500 px-2 cursor-pointer" @click="groupView()"> < </button>
                <h2 class="text-2xl font-bold text-gray-900 px-4">Group Name</h2>
            </div>
            <ChannelsList :channels="channels" :isOwner="current_member_data.membership.role === 'Owner'"
                v-model="selectedChannel" @newTextChannel="showCreateTextChannel = true"></ChannelsList>
        </aside>
        <!-- Chat Section -->
        <main class="flex-1 flex flex-col">
            <MessageChannel :channel="selectedChannel" :key="selectedChannel.id" :members="members"></MessageChannel>
        </main>
        <!-- Members List (Right) -->
        <aside class="w-64 bg-white border-l border-gray-200 flex flex-col" aria-label="member list">
            <div class="flex items-center h-16 px-6 border-b border-gray-200">
                <span class="text-xl font-semibold text-gray-900">Members - {{ members.length }}</span>
            </div>
            <MembersList :members="members"></MembersList>
        </aside>

        <Teleport to="body">
            <CreateChannelModal v-show="showCreateTextChannel" :groupId="groupId" @close="showCreateTextChannel = false"></CreateChannelModal>
        </Teleport>
    </div>

    <div v-else class="p-4 text-center">
        Loading…
    </div>

</template>
