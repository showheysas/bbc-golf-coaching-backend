import logging
import sys
from pathlib import Path

def setup_logger():
    """ロガーをセットアップ"""
    
    # ログディレクトリ作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # ロガー設定
    logger = logging.getLogger("golf_coaching")
    logger.setLevel(logging.DEBUG)
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(
        log_dir / "app.log", 
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # ハンドラー追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# グローバルロガー
logger = setup_logger()