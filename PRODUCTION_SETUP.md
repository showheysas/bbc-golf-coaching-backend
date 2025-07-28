# 本番環境セットアップ手順 (Docker不使用)

## 前提条件

### 1. システム要件
- Python 3.8+
- MySQL 8.0+
- Node.js 18+ (フロントエンド用)

### 2. MySQL設定
```bash
# MySQL 8.0をインストール (ポート3306)
# データベースとユーザーを作成
CREATE DATABASE bbc_production;
CREATE USER 'bbc_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON bbc_production.* TO 'bbc_user'@'localhost';
FLUSH PRIVILEGES;
```

## セットアップ手順

### 1. 本番環境設定の適用
```bash
cd backend
python setup_environment.py production
```

### 2. 本番用設定の編集
```bash
# .env.productionを編集
# - DATABASE_URLのパスワードを実際の値に変更
# - AZURE_STORAGE_CONNECTION_STRINGを本番用に変更
# - OPENAI_API_KEYを本番用に変更
```

### 3. 依存関係インストール
```bash
# バックエンド
cd backend
pip install -r requirements.txt

# フロントエンド
cd ../frontend
npm install
npm run build
```

### 4. データベース初期化
```bash
cd backend
alembic upgrade head
```

### 5. 本番サーバー起動

#### バックエンド
```bash
cd backend
python start_production.py
```

#### フロントエンド (別ターミナル)
```bash
cd frontend
npm start
```

## パフォーマンス最適化

### 1. **軽量化のメリット**
- ✅ Dockerオーバーヘッドなし
- ✅ 直接OS上で実行 (高速)
- ✅ メモリ使用量削減
- ✅ 起動時間短縮

### 2. **本番運用設定**
- Uvicorn: 4ワーカープロセス
- Keep-alive接続
- ログレベル: INFO
- 自動再起動: 無効

### 3. **推奨監視**
```bash
# プロセス監視
ps aux | grep uvicorn

# ポート確認
netstat -tulpn | grep 8000

# リソース監視
top -p $(pgrep -f uvicorn)
```

## 環境切り替え

### 開発環境に戻す
```bash
python setup_environment.py development
```

### 現在の設定確認
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Environment:', os.getenv('ENVIRONMENT', 'not set'))
print('Database:', os.getenv('DATABASE_URL', 'not set')[:50] + '...')
"
```

## トラブルシューティング

### MySQL接続エラー
```bash
# 接続テスト
python check_mysql_status.py

# MySQLサービス確認
systemctl status mysql  # Linux
net start mysql        # Windows
```

### ポート競合
```bash
# ポート使用状況確認
netstat -tulpn | grep :8000
lsof -i :8000  # Linux/Mac
```