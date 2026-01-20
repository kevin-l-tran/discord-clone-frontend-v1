<script setup lang="ts">
import GroupCard from './components/Group/GroupCard.vue';
import CreateGroupModal from './components/Group/CreateGroupModal.vue';
import AddGroupModal from './components/Group/AddGroupModal.vue';
import DeleteMembershipModal from './components/Group/DeleteMembershipModal.vue';

import { onMounted, ref } from 'vue';
import { BACKEND_URL } from './config';

const showCreate = ref(false);
const showAdd = ref(false);
const showDeleteMembership = ref(false);
const deleteId = ref('');

const groups = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  const token = localStorage.getItem('access_token');
  try {
    const res = await fetch(BACKEND_URL + '/user-groups', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    groups.value = await res.json();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
});

function redirect(group_id: string) {
  window.location.href = '/chat/#/' + group_id;
}

function logout() {
  localStorage.setItem('access_token', '');
  window.location.href = '/';
}

function showDeleteModal(id: string) {
  showDeleteMembership.value = true;
  deleteId.value = id;
}
</script>

<template>
  <div class="p-6 bg-neutral-100 min-h-screen relative">
    <div className="fixed inset-0 pointer-events-none">
      <svg width="100%" height="100%">
        <defs>
          <pattern id="dots" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="2" fill="#bae6fd" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#dots)" />
      </svg>
    </div>

    <header class="m-8 relative z-10">
      <div class="border-b-4 border-sky-500 mb-6 flex justify-between align-center">
        <h1 class="text-6xl text-blue-950 font-black mb-2 pb-3">Your Groups</h1>
        <button class="text-3xl bg-gray-200 rounded py-1 px-3 mb-2 cursor-pointer" @click="logout">Log Out</button>
      </div>
    </header>

    <div class="flex flex-wrap gap-10 m-8 relative z-10">
      <GroupCard v-for="group in groups" :key="group.id" :group-id="group.id" :group-image="group.img_url" :group-name="group.name"
        :group-description="group.description" @deleteMembership="showDeleteModal(group.id)">
      </GroupCard>

      <div
        class="w-80 bg-white shadow-lg rounded-xl border-3 border-white flex justify-evenly overflow-hidden transition duration-500 hover:shadow-xl hover:border-sky-300 flex flex-col items-center justify-between">
        <button class="text-5xl font-semibold text-gray-800 hover:text-sky-600 transition cursor-pointer p-10"
          @click="showAdd = true">
          + Add
        </button>
        <div class="w-64 h-1 bg-gray-300" />
        <button class="text-5xl font-semibold text-gray-800 hover:text-sky-600 transition cursor-pointer p-10"
          @click="showCreate = true">
          + Create
        </button>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <CreateGroupModal v-show="showCreate" @close="showCreate = false"></CreateGroupModal>
  </Teleport>
  <Teleport to="body">
    <AddGroupModal v-show="showAdd" @close="showAdd = false"></AddGroupModal>
  </Teleport>
  <Teleport to="body">
    <DeleteMembershipModal v-show="showDeleteMembership" @close="showDeleteMembership = false" :id="deleteId"></DeleteMembershipModal>
  </Teleport>
</template>
