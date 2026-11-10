import { defineConfig } from 'vitest/config';
export default defineConfig({test:{include:['apps/**/test/**/*.test.{ts,tsx}'],environment:'node',testTimeout:10000,restoreMocks:true},esbuild:{jsx:'automatic'}});
