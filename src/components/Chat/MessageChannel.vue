<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { io } from 'socket.io-client';
import { BACKEND_URL, GEMINI_API_KEY } from '../../config';
import { GoogleGenAI } from "@google/genai";


// Props
const props = defineProps<{
    channel: { id: string; name: string },
    members: [{ id: string; username: string }]
}>();
const channel = props.channel;
const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });
const ai_tools = [
    {
        googleSearch: {},
    },
];
const ai_config = {
    thinkingConfig: {
        thinkingBudget: -1,
    },
    ai_tools,
    responseMimeType: 'text/plain',
    systemInstruction: "You reply very tersely. Refuse to answer questions that are too long.",
};
const chat = ai.chats.create({
    model: 'gemini-2.5-flash',
    history: [
        {
            role: "model",
            parts: [{ text: "Great to meet you. What would you like to know?" }]
        }
    ],
    config: ai_config
})

// State
const messages = ref<any[]>([]);
const newText = ref('');
const nextCursor = ref<string | null>(null);
const messageContainer = ref<HTMLElement | null>(null);
const askAI = ref(false)

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

    messages.value.forEach((message) => {
        props.members.forEach((member) => {
            if (message.author === member.id) {
                message.username = member.username;
            }
        })
        if (!message.username) {
            message.username = "gemini";
        }
    })

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

    const msg = newText.value.trim();
    newText.value = '';

    if (askAI.value) {
        try {
            const response = await chat.sendMessageStream({
                message: msg
            });

            let reply = '';
            for await (const chunk of response) {
                reply += chunk.text;
            }

            const form = new FormData();
            form.append('content', reply);

            await fetch(
                `${BACKEND_URL}/group/${groupId.value}/channels/${channel.id}/messages/gemini`,
                {
                    method: 'POST',
                    headers: { Authorization: `Bearer ${token}` },
                    body: form,
                }
            );
        } catch (error) {
            console.error('Error with Gemini:', error)
        }
    }
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
            console.log(payload);
            payload.created_at = new Date(payload.created_at).toUTCString();
            messages.value.push(payload);
            appendUsername(payload);
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

function appendUsername(message: any) {
    props.members.forEach((member) => {
        if (message.author === member.id) {
            message.username = member.username;
        }
    })
    if (!message.username) {
        message.username = "gemini";
    }
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
            <img :src="'https://i.pravatar.cc/50?u=' + msg.author" alt="avatar"
                class="w-10 h-10 rounded-full mr-4 border border-gray-200 bg-gray-200" />
            <div>
                <div class="flex items-center mb-1">
                    <span class="font-bold text-blue-500 mr-2">{{ msg.username }}</span>
                    <span class="text-xs text-gray-400">{{ msg.created_at }}</span>
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
                class="ml-3 px-3 py-1 rounded-lg bg-indigo-600 text-white font-semibold cursor-pointer transition hover:bg-indigo-700">
                {{ !askAI ? 'Send' : 'Ask Gemini' }}
            </button>
            <!-- radio buttons -->
            <div class="ml-4 flex items-center space-x-4">
                <label class="flex items-center text-sm">
                    <input type="radio" class="form-radio" v-model="askAI" :value="false" />
                    <span class="ml-1">User</span>
                </label>
                <label class="flex items-center text-sm">
                    <input type="radio" class="form-radio" v-model="askAI" :value="true" />
                    <span class="ml-1">AI</span>
                </label>
            </div>
        </form>
    </footer>
</template>
