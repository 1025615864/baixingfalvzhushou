#!/usr/bin/env python3
"""
数据库迁移脚本：添加管理后台功能所需字段
适用于 SQLite 数据库
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


async def migrate():
    """执行数据库迁移"""
    print("开始数据库迁移...")
    
    async with engine.begin() as conn:
        # 1. 检查并添加 document_template_versions 表的字段
        print("检查 document_template_versions 表...")
        try:
            await conn.execute(text("""
                ALTER TABLE document_template_versions 
                ADD COLUMN variables TEXT
            """))
            print("  ✓ 添加 variables 字段")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("  ✓ variables 字段已存在")
            else:
                print(f"  ✗ 添加 variables 字段失败: {e}")
        
        try:
            await conn.execute(text("""
                ALTER TABLE document_template_versions 
                ADD COLUMN usage_count INTEGER DEFAULT 0
            """))
            print("  ✓ 添加 usage_count 字段")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("  ✓ usage_count 字段已存在")
            else:
                print(f"  ✗ 添加 usage_count 字段失败: {e}")
        
        # 2. 检查并添加 forum_posts 表的字段
        print("\n检查 forum_posts 表...")
        fields_to_add = [
            ("review_status", "VARCHAR(20) DEFAULT 'approved'"),
            ("review_reason", "TEXT"),
            ("is_sticky", "BOOLEAN DEFAULT FALSE"),
            ("sticky_priority", "INTEGER DEFAULT 0"),
            ("is_essence", "BOOLEAN DEFAULT FALSE"),
        ]
        
        for field_name, field_type in fields_to_add:
            try:
                await conn.execute(text(f"""
                    ALTER TABLE forum_posts 
                    ADD COLUMN {field_name} {field_type}
                """))
                print(f"  ✓ 添加 {field_name} 字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  ✓ {field_name} 字段已存在")
                else:
                    print(f"  ✗ 添加 {field_name} 字段失败: {e}")
        
        # 3. 检查并添加 lawfirms 表的字段
        print("\n检查 lawfirms 表...")
        lawfirm_fields = [
            ("is_verified", "BOOLEAN DEFAULT FALSE"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
        ]
        
        for field_name, field_type in lawfirm_fields:
            try:
                await conn.execute(text(f"""
                    ALTER TABLE lawfirms 
                    ADD COLUMN {field_name} {field_type}
                """))
                print(f"  ✓ 添加 {field_name} 字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  ✓ {field_name} 字段已存在")
                else:
                    print(f"  ✗ 添加 {field_name} 字段失败: {e}")
        
        # 4. 检查 consultation_templates 表是否存在，不存在则创建
        print("\n检查 consultation_templates 表...")
        try:
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='consultation_templates'
            """))
            table_exists = result.fetchone()
            
            if not table_exists:
                await conn.execute(text("""
                    CREATE TABLE consultation_templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        category VARCHAR(50) DEFAULT 'legal',
                        questions TEXT,
                        status VARCHAR(20) DEFAULT 'draft',
                        is_default BOOLEAN DEFAULT FALSE,
                        usage_count INTEGER DEFAULT 0,
                        created_by VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        published_at TIMESTAMP
                    )
                """))
                print("  ✓ 创建 consultation_templates 表")
                
                # 创建索引
                await conn.execute(text("""
                    CREATE INDEX idx_consultation_templates_key ON consultation_templates(key)
                """))
                await conn.execute(text("""
                    CREATE INDEX idx_consultation_templates_status ON consultation_templates(status)
                """))
                await conn.execute(text("""
                    CREATE INDEX idx_consultation_templates_category ON consultation_templates(category)
                """))
                print("  ✓ 创建索引")
            else:
                print("  ✓ consultation_templates 表已存在")
        except Exception as e:
            print(f"  ✗ 创建 consultation_templates 表失败: {e}")
        
        # 5. 更新现有数据
        print("\n更新现有数据...")
        try:
            await conn.execute(text("""
                UPDATE forum_posts SET review_status = 'approved' WHERE review_status IS NULL
            """))
            print("  ✓ 更新帖子审核状态")
        except Exception as e:
            print(f"  ✗ 更新帖子审核状态失败: {e}")
        
        try:
            await conn.execute(text("""
                UPDATE lawfirms SET is_active = TRUE WHERE is_active IS NULL
            """))
            print("  ✓ 更新律所状态")
        except Exception as e:
            print(f"  ✗ 更新律所状态失败: {e}")
    
    print("\n✅ 数据库迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
