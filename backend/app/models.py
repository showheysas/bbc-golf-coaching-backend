from sqlalchemy import Column, String, DateTime, Text, DECIMAL, JSON, ForeignKey, Enum as SQLEnum, TypeDecorator, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import CHAR as MYSQL_CHAR
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import relationship, sessionmaker
import uuid
from datetime import datetime, timezone
import enum
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

# Custom GUID TypeDecorator for cross-database compatibility
class GUID(TypeDecorator):
    impl = CHAR
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            return dialect.type_descriptor(MYSQL_CHAR(36))
        else:
            return dialect.type_descriptor(CHAR(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'mysql':
            return str(value)
        else:
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)

# Enums for specific columns
class LocationType(str, enum.Enum):
    simulation_golf = "simulation_golf"
    real_golf_course = "real_golf_course"

class ReservationStatus(str, enum.Enum):
    booked = "booked"
    completed = "completed"
    cancelled = "cancelled"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"

class Video(Base):
    __tablename__ = "videos"
    
    video_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), nullable=False)
    video_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    club_type = Column(String(50), nullable=True)
    swing_form = Column(String(50), nullable=True)
    swing_note = Column(Text, nullable=True)
    section_group_id = Column(GUID(), nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    section_groups = relationship("SectionGroup", back_populates="video")

class CoachingReservation(Base):
    __tablename__ = "coaching_reservation"
    
    session_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), nullable=False)
    coach_id = Column(GUID(), nullable=False)
    session_date = Column(DateTime(timezone=True), nullable=False)
    session_time = Column(DateTime(timezone=True), nullable=False)
    location_type = Column(SQLEnum(LocationType), nullable=False)
    location_id = Column(GUID(), nullable=False)
    status = Column(SQLEnum(ReservationStatus), default=ReservationStatus.booked)
    price = Column(DECIMAL(10, 2), nullable=False)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SectionGroup(Base):
    __tablename__ = "section_groups"
    
    section_group_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    video_id = Column(GUID(), ForeignKey("videos.video_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    video = relationship("Video", back_populates="section_groups")
    sections = relationship("SwingSection", back_populates="section_group")

class SwingSection(Base):
    __tablename__ = "swing_sections"
    
    section_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    section_group_id = Column(GUID(), ForeignKey("section_groups.section_group_id"), nullable=False)
    start_sec = Column(DECIMAL(6, 2), nullable=False)
    end_sec = Column(DECIMAL(6, 2), nullable=False)
    image_url = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    markup_json = Column(JSON, nullable=True)
    coach_comment = Column(Text, nullable=True)
    coach_comment_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    section_group = relationship("SectionGroup", back_populates="sections")

# Database connection setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./golf_coaching.db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session maker
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def create_tables():
    """Create database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()