/**
 * API调用方式统一修复脚本
 * 将使用 apiClient 的文件改为使用 api
 */

import fs from 'fs';
import path from 'path';

const filesToFix = [
  'src/features/admin/api/index.ts',
  'src/features/admin_monitor/api/index.ts',
  'src/features/ai-assistant/api/index.ts',
  'src/features/ai-consultation/api/index.ts',
  'src/features/ai_quality/api/index.ts',
  'src/features/analytics/api/index.ts',
  'src/features/calendar/api/index.ts',
  'src/features/channel/api/index.ts',
  'src/features/consultation/api/index.ts',
  'src/features/contract/api/index.ts',
  'src/features/contracts/api/index.ts',
  'src/features/cross-domain/api/index.ts',
  'src/features/document/api/index.ts',
  'src/features/enterprise/api/index.ts',
  'src/features/faq/api/index.ts',
  'src/features/feedback/api/index.ts',
  'src/features/forum-admin/api/index.ts',
  'src/features/forum-assistant/api/index.ts',
  'src/features/forum-reactions/api/index.ts',
  'src/features/forum/api/index.ts',
];

console.log('开始修复API调用方式...\n');

let fixedCount = 0;
let errorCount = 0;

for (const file of filesToFix) {
  const filePath = path.join(process.cwd(), file);
  
  try {
    if (!fs.existsSync(filePath)) {
      console.log(`⚠️  文件不存在: ${file}`);
      continue;
    }
    
    let content = fs.readFileSync(filePath, 'utf-8');
    
    // 检查是否使用了 apiClient
    if (!content.includes('apiClient')) {
      console.log(`⏭️  跳过(无需修复): ${file}`);
      continue;
    }
    
    // 1. 修改导入语句
    content = content.replace(
      /import\s+{\s*apiClient\s*}\s+from\s+['"]@\/shared\/lib\/api\/client['"];?/g,
      "import { api } from '@/shared/lib/api/client';"
    );
    
    // 2. 修改调用方式 - apiClient.xxx(...) => api.xxx(...)
    content = content.replace(/apiClient\./g, 'api.');
    
    // 3. 移除 .data 提取（因为 api 对象已经封装了）
    // 注意：这个需要谨慎处理，可能需要手动检查
    // content = content.replace(/\.data\.items/g, '.items');
    // content = content.replace(/\.data;/g, ';');
    
    fs.writeFileSync(filePath, content);
    console.log(`✅ 已修复: ${file}`);
    fixedCount++;
    
  } catch (error) {
    console.error(`❌ 修复失败 ${file}:`, error);
    errorCount++;
  }
}

console.log(`\n修复完成!`);
console.log(`- 成功: ${fixedCount}`);
console.log(`- 失败: ${errorCount}`);
console.log(`\n⚠️  注意：请手动检查修改后的文件，确保 .data 的提取逻辑正确`);
