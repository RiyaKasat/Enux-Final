from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    FOUNDER = "founder"
    CONTRIBUTOR = "contributor"
    MENTOR = "mentor"


class PlaybookStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class FileType(str, Enum):
    MD = "md"
    PDF = "pdf"
    CSV = "csv"
    DOCX = "docx"
    TXT = "txt"
    XLSX = "xlsx"
    PPTX = "pptx"
    JSON = "json"


class PRStatus(str, Enum):
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


class RecommendationStatus(str, Enum):
    NEW = "new"
    VIEWED = "viewed"
    FORKED = "forked"


class EmbeddingType(str, Enum):
    PLAYBOOK = "playbook"
    PR = "pr"


class UploadStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Base Models
class BaseDBModel(BaseModel):
    class Config:
        from_attributes = True
    
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


# Upload Models (for our upload workflow)
class UploadBase(BaseModel):
    filename: Optional[str] = None
    original_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    source_url: Optional[str] = None
    status: UploadStatus = UploadStatus.UPLOADED
    error_message: Optional[str] = None


class UploadCreate(UploadBase):
    pass


class UploadUpdate(BaseModel):
    status: Optional[UploadStatus] = None
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None


class Upload(BaseDBModel, UploadBase):
    processed_at: Optional[datetime] = None


class UploadResponse(BaseModel):
    success: bool
    upload_id: str
    message: str
    blocks_extracted: Optional[int] = None
    redirect_url: Optional[str] = None


# Content Block Models
class ContentBlockBase(BaseModel):
    upload_id: UUID
    type: str
    content: str
    confidence_score: float = 0.8
    suggested_asset_type: Optional[str] = None


class ContentBlockCreate(ContentBlockBase):
    pass


class ContentBlock(BaseDBModel, ContentBlockBase):
    pass


# User Models
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    role: UserRole
    stage: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    stage: Optional[str] = None


class User(BaseDBModel, UserBase):
    pass


# Playbook Models
class PlaybookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    stage: Optional[str] = None
    status: PlaybookStatus = PlaybookStatus.DRAFT
    version: str = "v1"


class PlaybookCreate(PlaybookBase):
    owner_id: UUID


class PlaybookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    stage: Optional[str] = None
    status: Optional[PlaybookStatus] = None
    version: Optional[str] = None


class Playbook(BaseDBModel, PlaybookBase):
    owner_id: UUID


# Playbook File Models
class PlaybookFileBase(BaseModel):
    file_name: str = Field(..., min_length=1)
    file_type: FileType
    file_size: Optional[int] = None
    storage_path: str


class PlaybookFileCreate(PlaybookFileBase):
    playbook_id: UUID
    uploaded_by: UUID


class PlaybookFile(BaseDBModel, PlaybookFileBase):
    playbook_id: UUID
    uploaded_by: UUID


# Upload Models
class UploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadCreate(BaseModel):
    filename: Optional[str] = None
    original_name: str
    file_path: Optional[str] = None
    source_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class Upload(BaseModel):
    class Config:
        from_attributes = True
    
    id: UUID
    filename: Optional[str] = None
    original_name: str
    file_path: Optional[str] = None
    source_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    status: UploadStatus
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    blocks_extracted: int = 0


# Content Block Models
class ContentBlockType(str, Enum):
    HEADING = "heading"
    TEXT = "text"
    CODE = "code"
    LIST = "list"
    TABLE = "table"
    IMAGE = "image"


class AssetType(str, Enum):
    GOAL = "goal"
    STRATEGY = "strategy"
    TIMELINE = "timeline"
    FAQ = "faq"
    TASK = "task"
    METRIC = "metric"
    TEMPLATE = "template"


class ContentBlockCreate(BaseModel):
    upload_id: UUID
    type: ContentBlockType
    content: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    suggested_asset_type: AssetType


class ContentBlock(BaseModel):
    class Config:
        from_attributes = True
    
    id: UUID
    upload_id: UUID
    type: ContentBlockType
    content: str
    confidence_score: float
    suggested_asset_type: AssetType
    created_at: datetime


# Response Models
class UploadResponse(BaseModel):
    success: bool
    upload_id: UUID
    message: str
    blocks_extracted: int = 0
    redirect_url: Optional[str] = None


class URLImportRequest(BaseModel):
    url: str = Field(..., regex=r'^https?://.+')
    title: Optional[str] = None
    description: Optional[str] = None


class FileUploadResponse(BaseModel):
    success: bool
    upload_id: UUID
    filename: str
    file_size: int
    message: str


# AI Processing Models
class ExtractedContent(BaseModel):
    source_type: str
    blocks: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


class AIProcessingRequest(BaseModel):
    file_path: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None
    source_type: str


class BlockMapping(BaseModel):
    block_id: str
    suggested_mappings: List[Dict[str, Any]]
    confidence_scores: List[float]


# Error Models
class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    code: Optional[str] = None


# Pagination Models
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    limit: int
    pages: int
