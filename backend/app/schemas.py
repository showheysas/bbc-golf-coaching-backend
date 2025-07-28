from pydantic import BaseModel, Field, field_serializer
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum
from app.utils.timezone import to_jst

# Enums matching the database models
class LocationType(str, Enum):
    simulation_golf = "simulation_golf"
    real_golf_course = "real_golf_course"

class ReservationStatus(str, Enum):
    booked = "booked"
    completed = "completed"
    cancelled = "cancelled"

class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"

# Swing section tags enum
class SwingSectionTag(str, Enum):
    address = "address"
    takeaway = "takeaway"
    halfway_back = "halfway_back"
    backswing = "backswing"
    top = "top"
    transition = "transition"
    downswing = "downswing"
    impact = "impact"
    follow_through = "follow_through"
    finish_1 = "finish_1"
    finish_2 = "finish_2"
    other = "other"

# Base schemas
class VideoBase(BaseModel):
    user_id: UUID
    video_url: str
    thumbnail_url: Optional[str] = None
    club_type: Optional[str] = None
    swing_form: Optional[str] = None
    swing_note: Optional[str] = None

class VideoCreate(VideoBase):
    pass

class VideoUpdate(BaseModel):
    club_type: Optional[str] = None
    swing_form: Optional[str] = None
    swing_note: Optional[str] = None
    thumbnail_url: Optional[str] = None

class VideoResponse(VideoBase):
    video_id: UUID
    upload_date: datetime
    section_group_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('upload_date')
    def serialize_upload_date(self, dt: datetime) -> datetime:
        return to_jst(dt)
    
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> datetime:
        return to_jst(dt)
    
    @field_serializer('updated_at')
    def serialize_updated_at(self, dt: datetime) -> datetime:
        return to_jst(dt)
    
    class Config:
        from_attributes = True

# Coaching Reservation schemas
class CoachingReservationBase(BaseModel):
    user_id: UUID
    coach_id: UUID
    session_date: datetime
    session_time: datetime
    location_type: LocationType
    location_id: UUID
    price: Decimal

class CoachingReservationCreate(CoachingReservationBase):
    pass

class CoachingReservationUpdate(BaseModel):
    session_date: Optional[datetime] = None
    session_time: Optional[datetime] = None
    location_type: Optional[LocationType] = None
    location_id: Optional[UUID] = None
    status: Optional[ReservationStatus] = None
    price: Optional[Decimal] = None
    payment_status: Optional[PaymentStatus] = None

class CoachingReservationResponse(CoachingReservationBase):
    session_id: UUID
    status: ReservationStatus
    payment_status: PaymentStatus
    
    class Config:
        from_attributes = True

# Section Group schemas
class SectionGroupBase(BaseModel):
    video_id: UUID

class SectionGroupCreate(SectionGroupBase):
    pass

class SectionGroupResponse(SectionGroupBase):
    section_group_id: UUID
    created_at: datetime
    overall_feedback: Optional[str] = None
    overall_feedback_summary: Optional[str] = None
    next_training_menu: Optional[str] = None
    next_training_menu_summary: Optional[str] = None
    feedback_created_at: Optional[datetime] = None
    
    @field_serializer('feedback_created_at')
    def serialize_feedback_created_at(self, dt: Optional[datetime]) -> Optional[datetime]:
        return to_jst(dt) if dt else None
    
    class Config:
        from_attributes = True

# Swing Section schemas
class MarkupObject(BaseModel):
    type: str  # "circle", "line", "arrow", etc.
    coordinates: List[float]
    color: str
    size: Optional[float] = None

class SwingSectionBase(BaseModel):
    section_group_id: UUID
    start_sec: Decimal
    end_sec: Decimal
    image_url: Optional[str] = None
    tags: Optional[List[SwingSectionTag]] = None
    markup_json: Optional[List[MarkupObject]] = None

class SwingSectionCreate(SwingSectionBase):
    pass

class SwingSectionUpdate(BaseModel):
    start_sec: Optional[Decimal] = None
    end_sec: Optional[Decimal] = None
    image_url: Optional[str] = None
    tags: Optional[List[SwingSectionTag]] = None
    markup_json: Optional[List[MarkupObject]] = None
    coach_comment: Optional[str] = None

class SwingSectionResponse(SwingSectionBase):
    section_id: UUID
    coach_comment: Optional[str] = None
    coach_comment_summary: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Upload request schemas
class VideoUploadRequest(BaseModel):
    club_type: Optional[str] = None
    swing_form: Optional[str] = None
    swing_note: Optional[str] = None

# Response schemas for complex operations
class VideoWithSectionsResponse(VideoResponse):
    section_group: Optional[SectionGroupResponse] = None
    sections: List[SwingSectionResponse] = []

class CoachCommentRequest(BaseModel):
    section_id: UUID
    comment: str

class CoachCommentResponse(BaseModel):
    section_id: UUID
    comment: str
    summary: str

# Overall feedback schemas
class OverallFeedbackRequest(BaseModel):
    section_group_id: UUID
    feedback_type: str  # "overall" or "next_training"

class OverallFeedbackResponse(BaseModel):
    section_group_id: UUID
    overall_feedback: Optional[str] = None
    overall_feedback_summary: Optional[str] = None
    next_training_menu: Optional[str] = None
    next_training_menu_summary: Optional[str] = None
    feedback_created_at: Optional[datetime] = None

# Error response schema
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None