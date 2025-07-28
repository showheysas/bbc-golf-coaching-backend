from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.models import create_tables
from app.routers import upload, coach, user, transcription
from app.services.storage import storage_service
import os
import io
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    yield
    # Shutdown - cleanup if needed

app = FastAPI(
    title="Golf Swing Coaching API",
    description="API for managing golf swing video coaching feedback",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(coach.router, prefix="/api/v1", tags=["coach"])
app.include_router(user.router, prefix="/api/v1", tags=["user"])
app.include_router(transcription.router, prefix="/api/v1", tags=["transcription"])

@app.get("/")
async def root():
    return {"message": "Golf Swing Coaching API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 動作確認済みのシンプルなSAS URL生成エンドポイント
@app.get("/media-url")
def get_media_url(filename: str):
    """
    Azure Blob StorageのファイルからSAS URLを生成（動作確認済み）
    """
    try:
        # Azure設定を取得
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_STORAGE_CONTAINER", "bbc-test")
        
        if not connection_string:
            raise HTTPException(status_code=500, detail="Azure接続設定が見つかりません")
        
        # Blob Service Client作成
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        account_key = blob_service_client.credential.account_key
        account_name = blob_service_client.account_name
        
        # SAS トークン生成（15分間有効）
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=filename,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=15),
        )
        
        # SAS付きURLを生成
        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{filename}?{sas_token}"
        
        return {"url": blob_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-section-image")
async def upload_section_image(image_file: UploadFile = File(...)):
    """
    セクション切り出し画像をAzure Blob Storageにアップロード
    """
    try:
        # ファイル形式チェック
        if not image_file.content_type or not image_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="画像ファイルのみアップロード可能です")
        
        # ファイル内容を読み込み
        file_content = await image_file.read()
        file_stream = io.BytesIO(file_content)
        
        # Azure Blob Storageにアップロード
        image_url = await storage_service.upload_image(file_stream, image_file.filename or "section_image.jpg")
        
        return {
            "success": True,
            "image_url": image_url,
            "message": "画像のアップロードが完了しました"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像アップロードに失敗しました: {str(e)}")