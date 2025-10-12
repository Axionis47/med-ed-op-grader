import { test, expect } from '@playwright/test';

// Assumes VITE_* env vars baked into build by the workflow (API URL, SINGLE_SUBMISSION_ID)

test('instructor app loads and shows dashboard/submissions', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  const root = page.locator('#root');
  await expect(root).toBeVisible();
  await page.screenshot({ path: 'instructor-dashboard.png', fullPage: true });
});

