-- 数据库迁移脚本：添加管理后台功能所需字段
-- 执行时间: 2024-01-01

-- ============================================
-- 1. 文档模板版本表新增字段
-- ============================================
ALTER TABLE document_template_versions 
ADD COLUMN IF NOT EXISTS variables TEXT,
ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;

-- ============================================
-- 2. 帖子表新增审核和置顶字段
-- ============================================
ALTER TABLE forum_posts 
ADD COLUMN IF NOT EXISTS review_status VARCHAR(20) DEFAULT 'approved',
ADD COLUMN IF NOT EXISTS review_reason TEXT,
ADD COLUMN IF NOT EXISTS is_sticky BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS sticky_priority INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_essence BOOLEAN DEFAULT FALSE;

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_forum_posts_review_status ON forum_posts(review_status);
CREATE INDEX IF NOT EXISTS idx_forum_posts_is_sticky ON forum_posts(is_sticky);
CREATE INDEX IF NOT EXISTS idx_forum_posts_is_essence ON forum_posts(is_essence);

-- ============================================
-- 3. 咨询模板表确认字段（如果表已存在）
-- ============================================
-- 检查咨询模板表是否存在，如果不存在则创建
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'public' 
                   AND table_name = 'consultation_templates') THEN
        CREATE TABLE consultation_templates (
            id SERIAL PRIMARY KEY,
            key VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) DEFAULT 'legal',
            questions TEXT, -- JSON格式存储问题列表
            status VARCHAR(20) DEFAULT 'draft',
            is_default BOOLEAN DEFAULT FALSE,
            usage_count INTEGER DEFAULT 0,
            created_by VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP WITH TIME ZONE
        );
        
        CREATE INDEX idx_consultation_templates_key ON consultation_templates(key);
        CREATE INDEX idx_consultation_templates_status ON consultation_templates(status);
        CREATE INDEX idx_consultation_templates_category ON consultation_templates(category);
    END IF;
END $$;

-- ============================================
-- 4. 律所表确认字段
-- ============================================
-- 确保律所表有所需字段
ALTER TABLE lawfirms 
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS idx_lawfirms_is_verified ON lawfirms(is_verified);
CREATE INDEX IF NOT EXISTS idx_lawfirms_is_active ON lawfirms(is_active);

-- ============================================
-- 5. 更新已存在的数据
-- ============================================
-- 将现有帖子设置为已审核状态
UPDATE forum_posts SET review_status = 'approved' WHERE review_status IS NULL;

-- 将现有律所设置为活跃状态
UPDATE lawfirms SET is_active = TRUE WHERE is_active IS NULL;

-- ============================================
-- 6. 添加注释说明
-- ============================================
COMMENT ON COLUMN document_template_versions.variables IS '模板变量定义（JSON格式）';
COMMENT ON COLUMN document_template_versions.usage_count IS '模板使用次数统计';
COMMENT ON COLUMN forum_posts.review_status IS '审核状态: approved-通过, rejected-拒绝, pending-待审核';
COMMENT ON COLUMN forum_posts.is_sticky IS '是否置顶';
COMMENT ON COLUMN forum_posts.is_essence IS '是否精华帖';
COMMENT ON COLUMN lawfirms.is_verified IS '是否通过认证';
COMMENT ON COLUMN lawfirms.is_active IS '是否启用';
