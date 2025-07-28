from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import uuid
import os
import shutil
import traceback
import aiohttp
import asyncio
import io
import subprocess
import tempfile
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from dotenv import load_dotenv

from app.deps import get_database, get_default_user_id
from app.schemas import VideoResponse, VideoUploadRequest
from app.crud import video_crud
from app.services.storage import storage_service
from app.services.thumbnail import thumbnail_service
from app.models import Video, Base, engine
from app.utils.logger import logger

router = APIRouter()

@router.post("/upload-video", response_model=VideoResponse)
async def upload_video(
    video_file: UploadFile = File(...),
    club_type: Optional[str] = Form(None),
    swing_form: Optional[str] = Form(None),
    swing_note: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_database)
):
    """
    Upload golf swing video
    
    - **video_file**: Video file to upload (MP4 recommended)
    - **club_type**: Type of club used (optional)
    - **swing_form**: Swing type (e.g., full_swing, chip) (optional)
    - **swing_note**: User's notes about the swing (optional)
    - **user_id**: User ID (optional, uses default if not provided)
    """
    try:
        logger.info(f"動画アップロード開始: ファイル名={video_file.filename}, サイズ={video_file.size}")
        
        # Validate file type
        if not video_file.content_type or not video_file.content_type.startswith('video/'):
            logger.error(f"無効なファイル形式: {video_file.content_type}")
            raise HTTPException(status_code=400, detail="アップロードされたファイルは動画ファイルである必要があります")
        
        # Get user ID (use provided or default)
        actual_user_id = user_id if user_id else get_default_user_id()
        logger.info(f"ユーザーID: {actual_user_id}")
        
        # Read video content once for both upload and thumbnail generation
        video_file.file.seek(0)
        video_content = video_file.file.read()
        logger.info(f"動画データ読み込み完了: {len(video_content)} bytes")
        
        # Upload video to storage
        from io import BytesIO
        video_bytes_for_upload = BytesIO(video_content)
        logger.info("動画をストレージにアップロード中...")
        video_url = await storage_service.upload_video(
            video_bytes_for_upload,
            video_file.filename or "video.mp4"
        )
        logger.info(f"動画アップロード完了: {video_url}")
        
        # Extract the actual filename from video URL for thumbnail naming
        video_filename = video_url.split('/')[-1]  # Get filename from URL
        thumbnail_base_name = video_filename.rsplit('.', 1)[0]  # Remove extension
        
        # Generate thumbnail from video
        thumbnail_url = None
        try:
            logger.info("サムネイル生成開始...")
            # Create BytesIO object for thumbnail generation
            video_bytes_for_thumbnail = BytesIO(video_content)
            
            thumbnail_data = await thumbnail_service.generate_thumbnail(
                video_bytes_for_thumbnail,
                video_file.filename or "video.mp4"
            )
            logger.info("サムネイル生成完了、ストレージにアップロード中...")
            
            # Upload thumbnail with same base name as video
            thumbnail_filename = f"{thumbnail_base_name}.jpg"
            thumbnail_url = await storage_service.upload_image_with_exact_name(
                thumbnail_data,
                thumbnail_filename
            )
            logger.info(f"サムネイルアップロード完了: {thumbnail_url}")
        except Exception as e:
            logger.warning(f"サムネイル生成失敗: {e}")
            logger.warning(f"サムネイルエラー詳細: {traceback.format_exc()}")
            # Continue without thumbnail - it's not critical for video upload
        
        # Create video record in database
        logger.info("データベースに動画レコードを保存中...")
        video_data = {
            "user_id": UUID(actual_user_id),
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "club_type": club_type,
            "swing_form": swing_form,
            "swing_note": swing_note
        }
        logger.info(f"動画データ: {video_data}")
        
        # Create video in database
        from app.schemas import VideoCreate
        video_create = VideoCreate(**video_data)
        db_video = await video_crud.create_video(db, video_create)
        logger.info(f"データベース保存完了: video_id={db_video.video_id}")
        
        return db_video
        
    except ValueError as e:
        logger.error(f"無効なデータ: {str(e)}")
        raise HTTPException(status_code=400, detail=f"無効なデータ: {str(e)}")
    except Exception as e:
        logger.error(f"動画アップロード失敗: {str(e)}")
        logger.error(f"エラー詳細: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"動画のアップロードに失敗しました: {str(e)}")

@router.post("/upload-thumbnail/{video_id}")
async def upload_thumbnail(
    video_id: UUID,
    thumbnail_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_database)
):
    """
    Upload thumbnail image for a video
    
    - **video_id**: ID of the video
    - **thumbnail_file**: Thumbnail image file
    """
    try:
        # Check if video exists
        video = await video_crud.get_video(db, video_id)
        if not video:
            raise HTTPException(status_code=404, detail="動画が見つかりません")
        
        # Validate file type
        if not thumbnail_file.content_type or not thumbnail_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="アップロードされたファイルは画像ファイルである必要があります")
        
        # Upload thumbnail to storage
        thumbnail_url = await storage_service.upload_image(
            thumbnail_file.file,
            thumbnail_file.filename or "thumbnail.jpg"
        )
        
        # Update video with thumbnail URL
        from app.schemas import VideoUpdate
        video_update = VideoUpdate(thumbnail_url=thumbnail_url)
        updated_video = await video_crud.update_video(db, video_id, video_update)
        
        return {
            "message": "サムネイルが正常にアップロードされました",
            "thumbnail_url": thumbnail_url,
            "video": updated_video
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"サムネイルのアップロードに失敗しました: {str(e)}")

