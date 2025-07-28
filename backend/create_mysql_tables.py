#!/usr/bin/env python3
"""
MySQL テーブル作成スクリプト - 初期設計に基づく
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from app.models import Base

load_dotenv()

async def create_mysql_tables():
    """MySQL にテーブルを作成"""
    
    # MySQL用のDATABASE_URLを設定
    mysql_url = os.getenv("MYSQL_DATABASE_URL", "mysql+asyncmy://root:password@localhost:3306/golf_coaching")
    
    print(f"🔗 MySQL接続: {mysql_url.replace('password', '****')}")
    
    try:
        # MySQL エンジンを作成
        engine = create_async_engine(mysql_url, echo=True)
        
        print("📋 テーブル作成開始...")
        
        # テーブル作成
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ テーブル作成完了!")
        
        # 作成されたテーブルを確認
        async with engine.begin() as conn:
            result = await conn.execute("SHOW TABLES")
            tables = result.fetchall()
            print(f"📊 作成されたテーブル: {[table[0] for table in tables]}")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("💡 MySQL サービスが起動していることを確認してください")
        print("💡 データベース 'golf_coaching' が存在することを確認してください")
        print("\n📝 データベース作成コマンド:")
        print("mysql -u root -p -e \"CREATE DATABASE IF NOT EXISTS golf_coaching;\"")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_mysql_tables())