import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  timeout: 60000,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    trace: 'off',
  },
  webServer: {
    command: 'npm run build && npm run preview -- --port=5173',
    port: 5173,
    reuseExistingServer: true,
    timeout: 120000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});

