from datetime import datetime, timezone
import pytz

# 日本時間のタイムゾーン
JST = pytz.timezone('Asia/Tokyo')

def to_jst(dt: datetime) -> datetime:
    """
    UTCの日時を日本時間に変換する
    
    Args:
        dt: UTC日時のdatetimeオブジェクト
        
    Returns:
        日本時間のdatetimeオブジェクト
    """
    if dt is None:
        return None
        
    # UTCタイムゾーンを設定（ない場合）
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # 日本時間に変換
    return dt.astimezone(JST)

def now_jst() -> datetime:
    """
    現在の日本時間を取得する
    
    Returns:
        現在の日本時間のdatetimeオブジェクト
    """
    return datetime.now(JST)