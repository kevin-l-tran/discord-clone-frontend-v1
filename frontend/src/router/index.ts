import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { 
      path: '/',
      name: 'home', 
      component: () => import('@/views/HomeView.vue') 
    },
    /*
    {
      path: '/app',
      component: () => import('@/views/AppShell.vue'),
      beforeEnter: (to, from, next) => {
        if (!isLoggedIn()) return next('/')
        next()
      },
      children: [ ] //your protected SPA routes
    }
    */
  ],
})

export default router
