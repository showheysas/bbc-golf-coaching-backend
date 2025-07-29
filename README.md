# ゴルフスイング コーチング管理アプリ

ゴルフスイング動画に対するコーチング用フィードバック管理アプリです。  
ユーザーが動画をアップロード → コーチがシーンごとにマークアップして音声コメント → ユーザーが結果を閲覧する流れをサポートします。

## １．主要機能

### ユーザー機能
1. **動画アップロード** - ドラッグ&ドロップ対応
2. **動画サムネイル** - 自動で生成・保存

### コーチ機能
1. **セクション分割** - 時間指定でスイングを分割
2. **タグ付け** - 12段階スイングフェーズの選択
3. **セクション別画像保存** - タグ付加名称で自動保存
4. **音声コメント** - Whisperで自動文字起こし

## ２．技術スタック

| カテゴリ | 採用ライブラリ／ツール | 主な用途 |
|----------|----------------------|----------|
| **バックエンド** | FastAPI / Pydantic / SQLAlchemy (async) | REST / DTO / ORM |
|  | python‑dotenv | `.env` 読み込み |
|  | azure‑storage‑blob | Blob 操作・SAS URL 発行 |
|  | **FFmpeg + subprocess.run** | 動画 → サムネイル & 静止画キャプチャ |
|  | OpenAI Whisper / GPT‑4o | 音声テキスト化／要約 |
| **スライダーバー & フレームキャプチャ** | HTML `<input type="range">` + `<video>` の `currentTime`<br>Canvas 2D API (`drawImage` → `canvas.toBlob`) | 任意フレームを即時キャプチャし画像生成 |
| **フロント PoC** | Next.js 14 / React 18 / TailwindCSS | UI 実装 |
|  | Axios | API 呼び出し |
| **CI / Dev** | Docker / docker‑compose | ローカル統合／本番ビルド |
|  | Ruff / Black | Lint／整形 |
|  | Pytest | 単体テスト |

## ３．プロジェクト構造

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

## ４．データベーステーブル

### 1. videos（動画情報）
| カラム名 | データ型 | Not Null | 説明 |
|---------|---------|----------|------|
| `video_id`          | `UUID`      | ✅ | 動画ID (PK) |
| `user_id`           | `UUID`      | ✅ | アップロードユーザーID |
| `video_url`         | `TEXT`      | ✅ | 動画ファイルURL |
| `thumbnail_url`     | `TEXT`      |  | サムネイル画像URL |
| `club_type`         | `VARCHAR(50)` |  | 使用クラブ種類 |
| `swing_form`        | `VARCHAR(50)` |  | スイング種類 |
| `swing_note`        | `TEXT`      |  | ユーザーメモ |
| `created_at`        | `DATETIME`  | ✅ | レコード作成日時 |
| `updated_at`        | `DATETIME`  | ✅ | レコード更新日時 |

---

### 2. section_groups（セクショングループ = 動画1本に1行）
| カラム名 | データ型 | Not Null | 説明 |
|---------|---------|----------|------|
| `section_group_id`          | `UUID`     | ✅ | グループID (PK) |
| `video_id`                  | `UUID`     | ✅ | 対応動画ID（videos.video_id 参照） |
| `overall_feedback`          | `TEXT`     |  | コーチ総合コメント全文 |
| `overall_feedback_summary`  | `TEXT`     |  | GPT 要約 (300〜500字) |
| `next_training_menu`        | `TEXT`     |  | 推奨ドリル／練習メニュー全文 |
| `next_training_menu_summary`| `TEXT`     |  | 練習メニュー要約 |
| `feedback_created_at`       | `DATETIME` |  | 音声→要約が完了した時刻 |
| `created_at`                | `DATETIME` | ✅ | レコード作成日時 |
| `updated_at`                | `DATETIME` | ✅ | レコード更新日時 |

---

### 3. swing_sections（スイングセクション）
| カラム名 | データ型 | Not Null | 説明 |
|---------|---------|----------|------|
| `section_id`             | `UUID`       | ✅ | セクションID (PK) |
| `section_group_id`       | `UUID`       | ✅ | 親グループID（section_groups.section_group_id 参照） |
| `start_sec`              | `DECIMAL(6,2)` | ✅ | 開始秒数 |
| `end_sec`                | `DECIMAL(6,2)` | ✅ | 終了秒数 |
| `image_url`              | `TEXT`       |  | マークアップ画像URL |
| `tags`                   | `JSON`       |  | 12段階スイングタグ配列 |
| `markup_json`            | `JSON`       |  | 円・線など描画オブジェクト |
| `coach_comment`          | `TEXT`       |  | コーチコメント全文 |
| `coach_comment_summary`  | `TEXT`       |  | GPT 要約コメント |
| `created_at`             | `DATETIME`   | ✅ | レコード作成日時 |
| `updated_at`             | `DATETIME`   | ✅ | レコード更新日時 |

