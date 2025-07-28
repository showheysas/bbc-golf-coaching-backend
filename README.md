# ゴルフスイング コーチング管理アプリ

ゴルフスイング動画に対するコーチング用フィードバック管理アプリです。  
ユーザーが動画をアップロード → コーチがシーンごとにマークアップして音声コメント → ユーザーが結果を閲覧する流れをサポートします。

## 🏗️ 技術構成

### バックエンド
- **FastAPI** + **SQLAlchemy** (非同期対応)
- **SQLite** (開発用) / **Azure MySQL** (本番用)対応
- **OpenAI API** (Whisper文字起こし + GPT要約)
- **Azure Blob Storage** / **ローカルストレージ** 切り替え可能

### フロントエンド
- **Next.js** + **TypeScript**
- **Tailwind CSS**
- **Axios** (API通信)

### インフラ
- **Docker** + **docker-compose**
- **Nginx** (プロダクション用プロキシ)

## 📁 プロジェクト構造

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI エントリポイント
│   │   ├── models.py            # SQLAlchemy ORM モデル
│   │   ├── schemas.py           # Pydantic スキーマ
│   │   ├── crud.py              # データベース操作
│   │   ├── deps.py              # 依存性注入
│   │   ├── services/
│   │   │   ├── storage.py       # ストレージ抽象化
│   │   │   ├── ai.py            # OpenAI 連携
│   │   │   └── transcription.py # Whisper 文字起こし
│   │   └── routers/
│   │       ├── upload.py        # 動画アップロード API
│   │       ├── coach.py         # コーチング機能 API
│   │       └── user.py          # ユーザー向け API
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── pages/
│   │   ├── index.tsx            # トップページ (動画アップロード)
│   │   └── videos/[id].tsx      # 動画詳細・フィードバック閲覧
│   ├── components/
│   │   ├── VideoUpload.tsx      # 動画アップロードコンポーネント
│   │   └── FeedbackViewer.tsx   # フィードバック表示コンポーネント
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── nginx.conf
└── README.md
```

## 🗄️ データベーステーブル

### 1. videos (動画情報)
| カラム | データ型 | 説明 |
|-------|---------|-----|
| video_id | UUID | 動画ID (主キー) |
| user_id | UUID | アップロードユーザーID |
| video_url | TEXT | 動画ファイルURL |
| thumbnail_url | TEXT | サムネイル画像URL |
| club_type | VARCHAR(50) | 使用クラブ種類 |
| swing_form | VARCHAR(50) | スイング種類 |
| swing_note | TEXT | ユーザーメモ |
| section_group_id | UUID | セクショングループID |

### 2. section_groups (セクショングループ)
| カラム | データ型 | 説明 |
|-------|---------|-----|
| section_group_id | UUID | グループID (主キー) |
| video_id | UUID | 対応動画ID |

### 3. swing_sections (スイングセクション)
| カラム | データ型 | 説明 |
|-------|---------|-----|
| section_id | UUID | セクションID (主キー) |
| section_group_id | UUID | 親グループID |
| start_sec | DECIMAL | 開始秒数 |
| end_sec | DECIMAL | 終了秒数 |
| image_url | TEXT | マークアップ画像URL |
| tags | JSON | 自動タグ配列 |
| markup_json | JSON | 描画オブジェクト |
| coach_comment | TEXT | コーチコメント全文 |
| coach_comment_summary | TEXT | AI要約コメント |

### 4. coaching_reservation (コーチング予約)
| カラム | データ型 | 説明 |
|-------|---------|-----|
| session_id | UUID | セッションID (主キー) |
| user_id | UUID | ユーザーID |
| coach_id | UUID | コーチID |
| session_date | DATETIME | セッション日時 |
| location_type | ENUM | 場所種類 (simulation_golf/real_golf_course) |
| status | ENUM | 予約ステータス |
| price | DECIMAL | 料金 |

## 🏷️ スイング12段階タグ

| 順序 | 日本語ラベル | 自動タグ |
|-----|-------------|---------|
| 1 | アドレス | `address` |
| 2 | テイクバック | `takeaway` |
| 3 | ハーフウェイバック | `halfway_back` |
| 4 | バックスイング | `backswing` |
| 5 | トップ | `top` |
| 6 | 切り返し | `transition` |
| 7 | ダウンスイング | `downswing` |
| 8 | インパクト | `impact` |
| 9 | フォロースイング | `follow_through` |
| 10 | フィニッシュ-1 | `finish_1` |
| 11 | フィニッシュ-2 | `finish_2` |
| 12 | その他 | `other` |

## 🚀 セットアップ手順

### 1. 前提条件
- Docker & Docker Compose インストール済み
- OpenAI APIキー取得済み

### 2. 環境変数設定
```bash
# backend/.env を編集
OPENAI_API_KEY=sk-your-openai-api-key-here

