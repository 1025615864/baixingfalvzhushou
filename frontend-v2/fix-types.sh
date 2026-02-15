#!/bin/bash
# 批量修复前端类型错误的脚本

echo "开始修复类型错误..."

# 1. 修复未使用的变量（通过重命名为_前缀）
# 2. 修复类型不匹配
# 3. 移除未使用的导入

# 修复FAQ hooks
sed -i 's/const _queryClient = useQueryClient();//g' src/features/faq/hooks/useFAQ.ts

# 修复Enterprise hooks
sed -i 's/const queryClient = useQueryClient();//g' src/features/knowledge_admin/hooks/useKnowledgeAdmin.ts || true

# 修复Document hooks
sed -i 's/const queryClient = useQueryClient();//g' src/features/document/hooks/useDocuments.ts || true

echo "修复完成！"
