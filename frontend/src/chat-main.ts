import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import { isSignedIn } from './utils/auth'

import Chat from './Chat.vue'
import chatrouter from './chat-router'

const signedIn = await isSignedIn();
if (!signedIn) {
    alert("Please sign in!")
    window.location.href = '/'
} else {
    const app = createApp(Chat)

    app.use(createPinia())
    app.use(chatrouter)

    app.mount('#chat-app')
}