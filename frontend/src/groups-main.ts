import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import { isSignedIn } from './utils/auth'

import Groups from './Groups.vue'
import grouprouter from './groups-router'

const signedIn = await isSignedIn();
if (!signedIn) {
    alert("Please sign in!")
    window.location.href = '/'
} else {
    const app = createApp(Groups)

    app.use(createPinia())
    app.use(grouprouter)

    app.mount('#groups-app')
}

