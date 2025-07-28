from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
from app.utils.logger import logger
from app.services.storage import storage_service
import io

load_dotenv()

router = APIRouter()

# OpenAI クライアント初期化
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/transcribe-audio")
async def transcribe_audio(
    audio: UploadFile = File(...),
    type: Optional[str] = Form("general"),
    video_filename: Optional[str] = Form(None),
    phase_code: Optional[str] = Form(None)
):
    """
    音声ファイルをWhisper APIを使って文字起こしし、Blobストレージに保存する
    
    - **audio**: 音声ファイル (WAV, MP3, M4A等)
    - **type**: 音声の種類 (advice, practice, phase_advice)
    - **video_filename**: 動画ファイル名
    - **phase_code**: スイング段階コード (phase_adviceの場合)
    """
    try:
        logger.info(f"音声文字起こし開始: ファイル名={audio.filename}, タイプ={type}")
        
        # OpenAI APIキーの確認
        if not client.api_key:
            raise HTTPException(status_code=500, detail="OpenAI APIキーが設定されていません")
        
        # 音声ファイルの検証
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            logger.error(f"無効なファイル形式: {audio.content_type}")
            raise HTTPException(status_code=400, detail="音声ファイルをアップロードしてください")
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file_path = temp_file.name
            
            # ファイル内容を読み込んで一時ファイルに書き込み
            audio_content = await audio.read()
            temp_file.write(audio_content)
            temp_file.flush()
            
            logger.info(f"一時ファイル作成: {temp_file_path}, サイズ: {len(audio_content)} bytes")
        
        try:
            # Whisper APIで文字起こし
            logger.info("Whisper APIで文字起こし中...")
            
            with open(temp_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ja"  # 日本語指定
                )
            
            transcription_text = transcript.text
            logger.info(f"文字起こし完了: {transcription_text[:100]}...")
            
            # 音声ファイルをBlobストレージに保存
            audio_url = None
            try:
                audio_filename = generate_audio_filename(type, video_filename, phase_code)
                logger.info(f"音声ファイル保存中: {audio_filename}")
                
                # 音声データをBytesIOに変換
                audio_stream = io.BytesIO(audio_content)
                audio_url = await storage_service.upload_audio_with_exact_name(audio_stream, audio_filename)
                
                logger.info(f"音声ファイル保存完了: {audio_url}")
            except Exception as e:
                logger.warning(f"音声ファイル保存失敗: {e}")
                # 文字起こしは成功しているので継続
            
            return {
                "success": True,
                "transcription": transcription_text,
                "type": type,
                "audio_url": audio_url,
                "audio_filename": audio_filename if 'audio_filename' in locals() else None,
                "audio_duration": None
            }
            
        finally:
            # 一時ファイルを削除
            try:
                os.unlink(temp_file_path)
                logger.info(f"一時ファイル削除: {temp_file_path}")
            except Exception as e:
                logger.warning(f"一時ファイル削除失敗: {e}")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"音声文字起こしエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"音声の文字起こしに失敗しました: {str(e)}")