@router.get("/upload-status/{video_id}")
async def get_upload_status(
    video_id: UUID,
    db: AsyncSession = Depends(get_database)
):
    """
    Get upload status and video information
    
    - **video_id**: ID of the video
    """
    try:
        video = await video_crud.get_video_with_sections(db, video_id)
        if not video:
            raise HTTPException(status_code=404, detail="動画が見つかりません")
        
        return {
            "video_id": video.video_id,
            "status": "completed",
            "video_url": video.video_url,
            "thumbnail_url": video.thumbnail_url,
            "upload_date": video.upload_date,
            "club_type": video.club_type,
            "swing_form": video.swing_form,
            "swing_note": video.swing_note,
            "has_sections": bool(video.section_groups)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アップロード状況の取得に失敗しました: {str(e)}")

@router.delete("/video/{video_id}")
async def delete_video(
    video_id: UUID,
    db: AsyncSession = Depends(get_database)
):
    """
    Delete a video and its associated files
    
    - **video_id**: ID of the video to delete
    """
    try:
        # Get video to retrieve file URLs
        video = await video_crud.get_video(db, video_id)
        if not video:
            raise HTTPException(status_code=404, detail="動画が見つかりません")
        
        # Delete files from storage
        try:
            await storage_service.delete_file(video.video_url)
            if video.thumbnail_url:
                await storage_service.delete_file(video.thumbnail_url)
        except Exception as e:
            print(f"Warning: Failed to delete files from storage: {e}")
        
        # Delete video record from database
        success = await video_crud.delete_video(db, video_id)
        if not success:
            raise HTTPException(status_code=404, detail="動画が見つかりません")
        
        return {"message": "動画が正常に削除されました"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"動画の削除に失敗しました: {str(e)}")


@router.post("/clear-all-data")
async def clear_all_data(
    db: AsyncSession = Depends(get_database)
):
    """
    Clear all video data and uploaded files
    WARNING: This will delete all data permanently!
    """
    try:
        # Delete all database tables and recreate them
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        # Clear uploads directory
        uploads_dir = "uploads"
        if os.path.exists(uploads_dir):
            shutil.rmtree(uploads_dir)
            os.makedirs(uploads_dir)
        
        return {"message": "全てのデータとファイルがクリアされました"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データクリアに失敗しました: {str(e)}")


@router.get("/proxy-file/{file_url:path}")
async def proxy_file(file_url: str):
    """
    Azure Blob Storage ファイルをプロキシ経由で配信
    CORS問題を回避するためのエンドポイント
    """
    try:
        # Azure Blob URLの場合のみプロキシ
        if not file_url.startswith('https://') or 'blob.core.windows.net' not in file_url:
            raise HTTPException(status_code=400, detail="Invalid file URL")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=404, detail="File not found")
                
                # Content-Typeを取得
                content_type = response.headers.get('content-type', 'application/octet-stream')
                
                # ファイルコンテンツを読み取り
                content = await response.read()
                
                return StreamingResponse(
                    io.BytesIO(content),
                    media_type=content_type,
                    headers={
                        "Cache-Control": "public, max-age=3600",  # 1時間キャッシュ
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET",
                        "Access-Control-Allow-Headers": "*"
                    }
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ファイルプロキシエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ファイルの取得に失敗しました: {str(e)}")


@router.get("/media-url")
async def get_media_url(blob_url: str):
    """
    Azure Blob URLからSAS付きURLを生成
    """
    try:
        # Azure Blob設定を取得
        load_dotenv()
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_STORAGE_CONTAINER", "bbc-test")
        
        if not connection_string:
            raise HTTPException(status_code=500, detail="Azure接続設定が見つかりません")
        
        # Blob URLからファイル名を抽出
        # 例: https://account.blob.core.windows.net/container/filename -> filename
        if not blob_url.startswith('https://') or 'blob.core.windows.net' not in blob_url:
            raise HTTPException(status_code=400, detail="無効なBlob URL")
        
        # URLからファイル名を抽出
        url_parts = blob_url.split('/')
        filename = url_parts[-1]
        
        # Blob Service Clientを作成
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # SASトークンを生成（10分間有効）
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_name,
            blob_name=filename,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=10)
        )
        
        # SAS付きURLを生成
        sas_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{filename}?{sas_token}"
        
        return {"url": sas_url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SAS URL生成エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL生成に失敗しました: {str(e)}")


@router.get("/media-url-simple")
async def get_media_url_simple(filename: str):
    """
    ファイル名からSAS付きURLを生成（シンプル版）
    """
    try:
        # Azure Blob設定を取得
        load_dotenv()
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_STORAGE_CONTAINER", "bbc-test")
        
        if not connection_string:
            raise HTTPException(status_code=500, detail="Azure接続設定が見つかりません")
        
        # Blob Service Clientを作成
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # SASトークンを生成（10分間有効）
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_name,
            blob_name=filename,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=10)
        )
        
        # SAS付きURLを生成
        sas_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{filename}?{sas_token}"
        
        return {"url": sas_url}
        
    except Exception as e:
        logger.error(f"SAS URL生成エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL生成に失敗しました: {str(e)}")

