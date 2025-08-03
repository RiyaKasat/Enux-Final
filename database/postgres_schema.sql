-- PostgreSQL Schema for Founders Playbook Hub (Updated to match Supabase)
-- Run this script to create tables in your local PostgreSQL database

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- for UUIDs (PostgreSQL equivalent of pgcrypto)
-- Note: For AI vector embeddings, you can install pgvector extension:
-- CREATE EXTENSION IF NOT EXISTS "vector";

-- USERS table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT CHECK (role IN ('founder', 'contributor', 'mentor')) NOT NULL,
    stage TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- USER_PASSWORDS table for authentication (PostgreSQL specific)
CREATE TABLE IF NOT EXISTS user_passwords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- PLAYBOOKS table
CREATE TABLE IF NOT EXISTS playbooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    tags TEXT[] DEFAULT '{}',
    stage TEXT,
    status TEXT CHECK (status IN ('draft', 'published', 'archived')) DEFAULT 'draft',
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    version TEXT DEFAULT 'v1',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- PLAYBOOK FILES table
CREATE TABLE IF NOT EXISTS playbook_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_type TEXT CHECK (file_type IN ('md', 'pdf', 'csv', 'docx', 'txt', 'xlsx', 'pptx', 'json')) NOT NULL,
    file_size INTEGER,
    storage_path TEXT NOT NULL,
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- FORKS table
CREATE TABLE IF NOT EXISTS forks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    fork_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- PULL REQUESTS table
CREATE TABLE IF NOT EXISTS pull_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fork_id UUID REFERENCES forks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_changes JSONB,
    summary TEXT,
    status TEXT CHECK (status IN ('open', 'approved', 'rejected', 'merged')) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT NOW()
);

-- PR COMMENTS table
CREATE TABLE IF NOT EXISTS pr_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pr_id UUID REFERENCES pull_requests(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_name TEXT,
    line_number INTEGER,
    comment TEXT,
    emoji TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- VERSION HISTORY table
CREATE TABLE IF NOT EXISTS version_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    pr_id UUID REFERENCES pull_requests(id) ON DELETE CASCADE,
    version TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- RECOMMENDATIONS table
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    recommended_pb UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    reason TEXT,
    status TEXT CHECK (status IN ('new', 'viewed', 'forked')) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT NOW()
);

-- EMBEDDINGS table (chunk-aware)
-- Option 1: Using JSONB for embeddings (compatible with all PostgreSQL versions)
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID REFERENCES playbook_files(id) ON DELETE CASCADE,
    pr_id UUID REFERENCES pull_requests(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    content TEXT,
    embedding JSONB, -- Store embedding as JSON array, or use VECTOR(1536) if you have pgvector
    type TEXT CHECK (type IN ('playbook', 'pr')) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Option 2: If you want to use pgvector extension (uncomment after installing pgvector):
-- CREATE TABLE IF NOT EXISTS embeddings (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     file_id UUID REFERENCES playbook_files(id) ON DELETE CASCADE,
--     pr_id UUID REFERENCES pull_requests(id) ON DELETE CASCADE,
--     chunk_index INTEGER,
--     content TEXT,
--     embedding VECTOR(1536), -- OpenAI embedding dimension
--     type TEXT CHECK (type IN ('playbook', 'pr')) NOT NULL,
--     created_at TIMESTAMP DEFAULT NOW()
-- );

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_playbooks_owner ON playbooks(owner_id);
CREATE INDEX IF NOT EXISTS idx_playbooks_stage ON playbooks(stage);
CREATE INDEX IF NOT EXISTS idx_playbooks_status ON playbooks(status);
CREATE INDEX IF NOT EXISTS idx_playbook_files_playbook ON playbook_files(playbook_id);
CREATE INDEX IF NOT EXISTS idx_playbook_files_type ON playbook_files(file_type);
CREATE INDEX IF NOT EXISTS idx_forks_user ON forks(user_id);
CREATE INDEX IF NOT EXISTS idx_forks_playbook ON forks(playbook_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_fork ON pull_requests(fork_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_status ON pull_requests(status);
CREATE INDEX IF NOT EXISTS idx_pr_comments_pr ON pr_comments(pr_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_file ON embeddings(file_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON embeddings(type);
CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status);

-- Add triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_playbooks_updated_at BEFORE UPDATE ON playbooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE users IS 'Platform users (founders, mentors, contributors)';
COMMENT ON TABLE user_passwords IS 'User authentication credentials (PostgreSQL specific)';
COMMENT ON TABLE playbooks IS 'Business playbooks and frameworks';
COMMENT ON TABLE playbook_files IS 'Files belonging to each playbook';
COMMENT ON TABLE forks IS 'User forks of playbooks';
COMMENT ON TABLE pull_requests IS 'Pull requests for playbook changes';
COMMENT ON TABLE pr_comments IS 'Comments on pull requests';
COMMENT ON TABLE version_history IS 'Version history of playbooks';
COMMENT ON TABLE recommendations IS 'AI-generated playbook recommendations';
COMMENT ON TABLE embeddings IS 'AI embeddings for semantic search';

-- Sample data for testing (optional)
INSERT INTO users (name, email, role, stage) VALUES 
    ('Demo User', 'demo@founders-playbook.com', 'founder', 'mvp')
ON CONFLICT (email) DO NOTHING;

-- Display success message
SELECT 'PostgreSQL schema created successfully with all Supabase tables!' as message;