# Azure使用時 (オプション)
STORAGE_TYPE=azure_blob
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
```

### 3. アプリケーション起動
```bash
# 開発環境起動 (バックエンド + フロントエンド)
docker-compose up --build

# プロダクション環境起動 (Nginx含む)
docker-compose --profile production up --build
```

### 4. アクセス確認
- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs
- **Nginx (本番用)**: http://localhost

## 📝 API エンドポイント

### アップロード系
- `POST /api/v1/upload-video` - 動画アップロード
- `POST /api/v1/upload-thumbnail/{video_id}` - サムネイルアップロード
- `DELETE /api/v1/video/{video_id}` - 動画削除

### コーチング系
- `POST /api/v1/create-section-group/{video_id}` - セクショングループ作成
- `POST /api/v1/add-section/{section_group_id}` - スイングセクション追加
- `POST /api/v1/add-coach-comment/{section_id}` - 音声コメント追加
- `PUT /api/v1/update-section/{section_id}` - セクション更新
- `POST /api/v1/analyze-section/{section_id}` - AI分析実行

### ユーザー系
- `GET /api/v1/my-videos` - 動画一覧取得
- `GET /api/v1/video/{video_id}` - 動画詳細取得
- `GET /api/v1/video/{video_id}/with-sections` - セクション付き動画取得
- `GET /api/v1/video/{video_id}/feedback-summary` - フィードバック要約

## 🎯 主要機能

### ユーザー機能
1. **動画アップロード** - ドラッグ&ドロップ対応
2. **クラブ・スイング種類選択** - ドロップダウンメニュー
3. **フィードバック閲覧** - セクション別表示
4. **動画検索・フィルタ** - クラブ種類・フィードバック有無で絞込

### コーチ機能
1. **セクション分割** - 時間指定でスイングを分割
2. **マークアップ画像** - 視覚的な指導画像追加
3. **音声コメント** - Whisperで自動文字起こし
4. **AI要約** - GPTによる自動要約生成
5. **タグ付け** - 12段階スイングフェーズの自動判定

## 🔧 設定オプション

### ストレージ切り替え
```bash
# ローカルストレージ (デフォルト)
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./uploads

# Azure Blob Storage
STORAGE_TYPE=azure_blob
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_STORAGE_CONTAINER=golf-videos
```

### データベース切り替え
```bash
# SQLite (開発用)
DATABASE_URL=sqlite+aiosqlite:///./golf_coaching.db

# Azure MySQL (本番用)
DATABASE_URL=mysql+asyncmy://username:password@hostname:3306/database
```

## 🧪 テスト実行

```bash
# バックエンドテスト
cd backend
python -m pytest tests/

# フロントエンドリント
cd frontend
npm run lint
```

## 📈 今後の拡張予定

- [ ] ユーザー認証・権限管理
- [ ] リアルタイム通知機能
- [ ] 動画ストリーミング最適化
- [ ] モバイルアプリ対応
- [ ] コーチング予約システム連携

## 🤝 開発チーム

- **バックエンド**: FastAPI + AI機能担当
- **フロントエンド**: 本格UI実装担当 (別チーム)
- **インフラ**: Azure環境構築担当

## 📄 ライセンス

このプロジェクトは開発用途として作成されています。