@router.post("/capture-video-frame")
async def capture_video_frame(
    video_url: str = Form(...),
    time_seconds: float = Form(...),
    filename: Optional[str] = Form(None)
):
    """
    動画の指定された時間のフレームをキャプチャしてAzure Blob Storageに保存
    
    - **video_url**: 動画のURL（Azure Blob URLまたはSAS URL）
    - **time_seconds**: キャプチャする時間（秒）
    - **filename**: 保存するファイル名（オプション）
    """
    try:
        logger.info(f"動画フレームキャプチャ開始: URL={video_url}, 時間={time_seconds}秒")
        
        # ファイル名を生成
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}_{time_seconds:.1f}s.jpg"
        
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
            video_temp_path = temp_video.name
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_image:
            image_temp_path = temp_image.name
        
        try:
            # 動画をダウンロード
            logger.info("動画をダウンロード中...")
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=400, detail="動画のダウンロードに失敗しました")
                    
                    video_content = await response.read()
                    with open(video_temp_path, 'wb') as f:
                        f.write(video_content)
            
            logger.info(f"動画ダウンロード完了: {len(video_content)} bytes")
            # ファイルサイズチェック（1MB未満は失敗とみなす）
            if os.path.getsize(video_temp_path) < 1024 * 1024:
                logger.error("ダウンロードした動画ファイルが小さすぎます。URLやSASトークンを確認してください。")
                raise HTTPException(status_code=400, detail="動画ファイルのダウンロードに失敗しました（サイズが小さすぎます）")
            
            # FFmpegを使用してフレームをキャプチャ（より確実な設定）
            logger.info(f"FFmpegでフレームキャプチャ中: {time_seconds}秒")
            cmd = [
                'ffmpeg',
                '-analyzeduration', '2147483647',
                '-probesize', '2147483647',
                '-ss', str(time_seconds),
                '-i', video_temp_path,
                '-frames:v', '1',
                '-q:v', '2',  # 高品質
                '-avoid_negative_ts', 'make_zero',  # 負のタイムスタンプを回避
                '-y',  # 上書き
                image_temp_path
            ]
            
            logger.info(f"FFmpegコマンド実行: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            logger.info(f"FFmpeg実行結果: returncode={result.returncode}")
            if result.stdout:
                logger.info(f"FFmpeg stdout: {result.stdout}")
            if result.stderr:
                logger.info(f"FFmpeg stderr: {result.stderr}")
            
            if result.returncode != 0:
                logger.error(f"FFmpegエラー: {result.stderr}")
                raise HTTPException(status_code=500, detail=f"フレームキャプチャに失敗しました: {result.stderr}")
            
            logger.info("フレームキャプチャ完了")
            
            # キャプチャした画像を読み込み
            with open(image_temp_path, 'rb') as f:
                image_data = f.read()
            
            # Azure Blob Storageにアップロード（正確なファイル名で保存）
            logger.info("Azure Blob Storageにアップロード中...")
            image_url = await storage_service.upload_image_with_exact_name(
                io.BytesIO(image_data),
                filename
            )
            
            logger.info(f"アップロード完了: {image_url}")
            
            return {
                "success": True,
                "image_url": image_url,
                "filename": filename,
                "capture_time": time_seconds,
                "ffmpeg_stdout": result.stdout,
                "ffmpeg_stderr": result.stderr
            }
            
        finally:
            # 一時ファイルを削除
            try:
                os.unlink(video_temp_path)
                os.unlink(image_temp_path)
            except:
                pass
                
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        logger.error("FFmpegタイムアウト")
        raise HTTPException(status_code=500, detail="フレームキャプチャがタイムアウトしました")
    except Exception as e:
        logger.error(f"動画フレームキャプチャエラー: {str(e)}")
        logger.error(f"エラー詳細: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"フレームキャプチャに失敗しました: {str(e)}")