<script setup>
import { computed } from 'vue'

const props = defineProps({
  channels: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: Object,
    default: null
  },
  isOwner: {
    type: Boolean,
    default: false
  }
})

// emit event names directly
const emit = defineEmits(['update:modelValue', 'newTextChannel'])

// computed getter/setter to mirror v-model
const selected = computed({
  get() {
    return props.modelValue
  },
  set(channel) {
    emit('update:modelValue', channel)
  }
})
</script>

<template>
  <div class="mb-4">
    <div class="flex justify-between items-center">
      <div class="px-3 py-2 text-xs text-gray-400 uppercase">Text Channels</div>
      <button v-if="isOwner" class="px-3 py-2 text-xl text-gray-400 cursor-pointer" @click="$emit('newTextChannel')">+</button>
    </div>
    <ul>
      <li v-for="channel in channels.filter(ch => ch.type === 'text')" :key="channel.id"
        :class="['flex items-center px-4 py-2 cursor-pointer rounded-lg mx-2 mb-1 transition', channel === selected ? 'bg-gray-100 text-indigo-700 font-semibold' : 'text-gray-700 hover:bg-gray-100']"
        @click="selected = channel">
        <span class="mr-2 text-lg">#</span>
        <span>{{ channel.name }}</span>
      </li>
    </ul>
  </div>
  <div class="overflow-y-auto">
    <div class="px-3 py-2 text-xs text-gray-400 uppercase">Voice Channels</div>
    <ul>
      <li v-for="channel in channels.filter(ch => ch.type === 'voice')" :key="channel.id"
        :class="['flex items-center px-4 py-2 cursor-pointer rounded-lg mx-2 mb-1 transition', channel === selected ? 'bg-gray-100 text-indigo-700 font-semibold' : 'text-gray-700 hover:bg-gray-100']"
        @click="selected = channel">
        <span class="mr-2 text-lg">#</span>
        <span>{{ channel.name }}</span>
      </li>
    </ul>
  </div>
</template>