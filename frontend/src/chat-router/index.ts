import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/chat/:group_id?',
      component: () => import('@/Chat.vue'),
    }
  ],
})

export default router;