#!/usr/bin/env python3
"""
Azure Blob Storage内のファイル一覧を表示
"""
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

load_dotenv()

def list_blob_files():
    """Blob Storage内のファイル一覧を表示"""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "bbc-test")
    
    if not connection_string:
        print("❌ AZURE_STORAGE_CONNECTION_STRINGが設定されていません")
        return
    
    try:
        # Blob Service Clientを作成
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        print(f"=== Container '{container_name}' のファイル一覧 ===")
        
        # ファイル一覧を取得
        blob_list = container_client.list_blobs()
        
        files = list(blob_list)
        if not files:
            print("ファイルが見つかりません")
            return
        
        print(f"ファイル数: {len(files)}")
        print("")
        
        for i, blob in enumerate(files, 1):
            print(f"{i}. {blob.name}")
            print(f"   サイズ: {blob.size:,} bytes")
            print(f"   最終更新: {blob.last_modified}")
            print(f"   Content-Type: {blob.content_settings.content_type if blob.content_settings else 'N/A'}")
            
            # 直接URLを構築
            direct_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob.name}"
            print(f"   直接URL: {direct_url}")
            print("")
        
        return files
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

if __name__ == "__main__":
    files = list_blob_files()