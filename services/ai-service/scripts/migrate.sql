-- AI服务数据库初始化脚本
-- PostgreSQL

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Token使用记录表
CREATE TABLE IF NOT EXISTS token_usage_records (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(100),
    model_name VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd DECIMAL(10, 6),
    cost_cny DECIMAL(10, 2),
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_token_usage_conversation ON token_usage_records(conversation_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_created ON token_usage_records(created_at);

-- 对话质量记录表
CREATE TABLE IF NOT EXISTS conversation_quality_records (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(100),
    user_id INTEGER,
    query TEXT,
    response TEXT,
    quality_score DECIMAL(3, 2),
    feedback INTEGER,
    issues JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quality_conversation ON conversation_quality_records(conversation_id);
CREATE INDEX IF NOT EXISTS idx_quality_created ON conversation_quality_records(created_at);

-- RAG检索日志表
CREATE TABLE IF NOT EXISTS retrieval_logs (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(100),
    query TEXT,
    intent VARCHAR(50),
    retrieval_level VARCHAR(50),
    docs_retrieved INTEGER DEFAULT 0,
    docs_used INTEGER DEFAULT 0,
    latency_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    sources JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_retrieval_conversation ON retrieval_logs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_level ON retrieval_logs(retrieval_level);
CREATE INDEX IF NOT EXISTS idx_retrieval_created ON retrieval_logs(created_at);

-- 审计日志表 (与shared模块共用)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    service VARCHAR(50),
    user_id INTEGER,
    user_role VARCHAR(50),
    action VARCHAR(50),
    resource_type VARCHAR(50),
    resource_id INTEGER,
    changes JSONB,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    request_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_service ON audit_logs(service);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_request ON audit_logs(request_id);

COMMENT ON TABLE token_usage_records IS 'LLM Token使用记录';
COMMENT ON TABLE conversation_quality_records IS '对话质量评分记录';
COMMENT ON TABLE retrieval_logs IS 'RAG检索日志';
COMMENT ON TABLE audit_logs IS '审计日志';
