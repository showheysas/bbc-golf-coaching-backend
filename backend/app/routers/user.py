from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.deps import get_database, get_default_user_id
from app.schemas import (
    VideoResponse, VideoWithSectionsResponse, CoachingReservationResponse,
    CoachingReservationCreate, CoachingReservationUpdate
)
from app.crud import video_crud, coaching_reservation_crud, section_group_crud, swing_section_crud

router = APIRouter()

@router.get("/my-videos", response_model=List[VideoResponse])
async def get_my_videos(
    user_id: Optional[str] = Query(None, description="User ID (uses default if not provided)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get all videos for a user
    
    - **user_id**: User ID (optional, uses default if not provided)
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    try:
        actual_user_id = user_id if user_id else get_default_user_id()
        videos = await video_crud.get_videos_by_user(db, UUID(actual_user_id), skip, limit)
        return videos
        
    except ValueError:
        raise HTTPException(status_code=400, detail="無効なユーザーIDです")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"動画一覧の取得に失敗しました: {str(e)}")

@router.get("/video/{video_id}", response_model=VideoResponse)
async def get_video_details(
    video_id: UUID,
    db: AsyncSession = Depends(get_database)
):
    """
    Get detailed information about a specific video
    
    - **video_id**: ID of the video
    """
    try:
        video = await video_crud.get_video(db, video_id)
        if not video:
            raise HTTPException(status_code=404, detail="動画が見つかりません")
        
        return video
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"動画詳細の取得に失敗しました: {str(e)}")

@router.get("/video/{video_id}/with-sections", response_model=VideoWithSectionsResponse)
async def get_video_with_sections(
    video_id: UUID,
    db: AsyncSession = Depends(get_database)
):
    """
    Get video with all coaching sections and comments
    
    - **video_id**: ID of the video
    """
    try:
        # Get video with sections
        video = await video_crud.get_video_with_sections(db, video_id)
        if not video:
            raise HTTPException(status_code=404, detail="動画が見つかりません")
        
        # Prepare response data
        response_data = {
            "video_id": video.video_id,
            "user_id": video.user_id,
            "video_url": video.video_url,
            "thumbnail_url": video.thumbnail_url,
            "upload_date": video.upload_date,
            "club_type": video.club_type,
            "swing_form": video.swing_form,
            "swing_note": video.swing_note,
            "section_group_id": video.section_groups[0].section_group_id if video.section_groups else None,
            "created_at": video.created_at,
            "updated_at": video.updated_at,
            "sections": []
        }
        
        # Add section group and sections if they exist
        if video.section_groups:
            # Get the first section group (assuming one per video for now)
            section_group = video.section_groups[0]
            response_data["section_group"] = {
                "section_group_id": section_group.section_group_id,
                "video_id": section_group.video_id,
                "created_at": section_group.created_at
            }
            
            if section_group.sections:
                response_data["sections"] = [
                    {
                        "section_id": section.section_id,
                        "section_group_id": section.section_group_id,
                        "start_sec": section.start_sec,
                        "end_sec": section.end_sec,
                        "image_url": section.image_url,
                        "tags": section.tags,
                        "markup_json": section.markup_json,
                        "coach_comment": section.coach_comment,
                        "coach_comment_summary": section.coach_comment_summary,
                        "created_at": section.created_at
                    }
                    for section in section_group.sections
                ]
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"動画とセクション情報の取得に失敗しました: {str(e)}")

