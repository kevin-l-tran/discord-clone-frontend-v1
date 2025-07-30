<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { io } from 'socket.io-client';
import { BACKEND_URL } from '../../config';

// Props
const props = defineProps<{ channel: { id: string; name: string } }>();
const channel = props.channel;

// State
const messages = ref<any[]>([]);
const newText = ref('');
const nextCursor = ref<string | null>(null);
const messageContainer = ref<HTMLElement | null>(null);

// Routing & auth
const route = useRoute();
const groupId = computed(() => String(route.params.group_id || ''));
const token = localStorage.getItem('access_token') || '';

let socket: ReturnType<typeof io>;

// Load paginated messages
async function loadMessages() {
  if (!channel?.id) return;
  const params = new URLSearchParams();
  params.append('limit', '50');
  if (nextCursor.value) {
    params.append('before', nextCursor.value);
  }

  const res = await fetch(
    `${BACKEND_URL}/group/${groupId.value}/channels/${channel.id}/messages?${params.toString()}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  const data = await res.json();
  if (data.messages) {
    // Returned newest-first, reverse to chronological
    messages.value = [...data.messages.reverse(), ...messages.value];
  }
  nextCursor.value = data.next_cursor || null;
}

// Infinite scroll older
function onScroll(e: Event) {
  const el = e.target as HTMLElement;
  if (el.scrollTop < 50 && nextCursor.value) {
    loadMessages();
  }
}

// Send new message
async function sendMessage() {
  if (!newText.value.trim()) return;
  const form = new FormData();
  form.append('content', newText.value.trim());

  await fetch(
    `${BACKEND_URL}/group/${groupId.value}/channels/${channel.id}/messages`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    }
  );

  newText.value = '';
}

// React to channel switch
watch(
  () => channel.id,
  (newId, oldId) => {
    messages.value = [];
    nextCursor.value = null;
    if (socket && oldId) {
      socket.emit('leave', { room: oldId });
    }
    loadMessages().then(() => {
      if (socket && newId) {
        socket.emit('join', { room: newId });
      }
    });
  }
);

// Scroll to bottom whenever messages change
watch(
  messages,
  () => {
    scrollToBottom();
  },
  { flush: 'post' }
);

// Setup WebSocket and initial load
onMounted(() => {
  socket = io(BACKEND_URL, { auth: { token } });

  socket.on('connect', () => {
    if (channel?.id) {
      socket.emit('join', { room: channel.id });
    }
  });

  socket.on('chat:recv', (payload: any) => {
    // Ensure message is for current channel
    if (payload.channel === channel.id || payload.channel_id === channel.id) {
      messages.value.push(payload);
      scrollToBottom();
    }
  });

  loadMessages().then(() => {
    scrollToBottom();
  });
});

// Cleanup
onBeforeUnmount(() => {
  if (socket) {
    socket.disconnect();
  }
});

function scrollToBottom() {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    }
  });
}
</script>

<template>
  <!-- Header -->
  <header class="flex items-center h-16 px-6 bg-white border-b border-gray-200">
    <span class="text-xl font-bold text-gray-900"># {{ channel.name }}</span>
  </header>

  <!-- Chat Messages -->
  <section class="flex-1 overflow-y-auto px-6 py-4 bg-gray-50" ref="messageContainer" @scroll.passive="onScroll">
    <div v-for="msg in messages" :key="msg.id" class="flex items-start mb-6">
      <img :src="msg.avatar" alt="avatar" class="w-10 h-10 rounded-full mr-4 border border-gray-200 bg-gray-200" />
      <div>
        <div class="flex items-center mb-1">
          <span class="font-semibold text-gray-900 mr-2">{{ msg.user }}</span>
          <span class="text-xs text-gray-400">{{ msg.time }}</span>
        </div>
        <div class="text-gray-800 leading-relaxed">
          <span v-html="msg.content"></span>
        </div>
      </div>
    </div>
  </section>

  <!-- Message Input -->
  <footer class="p-4 bg-white border-t border-gray-200">
    <form @submit.prevent="sendMessage" class="flex items-center bg-gray-100 rounded-xl px-4 py-2 w-full">
      <input v-model="newText" class="flex-1 bg-transparent outline-none text-gray-900 placeholder-gray-500"
        :placeholder="`Message #${channel.name}`" />
      <button type="submit"
        class="ml-3 px-3 py-1 rounded-lg bg-indigo-600 text-white font-semibold transition hover:bg-indigo-700">
        Send
      </button>
    </form>
  </footer>
</template>
