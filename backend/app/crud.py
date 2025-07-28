from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
import uuid

from app.models import Video, CoachingReservation, SectionGroup, SwingSection
from app.schemas import (
    VideoCreate, VideoUpdate, CoachingReservationCreate, CoachingReservationUpdate,
    SectionGroupCreate, SwingSectionCreate, SwingSectionUpdate
)

# Video CRUD operations
class VideoCRUD:
    
    @staticmethod
    async def create_video(db: AsyncSession, video: VideoCreate) -> Video:
        """Create a new video record"""
        db_video = Video(**video.model_dump())
        db.add(db_video)
        await db.commit()
        await db.refresh(db_video)
        return db_video
    
    @staticmethod
    async def get_video(db: AsyncSession, video_id: UUID) -> Optional[Video]:
        """Get video by ID"""
        result = await db.execute(
            select(Video).where(Video.video_id == video_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_video_with_sections(db: AsyncSession, video_id: UUID) -> Optional[Video]:
        """Get video with all sections loaded"""
        result = await db.execute(
            select(Video)
            .options(
                selectinload(Video.section_groups).selectinload(SectionGroup.sections)
            )
            .where(Video.video_id == video_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_videos_by_user(db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Video]:
        """Get videos by user ID"""
        result = await db.execute(
            select(Video)
            .where(Video.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Video.upload_date.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_all_videos_with_sections(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Video]:
        """Get all videos with sections for coach dashboard"""
        result = await db.execute(
            select(Video)
            .options(
                selectinload(Video.section_groups).selectinload(SectionGroup.sections)
            )
            .offset(skip)
            .limit(limit)
            .order_by(Video.upload_date.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_video(db: AsyncSession, video_id: UUID, video_update: VideoUpdate) -> Optional[Video]:
        """Update video"""
        # Filter out None values from update
        update_data = {k: v for k, v in video_update.model_dump().items() if v is not None}
        
        if update_data:
            await db.execute(
                update(Video)
                .where(Video.video_id == video_id)
                .values(**update_data)
            )
            await db.commit()
        
        return await VideoCRUD.get_video(db, video_id)
    
    @staticmethod
    async def delete_video(db: AsyncSession, video_id: UUID) -> bool:
        """Delete video"""
        result = await db.execute(
            delete(Video).where(Video.video_id == video_id)
        )
        await db.commit()
        return result.rowcount > 0

# Coaching Reservation CRUD operations
class CoachingReservationCRUD:
    
    @staticmethod
    async def create_reservation(db: AsyncSession, reservation: CoachingReservationCreate) -> CoachingReservation:
        """Create a new coaching reservation"""
        db_reservation = CoachingReservation(**reservation.model_dump())
        db.add(db_reservation)
        await db.commit()
        await db.refresh(db_reservation)
        return db_reservation
    
    @staticmethod
    async def get_reservation(db: AsyncSession, session_id: UUID) -> Optional[CoachingReservation]:
        """Get reservation by session ID"""
        result = await db.execute(
            select(CoachingReservation).where(CoachingReservation.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_reservations_by_user(db: AsyncSession, user_id: UUID) -> List[CoachingReservation]:
        """Get reservations by user ID"""
        result = await db.execute(
            select(CoachingReservation)
            .where(CoachingReservation.user_id == user_id)
            .order_by(CoachingReservation.session_date.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_reservations_by_coach(db: AsyncSession, coach_id: UUID) -> List[CoachingReservation]:
        """Get reservations by coach ID"""
        result = await db.execute(
            select(CoachingReservation)
            .where(CoachingReservation.coach_id == coach_id)
            .order_by(CoachingReservation.session_date.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_reservation(db: AsyncSession, session_id: UUID, reservation_update: CoachingReservationUpdate) -> Optional[CoachingReservation]:
        """Update coaching reservation"""
        update_data = {k: v for k, v in reservation_update.model_dump().items() if v is not None}
        
        if update_data:
            await db.execute(
                update(CoachingReservation)
                .where(CoachingReservation.session_id == session_id)
                .values(**update_data)
            )
            await db.commit()
        
        return await CoachingReservationCRUD.get_reservation(db, session_id)

# Section Group CRUD operations
class SectionGroupCRUD:
    
    @staticmethod
    async def create_section_group(db: AsyncSession, section_group: SectionGroupCreate) -> SectionGroup:
        """Create a new section group"""
        db_section_group = SectionGroup(**section_group.model_dump())
        db.add(db_section_group)
        await db.commit()
        await db.refresh(db_section_group)
        return db_section_group
    
    @staticmethod
    async def get_section_group(db: AsyncSession, section_group_id: UUID) -> Optional[SectionGroup]:
        """Get section group by ID"""
        result = await db.execute(
            select(SectionGroup).where(SectionGroup.section_group_id == section_group_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_section_group_with_sections(db: AsyncSession, section_group_id: UUID) -> Optional[SectionGroup]:
        """Get section group with all sections"""
        result = await db.execute(
            select(SectionGroup)
            .options(selectinload(SectionGroup.sections))
            .where(SectionGroup.section_group_id == section_group_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def add_overall_feedback(
        db: AsyncSession, 
        section_group_id: UUID, 
        overall_feedback: str, 
        overall_feedback_summary: str
    ) -> Optional[SectionGroup]:
        """Add overall feedback to section group"""
        from datetime import datetime, timezone
        
        await db.execute(
            update(SectionGroup)
            .where(SectionGroup.section_group_id == section_group_id)
            .values(
                overall_feedback=overall_feedback,
                overall_feedback_summary=overall_feedback_summary,
                feedback_created_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()
        
        return await SectionGroupCRUD.get_section_group(db, section_group_id)
    
    @staticmethod
    async def add_next_training_menu(
        db: AsyncSession, 
        section_group_id: UUID, 
        next_training_menu: str, 
        next_training_menu_summary: str
    ) -> Optional[SectionGroup]:
        """Add next training menu to section group"""
        from datetime import datetime, timezone
        
        await db.execute(
            update(SectionGroup)
            .where(SectionGroup.section_group_id == section_group_id)
            .values(
                next_training_menu=next_training_menu,
                next_training_menu_summary=next_training_menu_summary,
                feedback_created_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()
        
        return await SectionGroupCRUD.get_section_group(db, section_group_id)

# Swing Section CRUD operations
class SwingSectionCRUD:
    
    @staticmethod
    async def create_section(db: AsyncSession, section: SwingSectionCreate) -> SwingSection:
        """Create a new swing section"""
        db_section = SwingSection(**section.model_dump())
        db.add(db_section)
        await db.commit()
        await db.refresh(db_section)
        return db_section
    
    @staticmethod
    async def get_section(db: AsyncSession, section_id: UUID) -> Optional[SwingSection]:
        """Get swing section by ID"""
        result = await db.execute(
            select(SwingSection).where(SwingSection.section_id == section_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_sections_by_group(db: AsyncSession, section_group_id: UUID) -> List[SwingSection]:
        """Get all sections for a section group"""
        result = await db.execute(
            select(SwingSection)
            .where(SwingSection.section_group_id == section_group_id)
            .order_by(SwingSection.start_sec)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_section(db: AsyncSession, section_id: UUID, section_update: SwingSectionUpdate) -> Optional[SwingSection]:
        """Update swing section"""
        update_data = {k: v for k, v in section_update.model_dump().items() if v is not None}
        
        if update_data:
            await db.execute(
                update(SwingSection)
                .where(SwingSection.section_id == section_id)
                .values(**update_data)
            )
            await db.commit()
        
        return await SwingSectionCRUD.get_section(db, section_id)
    
    @staticmethod
    async def delete_section(db: AsyncSession, section_id: UUID) -> bool:
        """Delete swing section"""
        result = await db.execute(
            delete(SwingSection).where(SwingSection.section_id == section_id)
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def add_coach_comment(db: AsyncSession, section_id: UUID, comment: str, summary: str) -> Optional[SwingSection]:
        """Add coach comment and summary to section"""
        await db.execute(
            update(SwingSection)
            .where(SwingSection.section_id == section_id)
            .values(coach_comment=comment, coach_comment_summary=summary)
        )
        await db.commit()
        
        return await SwingSectionCRUD.get_section(db, section_id)

# Create instances for easy import
video_crud = VideoCRUD()
coaching_reservation_crud = CoachingReservationCRUD()
section_group_crud = SectionGroupCRUD()
swing_section_crud = SwingSectionCRUD()