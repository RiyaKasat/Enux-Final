from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text
from sqlalchemy.dialects.postgresql import JSONB
from abc import ABC, abstractmethod

from .database import get_db_session
from .schemas import (
    Upload, UploadCreate, UploadStatus,
    ContentBlock, ContentBlockCreate,
    User, UserCreate, UserUpdate,
    Playbook, PlaybookCreate, PlaybookUpdate,
    PlaybookFile, PlaybookFileCreate
)


class BaseRepository(ABC):
    """Base repository class following Repository pattern"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def execute_query(self, query, values: Optional[Dict] = None):
        """Execute a raw SQL query"""
        result = await self.session.execute(text(query), values or {})
        return result
    
    async def fetch_one(self, query, values: Optional[Dict] = None):
        """Fetch one record"""
        result = await self.execute_query(query, values)
        return result.fetchone()
    
    async def fetch_all(self, query, values: Optional[Dict] = None):
        """Fetch all records"""
        result = await self.execute_query(query, values)
        return result.fetchall()
    
    async def commit(self):
        """Commit transaction"""
        await self.session.commit()
    
    async def rollback(self):
        """Rollback transaction"""
        await self.session.rollback()


class UploadRepository(BaseRepository):
    """Repository for upload operations"""
    
    async def create(self, upload_data: UploadCreate) -> Upload:
        """Create a new upload record"""
        query = """
        INSERT INTO uploads (id, filename, original_name, file_path, source_url, 
                           file_size, mime_type, status, created_at)
        VALUES (uuid_generate_v4(), :filename, :original_name, :file_path, :source_url,
                :file_size, :mime_type, 'pending', NOW())
        RETURNING *
        """
        
        values = {
            'filename': upload_data.filename,
            'original_name': upload_data.original_name,
            'file_path': upload_data.file_path,
            'source_url': upload_data.source_url,
            'file_size': upload_data.file_size,
            'mime_type': upload_data.mime_type
        }
        
        result = await self.fetch_one(query, values)
        await self.commit()
        
        return Upload(**dict(result._mapping))
    
    async def get_by_id(self, upload_id: UUID) -> Optional[Upload]:
        """Get upload by ID"""
        query = """
        SELECT u.*, 
               COALESCE(cb.blocks_count, 0) as blocks_extracted
        FROM uploads u
        LEFT JOIN (
            SELECT upload_id, COUNT(*) as blocks_count 
            FROM content_blocks 
            GROUP BY upload_id
        ) cb ON u.id = cb.upload_id
        WHERE u.id = :upload_id
        """
        
        result = await self.fetch_one(query, {'upload_id': str(upload_id)})
        
        if result:
            return Upload(**dict(result._mapping))
        return None
    
    async def update_status(self, upload_id: UUID, status: UploadStatus, 
                          error_message: Optional[str] = None) -> bool:
        """Update upload status"""
        query = """
        UPDATE uploads 
        SET status = :status, 
            error_message = :error_message,
            processed_at = CASE WHEN :status = 'completed' THEN NOW() ELSE processed_at END,
            updated_at = NOW()
        WHERE id = :upload_id
        """
        
        values = {
            'upload_id': str(upload_id),
            'status': status.value,
            'error_message': error_message
        }
        
        await self.execute_query(query, values)
        await self.commit()
        return True
    
    async def get_recent_uploads(self, limit: int = 10) -> List[Upload]:
        """Get recent uploads"""
        query = """
        SELECT u.*, 
               COALESCE(cb.blocks_count, 0) as blocks_extracted
        FROM uploads u
        LEFT JOIN (
            SELECT upload_id, COUNT(*) as blocks_count 
            FROM content_blocks 
            GROUP BY upload_id
        ) cb ON u.id = cb.upload_id
        ORDER BY u.created_at DESC
        LIMIT :limit
        """
        
        results = await self.fetch_all(query, {'limit': limit})
        return [Upload(**dict(row._mapping)) for row in results]


class ContentBlockRepository(BaseRepository):
    """Repository for content block operations"""
    
    async def create(self, block_data: ContentBlockCreate) -> ContentBlock:
        """Create a new content block"""
        query = """
        INSERT INTO content_blocks (id, upload_id, type, content, confidence_score, 
                                  suggested_asset_type, created_at)
        VALUES (uuid_generate_v4(), :upload_id, :type, :content, :confidence_score,
                :suggested_asset_type, NOW())
        RETURNING *
        """
        
        values = {
            'upload_id': str(block_data.upload_id),
            'type': block_data.type.value,
            'content': block_data.content,
            'confidence_score': block_data.confidence_score,
            'suggested_asset_type': block_data.suggested_asset_type.value
        }
        
        result = await self.fetch_one(query, values)
        await self.commit()
        
        return ContentBlock(**dict(result._mapping))
    
    async def create_batch(self, blocks: List[ContentBlockCreate]) -> List[ContentBlock]:
        """Create multiple content blocks in batch"""
        if not blocks:
            return []
        
        # Build batch insert query
        values_list = []
        for i, block in enumerate(blocks):
            values_list.append(f"""
                (uuid_generate_v4(), :upload_id_{i}, :type_{i}, :content_{i}, 
                 :confidence_score_{i}, :suggested_asset_type_{i}, NOW())
            """)
        
        query = f"""
        INSERT INTO content_blocks (id, upload_id, type, content, confidence_score, 
                                  suggested_asset_type, created_at)
        VALUES {', '.join(values_list)}
        RETURNING *
        """
        
        # Build parameters
        params = {}
        for i, block in enumerate(blocks):
            params.update({
                f'upload_id_{i}': str(block.upload_id),
                f'type_{i}': block.type.value,
                f'content_{i}': block.content,
                f'confidence_score_{i}': block.confidence_score,
                f'suggested_asset_type_{i}': block.suggested_asset_type.value
            })
        
        results = await self.fetch_all(query, params)
        await self.commit()
        
        return [ContentBlock(**dict(row._mapping)) for row in results]
    
    async def get_by_upload_id(self, upload_id: UUID) -> List[ContentBlock]:
        """Get all content blocks for an upload"""
        query = """
        SELECT * FROM content_blocks 
        WHERE upload_id = :upload_id 
        ORDER BY created_at ASC
        """
        
        results = await self.fetch_all(query, {'upload_id': str(upload_id)})
        return [ContentBlock(**dict(row._mapping)) for row in results]


class UserRepository(BaseRepository):
    """Repository for user operations"""
    
    async def create(self, user_data: UserCreate, password_hash: str) -> User:
        """Create a new user with password"""
        # Start transaction
        try:
            # Create user
            user_query = """
            INSERT INTO users (id, name, email, role, stage, created_at, updated_at)
            VALUES (uuid_generate_v4(), :name, :email, :role, :stage, NOW(), NOW())
            RETURNING *
            """
            
            user_values = {
                'name': user_data.name,
                'email': user_data.email,
                'role': user_data.role.value,
                'stage': user_data.stage
            }
            
            user_result = await self.fetch_one(user_query, user_values)
            user = User(**dict(user_result._mapping))
            
            # Create password
            password_query = """
            INSERT INTO user_passwords (id, user_id, password_hash, created_at)
            VALUES (uuid_generate_v4(), :user_id, :password_hash, NOW())
            """
            
            await self.execute_query(password_query, {
                'user_id': str(user.id),
                'password_hash': password_hash
            })
            
            await self.commit()
            return user
            
        except Exception as e:
            await self.rollback()
            raise e
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = :email"
        result = await self.fetch_one(query, {'email': email})
        
        if result:
            return User(**dict(result._mapping))
        return None
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = :user_id"
        result = await self.fetch_one(query, {'user_id': str(user_id)})
        
        if result:
            return User(**dict(result._mapping))
        return None
    
    async def get_password_hash(self, user_id: UUID) -> Optional[str]:
        """Get password hash for user"""
        query = "SELECT password_hash FROM user_passwords WHERE user_id = :user_id"
        result = await self.fetch_one(query, {'user_id': str(user_id)})
        
        if result:
            return result.password_hash
        return None


class PlaybookRepository(BaseRepository):
    """Repository for playbook operations"""
    
    async def create(self, playbook_data: PlaybookCreate) -> Playbook:
        """Create a new playbook"""
        query = """
        INSERT INTO playbooks (id, title, description, content, tags, stage, 
                             status, owner_id, version, created_at, updated_at)
        VALUES (uuid_generate_v4(), :title, :description, :content, :tags, :stage,
                :status, :owner_id, :version, NOW(), NOW())
        RETURNING *
        """
        
        values = {
            'title': playbook_data.title,
            'description': playbook_data.description,
            'content': playbook_data.content,
            'tags': playbook_data.tags,
            'stage': playbook_data.stage,
            'status': playbook_data.status.value,
            'owner_id': str(playbook_data.owner_id),
            'version': playbook_data.version
        }
        
        result = await self.fetch_one(query, values)
        await self.commit()
        
        return Playbook(**dict(result._mapping))
    
    async def get_by_id(self, playbook_id: UUID) -> Optional[Playbook]:
        """Get playbook by ID"""
        query = "SELECT * FROM playbooks WHERE id = :playbook_id"
        result = await self.fetch_one(query, {'playbook_id': str(playbook_id)})
        
        if result:
            return Playbook(**dict(result._mapping))
        return None
    
    async def get_by_owner(self, owner_id: UUID, limit: int = 10) -> List[Playbook]:
        """Get playbooks by owner"""
        query = """
        SELECT * FROM playbooks 
        WHERE owner_id = :owner_id 
        ORDER BY updated_at DESC 
        LIMIT :limit
        """
        
        results = await self.fetch_all(query, {
            'owner_id': str(owner_id),
            'limit': limit
        })
        
        return [Playbook(**dict(row._mapping)) for row in results]


# Repository Factory
class RepositoryFactory:
    """Factory for creating repository instances"""
    
    @staticmethod
    async def get_upload_repository() -> UploadRepository:
        """Get upload repository instance"""
        session = await get_db_session()
        return UploadRepository(session)
    
    @staticmethod
    async def get_content_block_repository() -> ContentBlockRepository:
        """Get content block repository instance"""
        session = await get_db_session()
        return ContentBlockRepository(session)
    
    @staticmethod
    async def get_user_repository() -> UserRepository:
        """Get user repository instance"""
        session = await get_db_session()
        return UserRepository(session)
    
    @staticmethod
    async def get_playbook_repository() -> PlaybookRepository:
        """Get playbook repository instance"""
        session = await get_db_session()
        return PlaybookRepository(session)
