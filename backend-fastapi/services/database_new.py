import os
import asyncpg
from typing import Optional, AsyncContextManager
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.host = os.getenv('DATABASE_HOST', 'localhost')
        self.port = int(os.getenv('DATABASE_PORT', 5432))
        self.name = os.getenv('DATABASE_NAME', 'playbook_db')
        self.user = os.getenv('DATABASE_USER', 'postgres')
        self.password = os.getenv('DATABASE_PASSWORD', '')
    
    @property
    def asyncpg_url(self) -> str:
        """Get asyncpg database URL"""
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


# Global database configuration
db_config = DatabaseConfig()

# Global connection pool
_connection_pool = None


async def init_connection_pool():
    """Initialize asyncpg connection pool"""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = await asyncpg.create_pool(
                db_config.asyncpg_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            print("✅ Database connection pool initialized")
        except Exception as e:
            print(f"❌ Failed to create database pool: {e}")
            # Create a fallback connection for local development
            print("🔄 Attempting to connect to default PostgreSQL database...")
            try:
                fallback_url = f"postgresql://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/postgres"
                _connection_pool = await asyncpg.create_pool(
                    fallback_url,
                    min_size=1,
                    max_size=10,
                    command_timeout=60
                )
                print("✅ Connected to fallback PostgreSQL database")
            except Exception as e2:
                print(f"❌ Fallback connection also failed: {e2}")
                raise e2
    return _connection_pool


@asynccontextmanager
async def get_db_connection() -> AsyncContextManager[asyncpg.Connection]:
    """Get database connection using asyncpg"""
    pool = await init_connection_pool()
    async with pool.acquire() as connection:
        yield connection


async def init_database():
    """Initialize database connection and create missing tables"""
    try:
        # Initialize connection pool
        await init_connection_pool()
        
        # Test connection and create tables
        async with get_db_connection() as conn:
            # Test basic connection
            result = await conn.fetchval("SELECT 1")
            print(f"✅ Database connection test successful: {result}")
            
            # Check if we need to create the main database
            try:
                # Try to create the main database if it doesn't exist
                await conn.execute(f"CREATE DATABASE {db_config.name}")
                print(f"✅ Created database: {db_config.name}")
            except asyncpg.DuplicateDatabase:
                print(f"ℹ️ Database {db_config.name} already exists")
            except Exception as e:
                print(f"ℹ️ Could not create database (might already exist): {e}")
            
            # Create uploads table if it doesn't exist (for our upload workflow)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    filename TEXT,
                    original_name TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    mime_type TEXT,
                    source_url TEXT,
                    status TEXT CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')) DEFAULT 'uploaded',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    processed_at TIMESTAMP
                )
            """)
            
            # Create content_blocks table for storing extracted content
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS content_blocks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    upload_id UUID REFERENCES uploads(id) ON DELETE CASCADE,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence_score FLOAT DEFAULT 0.8,
                    suggested_asset_type TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create indexes for better performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_content_blocks_upload ON content_blocks(upload_id)")
            
            print("✅ Database tables created successfully")
            
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


async def close_database():
    """Close database connections"""
    global _connection_pool
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None
        print("✅ Database connections closed")


# For backward compatibility
async def get_db_session():
    """Legacy method for getting database session - now returns connection"""
    async with get_db_connection() as conn:
        return conn
