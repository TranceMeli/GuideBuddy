<script setup lang="ts">
/**
 * Line icons (stroke only, currentColor), so they take the colour of the text around them.
 * Always decorative here: the meaning is carried by visible text.
 */
const props = defineProps<{ name: IconName; size?: number }>()
</script>

<script lang="ts">
const PATHS = {
  check: 'M5 12.5l4.5 4.5L19 7.5',
  'check-circle': 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0zM8 12.5l2.8 2.8L16.5 9.5',
  alert: 'M12 3.5L22 20.5H2L12 3.5zM12 10v4.5M12 17.6v.1',
  stop: 'M8.5 3h7L21 8.5v7L15.5 21h-7L3 15.5v-7zM12 8v5M12 16.2v.1',
  info: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0zM12 11v6M12 7.6v.1',
  tip: 'M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.4 1.1 2.2h5c0-.8.4-1.6 1.1-2.2A6 6 0 0 0 12 3z',
  close: 'M6 6l12 12M18 6L6 18',
  menu: 'M4 7h16M4 12h16M4 17h16',
  'chevron-down': 'M6 9l6 6 6-6',
  'arrow-up': 'M12 19V5M6 11l6-6 6 6',
  'arrow-down': 'M12 5v14M6 13l6 6 6-6',
  undo: 'M9 14L4 9l5-5M4 9h10a6 6 0 0 1 0 12h-3',
  redo: 'M15 14l5-5-5-5M20 9H10a6 6 0 0 0 0 12h3',
  trash: 'M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3',
  'arrow-left': 'M19 12H5M11 6l-6 6 6 6',
  'arrow-right': 'M5 12h14M13 6l6 6-6 6',
  download: 'M12 4v11M7 10l5 5 5-5M5 20h14',
  printer: 'M7 9V4h10v5M7 17H5a1 1 0 0 1-1-1v-5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v5a1 1 0 0 1-1 1h-2M7 14h10v6H7z',
  clock: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0zM12 7v5l3 2',
  level: 'M5 19v-4M12 19V10M19 19V5',
  steps: 'M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01',
  search: 'M20 20l-4.5-4.5M17 10.5a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0z',
  star: 'M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9L12 17l-5.2 2.7 1-5.9L3.5 9.7l5.9-.8L12 3.5z',
  file: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5zM14 3v5h5',
  copy: 'M9 9h10v10H9zM5 15V5h10',
  plus: 'M12 5v14M5 12h14',
  code: 'M8 8l-4 4 4 4M16 8l4 4-4 4M14 5l-4 14',
  eye: 'M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  link: 'M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1',
  list: 'M9 6h11M9 12h11M9 18h11M4.5 6l.8.8L7 5M4.5 12l.8.8L7 11M4.5 18l.8.8L7 17',
  grip: 'M9 6h.01M9 12h.01M9 18h.01M15 6h.01M15 12h.01M15 18h.01',
  photo: 'M4 5h16v14H4zM4 16l5-5 4 4 3-3 4 4M15 9.5h.01',
  // placeholder illustrations of the guide cards (category, then guide type)
  bike: 'M2 17.5a3.5 3.5 0 1 0 7 0 3.5 3.5 0 1 0-7 0zM15 17.5a3.5 3.5 0 1 0 7 0 3.5 3.5 0 1 0-7 0zM5.5 17.5L9 10h7l2.5 7.5M12 17.5L9 10M14.5 6H17l-1 4M7.5 7H11',
  monitor: 'M3 5h18v11H3zM8 20h8M12 16v4',
  pot: 'M4 10h16v6a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4v-6zM2 10h2M20 10h2M9.5 7c0-1 1-1.5 1-2.5M13.5 7c0-1 1-1.5 1-2.5',
  hammer: 'M13 9l-8.5 8.5a1.5 1.5 0 0 0 2 2L15 11M10.5 6.5L14 3l7 7-3.5 3.5z',
  sprout: 'M12 21v-9M12 12c0-4 3-7 8-7 0 5-3 7-8 7zM12 15.5c0-3-2.5-5-6.5-5 0 3.5 2.5 5 6.5 5z',
  heart: 'M12 20s-7.5-4.5-7.5-10A4.5 4.5 0 0 1 12 7a4.5 4.5 0 0 1 7.5 3c0 5.5-7.5 10-7.5 10z',
  home: 'M3 11l9-7 9 7M5 9.5V20h14V9.5M10 20v-6h4v6',
  dice: 'M4 4h16v16H4zM8.5 8.5h.01M15.5 15.5h.01M15.5 8.5h.01M8.5 15.5h.01M12 12h.01',
  document: 'M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6',
  phone: 'M7 2.5h10a1 1 0 0 1 1 1v17a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-17a1 1 0 0 1 1-1zM11 18.5h2',
  compass: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0zM15.5 8.5l-2 5-5 2 2-5z',
  question: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0zM9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14M12 17.5v.1',
  fork: 'M6 20V4M6 12h5l7-7M11 12l7 7',
  grid: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  pen: 'M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4',
  pointer: 'M5 3l14 7.5-6.2 1.8L10.5 19 5 3z',
  heading: 'M6 4v16M18 4v16M6 12h12',
  minus: 'M4 12h16',
  quote: 'M7 7h4v4c0 3-1.500 5-4 6M15 7h4v4c0 3-1.500 5-4 6',
  table: 'M4 5h16v14H4zM4 10h16M4 15h16M10 5v14',
  bullets: 'M9 6h11M9 12h11M9 18h11M5 6h.01M5 12h.01M5 18h.01',
  diagram: 'M9 4h6v4H9zM3 16h6v4H3zM15 16h6v4h-6zM12 8v4M6 16v-4h12v4',
  terminal: 'M4 5h16v14H4zM8 10l3 2-3 2M13 15h4',
  compare: 'M12 4v16M4 8h5M4 16h5M15 8h5M15 16h5',
} as const
export type IconName = keyof typeof PATHS
</script>

<template>
  <svg
    class="icon"
    :width="props.size ?? 20"
    :height="props.size ?? 20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path :d="PATHS[props.name]" />
  </svg>
</template>
