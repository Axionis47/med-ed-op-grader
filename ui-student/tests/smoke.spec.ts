import { test, expect } from '@playwright/test';

// Assumes VITE_* env vars baked into build by the workflow (API URL, SUBMISSION_ID)

test('student app loads and shows overall', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  // Basic sanity check: page renders root element
  const root = page.locator('#root');
  await expect(root).toBeVisible();
  // Take a full-page screenshot for the demo
  await page.screenshot({ path: 'student-overall.png', fullPage: true });
});

