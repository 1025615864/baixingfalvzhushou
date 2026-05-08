#!/bin/bash
# ==========================================
# 生产环境数据库初始化脚本
# 功能：创建数据库、用户、表结构、初始数据
# 使用方式：docker exec -i baixing_db_prod bash < scripts/init_db_prod.sh
# ==========================================

set -euo pipefail

DB_NAME="${POSTGRES_DB:-baixing_law}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD}"

echo "[$(date)] 开始数据库初始化..."

# 创建各微服务数据库
DBS=("legal_service" "community_service" "order_service" "news_service" "search_service" "recommendation_service" "notification_service" "knowledge_service" "archive_service" "points_service")

for db in "${DBS[@]}"; do
    echo "[$(date)] 创建数据库: ${db}"
    psql -U "${DB_USER}" -d "${DB_NAME}" -c "CREATE DATABASE ${db};" 2>/dev/null || echo "  数据库 ${db} 已存在，跳过"
done

# 插入种子数据 - 法律分类
echo "[$(date)] 插入法律分类种子数据..."
psql -U "${DB_USER}" -d "legal_service" <<EOF
CREATE TABLE IF NOT EXISTS law_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO law_categories (name, code, description, sort_order) VALUES
    ('劳动法', 'labor', '劳动合同法、工资、工时、工伤等', 1),
    ('婚姻法', 'marriage', '离婚、财产分割、抚养等', 2),
    ('合同法', 'contract', '合同订立、履行、违约等', 3),
    ('侵权责任法', 'tort', '人身损害、财产损害等', 4),
    ('公司法', 'company', '公司设立、股东权利、治理等', 5),
    ('知识产权法', 'ip', '专利、商标、著作权等', 6),
    ('房地产法', 'real_estate', '买卖、租赁、物业等', 7),
    ('交通法', 'traffic', '交通事故、违章处理等', 8),
    ('刑法', 'criminal', '犯罪、刑罚、辩护等', 9),
    ('行政法', 'admin', '行政处罚、行政复议等', 10)
ON CONFLICT (code) DO NOTHING;
EOF

# 插入种子数据 - 新闻分类
echo "[$(date)] 插入新闻分类种子数据..."
psql -U "${DB_USER}" -d "news_service" <<EOF
CREATE TABLE IF NOT EXISTS news_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO news_categories (name, code, description, sort_order) VALUES
    ('法律法规', 'laws', '最新法律法规解读', 1),
    ('社会法治', 'society', '社会法治热点新闻', 2),
    ('案例分析', 'cases', '典型法律案例分析', 3),
    ('律师观点', 'lawyer', '专业律师法律观点', 4),
    ('普法知识', 'education', '法律知识普及', 5),
    ('行业动态', 'industry', '法律行业动态', 6)
ON CONFLICT (code) DO NOTHING;
EOF

# 插入种子数据 - 通知模板（已在代码中，此处仅验证表结构）
echo "[$(date)] 验证通知服务表结构..."
psql -U "${DB_USER}" -d "notification_service" <<EOF
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT TRUE,
    quiet_hours_start VARCHAR(5),
    quiet_hours_end VARCHAR(5),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
EOF

# 插入种子数据 - 搜索热门词
echo "[$(date)] 插入搜索热门词种子数据..."
psql -U "${DB_USER}" -d "search_service" <<EOF
CREATE TABLE IF NOT EXISTS hot_searches (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) UNIQUE NOT NULL,
    search_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS search_indices (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,
    item_id INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    keywords VARCHAR(1000),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO hot_searches (keyword, search_count, status) VALUES
    ('离婚程序', 15230, 'active'),
    ('劳动合同法', 12450, 'active'),
    ('工伤认定', 11200, 'active'),
    ('房屋买卖合同', 9850, 'active'),
    ('债务纠纷', 8900, 'active'),
    ('交通事故处理', 7650, 'active'),
    ('遗产继承', 6540, 'active'),
    ('医疗事故鉴定', 5430, 'active'),
    ('刑事拘留', 4320, 'active'),
    ('劳动仲裁', 3210, 'active')
ON CONFLICT (keyword) DO NOTHING;
EOF

echo "[$(date)] 数据库初始化完成！"
