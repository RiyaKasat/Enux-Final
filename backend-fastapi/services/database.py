import os
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime

load_dotenv()

# In-memory storage for demo purposes (replace with real database later)
_in_memory_db = {
    "uploads": {},
    "content_blocks": {}
}

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.host = os.getenv('DATABASE_HOST', 'localhost')
        self.port = int(os.getenv('DATABASE_PORT', 5432))
        self.name = os.getenv('DATABASE_NAME', 'playbook_db')
        self.user = os.getenv('DATABASE_USER', 'postgres')
        self.password = os.getenv('DATABASE_PASSWORD', '')

# Global database configuration
db_config = DatabaseConfig()

class MockConnection:
    """Mock database connection for demo"""
    
    async def execute(self, query: str, *args):
        """Mock execute for CREATE/INSERT/UPDATE statements"""
        print(f"Mock DB Execute: {query[:50]}...")
        return None
    
    async def fetchrow(self, query: str, *args):
        """Mock fetchrow for SELECT single row"""
        print(f"Mock DB Fetchrow: {query[:50]}...")
        
        if "uploads" in query and "WHERE id" in query:
            upload_id = args[0] if args else None
            return _in_memory_db["uploads"].get(upload_id)
        
        return None
    
    async def fetch(self, query: str, *args):
        """Mock fetch for SELECT multiple rows"""
        print(f"Mock DB Fetch: {query[:50]}...")
        
        if "content_blocks" in query and "WHERE upload_id" in query:
            upload_id = args[0] if args else None
            return [block for block in _in_memory_db["content_blocks"].values() 
                   if block.get("upload_id") == upload_id]
        
        return []
    
    async def fetchval(self, query: str, *args):
        """Mock fetchval for single value"""
        if "SELECT 1" in query:
            return 1
        if "COUNT(*)" in query:
            upload_id = args[0] if args else None
            return len([b for b in _in_memory_db["content_blocks"].values() 
                       if b.get("upload_id") == upload_id])
        return None

@asynccontextmanager
async def get_db_connection():
    """Get mock database connection"""
    yield MockConnection()

async def init_database():
    """Initialize mock database"""
    try:
        print("✅ Mock database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

async def close_database():
    """Close database connections"""
    print("✅ Database connections closed")

# Mock database operations
def store_upload(upload_data: Dict[str, Any]) -> str:
    """Store upload record"""
    upload_id = str(uuid.uuid4())
    upload_record = {
        "id": upload_id,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        **upload_data
    }
    _in_memory_db["uploads"][upload_id] = upload_record
    print(f"✅ Stored upload: {upload_id}")
    return upload_id

def update_upload_status(upload_id: str, status: str, error_message: str = None):
    """Update upload status"""
    if upload_id in _in_memory_db["uploads"]:
        _in_memory_db["uploads"][upload_id]["status"] = status
        _in_memory_db["uploads"][upload_id]["updated_at"] = datetime.now()
        if error_message:
            _in_memory_db["uploads"][upload_id]["error_message"] = error_message
        if status == "completed":
            _in_memory_db["uploads"][upload_id]["processed_at"] = datetime.now()
        print(f"✅ Updated upload {upload_id} status to {status}")

async def store_content_blocks(upload_id: str, blocks: List[Dict[str, Any]]):
    """Store content blocks"""
    for block in blocks:
        block_id = str(uuid.uuid4())
        block_record = {
            "id": block_id,
            "upload_id": upload_id,
            "created_at": datetime.now(),
            **block
        }
        _in_memory_db["content_blocks"][block_id] = block_record
    print(f"✅ Stored {len(blocks)} content blocks for upload {upload_id}")

# For backward compatibility
async def get_db_session():
    """Legacy method for getting database session"""
    return MockConnection()


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
