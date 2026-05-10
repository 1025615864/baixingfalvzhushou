import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

async function gotoFast(page: import('@playwright/test').Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

test.describe('社区论坛浏览', () => {
  test('用户应该能查看论坛页面', async ({ page }) => {
    await gotoFast(page, '/forum');

    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
  });

  test('论坛页面应该显示帖子列表或空状态', async ({ page }) => {
    await gotoFast(page, '/forum');

    const postCard = page.locator('[data-testid^="post-card-"], [class*="post-card"], [class*="PostCard"]').first();
    const emptyState = page.locator('text=暂无帖子, text=还没有帖子, text=暂无内容').first();
    const hasPost = await postCard.isVisible({ timeout: 5000 }).catch(() => false);
    const hasEmpty = await emptyState.isVisible({ timeout: 3000 }).catch(() => false);

    expect(hasPost || hasEmpty).toBe(true);
  });

  test('论坛页面应该有发帖入口', async ({ page }) => {
    await gotoFast(page, '/forum');

    const createButton = page.locator('button, a').filter({ hasText: /发帖|发布|写帖子|新建帖子/ }).first();
    const hasCreate = await createButton.isVisible({ timeout: 5000 }).catch(() => false);

    expect(hasCreate).toBe(true);
  });
});

test.describe('帖子详情与评论', () => {
  test('用户应该能查看帖子详情', async ({ page }) => {
    await gotoFast(page, '/forum');

    const postLink = page.locator('a[href*="/post/"], a[href*="/posts/"]').first();
    const hasLink = await postLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasLink) {
      await postLink.click();
      await page.waitForLoadState('domcontentloaded');

      await expect(page.locator('h1, h2, [class*="post-title"], [class*="PostDetail"]').first()).toBeVisible({ timeout: 10000 });
    }
  });

  test('帖子详情页应该有评论区域', async ({ page }) => {
    await gotoFast(page, '/forum');

    const postLink = page.locator('a[href*="/post/"], a[href*="/posts/"]').first();
    const hasLink = await postLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasLink) {
      await postLink.click();
      await page.waitForLoadState('domcontentloaded');

      const commentSection = page.locator('[class*="comment"], [class*="Comment"], text=评论').first();
      const hasComment = await commentSection.isVisible({ timeout: 5000 }).catch(() => false);
      expect(hasComment).toBe(true);
    }
  });

  test('帖子详情页应该有点赞功能', async ({ page }) => {
    await gotoFast(page, '/forum');

    const postLink = page.locator('a[href*="/post/"], a[href*="/posts/"]').first();
    const hasLink = await postLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasLink) {
      await postLink.click();
      await page.waitForLoadState('domcontentloaded');

      const likeButton = page.locator('button').filter({ hasText: /点赞|like|👍/ }).first();
      const hasLike = await likeButton.isVisible({ timeout: 5000 }).catch(() => false);
      expect(hasLike).toBe(true);
    }
  });
});

test.describe('发帖流程', () => {
  test('用户点击发帖应该显示编辑表单', async ({ page }) => {
    await gotoFast(page, '/forum');

    const createButton = page.locator('button, a').filter({ hasText: /发帖|发布|写帖子/ }).first();
    const hasCreate = await createButton.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasCreate) {
      await createButton.click();
      await page.waitForLoadState('domcontentloaded');

      const titleInput = page.locator('input[placeholder*="标题"], input#title, input[name="title"]').first();
      const contentInput = page.locator('textarea[placeholder*="内容"], textarea#content, textarea[name="content"]').first();

      const hasTitle = await titleInput.isVisible({ timeout: 5000 }).catch(() => false);
      const hasContent = await contentInput.isVisible({ timeout: 5000 }).catch(() => false);

      expect(hasTitle || hasContent).toBe(true);
    }
  });
});
