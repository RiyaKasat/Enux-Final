from pydantic import BaseModel
from typing import Optional
from enum import Enum

class UploadStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class UploadResponse(BaseModel):
    success: bool
    upload_id: str
    message: str
    blocks_extracted: Optional[int] = None
    redirect_url: Optional[str] = None

class ContentBlock(BaseModel):
    id: str
    type: str
    content: str
    confidence_score: float
    suggested_asset_type: Optional[str] = None

class PlaybookAssetType(str, Enum):
    GOAL = "goal"
    STRATEGY = "strategy"
    TIMELINE = "timeline"
    FAQ = "faq"
    TASK = "task"
    PROCESS = "process"
    TEMPLATE = "template"
    CHECKLIST = "checklist"
