import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

// Unit tests of plain TypeScript modules and small components, without a running Nuxt.
// "~" points to app/ like in Nuxt; the auto-imports these files rely on are set in tests/setup.ts.
// Component tests say `// @vitest-environment happy-dom` at the top; the others run in node.
export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '~': fileURLToPath(new URL('./app', import.meta.url)) } },
  test: { include: ['tests/**/*.test.ts'], setupFiles: ['tests/setup.ts'] },
})
