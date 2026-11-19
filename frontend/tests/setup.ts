import { computed, ref, toRaw, type Ref } from 'vue'
import { localKey } from '../app/utils/guideTypes'

// useState keeps one ref per key, like Nuxt's shared state
const states = new Map<string, Ref<unknown>>()
const useState = <T>(key: string, init?: () => T) => {
  if (!states.has(key)) states.set(key, ref(init ? init() : undefined))
  return states.get(key) as Ref<T>
}

// Nuxt imports these automatically; outside Nuxt the modules under test find them as globals
Object.assign(globalThis, { computed, ref, toRaw, localKey, useState })

// Every test starts without messages or open dialogs
export const resetState = () => states.clear()