---

### 4. coaching_reservation（コーチング予約）
| カラム名 | データ型 | Not Null | 説明 |
|---------|---------|----------|------|
| `session_id`   | `UUID`      | ✅ | セッションID (PK) |
| `user_id`      | `UUID`      | ✅ | ユーザーID |
| `coach_id`     | `UUID`      | ✅ | コーチID |
| `session_date` | `DATETIME`  | ✅ | セッション日時 |
| `location_type`| `ENUM('simulation_golf','real_golf_course')` | ✅ | 場所種類 |
| `status`       | `ENUM('reserved','completed','cancelled')` | ✅ | 予約ステータス |
| `price`        | `DECIMAL(10,2)` |  | 料金 |
| `created_at`   | `DATETIME`  | ✅ | レコード作成日時 |
| `updated_at`   | `DATETIME`  | ✅ | レコード更新日時 |

---

> **備考**  
> - 現状の業務ドメインでは上記4テーブルで完結しており、他に隠れたテーブルはありません。  
> - `created_at` / `updated_at` はトリガーではなくアプリケーション側（SQLAlchemy）で自動セットしています。  
> - 今後ユーザー管理や認証を実装する際には、別途 `users` テーブルを追加する想定です。

## ５．スイング12段階タグ

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

## ６. 環境変数一覧

### `.env` の記載例（必須最小セット）

```env
# ---------- Database ----------
DATABASE_URL=sqlite+aiosqlite:///./bbc_test.db
# 例）mysql+asyncmy://user:pass@host:3306/bbc_test?charset=utf8mb4

# ---------- Storage ----------
STORAGE_TYPE=azure_blob
LOCAL_STORAGE_PATH=./uploads
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=blobeastasiafor9th;AccountKey=qIORKvLHjPnn87SNmpnrM8175L4C/5SCwZx/78SrqlBeNbcKoJ5LeaQ1nOlXPieoIexEP8zXpJvh+AStOZ1+Nw==;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER=bbc-test

# ---------- OpenAI ----------
OPENAI_API_KEY=sk-********************************

# ---------- Dummy IDs (PoC 用) ----------
DEFAULT_USER_ID=550e8400-e29b-41d4-a716-446655440000
DEFAULT_COACH_ID=6ba7b810-9dad-11d1-80b4-00c04fd430c8
```

（参考）コードで参照済み（.env.sample 未記載）のキー
FFMPEG_PATH	ffmpeg	FFmpeg 実行パス
| キー                | デフォルト    | 用途          |
| ----------------- | -------- | ----------- |
| `ALLOWED_ORIGINS` | `*`      | CORS 許可ドメイン |
| `FFMPEG_PATH`     | `ffmpeg` | FFmpeg 実行パス |


♯## ストレージ切り替え
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

## ７．API エンドポイント

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


## ８．アプリケーション起動

#### バックエンド（FastAPI）

```bash
# 1) 依存ライブラリのインストール（Python 3.9+、仮想環境推奨）
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows の場合: .venv\Scripts\activate
pip install -r requirements.txt

# 2) 環境変数 .env を配置（backend/.env）
#    OPENAI_API_KEY や DATABASE_URL などを設定済みであることを確認

# 3) 開発サーバ起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# → API      : http://localhost:8000
# → Swagger  : http://localhost:8000/docs
```

#### 3.2 フロントエンド（Next.js）

```bash
# 1) 依存モジュールのインストール
cd frontend
npm install          # または pnpm install / yarn install

# 2) 開発サーバ起動
npm run dev

# → ブラウザで http://localhost:3000 を開く
```

### アクセス確認
- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs

## ９．テスト実行

```bash
# バックエンドテスト
cd backend
python -m pytest tests/

# フロントエンドリント
cd frontend
npm run lint
```

## １０．今後の拡張について

| 機能 | 推奨アーキテクチャ | 補足 |
|------|------------------|------|
| 認証・認可 | FastAPI‑Users + JWT（Access 5 min / Refresh 30 days） | `Depends(current_active_user)` をルーターに追加 |
| Blob 表示時の保護 | 短命 SAS URL (15 分) + JWT で `/media-url` 再発行 | フロントで期限切れを検知し自動リフレッシュ |
| LINE 連携 | LINE Messaging API + `line-bot-sdk-python` | コーチコメント保存完了時に Push |
| **シーン別マークアップ画像** | フロント：Fabric.js などで円・直線描画 → `toBlob()`<br>バックエンド：`/add-section` で画像受信 → Blob 保存 | セクション row に `markup_image_url` 列追加 |
| **アップロード時トリミング** | フロント：`@ffmpeg/ffmpeg` (WASM) or `MediaStreamRecorder` → 切り出し後アップロード<br>バックエンド：通常の `/upload-video` を流用 | クライアント側で処理するためサーバー負荷増なし |

## 📄 ライセンス

このプロジェクトは開発用途として作成されています。