@router.get("/my-reservations", response_model=List[CoachingReservationResponse])
async def get_my_reservations(
    user_id: Optional[str] = Query(None, description="User ID (uses default if not provided)"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get all coaching reservations for a user
    
    - **user_id**: User ID (optional, uses default if not provided)
    """
    try:
        actual_user_id = user_id if user_id else get_default_user_id()
        reservations = await coaching_reservation_crud.get_reservations_by_user(db, UUID(actual_user_id))
        return reservations
        
    except ValueError:
        raise HTTPException(status_code=400, detail="無効なユーザーIDです")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"予約一覧の取得に失敗しました: {str(e)}")

@router.post("/create-reservation", response_model=CoachingReservationResponse)
async def create_coaching_reservation(
    reservation: CoachingReservationCreate,
    db: AsyncSession = Depends(get_database)
):
    """
    Create a new coaching reservation
    
    - **reservation**: Reservation details
    """
    try:
        db_reservation = await coaching_reservation_crud.create_reservation(db, reservation)
        return db_reservation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"予約の作成に失敗しました: {str(e)}")

@router.put("/reservation/{session_id}", response_model=CoachingReservationResponse)
async def update_coaching_reservation(
    session_id: UUID,
    reservation_update: CoachingReservationUpdate,
    db: AsyncSession = Depends(get_database)
):
    """
    Update a coaching reservation
    
    - **session_id**: ID of the reservation session
    - **reservation_update**: Updated reservation data
    """
    try:
        updated_reservation = await coaching_reservation_crud.update_reservation(
            db, session_id, reservation_update
        )
        
        if not updated_reservation:
            raise HTTPException(status_code=404, detail="予約が見つかりません")
        
        return updated_reservation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"予約の更新に失敗しました: {str(e)}")

@router.get("/reservation/{session_id}", response_model=CoachingReservationResponse)
async def get_reservation_details(
    session_id: UUID,
    db: AsyncSession = Depends(get_database)
):
    """
    Get detailed information about a specific reservation
    
    - **session_id**: ID of the reservation session
    """
    try:
        reservation = await coaching_reservation_crud.get_reservation(db, session_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="予約が見つかりません")
        
        return reservation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"予約詳細の取得に失敗しました: {str(e)}")

@router.get("/video/{video_id}/feedback-summary")
async def get_video_feedback_summary(
    video_id: UUID,
    db: AsyncSession = Depends(get_database)
):
    """
    Get a summary of all feedback for a video
    
    - **video_id**: ID of the video
    """
    try:
        # Get video with sections
        video = await video_crud.get_video_with_sections(db, video_id)
        if not video:
            raise HTTPException(status_code=404, detail="動画が見つかりません")
        
        feedback_summary = {
            "video_id": video_id,
            "video_info": {
                "club_type": video.club_type,
                "swing_form": video.swing_form,
                "swing_note": video.swing_note,
                "upload_date": video.upload_date
            },
            "total_sections": 0,
            "sections_with_comments": 0,
            "feedback_sections": []
        }
        
        if video.section_groups and video.section_groups[0].sections:
            sections = video.section_groups[0].sections
            feedback_summary["total_sections"] = len(sections)
            
            for section in sections:
                section_data = {
                    "section_id": section.section_id,
                    "time_range": f"{section.start_sec}-{section.end_sec}秒",
                    "tags": section.tags or [],
                    "has_comment": bool(section.coach_comment),
                    "comment_summary": section.coach_comment_summary
                }
                
                if section.coach_comment:
                    feedback_summary["sections_with_comments"] += 1
                    section_data["full_comment"] = section.coach_comment
                
                feedback_summary["feedback_sections"].append(section_data)
        
        return feedback_summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"フィードバック要約の取得に失敗しました: {str(e)}")

@router.get("/videos", response_model=List[VideoWithSectionsResponse])
async def get_all_videos(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get all videos for coach dashboard (all users)
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    try:
        videos = await video_crud.get_all_videos_with_sections(db, skip, limit)
        return videos
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"全動画一覧の取得に失敗しました: {str(e)}")

@router.get("/videos/search")
async def search_videos(
    user_id: Optional[str] = Query(None, description="User ID (uses default if not provided)"),
    club_type: Optional[str] = Query(None, description="Filter by club type"),
    swing_form: Optional[str] = Query(None, description="Filter by swing form"),
    has_feedback: Optional[bool] = Query(None, description="Filter videos with/without feedback"),
    db: AsyncSession = Depends(get_database)
):
    """
    Search and filter videos based on criteria
    
    - **user_id**: User ID (optional, uses default if not provided)
    - **club_type**: Filter by club type
    - **swing_form**: Filter by swing form
    - **has_feedback**: Filter videos with or without coaching feedback
    """
    try:
        actual_user_id = user_id if user_id else get_default_user_id()
        
        # Get all user videos first (for simplicity - in production, this would be optimized)
        videos = await video_crud.get_videos_by_user(db, UUID(actual_user_id))
        
        # Apply filters
        filtered_videos = []
        for video in videos:
            # Filter by club type
            if club_type and video.club_type != club_type:
                continue
            
            # Filter by swing form
            if swing_form and video.swing_form != swing_form:
                continue
            
            # Filter by feedback presence
            if has_feedback is not None:
                has_sections = bool(video.section_groups)
                if has_feedback != has_sections:
                    continue
            
            filtered_videos.append(video)
        
        return {
            "total_found": len(filtered_videos),
            "filters_applied": {
                "club_type": club_type,
                "swing_form": swing_form,
                "has_feedback": has_feedback
            },
            "videos": filtered_videos
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="無効なユーザーIDです")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"動画検索に失敗しました: {str(e)}")