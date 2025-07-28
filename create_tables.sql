-- Golf Coaching App - 初期設計テーブル構成
-- MySQL用テーブル作成スクリプト

-- データベースの作成 (もし存在しなければ)
CREATE DATABASE IF NOT EXISTS golf_coaching;
USE golf_coaching;

-- 1. videos (動画情報)
CREATE TABLE IF NOT EXISTS videos (
    video_id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    video_url TEXT NOT NULL,
    thumbnail_url TEXT,
    club_type VARCHAR(50),
    swing_form VARCHAR(50),
    swing_note TEXT,
    section_group_id CHAR(36),
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. section_groups (セクショングループ)
CREATE TABLE IF NOT EXISTS section_groups (
    section_group_id CHAR(36) PRIMARY KEY,
    video_id CHAR(36) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
);

-- 3. swing_sections (スイングセクション)
CREATE TABLE IF NOT EXISTS swing_sections (
    section_id CHAR(36) PRIMARY KEY,
    section_group_id CHAR(36) NOT NULL,
    start_sec DECIMAL(6,2) NOT NULL,
    end_sec DECIMAL(6,2) NOT NULL,
    image_url TEXT,
    tags JSON,
    markup_json JSON,
    coach_comment TEXT,
    coach_comment_summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (section_group_id) REFERENCES section_groups(section_group_id) ON DELETE CASCADE
);

-- 4. coaching_reservation (コーチング予約)
CREATE TABLE IF NOT EXISTS coaching_reservation (
    session_id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    coach_id CHAR(36) NOT NULL,
    session_date DATETIME NOT NULL,
    session_time DATETIME NOT NULL,
    location_type ENUM('simulation_golf', 'real_golf_course') NOT NULL,
    location_id CHAR(36) NOT NULL,
    status ENUM('booked', 'completed', 'cancelled') DEFAULT 'booked',
    price DECIMAL(10,2) NOT NULL,
    payment_status ENUM('pending', 'paid') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- インデックスの作成 (パフォーマンス向上のため)
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_videos_upload_date ON videos(upload_date);
CREATE INDEX idx_section_groups_video_id ON section_groups(video_id);
CREATE INDEX idx_swing_sections_section_group_id ON swing_sections(section_group_id);
CREATE INDEX idx_coaching_reservation_user_id ON coaching_reservation(user_id);
CREATE INDEX idx_coaching_reservation_coach_id ON coaching_reservation(coach_id);
CREATE INDEX idx_coaching_reservation_session_date ON coaching_reservation(session_date);

-- 外部キー制約の追加 (videosテーブルのsection_group_id用)
-- ALTER TABLE videos ADD FOREIGN KEY (section_group_id) REFERENCES section_groups(section_group_id) ON DELETE SET NULL;